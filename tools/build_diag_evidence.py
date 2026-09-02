#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_diag_evidence.py — 为辨证规则生成「教材诊疗依据」。

对每个证型：
  1) 按名称/病机关键词在全库检索，评分选 top 出处段落 → 写入 rules.json 的 ev 字段
     （{slug, g, path, book, excerpt}，带目录路径与原文块锚点，App 可一键达原文）。
  2) 用代表方名在医案卡包反查相关医案 → med 字段（yian uuid 列表，最多 3 则）。

输出：gmzy-app/static/diag/rules.json（就地更新，ev+med 两字段）。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(ROOT, "md")
APP = os.path.join(ROOT, "gmzy-app", "static")
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build_learn_data import Anchor, blocks_of, read as raw_read, stem2slug  # noqa: E402

RULES = os.path.join(APP, "diag", "rules.json")
YIAN = os.path.join(APP, "learn", "deck-yian.json")

# 证型 → 重点参考书本（按类别指引检索域）
CAT_BOOKS = {
    "六经·八纲": ["11伤寒论讲解", "6中医药学概论", "15中医内科学"],
    "脏腑辨证": ["15中医内科学", "6中医药学概论", "10黄帝内经讲解"],
    "气血津液": ["15中医内科学", "12金匮要略讲解", "6中医药学概论"],
    "卫气营血": ["13温病条辨讲解", "6中医药学概论"],
    "妇科": ["19中医妇科学", "15中医内科学"],
    "儿科": ["20中医儿科学"],
    "经络相关": ["21针灸学-上", "21针灸学-中"],
}


def load_blocks(stem):
    return blocks_of(raw_read(stem))


def norm(s):
    return re.sub(r"[·（）()·、，。]", "", s)


def kw_of(z):
    """关键词集：主名（无修饰）+ 主名两段 + 病机分句 + 治法首法。"""
    name = z["name"]
    base = re.split(r"[·（(]", name)[0].replace("证", "")
    kws = []
    if len(base) >= 2:
        kws.append((norm(base), 5))
        # 两段拆分（风寒表→风寒+表）
        if len(base) >= 3:
            for cut in range(2, len(base)):
                a, b = norm(base[:cut]), norm(base[cut:])
                if len(a) >= 2 and '表' != a[-1:] or len(b) >= 2:
                    kws.append((a, 3))
                if len(b) >= 2 and b not in ('表', '里'):
                    kws.append((b, 3))
    bj0 = re.split(r"[，。；]", z["bj"])[0]
    for t in re.split(r"[，。、；]", z["bj"])[:3]:
        nt = norm(t)
        if 2 <= len(nt) <= 8:
            kws.append((nt, 2))
    zf0 = re.split(r"[，。；]", z["zf"])[0]
    nt = norm(zf0)
    if 2 <= len(nt) <= 8:
        kws.append((nt, 3))
    return kws


def build_evidence_pool(stems):
    pool = {}
    lvl = {}
    for stem in stems:
        slug = stem2slug(stem)
        try:
            blks = load_blocks(stem)
        except FileNotFoundError:
            continue
        titles = []
        for idx, b in enumerate(blks):
            kind, l, txt = b
            if kind == "h":
                lvl[l] = txt
                titles = [k for k in titles if k[0] < l]
                titles.append((l, txt))
            else:
                path = " > ".join(t for _, t in titles)[:48]
                yield stem, slug, idx, txt, path
    return pool


def score_text(kws, txt):
    sc = 0
    for k, w in kws:
        if k and k in txt:
            sc += w
    return sc


def main():
    rules = json.load(open(RULES, encoding="utf-8"))
    all_stems = sorted(f[:-3] for f in os.listdir(MD) if f.endswith(".md") and f[0].isdigit())
    pool = {}
    anchors = {}
    for stem in all_stems:
        slug = stem2slug(stem)
        anchors[slug] = Anchor(stem, slug)
        pool[stem] = list()
    # 收集全部段块
    seg = {}
    for stem in all_stems:
        slug = stem2slug(stem)
        try:
            blks = load_blocks(stem)
        except FileNotFoundError:
            continue
        rows = []
        titles = []
        for idx, (kind, l, txt) in enumerate(blks):
            if kind == "h":
                titles = [tp for tp in titles if tp[0] < l]
                titles.append((l, txt))
                rows.append((idx, None, 0, txt))
            else:
                path = " > ".join(t for _, t in titles)[:48]
                txt2 = re.sub(r"\*|\[|\]", "", txt)
                rows.append((idx, path, len(txt2), txt2))
        seg[(stem, slug)] = rows

    def path_at(rows, idx):
        g = rows[idx][0]
        for i in range(idx, -1, -1):
            if rows[i][1] is None:
                # 回推该块最近一个标题生成路径
                pass
        return rows[idx][1] or ""

    yian = json.load(open(YIAN, encoding="utf-8"))

    update_n = 0
    for z in rules["syndromes"]:
        cat = z["cat"]
        stems = CAT_BOOKS.get(cat, [])
        stems += ["15中医内科学", "6中医药学概论"]
        stems = list(dict.fromkeys(stems))
        kws = kw_of(z)
        cands = []
        for stem in stems:
            slug = stem2slug(stem)
            rows = seg.get((stem, slug))
            if not rows:
                continue
            for i, (g, path, ln, txt) in enumerate(rows):
                if not path or ln < 20 or ln > 420:
                    continue
                sc = score_text(kws, txt)
                if sc >= 4:
                    cands.append((sc, stem, slug, g, path[:40], txt))
        cands.sort(key=lambda x: -x[0])
        used_books = set()
        ev = []
        for sc, stem, slug, g, path, txt in cands:
            if stem in used_books:
                continue
            ex = txt
            pos = 0
            mpos = min((ex.find(k) for k, w in kws if ex.find(k) >= 0), default=0)
            start = max(0, mpos - 26)
            excerpt = ("…" if start > 0 else "") + ex[start:start + 78] + ("…" if start + 78 < len(ex) else "")
            anchors[slug].m1 if False else None
            ev.append({
                "slug": slug, "book": stem, "g": g, "path": path,
                "excerpt": excerpt[:96], "score": sc
            })
            used_books.add(stem)
            if len(ev) >= 2:
                break
        if ev:
            z["ev"] = ev
            update_n += 1
        else:
            z.pop("ev", None)
        # ---- 医案反查：代表方名或证型名出现在案中 ----
        fangs = re.split(r"[，、；;（(]", z.get("fang", ""))
        keys = [norm(f) for f in fangs if 2 <= len(norm(f)) <= 6]
        kws2 = [norm(re.split(r"[·（(]", z["name"])[0].replace("证", ""))]
        med = []
        for c in yian:
            if len(med) >= 3:
                break
            text = (c["back"] or "") + c["front"]
            for k in keys + kws2:
                if k and k in text and len(k) >= 2:
                    med.append(c["meta"]["uuid"])
                    break
        if med:
            z["med"] = med
    rules["version"] = 4
    json.dump(rules, open(RULES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with_ev = sum(1 for z in rules["syndromes"] if z.get("ev"))
    with_med = sum(1 for z in rules["syndromes"] if z.get("med"))
    print(f"依据注入: {with_ev}/{len(rules['syndromes'])} 证型  医案关联: {with_med} 证型")


if __name__ == "__main__":
    main()
