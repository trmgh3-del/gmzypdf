#!/usr/bin/env python3
# 问诊引导轨道生成（幂等）：
# 按教材问诊"十问"思路，把 103 项平铺症状组织成 8 条主诉驱动的分步问诊轨道。
# 数据约束：选项只能引用 rules.json 中真实存在的症状 id；脚本强校验引用闭合。
# 输出：gmzy-app/static/diag/guide.json
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = os.path.join(ROOT, 'gmzy-app/static/diag/rules.json')
OUT = os.path.join(ROOT, 'gmzy-app/static/diag/guide.json')

rules = json.load(open(RULES, encoding='utf-8'))
KNOWN = {it['id'] for g in rules['groups'] for it in g['items']}

# 每条轨道：base=选择该主诉即隐含记录的症状；steps 按序提问，
# 每问 2~5 个互斥选项（add 记入勾选项），UI 另有「跳过 / 上一步 / 直接辨证」。
TRACKS = [
    {
        'id': 'fa_re', 'name': '发热恶寒', 'icon': '🌡', 'desc': '感冒、外感发热初起',
        'base': [],
        'steps': [
            {'id': 're_s1', 'q': '恶寒与发热，哪个更重？', 'opts': [
                {'t': '恶寒重，发热轻', 'add': ['wl']},
                {'t': '发热重，恶寒轻', 'add': ['fr']},
                {'t': '忽冷忽热，寒热往来', 'add': ['hl_wl'], 'goto': 're_oy'},
                {'t': '只发热，不恶寒', 'add': ['dh_br'], 'goto': 're_li'}]},
            {'q': '出汗情况如何？', 'opts': [
                {'t': '基本无汗', 'add': ['wuhan']},
                {'t': '动不动就出汗', 'add': ['zihan']},
                {'t': '睡着后出汗（盗汗）', 'add': ['daohan']}]},
            {'q': '口渴与咽喉怎么样？', 'opts': [
                {'t': '口渴想喝凉的，咽喉肿痛', 'add': ['kouke_leng', 'yan_tong']},
                {'t': '口不渴，只想喝热的', 'add': ['koudan']},
                {'t': '咽干口燥但喝水不多', 'add': ['yanzao', 'kougan_bw']}]},
            {'q': '热势有什么特点？', 'opts': [
                {'t': '大热、大汗、烦渴明显', 'add': ['dh_br', 'kouke_leng']},
                {'t': '午后或傍晚热得更明显', 'add': ['rccb', 'wc_cr']},
                {'t': '身热不扬、头身沉困', 'add': ['shenreb', 'touzhong', 'shenzhong']},
                {'t': '不明显，就是一般发热', 'add': []}]},
            {'q': '舌苔偏哪一类？', 'opts': [
                {'t': '舌淡红、苔薄白', 'add': ['she_danbai']},
                {'t': '舌红、苔黄', 'add': ['she_honghuang']},
                {'t': '舌苔黄腻', 'add': ['she_huangni']}]},
            {'q': '脉象偏哪一类？', 'opts': [
                {'t': '浮紧（绷得紧）', 'add': ['mai_fujin']},
                {'t': '浮缓', 'add': ['mai_fuhuan']},
                {'t': '浮数（偏快）', 'add': ['mai_fushuo']},
                {'t': '洪大有力', 'add': ['mai_hong']}]},
            # —— 分支：里热（只热不寒）——
            {'id': 're_li', 'next': 're_li2', 'q': '热在里，更偏腑实还是偏营分？', 'opts': [
                {'t': '大汗、烦渴、大便秘结', 'add': ['dabian_mi', 'kouke_leng']},
                {'t': '夜间热更重、斑疹或说胡话', 'add': ['ye_re', 'ban_zhen', 'shenhun']},
                {'t': '都不典型', 'add': []}]},
            {'id': 're_li2', 'q': '舌脉偏哪一类？', 'opts': [
                {'t': '舌红苔黄、脉洪大有力', 'add': ['she_honghuang', 'mai_hong']},
                {'t': '舌红少苔、脉细数', 'add': ['she_shaotai', 'mai_xishuo']}]},
            # —— 分支：少阳（寒热往来）——
            {'id': 're_oy', 'next': 're_oy2', 'q': '兼见口苦、胸满、烦呕中的哪些？', 'opts': [
                {'t': '口苦、咽干、目眩', 'add': ['kouku', 'yanzao', 'touyun']},
                {'t': '胸胁胀满、不想吃东西', 'add': ['xiezhang', 'nadai']},
                {'t': '心烦、恶心欲呕', 'add': ['fanzao', 'outu']}]},
            {'id': 're_oy2', 'q': '脉象偏哪一类？', 'opts': [
                {'t': '脉弦', 'add': ['mai_xian']},
                {'t': '脉弦而快', 'add': ['mai_xian', 'mai_fushuo']}]}]
    },
    {
        'id': 'ke_sou', 'name': '咳嗽有痰', 'icon': '🫁', 'desc': '咳嗽、咯痰为主症',
        'base': ['kesou'],
        'steps': [
            {'q': '痰的颜色与质地？', 'opts': [
                {'t': '痰白清稀', 'add': ['tan_xi']},
                {'t': '痰黄黏稠', 'add': ['tan_huang']},
                {'t': '干咳少痰或痰很难咳出', 'add': ['yanzao', 'she_shaotai']}]},
            {'q': '伴随的寒热表现？', 'opts': [
                {'t': '怕冷、清鼻涕、不出汗', 'add': ['wl', 'wuhan']},
                {'t': '发热、咽痛、口微渴', 'add': ['fr', 'yan_tong']},
                {'t': '午后潮热、盗汗', 'add': ['wc_cr', 'daohan']},
                {'t': '没有明显寒热', 'add': []}]},
            {'q': '痰多吗？容易咳出吗？', 'opts': [
                {'t': '痰多色白黏，容易咳出', 'add': ['she_baini', 'mai_hua']},
                {'t': '痰黄稠有腥臭味', 'add': ['tan_huang', 'she_huangni']},
                {'t': '痰很少', 'add': []}]},
            {'q': '有没有胸闷气喘？', 'opts': [
                {'t': '胸闷憋气', 'add': ['xiongmen']},
                {'t': '没有', 'add': []}]},
            {'q': '舌脉偏哪一类？', 'opts': [
                {'t': '舌淡苔白、脉浮紧或弦', 'add': ['she_danbai', 'mai_fujin']},
                {'t': '舌红苔黄、脉数', 'add': ['she_honghuang', 'mai_fushuo']},
                {'t': '苔白腻、脉滑', 'add': ['she_baini', 'mai_hua']},
                {'t': '舌红少苔、脉细数', 'add': ['she_shaotai', 'mai_xishuo']}]}]
    },
    {
        'id': 'fu_tong', 'name': '脘腹疼痛胀满', 'icon': '🍚', 'desc': '胃痛、腹痛、腹胀、胃口差',
        'base': ['wanfu'],
        'steps': [
            {'q': '疼了喜欢按还是怕按？', 'opts': [
                {'t': '按着舒服（喜按）', 'add': ['futong_xian']},
                {'t': '拒按、越按越痛', 'add': ['futong_ju']}]},
            {'q': '疼痛的性质偏哪种？', 'opts': [
                {'t': '冷痛，热敷能缓解', 'add': ['tong_leng']},
                {'t': '以胀痛为主', 'add': ['tong_zhang']},
                {'t': '固定刺痛、夜里更重', 'add': ['tong_citong']},
                {'t': '隐隐作痛、绵绵不休', 'add': ['tong_yin']}]},
            {'q': '食欲与大便怎么样？', 'opts': [
                {'t': '特别能吃、容易饿', 'add': ['shanshi']},
                {'t': '食欲差、大便稀溏', 'add': ['nadai', 'dabian_tang']},
                {'t': '嗳气有酸腐味、吃太多后加重', 'add': ['aifu']},
                {'t': '大便秘结不通', 'add': ['dabian_mi']}]},
            {'q': '有没有恶心、胁胀？', 'opts': [
                {'t': '恶心呕吐', 'add': ['outu']},
                {'t': '两胁胀痛、与情绪有关', 'add': ['xiezhang', 'yiyu']},
                {'t': '都没有', 'add': []}]},
            {'q': '舌脉偏哪一类？', 'opts': [
                {'t': '舌红苔黄、脉滑或洪', 'add': ['she_honghuang', 'mai_hua']},
                {'t': '苔白腻、脉沉迟', 'add': ['she_baini', 'mai_chenchi']},
                {'t': '舌红少苔、脉细数', 'add': ['she_shaotai', 'mai_xishuo']},
                {'t': '脉弦明显', 'add': ['mai_xian']}]}]
    },
    {
        'id': 'er_bian', 'name': '二便异常', 'icon': '🚽', 'desc': '腹泻、便秘、小便问题',
        'base': [],
        'steps': [
            {'q': '大便的主要问题？', 'opts': [
                {'t': '稀溏不成形', 'add': ['dabian_tang']},
                {'t': '干结难解', 'add': ['dabian_mi']},
                {'t': '夹有没消化的食物', 'add': ['wanggu']},
                {'t': '天不亮就拉肚子（五更泻）', 'add': ['wugeng']}]},
            {'q': '小便怎么样？', 'opts': [
                {'t': '量少发黄（短赤）', 'add': ['niao_duan']},
                {'t': '清长、夜里起夜多', 'add': ['niao_qing']},
                {'t': '尿频尿急、排尿灼痛', 'add': ['niao_tong']},
                {'t': '基本正常', 'add': []}]},
            {'q': '身体偏寒还是偏热？', 'opts': [
                {'t': '怕冷、四肢不温', 'add': ['weihan']},
                {'t': '手足心发热、下午潮热', 'add': ['wuxin', 'wc_cr']},
                {'t': '不记得 / 都不明显', 'add': []}]},
            {'q': '有没有腰膝痠软、乏力？', 'opts': [
                {'t': '腰膝痠软明显', 'add': ['yaoxi']},
                {'t': '神疲乏力、少气懒言', 'add': ['shenpi', 'shaoqi']},
                {'t': '没有', 'add': []}]},
            {'q': '舌脉偏哪一类？', 'opts': [
                {'t': '舌淡苔白、脉沉迟', 'add': ['she_danbai', 'mai_chenchi']},
                {'t': '舌胖大有齿痕、脉细弱', 'add': ['she_pang', 'mai_xiruo']},
                {'t': '舌红少苔、脉细数', 'add': ['she_shaotai', 'mai_xishuo']},
                {'t': '舌苔黄腻、脉滑数', 'add': ['she_huangni', 'mai_fushuo']}]}]
    },
    {
        'id': 'jing_dai', 'name': '妇科经带', 'icon': '🌸', 'desc': '痛经、月经不调、带下、产后',
        'base': [],
        'steps': [
            {'id': 'jd_s1', 'q': '主要困扰是哪一类？', 'opts': [
                {'t': '经行小腹疼痛', 'add': ['jing_tong'], 'goto': 'jd_jing'},
                {'t': '月经周期紊乱', 'add': ['jing_diao'], 'goto': 'jd_zq'},
                {'t': '带下异常', 'add': [], 'goto': 'jd_dai'},
                {'t': '产后恶露或乳汁问题', 'add': [], 'goto': 'jd_chan'}]},
            # —— 分支：痛经 ——
            {'id': 'jd_jing', 'next': 'jd_jing2', 'q': '疼痛的性质更接近？', 'opts': [
                {'t': '冷痛，热敷能缓解', 'add': ['tong_leng']},
                {'t': '胀痛为主', 'add': ['tong_zhang']},
                {'t': '刺痛固定、夜里更重', 'add': ['tong_citong']},
                {'t': '隐痛绵绵、按着舒服', 'add': ['tong_yin']}]},
            {'id': 'jd_jing2', 'next': 'jd_she', 'q': '经血的颜色质地？', 'opts': [
                {'t': '紫暗、夹血块', 'add': ['yj_anh']},
                {'t': '色淡、质稀', 'add': ['yj_dan']},
                {'t': '量多或淋沥不尽', 'add': ['yj_bld']}]},
            # —— 分支：周期紊乱 ——
            {'id': 'jd_zq', 'next': 'jd_she', 'q': '周期与经色如何？', 'opts': [
                {'t': '总是推迟', 'add': ['yj_delay']},
                {'t': '先后无定期、伴胸胁胀', 'add': ['jing_diao', 'xiezhang']},
                {'t': '经色淡、质稀', 'add': ['yj_dan']}]},
            # —— 分支：带下 ——
            {'id': 'jd_dai', 'next': 'jd_dai2', 'q': '带下是什么样？', 'opts': [
                {'t': '清稀色白、量多、无异味', 'add': ['dai_bai']},
                {'t': '黄稠、有异味、伴瘙痒', 'add': ['dai_huang', 'dai_du']}]},
            {'id': 'jd_dai2', 'next': 'jd_she', 'q': '平时还有哪些表现？', 'opts': [
                {'t': '神疲乏力、食欲差、便溏', 'add': ['shenpi', 'nadai', 'dabian_tang']},
                {'t': '口苦口黏、小便黄', 'add': ['kouku', 'niao_duan']},
                {'t': '不明显', 'add': []}]},
            # —— 分支：产后 ——
            {'id': 'jd_chan', 'next': 'jd_she', 'q': '具体是哪种情况？', 'opts': [
                {'t': '恶露三周淋沥不尽', 'add': ['chanhr_xu']},
                {'t': '乳汁清稀、量很少', 'add': ['chan_ru_shao']}]},
            # —— 共用收尾：舌脉 ——
            {'id': 'jd_she', 'q': '舌脉偏哪一类？', 'opts': [
                {'t': '舌紫暗或有瘀斑、脉涩', 'add': ['she_zi', 'mai_se']},
                {'t': '舌淡苔白、脉细弱', 'add': ['she_danbai', 'mai_xiruo']},
                {'t': '舌苔黄腻、脉弦', 'add': ['she_huangni', 'mai_xian']},
                {'t': '苔白腻、脉缓', 'add': ['she_baini', 'mai_xiruo']}]}]
    },
    {
        'id': 'er_ke', 'name': '小儿不适', 'icon': '🧒', 'desc': '食积、疳积、惊风、遗尿',
        'base': [],
        'steps': [
            {'id': 'ek_s1', 'q': '孩子主要怎么了？', 'opts': [
                {'t': '不吃东西、肚胀、嗳腐', 'add': ['er_jishi'], 'goto': 'ek_shi'},
                {'t': '面黄肌瘦、肚大青筋', 'add': ['er_gan'], 'goto': 'ek_gan'},
                {'t': '突然高热', 'add': ['er_jire'], 'goto': 'ek_re'},
                {'t': '睡中遗尿', 'add': ['er_yn'], 'goto': 'ek_yi'}]},
            # —— 分支：食积 ——
            {'id': 'ek_shi', 'next': 'ek_she', 'q': '呕吐与大便怎么样？', 'opts': [
                {'t': '呕吐酸腐', 'add': ['outu', 'aifu']},
                {'t': '大便酸臭、夹没消化的食渣', 'add': ['er_dabian_chou']},
                {'t': '肚胀、不让按', 'add': ['futong_ju']}]},
            # —— 分支：疳积 ——
            {'id': 'ek_gan', 'next': 'ek_she', 'q': '瘦与食的状态再细看看？', 'opts': [
                {'t': '胃纳很差、形体偏瘦', 'add': ['er_wei_ruo', 'nadai']},
                {'t': '大便稀溏、夹不消化食物', 'add': ['dabian_tang', 'wanggu']},
                {'t': '盗汗或自汗很明显', 'add': ['er_qire']}]},
            # —— 分支：高热惊风 ——
            {'id': 'ek_re', 'next': 'ek_she', 'q': '有没有惊惕之兆？', 'opts': [
                {'t': '有：抽搐、目上翻、神志不清', 'add': ['er_jingfeng']},
                {'t': '烦躁啼哭、睡不安稳', 'add': ['fanshen', 'shimian']},
                {'t': '暂时没有', 'add': []}]},
            # —— 分支：遗尿 ——
            {'id': 'ek_yi', 'next': 'ek_she', 'q': '还伴见什么？', 'opts': [
                {'t': '白天小便也频数清长', 'add': ['niao_qing']},
                {'t': '怕冷、手脚偏凉', 'add': ['weihan']},
                {'t': '盗汗明显', 'add': ['er_qire']},
                {'t': '没有其他', 'add': []}]},
            # —— 共用收尾：舌脉 ——
            {'id': 'ek_she', 'q': '舌脉偏哪一类？', 'opts': [
                {'t': '舌苔厚腻或黄腻、脉滑', 'add': ['she_huangni', 'mai_hua']},
                {'t': '舌淡苔白、脉细弱', 'add': ['she_danbai', 'mai_xiruo']},
                {'t': '舌红苔黄、脉数', 'add': ['she_honghuang', 'mai_fushuo']}]}]
    },
    {
        'id': 'shen_zhi', 'name': '心神与情志', 'icon': '🧠', 'desc': '失眠、心悸、头晕、情绪',
        'base': [],
        'steps': [
            {'q': '最困扰你的是哪一样？', 'opts': [
                {'t': '失眠、多梦', 'add': ['shimian']},
                {'t': '心慌心悸', 'add': ['xinji']},
                {'t': '头晕目眩', 'add': ['touyun']},
                {'t': '情绪低落或急躁易怒', 'add': ['yiyu']}]},
            {'q': '有没有"火"的表现？', 'opts': [
                {'t': '心烦、口苦、面红目赤', 'add': ['fanzao', 'kouku', 'mianhong']},
                {'t': '五心烦热、盗汗', 'add': ['wuxin', 'daohan']},
                {'t': '没有明显热象', 'add': []}]},
            {'q': '身体底子感觉如何？', 'opts': [
                {'t': '面色无华、乏力、食欲差', 'add': ['mianbai', 'shenpi', 'nadai']},
                {'t': '腰膝痠软、耳鸣', 'add': ['yaoxi', 'erming']},
                {'t': '常叹气、胁肋胀痛', 'add': ['taixi', 'xiezhang']},
                {'t': '没什么特别', 'add': []}]},
            {'q': '舌脉偏哪一类？', 'opts': [
                {'t': '舌淡苔白、脉细弱', 'add': ['she_danbai', 'mai_xiruo']},
                {'t': '舌红少苔、脉细数', 'add': ['she_shaotai', 'mai_xishuo']},
                {'t': '舌红苔黄、脉弦数', 'add': ['she_honghuang', 'mai_xian']},
                {'t': '脉弦为主', 'add': ['mai_xian']}]}]
    },
    {
        'id': 'yao_shui', 'name': '腰膝与浮肿', 'icon': '🦴', 'desc': '腰膝痠软、畏寒、水肿',
        'base': [],
        'steps': [
            {'q': '主要问题是哪一个？', 'opts': [
                {'t': '腰膝痠软无力', 'add': ['yaoxi']},
                {'t': '面部或肢体浮肿', 'add': ['shuizhong']},
                {'t': '特别怕冷、四肢冰凉', 'add': ['weihan']}]},
            {'q': '整体偏寒还是偏热？', 'opts': [
                {'t': '偏寒：怕冷、小便清长、夜尿多', 'add': ['weihan', 'niao_qing']},
                {'t': '偏热：手足心热、潮热、盗汗', 'add': ['wuxin', 'wc_cr', 'daohan']},
                {'t': '不明显', 'add': []}]},
            {'q': '排便有什么规律？', 'opts': [
                {'t': '天不亮就泻（五更泻）', 'add': ['wugeng']},
                {'t': '大便常稀、夹不消化食物', 'add': ['wanggu', 'dabian_tang']},
                {'t': '正常', 'add': []}]},
            {'q': '还有哪些伴随？', 'opts': [
                {'t': '身重困倦、头重', 'add': ['shenzhong', 'touzhong']},
                {'t': '心悸、失眠', 'add': ['xinji', 'shimian']},
                {'t': '头晕目眩、耳鸣', 'add': ['touyun', 'erming']},
                {'t': '没有', 'add': []}]},
            {'q': '舌脉偏哪一类？', 'opts': [
                {'t': '舌淡胖大有齿痕、苔白滑、脉沉迟', 'add': ['she_pang', 'mai_chenchi']},
                {'t': '舌红少苔、脉细数', 'add': ['she_shaotai', 'mai_xishuo']},
                {'t': '舌淡苔白、脉细弱', 'add': ['she_danbai', 'mai_xiruo']}]}]
    }
]

# ---- 强校验 ----
for tr in TRACKS:
    for sid in tr.get('base', []):
        assert sid in KNOWN, f"{tr['id']} base 未知症状 {sid}"
    step_ids = [s.get('id') for s in tr['steps'] if s.get('id')]
    assert len(step_ids) == len(set(step_ids)), f"{tr['id']} 步骤 id 重复"
    idset = set(step_ids)
    for st in tr['steps']:
        if st.get('next'):
            assert st['next'] in idset, f"{tr['id']} next 悬空 {st['next']}"
        for o in st['opts']:
            if o.get('goto'):
                assert o['goto'] in idset, f"{tr['id']}/{st.get('id','?')} goto 悬空 {o['goto']}"
            for sid in o['add']:
                assert sid in KNOWN, f"{tr['id']}/{st['q']} 未知症状 {sid}"
n_opt = sum(len(s['opts']) for tr in TRACKS for s in tr['steps'])
n_step = sum(len(tr['steps']) for tr in TRACKS)

json.dump({'version': rules['version'], 'tracks': TRACKS},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'  问诊轨道 {len(TRACKS)} 条 · {n_step} 问 · {n_opt} 项映射，引用全部闭合 → {OUT}')
