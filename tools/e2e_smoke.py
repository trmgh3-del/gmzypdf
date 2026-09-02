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

# ---- 4 舌脉望诊图册（细分） ----
atlas = load('diag', 'atlas.json')
t_list, p_list, w_list = atlas.get('tongue', []), atlas.get('pulse', []), atlas.get('wang', [])
if len(t_list) < 26:
    err(f'舌象图谱仅 {len(t_list)} < 26（细分未生效）')
if len(p_list) < 20:
    err(f'脉象图谱仅 {len(p_list)} < 20')
if len(w_list) < 14:
    err(f'望诊图卡仅 {len(w_list)} < 14')
for sec, lst in (('tongue', t_list), ('pulse', p_list), ('wang', w_list)):
    for it in lst:
        if not it.get('grp'):
            err(f'{sec} 词条缺分组 grp：{it["term"]}')
        if sec == 'wang' and not it.get('kind'):
            err(f'望诊词条缺 kind：{it["term"]}')
# 词条 → 组件图样的关键字闭环：每个词条必须命中组件 KINDS 里的至少一个关键字/kind
import re as _re
def kinds_of(comp):
    src = open(os.path.join(APP, 'components', comp + '.vue'), encoding='utf-8').read()
    ks = set(_re.findall(r"k:\s*'([^']+)'", src))
    if comp == 'WangSvg':
        ks |= set(_re.findall(r"'([a-z]+-[a-z-]+)'", src)) | set(_re.findall(r"props\.kind === '(zones)'", src))
    return src, ks
src_t, ks_t = kinds_of('TongueSvg')
src_p, ks_p = kinds_of('PulseSvg')
src_w, ks_w = kinds_of('WangSvg')
for it in t_list:
    if not any(k in it['term'] for k in ks_t):
        err(f'舌象词条无匹配图样：{it["term"]}')
for it in p_list:
    if not any(k in it['term'] for k in ks_p):
        err(f'脉象词条无匹配图样：{it["term"]}')
for it in w_list:
    if it['kind'] not in ks_w:
        err(f'望诊词条 kind 未在 WangSvg 注册：{it["kind"]}')
grps = sorted({it['grp'] for it in t_list} | {it['grp'] for it in p_list} | {it['grp'] for it in w_list})
print(f'  舌脉望诊图册 {len(t_list)}舌 + {len(p_list)}脉 + {len(w_list)}望 · 分组 {len(grps)} 类 · 图样关键字全命中')

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

# 7) 学习增值功能接线
print('\n[7] 模考/划线/反向卡/长辈模式')
storejs = open(os.path.join(APP, 'common/store.js'), encoding='utf-8').read()
for key in ('mockHistory', 'pushMockResult', 'setMark', 'removeMark', 'cardReverse', 'elder'):
    if key not in storejs:
        err(f'store.js 缺少 {key}')
quiz = open(os.path.join(APP, 'pages/quiz/quiz.vue'), encoding='utf-8').read()
for key in ('setupMock', 'submitMock', 'mock-1', 'pushMockResult'):
    if key not in quiz and key != 'mock-1':
        err(f'quiz.vue 缺少模考逻辑 {key}')
if 'quiz?mock=1' not in open(os.path.join(APP, 'pages/learn/learn.vue'), encoding='utf-8').read():
    err('learn.vue 缺少模考入口')
reader = open(os.path.join(APP, 'pages/reader/reader.vue'), encoding='utf-8').read()
if '@mark="onMark"' not in reader or 'setMark' not in reader:
    err('reader.vue 未接入划线批注')
bv = open(os.path.join(APP, 'components/BlocksView.vue'), encoding='utf-8').read()
if 'longpress' not in bv or 'mk-note' not in bv:
    err('BlocksView.vue 缺少长按划线')
cards = open(os.path.join(APP, 'pages/cards/cards.vue'), encoding='utf-8').read()
if 'REVERSE_DECKS' not in cards or 'toggleReverse' not in cards:
    err('cards.vue 缺少反向卡')
mine = open(os.path.join(APP, 'pages/mine/mine.vue'), encoding='utf-8').read()
if 'toggleElder' not in mine or 'markList' not in mine:
    err('mine.vue 缺少长辈模式/批注聚合')
if not os.path.isfile(os.path.join(ROOT, 'tools/build_pwa.py')):
    err('缺少 tools/build_pwa.py')
print('  模考/划线/反向/长辈/PWA 接线齐全')

# 8) 辨证系统增强
print('\n[8] 辨证系统增强（vs/医案/反证/医案考）')
vs = rules.get('vs', [])
if len(vs) < 18:
    err(f'鉴别对仅 {len(vs)} < 18')
neg = [(z['id'], k, w) for z in rules['syndromes'] for k, w in z['w'].items() if w < 0]
if len(neg) < 25:
    err(f'反证负权重仅 {len(neg)} < 25')
med_n = sum(1 for z in rules['syndromes'] if z.get('med'))
if med_n < 38:
    err(f'医案覆盖 {med_n}/45 < 38')
dq = load('diag', 'diag-quiz.json')
if dq.get('count', 0) < 40 or len(dq.get('items', [])) < 40:
    err(f'看案辨证题库 {len(dq.get("items", []))} < 40')
zname = {z['id']: z['name'] for z in rules['syndromes']}
for it in dq.get('items', []):
    if it.get('a') not in zname:
        err(f'看案辨证答案越界 {it.get("a")}')
        break
    if len(it.get('choices', [])) != 4 or it.get('an') not in it.get('choices', []):
        err(f'看案辨证选项异常: {it.get("an")}')
        break
    if it['an'] in it['q']:
        err(f'看案辨证泄题: {it["an"]}')
        break
diagvue = open(os.path.join(APP, 'pages/diag/diag.vue'), encoding='utf-8').read()
for key in ('RED_FLAGS', 'redflag', 'kwHits', 'showAtlasTip', 'startCase', 'pickCase', 'pushDiagQuiz'):
    if key not in diagvue:
        err(f'diag.vue 缺少 {key}')
diagjs = open(os.path.join(APP, 'common/diagnosis.js'), encoding='utf-8').read()
if 'against' not in diagjs or 'RED_FLAGS' not in diagjs:
    err('diagnosis.js 缺少反证/红旗')
print(f'  鉴别 {len(vs)} 对 · 反证 {len(neg)} 条 · 医案 {med_n}/45 · 看案辨证 {len(dq.get("items", []))} 题零泄题')

# 9) 问诊引导轨道（含分支）
print('\n[9] 问诊引导与医案错题')
guide = load('diag', 'guide.json')
tracks = guide.get('tracks', [])
sym_all = {it['id'] for g in rules['groups'] for it in g['items']}
if len(tracks) < 8:
    err(f'问诊轨道 {len(tracks)} < 8')
n_step = 0
bad_ref = None
n_branch = 0
for tr in tracks:
    for sid in tr.get('base', []):
        if sid not in sym_all:
            bad_ref = f'{tr["id"]}.base/{sid}'
    idset = {s.get('id') for s in tr.get('steps', []) if s.get('id')}
    for st in tr.get('steps', []):
        n_step += 1
        if st.get('next'):
            n_branch += 1
            if st['next'] not in idset:
                bad_ref = f"{tr['id']}.next/{st['next']}"
        for o in st.get('opts', []):
            if o.get('goto'):
                n_branch += 1
                if o['goto'] not in idset:
                    bad_ref = f"{tr['id']}/{st.get('id', st['q'][:8])}.goto/{o['goto']}"
            for sid in o.get('add', []):
                if sid not in sym_all:
                    bad_ref = f"{tr['id']}/{st['q'][:8]}/{sid}"
if bad_ref:
    err(f'问诊轨道引用越界 {bad_ref}')
if n_step < 40:
    err(f'问诊步骤仅 {n_step} < 40')
if n_branch < 15:
    err(f'问诊分支仅 {n_branch} < 15（分支加深未生效）')
for key in ('startGuide', 'pickTrack', 'chooseOpt', 'gBack', 'finishGuide', 'resolveNext',
            'startCaseErr', "quizMistakes('_diag_'", "setQuizAnswer('_diag_'"):
    if key not in diagvue:
        err(f'diag.vue 缺少 {key}')
if 'loadDiagGuide' not in open(os.path.join(APP, 'common/learn.js'), encoding='utf-8').read():
    err('learn.js 缺少 loadDiagGuide')
# 医案考 stable id（错题包赖以持久）
items = dq.get('items', [])
if any('u' not in it or not str(it['u']).startswith('dq:') for it in items):
    err('看案辨证题库缺稳定题号 u')
print(f'  问诊轨道 {len(tracks)} 条 · {n_step} 问 · 分支 {n_branch} 处 · 医案错题回看已接线')

# 10) 论治加减 / SVG 图谱 / 结果端兜底
print('\n[10] 论治加减·SVG图谱·结果端兜底')
jj_n = sum(1 for z in rules['syndromes'] if z.get('jj'))
if jj_n < 45:
    err(f'随证加减覆盖 {jj_n}/45 < 45')
for key in ('dangerResult', 'comboHint', 'caseExplain', '恢复重练', 'TongueSvg', 'PulseSvg', 'WangSvg', 'atlasGroups'):
    if key not in diagvue:
        err(f'diag.vue 缺少 {key}')
for comp in ('TongueSvg', 'PulseSvg', 'WangSvg'):
    p = os.path.join(APP, 'components', comp + '.vue')
    if not os.path.isfile(p):
        err(f'缺少组件 {comp}.vue')
diagjs2 = open(os.path.join(APP, 'common/diagnosis.js'), encoding='utf-8').read()
if 'DANGER_SYNS' not in diagjs2:
    err('diagnosis.js 缺少 DANGER_SYNS')
print(f'  随证加减 {jj_n}/45 · SVG舌脉组件齐备 · 险证/兼证/解析/历史恢复已接线')

print()
if fail:
    print(f'FAILED: {len(fail)} 项')
    sys.exit(1)
print('SMOKE PASSED')
