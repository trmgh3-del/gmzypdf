#!/usr/bin/env python3
# 辨证规则增强（幂等）：
#   1) vs 相近证型鉴别 7 → 20 对（教材口径人工撰写）
#   2) 5 个高置信医案补绑 med（医案实据匹配）
#   3) 反证负权重 18 条（有汗↓风寒/舌淡白↓实热/苔腻↓阴虚…），scorer 需支持负数
#   4) 生成 static/diag/diag-quiz.json 「看案辨证」题库（医案案要/教材证候描述 → 选证型）
# 输出：重写 static/diag/rules.json（version+1）与 diag-quiz.json
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = os.path.join(ROOT, 'gmzy-app/static/diag/rules.json')
YIAN = os.path.join(ROOT, 'gmzy-app/static/learn/deck-yian.json')
QUIZ_OUT = os.path.join(ROOT, 'gmzy-app/static/diag/diag-quiz.json')

rules = json.load(open(RULES, encoding='utf-8'))
yian = json.load(open(YIAN, encoding='utf-8'))
syn_by_id = {z['id']: z for z in rules['syndromes']}

# ============ 1) vs 鉴别扩充（人工撰写，教材口径） ============
NEW_VS = [
    ('feng_han', 'feng_re',
     '同属表证初起、皆见恶寒发热脉浮：风寒恶寒重发热轻、无汗、苔薄白脉浮紧，寒束卫表；'
     '风热发热重恶寒轻、口微渴咽红、舌尖红脉浮数，热犯肺卫。辨之在【寒热孰重、汗与渴咽】。'),
    ('fh_fanfei', 'fr_fanfei',
     '皆以咳嗽为主症而兼表证：风寒犯肺咳声重浊、痰白清稀、鼻塞流清涕；'
     '风热犯肺咳声不扬、痰黄黏稠、咽痛口渴。辨之在【痰之色质、咽痛有无】。'),
    ('tan_re_fei', 'tan_shi_fei',
     '皆为痰浊壅肺、咳喘气粗胸闷苔腻脉滑：痰热者痰黄黏稠或带腥臭、苔黄腻脉滑数；'
     '痰湿者痰白黏量多易咯、苔白腻脉滑而濡。辨之在【痰色、苔色与热象】。'),
    ('pi_qixu', 'pi_yangxu',
     '同属脾虚、皆食少便溏神疲：脾气虚以运化乏力为主，无明显寒象；'
     '脾阳虚必由气虚及阳，兼腹中冷痛、畏寒肢冷、脉沉迟。辨之在【寒象之有无】。'),
    ('shen_yinxu', 'shen_yangxu',
     '皆见腰膝酸软、耳鸣：肾阴虚腰膝痠软而兼潮热盗汗、五心烦热、舌红少苔脉细数；'
     '肾阳虚腰膝痠冷而兼畏寒肢冷、夜尿清长、舌淡胖脉沉迟。辨之在【寒、热二端】。'),
    ('gan_huo', 'gan_yang',
     '皆见头痛眩晕、面红目赤、急躁耳鸣：肝火上炎为实火，口苦便秘、苔黄脉弦数、纯实无虚；'
     '肝阳上亢为本虚标实，眩晕欲仆、头重脚轻、腰膝酸软，上盛下虚。辨之在【虚实与下元】。'),
    ('xin_xuexu', 'xin_pi_lx',
     '皆心悸失眠、面色少华、脉细：心血虚以血不养心为主；'
     '心脾两虚必兼食少腹胀便溏等脾失健运之象。辨之在【脾象有无】。'),
    ('wei_huo', 'wei_yinxu',
     '皆见胃脘热象口干：胃火炽盛消谷善饥、牙龈肿痛口臭、大便秘结苔黄厚脉滑数，实也；'
     '胃阴虚饥不欲食、口燥咽干、舌红少津少苔脉细数，虚也。辨之在【食量与苔之厚薄】。'),
    ('qx_lianxu', 'qz_xy',
     '皆可面见无华、脉象无力：气血两虚以乏力气短麻木为要、痛多隐痛喜按，属虚；'
     '气滞血瘀以胸胁刺痛固定、入夜痛甚、舌紫脉涩为要，属实。辨之在【痛性与舌脉】。'),
    ('wei_fen', 'ying_fen',
     '温病传变之浅深：卫分证发热微恶风寒、口微渴、舌边尖红脉浮数，病位在表；'
     '营分证身热夜甚、心烦不寐、斑疹隐隐、舌红绛，邪已入里扰神。辨之在【热势昼夜与神志】。'),
    ('dx_px', 'dx_sr',
     '带下为病皆量多：脾虚湿注带下色白或淡黄、清稀无臭、缠绵难愈、伴纳呆便溏；'
     '湿热下注带下黄稠臭秽、阴中瘙痒、口苦溲赤。辨之在【色、臭、痒】。'),
    ('shi_ji', 'er_gan_ji',
     '小儿食伤之二候：食积为新病，脘腹胀满、嗳腐厌食、得吐泻则缓；'
     '疳积为久病，面黄肌瘦、毛发枯槁、肚大青筋、精神萎靡。辨之在【病程与形瘦】。'),
    ('yx_hw', 'xin_shen_bj',
     '皆见潮热盗汗、心烦失眠、舌红少苔脉细数：阴虚火旺以肾阴亏虚为本、'
     '虚火上炎骨蒸颧赤为著；心肾不交则心烦失眠（心火不下）与腰膝痠软（肾水不升）并见。'
     '辨之在【心神症状之比重】。'),
]
added_vs = 0
existing = {tuple(sorted((v['a'], v['b']))) for v in rules.get('vs', [])}
for a, b, text in NEW_VS:
    key = tuple(sorted((a, b)))
    if key in existing:
        continue
    ra, rb = syn_by_id[a]['ref'], syn_by_id[b]['ref']
    rules['vs'].append({'a': a, 'b': b, 'text': text,
                        'refs': ra if ra == rb else f'{ra}；{rb}'})
    existing.add(key)
    added_vs += 1

# ============ 2) 高置信医案补绑 med ============
MED_PATCH = {
    'fei_yinxu': '龚廷贤治劳嗽发热案',
    'fh_fanfei': '胡慎柔治小儿咳嗽案',
    'feng_re': '程门雪治春温夹湿滞案',
    'wei_yinxu': '费伯雄治虚损案',
    'chr_e_ru_xue': '何鸿舫治产后虚热案',
}
added_med = 0
for sid, title in MED_PATCH.items():
    z = syn_by_id[sid]
    if z.get('med'):
        continue
    card = next((c for c in yian if c['front'] == title), None)
    if not card:
        print(' ! 医案未找到', title)
        continue
    z['med'] = [card['meta']['uuid']]
    added_med += 1

# ============ 3) 反证负权重 ============
NEG = {
    'feng_han': {'zihan': -3, 'daohan': -2},
    'biao_xu': {'wuhan': -3},
    'feng_re': {'wl': -2, 'she_danbai': -1},
    'yangming_jing': {'wl': -2, 'she_danbai': -2},
    'yangming_fu': {'dabian_tang': -3, 'wuhan': -1},
    'tan_shi_fei': {'she_shaotai': -2},
    'fei_yinxu': {'she_baini': -1, 'tan_xi': -1},
    'pi_yangxu': {'she_honghuang': -2, 'kouke_leng': -1},
    'shen_yangxu': {'wuxin': -2, 'she_honghuang': -2},
    'shen_yinxu': {'weihan': -2, 'she_danbai': -1, 'mai_chenchi': -1},
    'wei_huo': {'she_danbai': -2, 'koudan': -2},
    'wei_yinxu': {'she_huangni': -2},
    'pi_shi_kun': {'she_shaotai': -2},
    'tan_re_fei': {'she_danbai': -2, 'tan_xi': -2},
    'fr_fanfei': {'wl': -1, 'tan_xi': -2},
    'fh_fanfei': {'she_honghuang': -2, 'tan_huang': -2},
    'yx_hw': {'weihan': -2, 'she_baini': -2},
    'qx_lianxu': {'mai_hong': -2},
}
known_sym = {i['id'] for g in rules['groups'] for i in g['items']}
added_neg = 0
for sid, negs in NEG.items():
    z = syn_by_id[sid]
    for sym, w in negs.items():
        assert sym in known_sym, f'未知症状 {sym}'
        if z['w'].get(sym) != w:
            z['w'][sym] = w
            added_neg += 1

rules['version'] = 6  # 数据语义版本：增强后为 6（幂等，不随跑次递增）
json.dump(rules, open(RULES, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'  vs +{added_vs}（共 {len(rules["vs"])} 对） med +{added_med}（共 {sum(1 for z in rules["syndromes"] if z.get("med"))}/45） 反证 +{added_neg} 条')

# ============ 4) 生成「看案辨证」题库 ============
random.seed(45)

def yian_case(card):
    """从医案卡 back 提取【案要】段。"""
    back = card['back']
    a = back.find('【案要】')
    b = back.find('【评按】')
    if a >= 0 and b > a:
        return back[a + 4:b].strip()
    return back.split('\n')[0].strip()

def clip(text, n=180):
    if len(text) <= n:
        return text
    cut = text[:n]
    for p in '。；！？':
        i = cut.rfind(p)
        if i > n * 0.55:
            return cut[:i + 1]
    return cut + '…'

def redact(text, name):
    """隐去证名与其括注/尾部证名，防止泄题。"""
    core, paren = name, ''
    if '（' in name:
        core, paren = name.split('（', 1)
        paren = paren.rstrip('）')
    for t in (name, core, paren):
        if t:
            text = text.replace(t, '□□')
    if '·' in core:
        text = text.replace(core.split('·', 1)[1], '□□')
    return text

BY_MED = {}
for z in rules['syndromes']:
    for u in z.get('med') or []:
        BY_MED[u] = z['id']

quiz = []
zids = [z['id'] for z in rules['syndromes']]
for z in rules['syndromes']:
    src, q, sid = '', '', z['id']
    if z.get('med'):
        card = next((c for c in yian if c['meta']['uuid'] == z['med'][0]), None)
        if card:
            q, src = clip(yian_case(card)), card['sub'].split('·', 1)[-1]
    if not q and z.get('ev'):
        evs = sorted(z['ev'], key=lambda x: len(x.get('excerpt', '')), reverse=True)
        e = evs[0]
        q = e['excerpt'].strip()
        if len(q) < 60 and len(evs) > 1:
            q = q.rstrip('。；，') + '；' + evs[1]['excerpt'].strip()
        q = clip(q)
        src = '《' + e['book'].lstrip('0123456789') + '》' + e.get('path', '')
    if not q or len(redact(q, z['name'])) < 40:
        # 兜底：以证型主症谱合成极简医案（负权重反证不出现在题干）
        sym_label = {i['id']: i['label'] for g in rules['groups'] for i in g['items']}
        pos = sorted(((k, v) for k, v in z['w'].items() if v > 0), key=lambda x: -x[1])[:7]
        q = '患者诊见：' + '、'.join(sym_label.get(k, k) for k, _ in pos) + '。'
        src = '证型主症谱'
        if not src:
            src = '教材证候'
    q = redact(q, z['name'])
    if len(q) < 40:
        continue
    # 同 cat 优先的干扰项（排除互鉴 vs 过于接近者不做干扰，以免两可）
    pool = [x for x in rules['syndromes'] if x['id'] != sid]
    same = [x for x in pool if x['cat'] == z['cat']]
    others = [x for x in pool if x['cat'] != z['cat']]
    random.shuffle(same)
    random.shuffle(others)
    distract = (same + others)[:3]
    choices = [{'id': sid, 'name': z['name']}] + [{'id': d['id'], 'name': d['name']} for d in distract]
    random.shuffle(choices)
    quiz.append({'u': f"dq:{len(quiz)}", 'q': q, 'a': sid, 'an': z['name'], 'src': src,
                 'choices': [c['name'] for c in choices]})

json.dump({'version': rules['version'], 'count': len(quiz), 'items': quiz},
          open(QUIZ_OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'  看案辨证题库 {len(quiz)} 题 → {QUIZ_OUT}')
assert len(quiz) >= 40, '题库不足 40 题'
