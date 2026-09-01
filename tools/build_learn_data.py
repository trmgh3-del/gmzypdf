#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_learn_data.py — 从 md/ 提取学习系统数据：

输出（写入 gmzy-app/static/learn/ 与 gmzy-app/static/quiz/）：
  decks.json          记忆卡包总录
  deck-<id>.json      记忆卡（front/back/meta）
  quiz.json           各书复习思考题题库

卡片来源：
  deck-fangji.json  方剂卡（29方剂讲解：### 方名《出处》+〔组成〕〔讲解〕〔临证应用〕）
  deck-herb.json    中药卡（14本草备要讲解：#### 药名 +〔原文〕【讲解】【临证应用】）
  deck-point.json   穴位卡（21针灸学系列：###### 穴名 +〔定位〕〔主治〕）
  deck-koujue.json  口诀卡（7中药诊断方剂口诀：分节歌诀）
"""

import os
import re
import json
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_DIR = os.path.join(ROOT, "md")
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


# ---------------- 方剂卡 ----------------
def deck_fangji():
    blks = blocks_of(read("29方剂讲解"))
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
            comp = jiang = lin = ""
            j = i + 1
            while j < len(blks) and blks[j][0] != "h":
                txt = blks[j][2]
                lab = label_of(txt)
                body = plain(txt)
                if lab == "〔组成〕" and not comp:
                    comp = body
                elif lab == "〔讲解〕" and not jiang:
                    jiang = body
                elif lab == "〔临证应用〕" and not lin:
                    lin = body
                j += 1
            if comp:
                zhu = ""
                for cand in (jiang, lin):
                    m = re.search(r"(本方主治[^。；]*|具[^。]{0,40}效。?)[。；]?", cand)
                    if m:
                        zhu = m.group(0).rstrip("。；")
                        break
                back = "〔组成〕" + trunc(comp, 110)
                if zhu:
                    back += "\n〔主治〕" + trunc(zhu, 60)
                cards.append({
                    "front": name,
                    "sub": f"《{src}》" if src else cur_cat,
                    "back": back,
                    "meta": {"deck": "fangji"}
                })
            i = j
            continue
        i += 1
    return cards


# ---------------- 中药卡 ----------------
def deck_herb():
    blks = blocks_of(read("14本草备要讲解"))
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
            yuan = jiang = lin = ""
            j = i + 1
            seen = 0
            while j < len(blks) and blks[j][0] != "h":
                txt = blks[j][2]
                lab = label_of(txt)
                body = plain(txt)
                if lab == "〔原文〕" and not yuan:
                    yuan = body.split("。")[0] + "。"
                elif lab in ("【讲解】", "〔讲解〕") and not jiang:
                    jiang = body
                elif lab == "【临证应用】" and not lin:
                    lin = body
                j += 1
            parts = []
            if yuan:
                parts.append("〔性味原文〕" + trunc(yuan, 60))
            if jiang:
                parts.append(trunc(jiang, 110))
            elif lin:
                parts.append(trunc(lin, 110))
            if parts:
                cards.append({
                    "front": name,
                    "sub": cur_sec.replace("节", "节·") if cur_sec else cur_ch,
                    "back": "\n".join(parts),
                    "meta": {"deck": "herb"}
                })
            i = j
            continue
        i += 1
    return cards


# ---------------- 穴位卡 ----------------
def deck_point():
    cards = []
    for stem in ["21针灸学-上", "21针灸学-中", "21针灸学-下"]:
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
                loc = zhu = ""
                j = i + 1
                while j < len(blks) and not (blks[j][0] == "h" and blks[j][1] >= 5):
                    txt = blks[j][2]
                    lab = label_of(txt)
                    body = plain(txt)
                    if lab == "〔定位〕" and not loc:
                        loc = re.sub(r"（图[^）]*）", "", body)
                    elif lab == "〔主治〕" and not zhu:
                        zhu = body
                    j += 1
                if loc and zhu:
                    cards.append({
                        "front": name,
                        "sub": cur_mer,
                        "back": "〔定位〕" + trunc(loc, 70) + "\n〔主治〕" + trunc(zhu, 70),
                        "meta": {"deck": "point"}
                    })
                    i = j
                    continue
            i += 1
    return cards


# ---------------- 口诀卡 ----------------
def deck_koujue():
    blks = blocks_of(read("7中药诊断方剂口诀"))
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
            last_short = plain(t)  # 候选小节名（如“望诊”）
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
                "meta": {"deck": "koujue"}
            })
            i = j
            continue
        i += 1
    return cards


# ---------------- 复习思考题 ----------------
QUIZ_HEAD_RE = re.compile(r"^(附：)?复习思考题[：:]?$|^思考题$")


def extract_quiz(stem):
    lines = read(stem).split("\n")
    items = []
    cur_ch = ""
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        mh = HEAD_RE.match(s)
        if mh:
            title = mh.group(2).strip()
            if QUIZ_HEAD_RE.match(title) or "复习思考题" in title:
                # 收集随后编号题目
                j = i + 1
                while j < len(lines):
                    l2 = lines[j].strip()
                    if not l2:
                        j += 1
                        continue
                    if HEAD_RE.match(l2):
                        break
                    m = re.match(r"^(\(?\d{1,2}\)|\d{1,2}[．.、)]|\(\d{1,2}\))\s*(.+)", l2)
                    if m and len(m.group(2).strip()) >= 4:
                        q = m.group(2).strip()
                        if not re.search(r"学时|(目的要求)", q):
                            items.append({"chapter": cur_ch, "q": q})
                        j += 1
                        continue
                    if items and not m and len(l2) > 0 and not re.match(r"^[一二三四五六七八九十]、", l2) \
                            and not items[-1]["q"].endswith(("？", "?", "。")) \
                            and not l2.startswith("**"):
                        items[-1]["q"] += l2
                        j += 1
                        continue
                    break
                i = j
                continue
            else:
                cur_ch = title
                i += 1
                continue
        if QUIZ_HEAD_RE.match(s):
            j = i + 1
            while j < len(lines):
                l2 = lines[j].strip()
                if not l2:
                    j += 1
                    continue
                if HEAD_RE.match(l2):
                    break
                m = re.match(r"^(\(?\d{1,2}\)|\d{1,2}[．.、)]|\(\d{1,2}\))\s*(.+)", l2)
                if m and len(m.group(2).strip()) >= 4:
                    q = m.group(2).strip()
                    if not re.search(r"学时|(目的要求)", q):
                        items.append({"chapter": cur_ch, "q": q})
                    j += 1
                    continue
                break
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
        out.append(it)
    return out


def main():
    os.makedirs(LEARN_DIR, exist_ok=True)
    os.makedirs(QUIZ_DIR, exist_ok=True)

    decks = [
        ("fangji", "方剂卡", "组成功用·主治病机", deck_fangji()),
        ("herb", "中药卡", "性味归经·药效应用", deck_herb()),
        ("point", "穴位卡", "定位取穴·主治功效", deck_point()),
        ("koujue", "口诀卡", "歌诀背诵·朗朗上口", deck_koujue()),
    ]
    summary = []
    icons = {"fangji": "方", "herb": "药", "point": "穴", "koujue": "诀"}
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
    for md_path in sorted(glob.glob(os.path.join(MD_DIR, "*.md"))):
        stem = os.path.splitext(os.path.basename(md_path))[0]
        qs = extract_quiz(stem)
        if len(qs) >= 5:
            all_quiz.append({"slug": re.match(r"^(\d+)", stem).group(1)
                             if re.match(r"^(\d+)", stem) else stem,
                             "book": re.sub(r"^\d+", "", stem),
                             "count": len(qs)})
            total_q += len(qs)
            with open(os.path.join(QUIZ_DIR, f"{stem}.json"), "w", encoding="utf-8") as f:
                json.dump(qs, f, ensure_ascii=False, separators=(",", ":"))
        if qs:
            print(f"[quiz] {stem}: {len(qs)} 题")
    with open(os.path.join(QUIZ_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(all_quiz, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[ok] 题库共 {total_q} 题，{len(all_quiz)} 本")


if __name__ == "__main__":
    main()
