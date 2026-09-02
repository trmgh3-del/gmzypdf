#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_learn_data.py — 从 md/ 提取学习系统数据（含原文锚点）：

输出（写入 gmzy-app/static/learn/ 与 gmzy-app/static/quiz/）：
  decks.json          记忆卡包总录
  deck-<id>.json      记忆卡（front/sub/back/meta{deck,book,g}）
  index.json + <书>.json  各书复习思考题题库（chapter/q/g/book）

锚点：book = catalog slug，g = 书籍内容块序号，可直接跳
      /pages/reader/reader?slug=<book>&g=<g> 定位原文。

卡片来源：
  deck-fangji.json  方剂卡（29方剂讲解：### 方名《出处》+〔组成〕〔讲解〕〔临证应用〕）
  deck-herb.json    中药卡（14本草备要讲解：#### 药名 +〔原文〕【讲解】【临证应用】）
  deck-point.json   穴位卡（21针灸学三册：###### 穴名 +〔定位〕〔主治〕）
  deck-koujue.json  口诀卡（7中药诊断方剂口诀：分节歌诀）
"""

import os
import re
import json
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_DIR = os.path.join(ROOT, "md")
DATA_DIR = os.path.join(ROOT, "gmzy-app", "static", "books-data")
LEARN_DIR = os.path.join(ROOT, "gmzy-app", "static", "learn")
QUIZ_DIR = os.path.join(ROOT, "gmzy-app", "static", "quiz")

HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def read(stem):
    with open(os.path.join(MD_DIR, stem + ".md"), encoding="utf-8") as f:
        return f.read()


def blocks_of(text):
    """md → [(kind, level, text)]，kind: h|p；label 保留 ** 标注。"""
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        m = HEAD_RE.match(s)
        if m:
            out.append(("h", len(m.group(1)), m.group(2).strip()))
        elif s.startswith("|") or s.startswith("!["):
            continue
        else:
            out.append(("p", 0, s))
    return out


def plain(t):
    t = re.sub(r"\*\*", "", t).strip()
    return re.sub(r"^(【[^】]{1,20}】|〔[^〕]{1,20}〕)\s*", "", t).strip()


def label_of(t):
    m = re.match(r"^\*\*(【[^】]{1,20}】|〔[^〕]{1,20}〕)\*\*", t)
    return m.group(1) if m else None


def trunc(t, n):
    t = t.strip()
    return t if len(t) <= n else t[: n - 1] + "…"


# ---------------- 原文锚点 ----------------
def norm(s):
    return re.sub(r"\s+", "", re.sub(r"\*\*", "", s))


def crc(s):
    """稳定短散列，用于卡片/题目稳定 uuid。"""
    import zlib
    return format(zlib.crc32(s.encode("utf-8")) & 0xFFFFFFFF, "08x")


def block_text(b):
    if "x" in b:
        return b["x"]
    if "segs" in b:
        return "".join(seg.get("x", "") for seg in b["segs"])
    return ""


class Anchor:
    """把 md 块顺序映射到 books-data json 块序号（双向顺序一致，游标前进）。"""

    def __init__(self, stem, slug):
        self.stem = stem
        self.slug = slug
        with open(os.path.join(DATA_DIR, slug + ".json"), encoding="utf-8") as f:
            self.blocks = json.load(f)["blocks"]
        self.cursor = 0
        self.miss = 0

    def find(self, kind, md_text):
        want = norm(md_text)
        if not want:
            return None
        n = len(self.blocks)
        for i in range(self.cursor, min(n, self.cursor + 3000)):
            b = self.blocks[i]
            if b.get("t") != kind:
                continue
            if norm(block_text(b)) == want:
                self.cursor = i + 1
                return i
        self.miss += 1
        return None


_STEM2SLUG = None


def stem2slug(stem):
    global _STEM2SLUG
    if _STEM2SLUG is None:
        with open(os.path.join(DATA_DIR, "catalog.json"), encoding="utf-8") as f:
            _STEM2SLUG = {b["stem"]: b["slug"] for b in json.load(f)}
    return _STEM2SLUG.get(stem)


# ---------------- 带标签段落收集（支持标签独占行 & 续段） ----------------
def collect_parts(blks, start, wanted):
    """扫一个节内的段落，返回 {label: body}；未到下一个标题为止。

    规则：标签行的标签后文本为该 label 首段；若标签独占行则正文取后续段；
    之后的无标签段落并入当前 label（换行拼接）。
    """
    parts = {}
    cur = None
    j = start
    while j < len(blks) and blks[j][0] != "h":
        txt = blks[j][2]
        lab = label_of(txt)
        if lab:
            cur = lab if lab in wanted else None
            if cur and not parts.get(cur):
                body = re.sub(r"^\*\*(【[^】]{1,20}】|〔[^〕]{1,20}〕)\*\*\s*", "", txt).strip()
                body = re.sub(r"\*\*", "", body)
                parts[cur] = body
            j += 1
            continue
        if cur and parts.get(cur) is not None:
            body = re.sub(r"\*\*", "", txt).strip()
            if body:
                parts[cur] = (parts[cur] + "\n" + body).strip()
        j += 1
    return parts, j


# ---------------- 方剂卡 ----------------
def deck_fangji():
    stem = "29方剂讲解"
    slug = stem2slug(stem)
    anch = Anchor(stem, slug)
    blks = blocks_of(read(stem))
    cards = []
    i = 0
    cur_cat = ""
    while i < len(blks):
        kind, lv, t = blks[i]
        if kind == "h" and lv <= 2:
            cur_cat = t
        if kind == "h" and lv == 3 and re.search(r"《[^》]+》", t):
            name = re.sub(r"《[^》]+》.*$", "", t).strip()
            src = (re.search(r"《([^》]+)》", t) or [None, ""])[1]
            parts, j = collect_parts(blks, i + 1, ("〔组成〕", "〔讲解〕", "〔临证应用〕"))
            comp, jiang, lin = parts.get("〔组成〕"), parts.get("〔讲解〕", ""), parts.get("〔临证应用〕", "")
            if comp:
                zhu = ""
                for cand in (jiang, lin):
                    cand = cand.replace("\n", "")
                    m = re.search(r"(本方主治[^。；]*|具[^。]{0,40}效。?)[。；]?", cand)
                    if m:
                        zhu = m.group(0).rstrip("。；")
                        break
                back = "〔组成〕" + trunc(comp.replace("\n", ""), 110)
                if zhu:
                    back += "\n〔主治〕" + trunc(zhu, 60)
                cards.append({
                    "front": name,
                    "sub": f"《{src}》" if src else cur_cat,
                    "back": back,
                    "meta": {"deck": "fangji", "book": slug, "g": anch.find("h", t), "uuid": "fangji:" + crc(name + "|" + back)}
                })
            i = j
            continue
        i += 1
    print(f"  [锚点miss:{anch.miss}]", end=" ")
    return cards


# ---------------- 中药卡 ----------------
def deck_herb():
    stem = "14本草备要讲解"
    slug = stem2slug(stem)
    anch = Anchor(stem, slug)
    blks = blocks_of(read(stem))
    cards = []
    cur_ch = cur_sec = ""
    i = 0
    while i < len(blks):
        kind, lv, t = blks[i]
        if kind == "h" and lv == 2:
            cur_ch = t
        if kind == "h" and lv == 3:
            cur_sec = t
        if kind == "h" and lv == 4:
            name = re.split(r"[（(]", t)[0].strip()
            if not name or len(name) > 8 or re.search(r"[第章节\s]", name):
                i += 1
                continue
            parts, j = collect_parts(blks, i + 1, ("〔原文〕", "【讲解】", "〔讲解〕", "【临证应用】"))
            yuan = parts.get("〔原文〕", "")
            jiang = parts.get("【讲解】") or parts.get("〔讲解〕", "")
            lin = parts.get("【临证应用】", "")
            body = []
            if yuan:
                body.append("〔性味原文〕" + trunc(yuan.replace("\n", "").split("。")[0] + "。", 60))
            if jiang:
                # 讲解=脚注+正文的，跳到正文首句起
                jiang_clean = jiang.replace("\n", "")
                m = re.split(r"(?<=。)(?=[\u4e00-\u9fff])", jiang_clean)
                if len(m) >= 2 and (m[0].startswith("（") or len(m[0]) < 16):
                    jiang_clean = "".join(m[1:])
                body.append(trunc(jiang_clean, 200))
            elif lin:
                body.append(trunc(lin.replace("\n", ""), 200))
            if body:
                cards.append({
                    "front": name,
                    "sub": cur_sec.replace("节", "节·") if cur_sec else cur_ch,
                    "back": "\n".join(body),
                    "meta": {"deck": "herb", "book": slug, "g": anch.find("h", t), "uuid": "herb:" + crc(name + "|" + "\n".join(body))}
                })
            i = j
            continue
        i += 1
    print(f"  [锚点miss:{anch.miss}]", end=" ")
    return cards


# ---------------- 穴位卡 ----------------
def deck_point():
    cards = []
    for stem in ["21针灸学-上", "21针灸学-中", "21针灸学-下"]:
        slug = stem2slug(stem)
        anch = Anchor(stem, slug)
        blks = blocks_of(read(stem))
        cur_mer = ""
        i = 0
        while i < len(blks):
            kind, lv, t = blks[i]
            if kind == "h" and lv == 4 and "经" in t:
                cur_mer = re.sub(r"（[^）]*）", "", t)
            if kind == "h" and lv >= 5:
                name = t.strip()
                if not name or len(name) > 6 or re.search(r"[第章节、\d]", name):
                    i += 1
                    continue
                parts, j = collect_parts(blks, i + 1, ("〔定位〕", "〔主治〕"))
                loc, zhu = parts.get("〔定位〕"), parts.get("〔主治〕")
                if loc and zhu:
                    loc = re.sub(r"（图[^）]*）", "", loc).replace("\n", "")
                    cards.append({
                        "front": name,
                        "sub": cur_mer,
                        "back": "〔定位〕" + trunc(loc, 70) + "\n〔主治〕" + trunc(zhu.replace("\n", ""), 70),
                        "meta": {"deck": "point", "book": slug, "g": anch.find("h", t), "uuid": "point:" + crc(slug + name + "|" + loc + zhu)}
                    })
                    i = j
                    continue
            i += 1
        print(f"{stem.split('-')[1]}[miss:{anch.miss}]", end=" ")
    return cards


# ---------------- 病证·方药卡（16外科学 / 19妇科学 / 20儿科学） ----------------
def _extract_case(blks, i, stop_pat, mcase):
    """从 i 之后收集 证候/治法/方例（药），遇到标题或下一编号条目停止。"""
    zhenghou = zhifa = fang = ""
    j = i + 1
    end = min(len(blks), i + 14)
    while j < end and blks[j][0] == "p":
        tt = blks[j][2].strip()
        if not tt:
            j += 1
            continue
        if (mcase and mcase.match(tt)) or (stop_pat and stop_pat.match(tt)):
            break
        if tt.startswith("证候"):
            zhenghou = re.sub(r"^证候[:：]?\s*", "", tt)
        elif tt.startswith("治法"):
            zhifa = re.sub(r"^治法[:：]?\s*", "", tt).rstrip("。")
        elif tt.startswith(("方例", "方药", "验方", "处方")):
            fang = re.sub(r"^(方例|方药|验方|处方)[:：]?\s*", "", tt).rstrip("。")
        elif zhenghou and not zhifa and len(tt) < 110:
            zhenghou += tt
        j += 1
    return zhenghou, zhifa, fang


def deck_bingz():
    """病 → 证型 → 证候/治法/方药。
    - inline(16外科)：『N.××证：证候…』内联式（治法：、方药：同段）
    - block(20儿科)：『N.证型名：』起头，后跟 证候：…治法：…方例：…
    - gyn(19妇科)：L1『N.类别：』下兼有直接卡与子项『（n）××证：』系列"""
    decks = []
    plans = (("16中医外科学", "inline"), ("19中医妇科学", "gyn"), ("20中医儿科学", "block"))
    for stem, mode in plans:
        slug = stem2slug(stem)
        anch = Anchor(stem, slug)
        blks = blocks_of(read(stem))
        cards = []
        cur_bing = cur_chap = ""
        mcase_inline = re.compile(r"^\d{1,2}[.．、]\s*(.{1,16}?证)[:：](.*)$")
        mcase_block = re.compile(r"^(\d{1,2})[.．、]\s*([^：:]{1,12})[:：]\s*$")
        mcase_l1 = mcase_block
        mcase_sub = re.compile(r"^[（(]\d{1,2}[)）]\s*(.{1,14}?证)[:：]\s*$")
        i = 0
        while i < len(blks):
            kind, lv, t = blks[i]
            if kind == "h":
                if lv == 2:
                    cur_chap = t
                elif lv == 3:
                    cur_bing = re.sub(r"^第[一二三四五六七八九十\d]+[章节]", "", t).split("（")[0].strip()
                i += 1
                continue
            if not cur_bing or not t:
                i += 1
                continue
            front = zhenghou = zhifa = fang = ""
            g0 = None
            if mode == "inline":
                m = mcase_inline.match(t)
                if m:
                    xing, zhenghou = m.group(1).strip(), m.group(2).strip()
                    g0 = anch.find("p", t)
                    found = False
                    j = i + 1
                    while j < len(blks) and blks[j][0] != "h" and j - i <= 14:
                        tt = blks[j][2].strip()
                        if tt.startswith("治法"):
                            zhifa = re.sub(r"^治法[:：]?\s*", "", tt).rstrip("。")
                            k = j + 1
                            while k < len(blks) and blks[k][0] == "p" and k - j <= 4:
                                tf = blks[k][2].strip()
                                if tf.startswith("方药"):
                                    fang = re.sub(r"^方药[:：]?\s*", "", tf).rstrip("。")
                                break
                            found = True
                            break
                        if len(tt) < 60 and not label_of(tt):
                            zhenghou += tt
                        j += 1
                    if zhifa and fang and zhenghou:
                        front = f"{cur_bing}·{xing}"
            elif mode == "block":
                m = mcase_block.match(t)
                if m:
                    xing = m.group(2).strip()
                    g0 = anch.find("p", t)
                    zhenghou, zhifa, fang = _extract_case(blks, i, mcase_block, mcase_block)
                    if zhifa and fang and zhenghou:
                        front = f"{cur_bing}·{xing}"
            else:  # gyn
                m1 = mcase_l1.match(t)
                if m1:
                    cat = m1.group(2).strip().rstrip("证")
                    g0 = anch.find("p", t)
                    # 子项 （n）××证： 系列
                    subs = []
                    j = i + 1
                    while j < len(blks) and blks[j][0] == "p" and j - i <= 40:
                        tt = blks[j][2].strip()
                        ms = mcase_sub.match(tt)
                        if ms:
                            zh, zf, fa = _extract_case(blks, j, mcase_sub, mcase_l1)
                            if zh and zf and fa:
                                subs.append((ms.group(1).strip(), zh, zf, fa, anch.find("p", tt)))
                        elif mcase_l1.match(tt):
                            break
                        j += 1
                    for xing, zh, zf, fa, gg in subs:
                        fr = f"{cur_bing}·{cat}{xing}"
                        back = f"【证候】{trunc(zh, 90)}\n【治法】{trunc(zf, 40)}\n【方药】{trunc(fa, 70)}"
                        cards.append({
                            "front": fr, "sub": f"{stem}·{cur_chap}", "back": back,
                            "meta": {"deck": "bingz", "book": slug, "g": gg,
                                     "uuid": "bingz:" + crc(fr + "|" + back)}
                        })
                    if subs:
                        i += 1
                        continue
                    # 无子项：L1 自身为卡（如 3.脾虚：）
                    zhenghou, zhifa, fang = _extract_case(blks, i, mcase_l1, mcase_l1)
                    if zhifa and fang and zhenghou:
                        front = f"{cur_bing}·{cat}证"
            if front:
                back = f"【证候】{trunc(zhenghou, 90)}\n【治法】{trunc(zhifa, 40)}\n【方药】{trunc(fang, 70)}"
                cards.append({
                    "front": front, "sub": f"{stem}·{cur_chap}", "back": back,
                    "meta": {"deck": "bingz", "book": slug, "g": g0,
                             "uuid": "bingz:" + crc(front + "|" + back)}
                })
            i += 1
        print(f"  [{stem} {len(cards)}张 锚点miss:{anch.miss}]", end=" ")
        decks.extend(cards)
    return decks


# ---------------- 医案卡（23名医医案选读：读案猜证） ----------------
def deck_yian():
    """每案一张：front=案名+主诉首尾，back=〔评按〕精要（猜证自测）。"""
    stem = "23名医医案选读"
    slug = stem2slug(stem)
    anch = Anchor(stem, slug)
    blks = blocks_of(read(stem))
    cards = []
    cur_chap = ""
    i = 0
    mh3 = re.compile(r"^\d+\.\d+\s+(.+案)$")
    while i < len(blks):
        kind, lv, t = blks[i]
        if kind == "h" and lv == 2:
            cur_chap = re.sub(r"^第[一二三四五六七八九十\d]+章", "", t).strip()
            i += 1
            continue
        # h3 标题本身就是案名
        if kind == "h" and lv == 3:
            m = mh3.match(t)
            if not m:
                i += 1
                continue
            aname = m.group(1).strip()
            g0 = anch.find("h", t)
            # 收集本案块
            brief = ""
            pja = ""
            got = 0
            j = i + 1
            while j < len(blks) and not (blks[j][0] == "h" and blks[j][1] <= 3):
                tt = blks[j][2].strip()
                if not brief and tt and not tt.startswith(("〔", "【")) and len(tt) > 14:
                    brief = tt
                    got += 1
                if "〔评按〕" in tt or "【评按】 " in tt or tt.startswith("**〔评按〕"):
                    pja = re.sub(r"\*|\[|\]|〔评按〕|【评按】|〈|〉", "", tt).strip()
                if pja and "《" in tt and "页" in tt:
                    pass
                j += 1
            if pja and brief and len(brief) > 20:
                brief = re.sub(r"^(.{0,6}，(男|女)，[0-9]{1,3}岁[a-z0-9一-龥，。]*?)。", r"\1。", brief)
                front = f"{aname}"
                back = f"【案要】{trunc(brief, 80)}\n【评按】{trunc(pja, 110)}"
                cards.append({
                    "front": front,
                    "sub": f"23医案·{cur_chap}",
                    "back": back,
                    "meta": {"deck": "yian", "book": slug, "g": g0,
                             "uuid": "yian:" + crc(front + "|" + back)}
                })
                i = j
                continue
            i += 1
            continue
        i += 1
    # 去重（同名案&同 back）
    seen, out = set(), []
    for c in cards:
        k = c["meta"]["uuid"]
        if k in seen:
            continue
        seen.add(k)
        out.append(c)
    print(f"  [锚点miss:{anch.miss}]", end=" ")
    return out


# ---------------- 口诀卡 ----------------
def deck_koujue():
    stem = "7中药诊断方剂口诀"
    slug = stem2slug(stem)
    anch = Anchor(stem, slug)
    blks = blocks_of(read(stem))
    cards = []
    cur1 = cur2 = last_short = ""
    mnum = re.compile(r"^\d{1,2}[.．、]")
    short_sec = re.compile(r"^[\u4e00-\u9fff（）()、]{2,10}$")
    i = 0
    while i < len(blks):
        kind, lv, t = blks[i]
        if kind == "h" and lv == 2:
            cur1 = t
            cur2 = ""
            last_short = ""
        elif kind == "h" and lv == 3:
            cur2 = t
        elif kind == "p" and not mnum.match(t) and short_sec.match(plain(t)) \
                and not label_of(t):
            last_short = plain(t)  # 候选小节名（如"望诊"）
        elif kind == "p" and mnum.match(t):
            sec = cur2 or last_short or cur1
            if not sec:
                i += 1
                continue
            verses = [t]
            j = i + 1
            while j < len(blks) and blks[j][0] == "p" and not mnum.match(blks[j][2]):
                verses.append(blks[j][2])
                j += 1
            cards.append({
                "front": sec,
                "sub": f"{cur1}·第{len([c for c in cards if c['front']==sec])+1}诀",
                "back": "\n".join(plain(v) for v in verses),
                "meta": {"deck": "koujue", "book": slug, "g": anch.find("p", t), "uuid": "koujue:" + crc(sec + t + "|" + "\n".join(plain(v) for v in verses))}
            })
            i = j
            continue
        i += 1
    print(f"  [锚点miss:{anch.miss}]", end=" ")
    return cards


# ---------------- 复习思考题 ----------------
QUIZ_MARK_RE = re.compile(r"^(附：)?复习思考题[：:]?$|^思考题$")
WEAK_RE = re.compile(r"小结|思考题|复习|学习|方法|目的|要求|学时|目录|前言|序言|凡例|编写|出版|版权|说明|附录|索引|编者|提要|自序")


def weak(title):
    return bool(WEAK_RE.search(title))


def chapter_of(lvl_map):
    for lv in (2, 3, 4, 5, 6):
        if lvl_map.get(lv):
            return lvl_map[lv]
    return ""


def collect_q(lines, start, lvl_map, anch, anchor_kind, anchor_text, stem):
    """从 start 行起收集编号题。返回 (items, end)。"""
    items = []
    g = anch.find(anchor_kind, anchor_text) if anch else None
    chapter = chapter_of(lvl_map)
    j = start
    phase = 0  # 0 找题 1 续题
    while j < len(lines):
        s = lines[j].strip()
        if not s:
            j += 1
            continue
        if HEAD_RE.match(s):
            break
        if phase == 0 and not re.match(r"^(\(?\d{1,2}\)|\d{1,2}[．.、)]|\(\d{1,2}\)|[一二三四五六七八九十][.．、])", s):
            # 跳过"复习思考题"后还可能有非编号引言行
            if len(items) == 0 and not QUIZ_MARK_RE.match(s):
                j += 1
                continue
        m = re.match(r"^(?:\(?\d{1,2}\)|\d{1,2}[．.、)]|\(\d{1,2}\))\s*(.+)", s)
        if m and len(m.group(1).strip()) >= 4:
            phase = 1
            q = m.group(1).strip()
            if not re.search(r"学时|(目的要求)", q):
                items.append({"chapter": chapter, "q": q, "g": g, "u": "q:" + crc(stem + "|" + q)})
            j += 1
            continue
        if phase == 1 and items and not re.match(r"^[一二三四五六七八九十]、", s) \
                and not items[-1]["q"].endswith(("？", "?", "。")) \
                and not s.startswith("**"):
            items[-1]["q"] += re.sub(r"\*\*", "", s)
            j += 1
            continue
        break
    return items, j


def extract_quiz(stem):
    slug = stem2slug(stem)
    anch = Anchor(stem, slug) if slug else None
    lines = read(stem).split("\n")
    items = []
    lvl_map = {}
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        mh = HEAD_RE.match(s)
        if mh:
            lv = len(mh.group(1))
            title = mh.group(2).strip()
            if QUIZ_MARK_RE.match(title) or (("复习思考题" in title) and len(title) <= 14):
                qs, j = collect_q(lines, i + 1, lvl_map, anch, "h", title, stem)
                items += qs
                i = j
                continue
            if not weak(title):
                lvl_map[lv] = title
                for k in [k for k in lvl_map if k > lv]:
                    del lvl_map[k]
            i += 1
            continue
        if QUIZ_MARK_RE.match(s):
            qs, j = collect_q(lines, i + 1, lvl_map, anch, "p", s, stem)
            items += qs
            i = j
            continue
        i += 1
    # 去重 & 过滤异常短题
    seen = set()
    out = []
    for it in items:
        q = it["q"].strip()
        if len(q) < 6 or q in seen:
            continue
        seen.add(q)
        it["q"] = q
        it["book"] = slug
        out.append(it)
    print(f"[quiz] {stem}: {len(out)} 题  [锚点miss:{anch.miss if anch else '-'}]")
    return slug, out


# ---------------- 主流程 ----------------
def main():
    os.makedirs(LEARN_DIR, exist_ok=True)
    os.makedirs(QUIZ_DIR, exist_ok=True)

    decks = [
        ("fangji", "方剂卡", "组成功用·主治病机", deck_fangji()),
        ("herb", "中药卡", "性味归经·药效应用", deck_herb()),
        ("point", "穴位卡", "定位取穴·主治功效", deck_point()),
        ("koujue", "口诀卡", "歌诀背诵·朗朗上口", deck_koujue()),
        ("bingz", "病证卡", "病→证→治法方药", deck_bingz()),
        ("yian", "医案卡", "读案·猜证·悟思路", deck_yian()),
    ]
    summary = []
    icons = {"fangji": "方", "herb": "药", "point": "穴", "koujue": "诀", "bingz": "证", "yian": "案"}
    for did, name, desc, cards in decks:
        with open(os.path.join(LEARN_DIR, f"deck-{did}.json"), "w", encoding="utf-8") as f:
            json.dump(cards, f, ensure_ascii=False, separators=(",", ":"))
        summary.append({"id": did, "name": name, "desc": desc,
                        "icon": icons[did], "count": len(cards)})
        print(f"[deck] {name}: {len(cards)} 张")
    with open(os.path.join(LEARN_DIR, "decks.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, separators=(",", ":"))

    all_quiz = []
    total_q = 0
    # 先清掉旧产物（文件名以 q<N>.json 定名，ASCII 兼容全平台路径）
    for old in glob.glob(os.path.join(QUIZ_DIR, "*.json")):
        os.remove(old)
    qidx = 0
    for md_path in sorted(glob.glob(os.path.join(MD_DIR, "*.md"))):
        stem = os.path.splitext(os.path.basename(md_path))[0]
        slug, qs = extract_quiz(stem)
        if len(qs) >= 5 and slug:
            fname = f"q{qidx}.json"
            qidx += 1
            all_quiz.append({"slug": slug,
                             "book": re.sub(r"^\d+", "", stem),
                             "f": fname,
                             "count": len(qs)})
            total_q += len(qs)
            with open(os.path.join(QUIZ_DIR, fname), "w", encoding="utf-8") as f:
                json.dump(qs, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(QUIZ_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(all_quiz, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[ok] 题库共 {total_q} 题，{len(all_quiz)} 本")


if __name__ == "__main__":
    main()
