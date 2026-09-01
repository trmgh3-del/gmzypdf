#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_app_data.py — 将 md/ 目录中的 26 部 Markdown 医书编译为 UniApp 数据包。

输出：
  gmzy-app/static/books-data/catalog.json     书目总录（书名/封面/章节数/字数/摘要）
  gmzy-app/static/books-data/<slug>.json      每本书的章节与内容块（运行时按需读取）
  gmzy-app/static/books/<slug>/               每本书的图片资源

块类型（紧凑字段）：
  {"t":"h","l":2,"x":"标题","g":12}         标题（l=2..6，g=全局块序号）
  {"t":"p","segs":[{"x":"文本","b":1},...]} 段落（segs 支持加粗片段）
  {"t":"img","s":"img-x.jpeg","a":"说明"}   图片
  {"t":"tbl","h":["表头"],"r":[[...]]}      表格
"""

import os
import re
import json
import shutil
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_DIR = os.path.join(ROOT, "md")
APP_DIR = os.path.join(ROOT, "gmzy-app")
BOOKS_DIR = os.path.join(APP_DIR, "static", "books-data")
STATIC_DIR = os.path.join(APP_DIR, "static", "books")

IMG_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


def slug_of(stem: str) -> str:
    m = re.match(r"^(\d+)", stem)
    return m.group(1) if m else stem


def assign_slugs(stems):
    """数字书号重复时追加 b/c 后缀，保证 slug 唯一且稳定（按文件名排序）。"""
    from collections import defaultdict
    groups = defaultdict(list)
    for s in stems:
        groups[slug_of(s)].append(s)
    mapping = {}
    for base, names in groups.items():
        names.sort()
        for i, name in enumerate(names):
            mapping[name] = base if i == 0 else base + chr(ord("a") + i)
    return mapping


def parse_md(stem, text):
    """将 markdown 文本解析为 blocks 列表。"""
    blocks = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        s = line.strip()
        if not s:
            i += 1
            continue
        m = HEAD_RE.match(s)
        if m:
            lv = len(m.group(1))
            blocks.append({"t": "h", "l": lv, "x": m.group(2).strip()})
            i += 1
            continue
        mi = IMG_RE.match(s)
        if mi:
            alt, src = mi.group(1), mi.group(2)
            fname = src.split("/")[-1]
            blocks.append({"t": "img", "s": fname, "a": alt or "插图"})
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [c.strip().replace("\\|", "|")
                       for c in lines[i].strip().strip("|").split("|")]
                rows.append(row)
                i += 1
            # 去掉分隔行（---）
            rows = [r for r in rows if any(re.sub(r"[-:\s]", "", c) for c in r)]
            if rows:
                blocks.append({"t": "tbl", "h": rows[0], "r": rows[1:]})
            continue
        # 普通段落：拆分 **加粗** 片段
        segs = []
        pos = 0
        for mb in BOLD_RE.finditer(s):
            if mb.start() > pos:
                segs.append({"x": s[pos:mb.start()]})
            segs.append({"x": mb.group(1), "b": 1})
            pos = mb.end()
        if pos < len(s):
            segs.append({"x": s[pos:]})
        if segs:
            blocks.append({"t": "p", "segs": segs})
        i += 1
    return blocks


def split_chapters(blocks, max_blocks=700):
    """在 H2 处切分章节（存 blocks 索引区间 [s,e)）；超长章节按 H3 或块数硬切。"""
    idxs = [i for i, b in enumerate(blocks) if b["t"] == "h" and b["l"] <= 2]
    bounds = [0] + idxs + [len(blocks)]
    chapters = []
    for s, e in zip(bounds, bounds[1:]):
        b0 = blocks[s]
        if s == 0 and not (b0["t"] == "h" and b0["l"] <= 2):
            chapters.append({"title": "卷首", "level": 0, "s": s, "e": e})
        else:
            chapters.append({"title": b0["x"], "level": b0["l"], "s": s, "e": e})
    # 二次切分超长章节
    out = []
    for ch in chapters:
        if ch["e"] - ch["s"] <= max_blocks:
            out.append(ch)
            continue
        cur_s = ch["s"]
        for i in range(ch["s"], ch["e"]):
            b = blocks[i]
            if i - cur_s >= max_blocks and b["t"] == "h" and b["l"] <= 3:
                out.append({"title": blocks[cur_s]["x"] if blocks[cur_s]["t"] == "h"
                            else ch["title"], "level": ch["level"], "s": cur_s, "e": i})
                cur_s = i
            elif i - cur_s >= int(max_blocks * 1.5):
                out.append({"title": ch["title"] + "（续）", "level": ch["level"],
                            "s": cur_s, "e": i})
                cur_s = i
        out.append({"title": blocks[cur_s]["x"] if blocks[cur_s]["t"] == "h"
                    else ch["title"], "level": ch["level"], "s": cur_s, "e": ch["e"]})
    return [c for c in out if c["e"] > c["s"]]


def attach_heading_tree(blocks):
    """目录抽屉：从 blocks 中提取标题树（含全局块序号）。"""
    tree = []
    stack = []
    for gi, b in enumerate(blocks):
        if b["t"] != "h":
            continue
        node = {"x": b["x"], "l": b["l"], "g": gi, "c": []}
        while stack and stack[-1]["l"] >= b["l"]:
            stack.pop()
        if stack:
            stack[-1]["c"].append(node)
        else:
            tree.append(node)
        stack.append(node)
    return tree


def count_chars(blocks):
    n = 0
    for b in blocks:
        if b["t"] == "p":
            n += sum(len(s["x"]) for s in b["segs"])
        elif b["t"] == "h":
            n += len(b["x"])
        elif b["t"] == "tbl":
            n += sum(len(c) for r in ([b["h"]] + b["r"]) for c in r)
    return n


def first_excerpt(blocks, limit=90):
    for b in blocks:
        if b["t"] == "p":
            t = "".join(s["x"] for s in b["segs"]).strip()
            if len(t) >= 30:
                return t[:limit] + ("…" if len(t) > limit else "")
    return ""


def main():
    os.makedirs(BOOKS_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)

    catalog = []
    stems = [os.path.splitext(os.path.basename(p))[0]
             for p in sorted(glob.glob(os.path.join(MD_DIR, "*.md")))]
    slug_map = assign_slugs(stems)
    for stem in stems:
        md_path = os.path.join(MD_DIR, stem + ".md")
        slug = slug_map[stem]
        title = re.sub(r"^\d+", "", stem).strip() or stem
        with open(md_path, encoding="utf-8") as f:
            text = f.read()
        blocks = parse_md(stem, text)
        tree = attach_heading_tree(blocks)
        chapters = split_chapters(blocks)

        # 图片拷贝
        src_assets = os.path.join(MD_DIR, "assets", stem)
        dst_assets = os.path.join(STATIC_DIR, slug)
        cover = None
        if os.path.isdir(src_assets):
            os.makedirs(dst_assets, exist_ok=True)
            for fn in os.listdir(src_assets):
                shutil.copy2(os.path.join(src_assets, fn),
                             os.path.join(dst_assets, fn))
        for b in blocks:
            if b["t"] == "img":
                if cover is None and os.path.exists(os.path.join(dst_assets, b["s"])):
                    cover = f"static/books/{slug}/{b['s']}"
                break

        book = {
            "slug": slug,
            "stem": stem,
            "title": title,
            "chapters": chapters,
            "tree": tree,
            "blocks": blocks,
        }
        with open(os.path.join(BOOKS_DIR, f"{slug}.json"), "w", encoding="utf-8") as f:
            json.dump(book, f, ensure_ascii=False, separators=(",", ":"))

        catalog.append({
            "slug": slug,
            "stem": stem,
            "title": title,
            "cover": cover,
            "chars": count_chars(blocks),
            "chapters": len(chapters),
            "blocks": len(blocks),
            "excerpt": first_excerpt(blocks),
        })
        print(f"[book] {slug:>4} {title:<12} blocks={len(blocks):6d} "
              f"chapters={len(chapters):3d} cover={'Y' if cover else 'N'}")

    # 排序：按书号（数字）+名称
    def sort_key(c):
        m = re.match(r"^(\d+)", c["stem"])
        return (int(m.group(1)) if m else 9999, c["stem"])
    catalog.sort(key=sort_key)

    with open(os.path.join(BOOKS_DIR, "catalog.json"), "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[ok] catalog.json: {len(catalog)} 本书")


if __name__ == "__main__":
    main()
