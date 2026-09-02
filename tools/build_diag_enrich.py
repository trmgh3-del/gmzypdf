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

# ============ 2.6) 特异权重修正（让妇儿特异证不被泛证压制） ============
SPEC_W = {
    'tj_qzxy': {'jing_tong': 4},  # 痛经·气滞血瘀：经行腹痛为靶症，权重高于其余
}
for sid, patch in SPEC_W.items():
    z = syn_by_id[sid]
    for sym, w in patch.items():
        if z['w'].get(sym) != w:
            z['w'][sym] = w

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

# ============ 2.5) 随证加减（45 证型全量，教材方书口径人工撰写） ============
JJ = {
    'feng_han': '咳甚加杏仁、桔梗；头身痛甚加羌活、川芎；鼻塞不闻加辛夷、苍耳子。',
    'feng_re': '咽肿甚加牛蒡子、射干；咳甚加桑叶、杏仁；口渴加天花粉；鼻衄加白茅根。',
    'biao_xu': '汗多加黄芪、防风固表；项背强加葛根；兼咳喘加厚朴、杏仁。',
    'shao_yang': '呕甚加半夏、竹茹；口渴者去半夏加天花粉；胁痛甚加香附、郁金。',
    'yangming_jing': '汗多伤津加人参；烦渴甚加天花粉、芦根；热盛斑疹加玄参、生地。',
    'yangming_fu': '痞满而未坚者去芒硝（小承气意）；津亏便秘加玄参、麦冬、生地（增液承气意）。',
    'shu_shi': '湿偏重加佩兰、滑石；兼食滞加神曲、麦芽；呕逆加生姜、竹茹。',
    'fh_fanfei': '痰多加法半夏、陈皮；喉痒加蝉蜕、防风；鼻塞清涕加细辛、白芷。',
    'fr_fanfei': '热甚加黄芩、知母；咽哑加蝉蜕、胖大海；鼻衄加白茅根、黄芩。',
    'tan_re_fei': '喘促加苏子、葶苈子；痰稠难咯加瓜蒌、贝母；热毒甚加鱼腥草、金荞麦。',
    'tan_shi_fei': '寒饮偏重加干姜、细辛；胸闷加枳壳、桔梗；湿聚久咳加白芥子、莱菔子。',
    'fei_yinxu': '潮热盗汗加地骨皮、银柴胡；咯血加白及、仙鹤草；干咳加百部、款冬花。',
    'xin_huo': '口疮糜痛加黄连、连翘；心烦加栀子、莲子心；失眠加酸枣仁、夜交藤。',
    'xin_xuexu': '心悸甚加龙骨、牡蛎；不寐加酸枣仁、柏子仁；面白无华加阿胶、龙眼肉。',
    'xin_pi_lx': '腹胀加木香；便溏加山药、芡实；兼见出血加阿胶、仙鹤草。',
    'pi_qixu': '腹胀加陈皮、木香；久泻加莲子、芡实；中气下陷见坠胀加升麻、柴胡、黄芪。',
    'pi_yangxu': '寒盛加附子、肉桂；泻久加肉豆蔻、补骨脂；腹痛喜温加高良姜、香附。',
    'pi_shi_kun': '湿浊上泛加藿香、佩兰；腹胀加砂仁、厚朴；苔腻不化加半夏、茯苓增量。',
    'wei_huo': '大便秘结加大黄；口臭加藿香、栀子；牙龈肿痛甚加生石膏、怀牛膝。',
    'wei_yinxu': '干呕呃逆加竹茹、枇杷叶；便秘加火麻仁、瓜蒌仁；饥嘈不适加石斛增量。',
    'gan_yu': '气郁甚加郁金、青皮；痛经加当归、川芎；嗳气频作加旋覆花、代赭石。',
    'gan_huo': '头痛目赤甚加石决明、钩藤；便秘加芦荟、大黄；胁肋灼痛加川楝子、延胡索。',
    'gan_yang': '眩晕甚加石决明、珍珠母；阴液不足加枸杞子、女贞子；筋惕加白芍、龟板。',
    'gan_xuexu': '目干涩加枸杞子、菊花；筋脉拘急加木瓜并重用白芍；不寐加酸枣仁、夜交藤。',
    'shen_yinxu': '潮热骨蒸加知母、黄柏（知柏地黄意）；遗精加金樱子、芡实；耳鸣加磁石。',
    'shen_yangxu': '五更泄泻加补骨脂、肉豆蔻（合四神意）；水肿加牛膝、车前子（济生肾气意）。',
    'xin_shen_bj': '心烦甚加黄连、栀子；盗汗加浮小麦、煅牡蛎；多梦加珍珠母、夜交藤。',
    'pg_shire': '尿血加小蓟、白茅根；腰痛加桑寄生、牛膝；尿浊加萆薢、车前子。',
    'qx_lianxu': '心悸加龙眼肉；自汗加黄芪、浮小麦；经量少加丹参、香附。',
    'qz_xy': '痛甚加乳香、没药；癥块加三棱、莪术；气滞偏重加佛手、香橼。',
    'yx_shuifan': '肿甚加泽泻、车前子；心悸加桂枝；喘促不得卧加葶苈子、大枣。',
    'yx_hw': '骨蒸潮热加地骨皮、银柴胡；口舌生疮加黄连；遗精加龙骨、牡蛎。',
    'wei_fen': '项肿咽痛加马勃、玄参；咳甚加杏仁、前胡；鼻衄加白茅根、黄芩。',
    'ying_fen': '神昏谵语配用安宫牛黄丸或局方至宝丹开窍；斑疹加赤芍、丹皮凉血。',
    'xue_fen': '出血甚加紫草、白茅根；抽搐动风加羚羊角、钩藤；热毒盛合清瘟败毒之意。',
    'shi_ji': '腹胀甚加枳实、厚朴；食积化热加连翘、黄芩；脾虚夹积加白术（大安丸意）。',
    'tj_qzxy': '胀痛甚加香附、乌药；血块多加三棱、莪术；兼寒加艾叶、小茴香。',
    'dx_px': '兼色黄有热加黄柏、车前子；带下日久加金樱子、芡实；腰痛加续断、桑寄生。',
    'dx_sr': '阴痒甚加苦参、白鲜皮；带下臭秽加土茯苓、败酱草；黄疸胁痛合茵陈蒿之意。',
    'er_jf_re': '神昏加紫雪丹或安宫牛黄丸开窍；痰涎壅盛加天竺黄、胆南星；痉甚加蜈蚣、全蝎。',
    'er_gan_ji': '兼虫积加使君子、槟榔；腹胀加厚朴、枳实；脾虚明显加党参、黄芪。',
    'er_ynia': '畏寒肢冷加附子、肉桂；神疲倦怠加党参、黄芪；尿多清长加桑螵蛸增量。',
    'yj_bxx': '兼气滞加香附、柴胡调经；兼虚寒加艾叶、肉桂、炮姜。',
    'chr_e_ru_xue': '腹痛拒按加蒲黄、五灵脂；块下痛减者重益母草；兼热加丹皮、赤芍。',
    'chr_ru_xu': '乳房虚软甚加黄芪增量、通草；兼情志不舒加柴胡、青皮、桔梗。',
}
added_jj = 0
for sid, text in JJ.items():
    z = syn_by_id[sid]
    if z.get('jj') != text:
        z['jj'] = text
        added_jj += 1
print(f'  随证加减 +{added_jj}（覆盖 {sum(1 for x in rules["syndromes"] if x.get("jj"))}/45）')

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

# ============ 5) 评分器回归自检（规则改动体检） ============
# 以"完美患者"（某证型全部正权重症状全勾）喂回 diagnose 引擎（Python 镜像），
# 正解应排第一；允许少量近似证超越，但命中率设阈值把关。
def diagnose_top1(sel_ids, rules_obj):
    sel = set(sel_ids)
    best = (None, 0.0, 0)
    for z in rules_obj['syndromes']:
        hit = 0
        total = 0
        for k, w in z['w'].items():
            if w > 0:
                total += w
                if k in sel:
                    hit += w
            elif k in sel:
                hit += w
        ratio = (max(0, hit) / total) if total else 0
        if ratio > best[1] or (ratio == best[1] and hit > best[2]):
            best = (z['id'], ratio, hit)
    return best[0]

selftest_ok = 0
misses = []
for z in rules['syndromes']:
    full = [k for k, w in z['w'].items() if w > 0]
    top = diagnose_top1(full, rules)
    if top == z['id']:
        selftest_ok += 1
    else:
        misses.append(f"{z['id']}→{top}")
print(f'  评分器自检 top1 {selftest_ok}/45 {"未中：" + "、".join(misses) if misses else "全中"}')
assert selftest_ok >= 38, f'评分器自检未达标：{selftest_ok}/45，请检查权重或反证改动'
