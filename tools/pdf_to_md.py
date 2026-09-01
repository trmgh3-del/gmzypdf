#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_to_md.py — 将中医 PDF 教材完整转换为结构化、美化的 Markdown。

特性：
- 依据 PDF 书签目录（TOC）生成 Markdown 标题层级，并精确替换正文中对应的标题行；
- 依据版面右边界与行距自动把折行合并为自然段（支持跨页段落）；
- 识别页码、页眉页脚并清除；
- 识别表格并转换为 Markdown 表格；
- 提取插图（按 xref 去重）并以 Markdown 图片语法嵌入对应位置；
- 段首【…】/〔…〕标注自动加粗；清理 CJK 之间多余的空格。

用法：python3 pdf_to_md.py <pdf路径> [更多pdf...] --out <输出目录>
"""

import os
import re
import sys
import unicodedata
import difflib
import pymupdf


# ---------------------------------------------------------------- 常量

# CJK 字符及其常用全角标点的 Unicode 区间（用于“汉字间空格”清理）
CJK_CLASS = (
    "\u2e80-\u2eff\u3000-\u303f\u31c0-\u31ef\u3400-\u4dbf"
    "\u4e00-\u9fff\uf900-\ufaff\uff00-\uff60\uffe0-\uffef"
)
CJK_SPACE_RE = re.compile(rf"(?<=[{CJK_CLASS}]) (?=[{CJK_CLASS}])")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufeff]")
PAGENUM_RE = re.compile(r"^\d{1,4}$")
LIST_MARK_RE = re.compile(
    r"^("
    r"[一二三四五六七八九十百]+、"           # 一、 十一、
    r"|（[一二三四五六七八九十]+）"          # （一）
    r"|\([一二三四五六七八九十]+\)"
    r"|\d{1,2}[.．、]"                       # 1. 1． 1、
    r"|\(\d{1,2}\)"                          # (1)
    r"|【[^】]{1,12}】"                      # 【讲解】
    r"|〔[^〕]{1,12}〕"                      # 〔原文〕
    r")"
)
BOLD_LABEL_RE = re.compile(r"^(【[^】]{1,20}】|〔[^〕]{1,20}〕)")


def norm(s: str) -> str:
    """标题匹配用归一化：全半角统一、去全部空白。"""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[\s　]+", "", s)
    return s


def tidy(s: str) -> str:
    """输出文本美化：去掉控制字符与 CJK 之间的单个多余空格。"""
    s = CONTROL_RE.sub("", s).strip()
    s = CJK_SPACE_RE.sub("", s)
    return s


def is_ascii_edge(prev_tail: str, cur_head: str) -> bool:
    """拼接时若两侧都是西文/数字字符，补一个空格。"""
    if not prev_tail or not cur_head:
        return False
    a, b = prev_tail[-1], cur_head[0]
    return (ord(a) < 128 and not a.isspace()) and (ord(b) < 128 and not b.isspace())


def cell_join(s: str) -> str:
    """表格单元格内的折行合并，并转义竖线。"""
    out = ""
    for p in (s or "").split("\n"):
        p = tidy(p)
        if not p:
            continue
        if out and is_ascii_edge(out, p):
            out += " "
        out += p
    return out.replace("|", "\\|").strip()


# ---------------------------------------------------------------- 版面分析

def get_page_lines(page):
    """提取一页的文本行：list[dict]，按 (y, x) 排序。"""
    out = []
    d = page.get_text("dict", sort=True)
    for b in d["blocks"]:
        if b.get("type") != 0:
            continue
        for line in b["lines"]:
            txt = tidy("".join(s["text"] for s in line["spans"]))
            if not txt:
                continue
            size = max((sp.get("size", 10) for sp in line["spans"]), default=10)
            x0, y0, x1, y1 = line["bbox"]
            out.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1,
                        "size": size, "text": txt})
    out.sort(key=lambda l: (round(l["y0"], 1), l["x0"]))
    return out


def book_stats(pages_lines):
    """全书统计：正文字号、正文右边界、行距中位数。"""
    from collections import Counter
    size_cnt = Counter()
    flat = [l for ls in pages_lines for l in ls]
    for ln in flat:
        size_cnt[round(ln["size"])] += len(ln["text"])
    body_size = float(size_cnt.most_common(1)[0][0]) if size_cnt else 10.0
    xs = sorted(l["x1"] for l in flat if abs(l["size"] - body_size) <= 2)
    right_edge = xs[int(len(xs) * 0.97)] if xs else 500.0
    diffs = []
    for ls in pages_lines:
        for a, b in zip(ls, ls[1:]):
            d = b["y0"] - a["y0"]
            if 0 < d < 3 * body_size:
                diffs.append(d)
    diffs.sort()
    pitch = diffs[len(diffs) // 2] if diffs else body_size * 1.4
    return body_size, right_edge, pitch


def detect_runnings(pages_lines, npages):
    """检测重复出现的页眉/页脚（各页首行或末行的高频重复文本）。"""
    from collections import Counter
    first_cnt = Counter()
    last_cnt = Counter()
    for lines in pages_lines:
        if not lines:
            continue
        first_cnt[norm(lines[0]["text"])] += 1
        last_cnt[norm(lines[-1]["text"])] += 1
    th = max(10, int(0.30 * npages))
    head = {t for t, c in first_cnt.items() if c >= th and t and not t.isdigit()}
    foot = {t for t, c in last_cnt.items() if c >= th and t and not t.isdigit()}
    return head, foot


def tables_overlap(ln, bbox):
    x0, y0, x1, y1 = bbox
    cy = (ln["y0"] + ln["y1"]) / 2
    cx = (ln["x0"] + ln["x1"]) / 2
    return x0 - 2 <= cx <= x1 + 2 and y0 - 2 <= cy <= y1 + 2


def beautify_para(text: str) -> str:
    """段首【…】/〔…〕标注加粗。"""
    m = BOLD_LABEL_RE.match(text)
    if m:
        label = m.group(1)
        return f"**{label}**" + text[len(label):]
    return text


def heading_title_out(title: str) -> str:
    t = tidy(title)
    t = re.sub(rf"(?<=[{CJK_CLASS}])\s+(?=[{CJK_CLASS}])", "", t)
    return t


# 标题候选行中不允许出现的句读符号（顿号除外，标题常含“一、”式顿号）
SENT_PUNCT_RE = re.compile("[。，；！]")


def find_title_line(lines, target):
    """在页内寻找与书签标题对应的文本行：精确→包含→模糊三级匹配。"""
    cands = [ln for ln in lines if not ln.get("_eaten")]
    for ln in cands:
        if norm(ln["text"]) == target:
            return ln
    if not target:
        return None
    L1 = len(target)
    # 包含匹配：标题行被截断、或同行附着小字
    for ln in cands:
        n = norm(ln["text"])
        if not n or SENT_PUNCT_RE.search(ln["text"]):
            continue
        if L1 >= 3 and len(n) <= L1 + 8 and len(n) <= 22 \
                and (target in n or n in target):
            return ln
    # 模糊匹配：书签中的错别字（如 桅子/栀子）
    th = 0.5 if L1 <= 3 else 0.55
    best, best_r = None, 0.0
    for ln in cands:
        n = norm(ln["text"])
        if not n or len(n) > L1 + 6 or SENT_PUNCT_RE.search(ln["text"]):
            continue
        r = difflib.SequenceMatcher(None, target, n).ratio()
        if r >= th and r > best_r:
            best, best_r = ln, r
    return best


def rect_overlap_area(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    w = min(ax1, bx1) - max(ax0, bx0)
    h = min(ay1, by1) - max(ay0, by0)
    return max(w, 0) * max(h, 0)


def find_vector_figures(page, lines, table_bboxes, placed_imgs, body_size=11.0):
    """检测页面上成片的矢量绘图区域（示意图），返回 [(rect, 区域内文本行, 吸附标签)]。

    判据：多个绘图对象的并集区域面积占比足够大、区域内文字行少且短，
    且不与已识别表格、已嵌入位图重叠。区域上下方紧邻（或字号较大的）
    短标签行视为图题一并圈入。
    """
    try:
        drawings = page.get_drawings()
    except Exception:
        return []
    pw, ph = page.rect.width, page.rect.height
    page_area = max(pw * ph, 1)
    rects = []
    for dr in drawings:
        r = dr["rect"]
        if r.width > 3 and r.height > 3 and r.width < pw * 1.2 and r.height < ph * 1.2:
            rects.append([r.x0, r.y0 - 6, r.x1, r.y1 + 6, 1.0])  # 末位: 合并标记
    if len(rects) < 4:
        return []
    # 扩张并迭代合并相交矩形
    merged = True
    while merged:
        merged = False
        out = []
        while rects:
            cur = rects.pop()
            hit = None
            for j, o in enumerate(rects):
                if (min(cur[2], o[2]) - max(cur[0], o[0]) > -4
                        and min(cur[3], o[3]) - max(cur[1], o[1]) > -4):
                    hit = j
                    break
            if hit is None:
                out.append(cur)
            else:
                o = rects.pop(hit)
                out.append([min(cur[0], o[0]), min(cur[1], o[1]),
                            max(cur[2], o[2]), max(cur[3], o[3]), cur[4] + o[4]])
                merged = True
        rects = out
    figs = []
    for r in rects:
        rw, rh = r[2] - r[0], r[3] - r[1]
        area = rw * rh
        if r[4] < 4 or area < page_area * 0.06 or rw < 60 or rh < 60:
            continue
        inside = [ln for ln in lines
                  if r[0] <= (ln["x0"] + ln["x1"]) / 2 <= r[2]
                  and r[1] <= (ln["y0"] + ln["y1"]) / 2 <= r[3]]
        # 吸附紧邻区域上下边缘的短标签/大字图题
        core = len(inside)
        for ln in lines:
            if ln in inside:
                continue
            cx = (ln["x0"] + ln["x1"]) / 2
            if not (r[0] - 12 <= cx <= r[2] + 12):
                continue
            gap = max(r[1] - ln["y1"], ln["y0"] - r[3], 0)
            if gap <= 30 or (ln["size"] >= body_size * 1.25 and gap <= 60):
                inside.append(ln)
        adsorbed = inside[core:]
        # 表格区域不动
        if any(rect_overlap_area(r[:4], tb) > 0.25 * area for tb in table_bboxes):
            continue
        # 已被位图覆盖的区域不动
        if any(rect_overlap_area(r[:4], (im["x0"], im["y0"], im.get("x1", im["x0"]),
                                     im.get("y1", im["y0"]))) > 0.5 * area
               for im in placed_imgs):
            continue
        # 区域内文字应为少量短标签
        if len(inside) > 24:
            continue
        if inside:
            avg_len = sum(min(len(ln["text"]), 40) for ln in inside) / len(inside)
            if avg_len > 14:
                continue
        # 渲染矩形 = 绘图并集 ∪ 吸入行外框，四周留白
        box = pymupdf.Rect(max(r[0] - 5, 0), max(r[1] - 5, 0),
                           min(r[2] + 5, pw), min(r[3] + 5, ph))
        for ln in inside:
            box |= pymupdf.Rect(max(ln["x0"] - 2, 0), max(ln["y0"] - 2, 0),
                                min(ln["x1"] + 2, pw), min(ln["y1"] + 2, ph))
        figs.append((box, inside, adsorbed))
    figs.sort(key=lambda f: f[0].y0)
    return figs



    """在页内寻找与书签标题对应的文本行：精确→包含→模糊三级匹配。"""
    cands = [ln for ln in lines if not ln.get("_eaten")]
    for ln in cands:
        if norm(ln["text"]) == target:
            return ln
    if not target:
        return None
    L1 = len(target)
    # 包含匹配：标题行被截断、或同行附着小字
    for ln in cands:
        n = norm(ln["text"])
        if not n or SENT_PUNCT_RE.search(ln["text"]):
            continue
        if L1 >= 3 and len(n) <= L1 + 8 and len(n) <= 22 \
                and (target in n or n in target):
            return ln
    # 模糊匹配：书签中的错别字（如 桅子/栀子）
    th = 0.5 if L1 <= 3 else 0.55
    best, best_r = None, 0.0
    for ln in cands:
        n = norm(ln["text"])
        if not n or len(n) > L1 + 6 or SENT_PUNCT_RE.search(ln["text"]):
            continue
        r = difflib.SequenceMatcher(None, target, n).ratio()
        if r >= th and r > best_r:
            best, best_r = ln, r
    return best


# ---------------------------------------------------------------- 主转换

def convert(pdf_path, out_dir):
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    os.makedirs(out_dir, exist_ok=True)
    asset_dir = os.path.join(out_dir, "assets", stem)

    doc = pymupdf.open(pdf_path)
    npages = len(doc)
    toc = doc.get_toc(simple=True)  # [level, title, page(1-based)]

    # 1) 逐页取行
    pages_lines = [get_page_lines(doc[i]) for i in range(npages)]

    # 2) 全书统计
    body_size, right_edge, pitch = book_stats(pages_lines)

    # 3) 清理：页码（页首/页末的孤立数字）、重复页眉页脚
    run_head, run_foot = detect_runnings(pages_lines, npages)
    for i in range(npages):
        ls = pages_lines[i]
        h = doc[i].rect.height
        out = []
        for j, ln in enumerate(ls):
            t2 = ln["text"].strip(" ·•-—–_.○◦●…　")
            if PAGENUM_RE.match(t2) and (ln["y1"] < 0.13 * h or ln["y0"] > 0.85 * h
                                         or j == 0 or j == len(ls) - 1):
                continue
            out.append(ln)
        while out and norm(out[0]["text"]) in run_head:
            out.pop(0)
        while out and norm(out[-1]["text"]) in run_foot:
            out.pop()
        pages_lines[i] = out

    # 3.5) 识别并跳过“印刷目录页”：过半行都能匹配书签标题的页面
    title_set = {norm(t) for _, t, _ in toc}
    def is_toc_line(txt):
        n1 = norm(txt)
        if n1 in title_set:
            return True
        n2 = norm(re.sub(r"[.\s·•…]*\d+$", "", txt))
        return bool(n2) and n2 in title_set
    skip_page = [False] * npages
    if title_set:
        for i in range(npages):
            ls = pages_lines[i]
            if len(ls) < 5:
                continue
            hits = sum(1 for ln in ls if is_toc_line(ln["text"]))
            if hits / len(ls) >= 0.5:
                skip_page[i] = True

    # 4) TOC 标题定位：在目标页正文中找到对应行并占据其位置
    headings_by_page = {i: [] for i in range(npages)}
    n_missed = 0
    for lv, title, pg in toc:
        idx = pg - 1
        title_out = heading_title_out(title)
        if not (0 <= idx < npages) or skip_page[idx]:
            n_missed += 1
            continue
        target = norm(title)
        match = find_title_line(pages_lines[idx], target)
        if match is not None:
            match["_eaten"] = True
            headings_by_page[idx].append({"y0": match["y0"] - 0.05,
                                          "level": min(lv, 5),
                                          "title": title_out})
        if match is None and not skip_page[idx]:
            headings_by_page[idx].append({"y0": -1e9, "level": min(lv, 5),
                                          "title": title_out})
            n_missed += 1

    # 5) 图片提取（全书 xref 去重）
    img_files = {}
    img_items_by_page = {i: [] for i in range(npages)}
    for pno in range(npages):
        try:
            infos = doc[pno].get_image_info(xrefs=True)
        except Exception:
            infos = []
        for info in infos:
            xref = info["xref"]
            x0, y0, x1, y1 = info["bbox"]
            if (x1 - x0) < 40 or (y1 - y0) < 40:
                continue  # 装饰小图忽略
            if xref and xref not in img_files:
                try:
                    ext_img = doc.extract_image(xref)
                    data, ext = ext_img["image"], ext_img["ext"]
                    if ext not in ("png", "jpg", "jpeg", "gif", "webp", "bmp"):
                        pix = pymupdf.Pixmap(doc, xref)
                        if pix.colorspace and pix.colorspace.n > 3:
                            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                        data = pix.tobytes("png")
                        ext = "png"
                    os.makedirs(asset_dir, exist_ok=True)
                    fname = f"img-{xref}.{ext}"
                    with open(os.path.join(asset_dir, fname), "wb") as f:
                        f.write(data)
                    img_files[xref] = fname
                except Exception as e:
                    print(f"  [warn] 图片提取失败 xref={xref}: {e}", file=sys.stderr)
            if xref in img_files:
                rel = f"assets/{stem}/{img_files[xref]}"
                img_items_by_page[pno].append({"y0": y0, "x0": x0,
                                               "x1": x1, "y1": y1, "rel": rel})

    # 6) 表格识别
    table_items_by_page = {i: [] for i in range(npages)}
    table_bboxes_by_page = {i: [] for i in range(npages)}
    for pno in range(npages):
        page = doc[pno]
        try:
            finder = page.find_tables()
        except Exception:
            continue
        for t in finder.tables:
            rows = t.extract()
            if len(rows) < 2 or not rows or len(rows[0]) < 2:
                continue
            nonempty = sum(1 for r in rows for c in r if (c or "").strip())
            if nonempty < 4:
                continue
            header = [cell_join(c) for c in rows[0]]
            md_rows = ["| " + " | ".join(header) + " |",
                       "|" + "|".join([" --- "] * len(header)) + "|"]
            seen_rows = {tuple(header)}
            for r in rows[1:]:
                r = list(r) + [None] * (len(header) - len(r))
                cells = [cell_join(c) for c in r[:len(header)]]
                if not any(cells):
                    continue  # 丢弃整行空单元格
                key = tuple(cells)
                if key in seen_rows:
                    continue  # 丢弃重复行（长表中重复出现的次级表头）
                seen_rows.add(key)
                md_rows.append("| " + " | ".join(cells) + " |")
            if len(md_rows) <= 2:
                continue
            for ln in pages_lines[pno]:
                if tables_overlap(ln, t.bbox):
                    ln["_table"] = True
            table_items_by_page[pno].append({"y0": t.bbox[1], "md": "\n".join(md_rows)})
            table_bboxes_by_page[pno].append(t.bbox)
        pages_lines[pno] = [ln for ln in pages_lines[pno] if not ln.get("_table")]

    # 6.5) 矢量图形区域：整片绘制图形（非表格）渲染为图片，避免图中文字散落
    n_figs = 0
    for pno in range(npages):
        page = doc[pno]
        figs = find_vector_figures(page, pages_lines[pno],
                                   table_bboxes_by_page[pno],
                                   img_items_by_page[pno], body_size)
        for rect, inside, adsorbed in figs:
            os.makedirs(asset_dir, exist_ok=True)
            fname = f"fig-p{pno + 1}-{n_figs}.png"
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=rect)
            with open(os.path.join(asset_dir, fname), "wb") as f:
                f.write(pix.tobytes("png"))
            n_figs += 1
            for ln in inside:
                ln["_fig"] = True
            alt = " ".join(ln["text"] for ln in adsorbed) or "插图"
            img_items_by_page[pno].append(
                {"y0": rect.y0 - 0.1, "x0": rect.x0, "rel": f"assets/{stem}/{fname}",
                 "alt": alt})
        if figs:
            pages_lines[pno] = [ln for ln in pages_lines[pno] if not ln.get("_fig")]

    # 7) 组装 Markdown
    out = []

    def flush_para(buf):
        if not buf:
            return
        joined = buf[0]["text"]
        for ln in buf[1:]:
            if is_ascii_edge(joined, ln["text"]):
                joined += " "
            joined += ln["text"]
        out.append(beautify_para(joined))

    para = []
    join_prev = None

    for pno in range(npages):
        if skip_page[pno]:
            flush_para(para)
            para = []
            join_prev = None
            continue
        items = []
        for ln in pages_lines[pno]:
            if ln.get("_eaten"):
                continue
            items.append(("line", ln["y0"], ln["x0"], ln))
        for hinfo in headings_by_page[pno]:
            items.append(("head", hinfo["y0"], 0.0, hinfo))
        for iinfo in img_items_by_page[pno]:
            items.append(("img", iinfo["y0"], iinfo["x0"], iinfo))
        for tinfo in table_items_by_page[pno]:
            items.append(("table", tinfo["y0"], -1.0, tinfo))
        items.sort(key=lambda it: (it[1], it[2], 0 if it[0] != "line" else 1))

        first_item = True
        for kind, y0, x0, obj in items:
            if kind == "head":
                flush_para(para)
                para = []
                join_prev = None
                out.append("#" * (obj["level"] + 1) + " " + obj["title"])
                first_item = False
                continue
            if kind == "img":
                flush_para(para)
                para = []
                join_prev = None
                alt = obj.get("alt") or "插图"
                out.append(f"![{alt}]({obj['rel']})")
                first_item = False
                continue
            if kind == "table":
                flush_para(para)
                para = []
                join_prev = None
                out.append(obj["md"])
                first_item = False
                continue
            ln = obj
            if para and join_prev is not None:
                prev = join_prev
                # 字号突变（如插图内的大字标题）不并入上一段
                big_diff = max(ln["size"], prev["size"]) / max(min(ln["size"], prev["size"]), 1e-6) > 1.5
                full = prev["x1"] >= right_edge - max(2.2 * prev["size"], 18) and not big_diff
                starts_list = LIST_MARK_RE.match(ln["text"])
                if first_item:
                    # 跨页续段：上一页末行顶格排满，则本页首行与之相接
                    cont = full and not starts_list
                else:
                    gap = ln["y0"] - prev["y0"]
                    cont = (full and 0 < gap <= pitch * 1.45
                            and not starts_list
                            and ln["x0"] <= prev["x0"] + prev["size"] * 1.5)
                if cont:
                    para.append(ln)
                else:
                    flush_para(para)
                    para = [ln]
            else:
                para.append(ln)
            join_prev = ln
            first_item = False

    flush_para(para)

    # 8) 后处理：合并相邻同表头表格（跨页长表）；去除连续重复图片
    merged = []
    for chunk in out:
        if merged:
            prev = merged[-1]
            if (prev.startswith("| ") and chunk.startswith("| ")):
                ph = prev.split("\n", 1)[0]
                ch = chunk.split("\n", 1)[0]
                if ph == ch:
                    merged[-1] = prev + "\n" + "\n".join(chunk.split("\n")[2:])
                    continue
            if prev == chunk and chunk.startswith("!["):
                continue
        merged.append(chunk)
    out = merged

    # 9) 输出
    title = re.sub(r"^\d+", "", stem).strip() or stem
    final = f"# {title}\n\n" + "\n\n".join(out) + "\n"
    final = re.sub(r"\n{3,}", "\n\n", final)

    out_path = os.path.join(out_dir, f"{stem}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(final)
    n_head = sum(len(v) for v in headings_by_page.values())
    n_tab = sum(len(v) for v in table_items_by_page.values())
    print(f"[ok] {stem}: {npages}页 -> {out_path} | 标题{n_head} 图片{len(img_files) + n_figs} "
          f"表格{n_tab} 未定位标题{n_missed}")
    doc.close()
    return out_path


def main():
    args = sys.argv[1:]
    out_dir = "md"
    if "--out" in args:
        i = args.index("--out")
        out_dir = args[i + 1]
        args = args[:i] + args[i + 2:]
    if not args:
        print("usage: pdf_to_md.py <pdf...> --out <dir>")
        sys.exit(1)
    for pdf in args:
        try:
            convert(pdf, out_dir)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[fail] {pdf}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
