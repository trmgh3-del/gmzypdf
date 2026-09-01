#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_learn_data.py — 学习/辨证数据完整性校验（仓库自包含，仅标准库）

校验内容：
  1. 记忆卡：四个卡包数量阈值、front/back 非空、meta.book/g 锚点存在且指向正确文本
  2. 题库：index 与分卷文件一致、章节命名不含弱标签（小结/单元N）、每题带 g/book 锚点
  3. 辨证规则：症状 id 与权重引用闭合、vs 鉴别对的证型 id 存在

用法：python3 tools/validate_learn_data.py   （exit 0 = 通过）
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "gmzy-app", "static")

fail = []


def err(msg):
    fail.append(msg)
    print("  ✗", msg)


def ok(msg):
    print("  ✓", msg)


def load(*p):
    with open(os.path.join(APP, *p), encoding="utf-8") as f:
        return json.load(f)


def norm(s):
    return re.sub(r"\s+", "", re.sub(r"\*\*", "", s or ""))


def block_text(b):
    if "x" in b:
        return b["x"]
    if "segs" in b:
        return "".join(seg.get("x", "") for seg in b["segs"])
    return ""


BOOK_CACHE = {}


def book_blocks(slug):
    if slug not in BOOK_CACHE:
        BOOK_CACHE[slug] = load("books-data", slug + ".json")["blocks"]
    return BOOK_CACHE[slug]


# ---------------- 1. 记忆卡 ----------------
print("== 记忆卡 ==")
decks = load("learn", "decks.json")
EXPECT_MIN = {"fangji": 100, "herb": 200, "point": 380, "koujue": 380}
for d in decks:
    cards = load("learn", f"deck-{d['id']}.json")
    if len(cards) != d["count"]:
        err(f"{d['id']} decks.json 数量 {d['count']} 与实际 {len(cards)} 不符")
    if len(cards) < EXPECT_MIN[d["id"]]:
        err(f"{d['id']} 卡片过少: {len(cards)} < {EXPECT_MIN[d['id']]}")
    empty = short = anch_bad = 0
    for c in cards:
        if not c.get("front") or not c.get("back"):
            empty += 1
            continue
        if d["id"] == "herb" and len(c["back"]) < 40:
            short += 1
        m = c.get("meta") or {}
        slug, g = m.get("book"), m.get("g")
        if not slug or g is None:
            anch_bad += 1
            continue
        blks = book_blocks(slug)
        if not (0 <= g < len(blks)):
            anch_bad += 1
    if empty:
        err(f"{d['id']} 有空 front/back: {empty}")
    if short:
        err(f"{d['id']} 背面过短(<40字): {short}")
    if anch_bad:
        err(f"{d['id']} 锚点异常: {anch_bad}")
    ok(f"{d['id']}: {len(cards)} 张，锚点/内容正常")

# ---------------- 2. 题库 ----------------
print("== 题库 ==")
idx = load("quiz", "index.json")
total_declared = sum(b["count"] for b in idx)
total_real = 0
# "卷首"在《温病条辨》为正式篇目（原病篇），不算弱标签
WEAK = re.compile(r"小结|单元\d|学习方法|目的要求")
for b in idx:
    fname = b.get("f") or f"{b['slug']}{b['book']}.json"
    fpath = os.path.join(APP, "quiz", fname)
    qs = json.load(open(fpath, encoding="utf-8"))
    if len(qs) != b["count"]:
        err(f"{b['book']} index 数量 {b['count']} 与实际 {len(qs)} 不符")
    total_real += len(qs)
    bad_ch = sum(1 for q in qs if WEAK.search(q["chapter"]))
    if bad_ch:
        err(f"{b['book']} 弱章节标签 {bad_ch} 处: " +
            str(sorted({q['chapter'] for q in qs if WEAK.search(q['chapter'])}))[:120])
    anch_bad = 0
    for q in qs:
        slug, g = q.get("book"), q.get("g")
        if not slug or g is None:
            anch_bad += 1
            continue
        blks = book_blocks(slug)
        if not (0 <= g < len(blks)):
            anch_bad += 1
            continue
        if "复习思考题" not in block_text(blks[g])[:12] and "思考题" not in block_text(blks[g])[:12]:
            anch_bad += 1
    if anch_bad:
        err(f"{b['book']} 锚点异常题 {anch_bad}")
    emptyq = sum(1 for q in qs if len(q["q"]) < 6)
    if emptyq:
        err(f"{b['book']} 过短题 {emptyq}")
print(f"  合计 {total_real} 题（声明 {total_declared}）")
if total_real != total_declared:
    err("题库总量与 index 声明不一致")
else:
    ok("题库锚点/数量/章节标签全部正常")

# ---------------- 3. 辨证规则 ----------------
print("== 辨证规则 ==")
rules = load("diag", "rules.json")
sym_ids = {it["id"] for g in rules["groups"] for it in g["items"]}
syn_ids = {s["id"] for s in rules["syndromes"]}
bad = 0
for s in rules["syndromes"]:
    if not s.get("w"):
        err(f"证型 {s['id']} 无权重表")
        bad += 1
    for k, w in s["w"].items():
        if k not in sym_ids:
            err(f"证型 {s['id']} 引用未定义症状 {k}")
            bad += 1
        if not isinstance(w, (int, float)) or w <= 0:
            err(f"证型 {s['id']} 权重异常 {k}={w}")
            bad += 1
    for f_ in ("name", "bj", "zf", "fang", "points", "ref", "cat"):
        if not s.get(f_):
            err(f"证型 {s['id']} 缺字段 {f_}")
            bad += 1
for v in rules.get("vs", []):
    for x in (v["a"], v["b"]):
        if x not in syn_ids:
            err(f"鉴别对引用未知证型 {x}")
            bad += 1
if not bad:
    ok(f"规则库 {len(syn_ids)} 证型 × {len(sym_ids)} 症状引用闭合，鉴别对 {len(rules.get('vs', []))} 组")

print()
if fail:
    print(f"FAILED: {len(fail)} 项问题")
    sys.exit(1)
print("ALL LEARN/DIAG DATA OK")
