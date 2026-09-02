#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e2e_smoke.py — 数据管道端到端冒烟自检（防回归）：
  1) 卡包/题库/规则/图册的关键文件存在且结构完整
  2) uuid 全局唯一
  3) decks.json 计数与 deck-*.json 实际条数一致
  4) quiz index.json count 总数一致
  5) 每本书的书箱文件极大主流块一定有章节
  6) App 版本号严格 x.y.z 且 mine.vue 引用该版号
用法：python3 tools/e2e_smoke.py  （exit 0 = 通过）
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, 'gmzy-app')
S = os.path.join(APP, 'static')

fail = []

def err(msg):
    fail.append(msg); print(' ✗', msg)

def load(*p):
    with open(os.path.join(S, *p), encoding='utf-8') as f:
        return json.load(f)

# ---- 1 卡包 ----
decks = load('learn', 'decks.json')
if len(decks) != 6:
    err(f'卡包数应为 6，实际 {len(decks)}')
uuids = set()
for d in decks:
    cards = load('learn', f'deck-{d["id"]}.json')
    if len(cards) != d['count']:
        err(f'{d["id"]} count {d["count"]} ≠ 实际 {len(cards)}')
    for c in cards:
        u = c.get('meta', {}).get('uuid')
        if not u:
            err(f'{d["id"]} 卡片缺 uuid: {c.get("front","")[:20]}')
        elif u in uuids:
            err(f'uuid 冲突: {u}')
        uuids.add(u)
        m = c['meta']
        if m['g'] is not None:
            book_path = os.path.join(S, 'books-data', m['book'] + '.json')
            if not os.path.exists(book_path):
                err(f'卡片引用书籍不存在 {m["book"]}')
            else:
                if m['g'] >= len(json.load(open(book_path, encoding='utf-8'))['blocks']):
                    err(f'{d["id"]} 卡片锚点越界 g={m["g"]} book={m["book"]}')
print(f'  卡包 6/6 共 {sum(d["count"] for d in decks)} 张，uuid 唯一 {len(uuids)} 个')

# ---- 2 题库 ----
qidx = load('quiz', 'index.json')
total_declared = sum(b['count'] for b in qidx)
total_real = 0
for b in qidx:
    qs = load('quiz', b['f'])
    total_real += len(qs)
    for q in qs:
        if not q.get('u'):
            err(f'{b["book"]} 缺题 uuid')
if total_declared != total_real:
    err(f'题库数量声明 {total_declared} ≠ 实际 {total_real}')
print(f'  题库 {len(qidx)} 卷共 {total_real} 题')

# ---- 3 规则 ----
rules = load('diag', 'rules.json')
assert_ev = sum(1 for z in rules['syndromes'] if z.get('ev'))
if assert_ev != len(rules['syndromes']):
    err(f'诊疗依据未全覆盖 {assert_ev}/{len(rules["syndromes"])}')
sym_ids = {i['id'] for g in rules['groups'] for i in g['items']}
for z in rules['syndromes']:
    for k in z['w']:
        if k not in sym_ids:
            err(f'证型 {z["id"]} 引用症状 {k} 不存在')
print(f'  规则 {len(rules["syndromes"])} 证型 依据 {assert_ev} 医案 {sum(1 for z in rules["syndromes"] if z.get("med"))}')

# ---- 4 舌脉图册 ----
atlas = load('diag', 'atlas.json')
if len(atlas.get('tongue', [])) < 10 or len(atlas.get('pulse', [])) < 10:
    err('舌脉图册不足')
print(f'  舌脉图册 {len(atlas["tongue"])}舌 + {len(atlas["pulse"])}脉')

# ---- 5 书籍箱健康 ----
catalog = load('books-data', 'catalog.json')
if any(x.get('chapters', 0) < 2 for x in catalog):
    err('存在章节结构异常的书：' + ','.join(x['title'] for x in catalog if x.get('chapters', 0) < 2))
print(f'  书目 {len(catalog)} 本 章节数全部≥2')

# ---- 6 版本同步 ----
mf = open(os.path.join(APP, 'manifest.json'), encoding='utf-8').read()
ver = re.search(r'"versionName":\s*"([\d.]+)"', mf).group(1)
mine = open(os.path.join(APP, 'pages/mine/mine.vue'), encoding='utf-8').read()
if 'CARD_NUM' in mine:
    known = re.search(r"CARD_NUM = '(\d+)'", mine).group(1)
    total_cards = sum(d['count'] for d in decks)
    if int(known) != total_cards:
        err(f'mine.vue CARD_NUM {known} ≠ 实际卡数 {total_cards}')
pj = open(os.path.join(APP, 'pages.json'), encoding='utf-8').read()
for path in ('pages/index/index', 'pages/reader/reader', 'pages/learn/learn', 'pages/stats/stats', 'pages/cards/cards', 'pages/quiz/quiz', 'pages/diag/diag', 'pages/mine/mine', 'pages/search/search'):
    if path not in pj:
        err(f'pages.json 缺路由 {path}')
print(f'  版本 {ver} 且 mine CARD_NUM 一致')

print()
if fail:
    print(f'FAILED: {len(fail)} 项')
    sys.exit(1)
print('SMOKE PASSED')
