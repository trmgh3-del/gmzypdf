#!/usr/bin/env python3
# 知识库学科索引构建器：教材 tree 拆分为学科知识条目 → static/kg/index.json
# 条目粒度：目录树 l>=3 节点（无 l3 则取 l2），按所在书目录分组
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), '..', 'gmzy-app')
BD = os.path.join(ROOT, 'static', 'books-data')
OUT = os.path.join(ROOT, 'static', 'kg', 'index.json')

# 学科课程分类（curriculum taxonomy）→ 教材 slugs
CATS = [
    {'key': 'basics',  'name': '中医基础', 'icon': '◐', 'desc': '阴阳五行·藏象经络·精气血津液·病因病机',
     'slugs': ['0', '5', '6']},
    {'key': 'diag',    'name': '中医诊法', 'icon': '☝', 'desc': '望闻问切·八纲辨证·临证程序·口诀速记',
     'slugs': ['8', '7', '7b'], 'atlas': True},
    {'key': 'classic', 'name': '经典医著', 'icon': '典', 'desc': '内经·伤寒·金匮·温病·历代医籍评介',
     'slugs': ['10', '11', '12', '13', '25']},
    {'key': 'herb',    'name': '中药学',   'icon': '艹', 'desc': '本草备要四百味·性味归经·功效主治',
     'slugs': ['14']},
    {'key': 'fangji',  'name': '方剂学',   'icon': '方', 'desc': '君臣佐使·常用成方组成与方解',
     'slugs': ['29']},
    {'key': 'neike',   'name': '中医内科', 'icon': '内', 'desc': '脏腑病证·气血津液·常见内科证治',
     'slugs': ['15', '26']},
    {'key': 'clinic',  'name': '临床各科', 'icon': '临', 'desc': '外·骨伤·眼·妇·儿·喉科证治',
     'slugs': ['16', '17', '18', '19', '20', '22']},
    {'key': 'acu',     'name': '针灸学',   'icon': '针', 'desc': '经络腧穴·刺灸法·处方配穴',
     'slugs': ['21', '21b', '21c']},
    {'key': 'misc',    'name': '医案与附录', 'icon': '医', 'desc': '名医医案选读·文库树录',
     'slugs': ['23', '1000']}
]

# 学科 → 学习工具映射（枢纽入口）
TOOLS = {
    'basics':  {'decks': ['koujue'],              'atlas': False},
    'diag':    {'decks': ['bingz'],               'atlas': True},
    'classic': {'decks': [],                      'atlas': False},
    'herb':    {'decks': ['herb'],                'atlas': False},
    'fangji':  {'decks': ['fangji', 'koujue'],    'atlas': False},
    'neike':   {'decks': [],                      'atlas': False},
    'clinic':  {'decks': [],                      'atlas': False},
    'acu':     {'decks': ['point'],               'atlas': False},
    'misc':    {'decks': ['yian'],                'atlas': False}
}

SKIP_TITLES = ('校对', '版权', '封面', '电子录入')


def entries_of_book(data):
    """取树 l>=3 节点；全树无 l3 则取 l2；返回 [{t, pt, g}]"""
    tree = data.get('tree') or []
    out = []

    def walk(node, parent_title):
        for child in node.get('c') or []:
            lv = child.get('l', 0)
            if lv >= 3 and child.get('g') is not None:
                out.append({'t': child.get('x', ''), 'pt': parent_title, 'g': child['g']})
            walk(child, child.get('x') if lv >= 2 else parent_title)

    for root in tree:
        walk(root, '')
    if not out:  # 兜底：l2 章级
        def walk2(node, parent_title):
            for child in node.get('c') or []:
                if child.get('l', 0) >= 2 and child.get('g') is not None:
                    out.append({'t': child.get('x', ''), 'pt': parent_title, 'g': child['g']})
                walk2(child, child.get('x', ''))
        for root in tree:
            walk2(root, '')
    return [e for e in out if e['t'] and not any(k in e['t'] for k in SKIP_TITLES)]


def main():
    catalog = {b['slug']: b for b in json.load(open(os.path.join(BD, 'catalog.json'), encoding='utf-8'))}
    quiz_index = {e['slug']: e for e in json.load(open(os.path.join(ROOT, 'static', 'quiz', 'index.json'), encoding='utf-8'))}

    result_cats = []
    total = 0
    for cat in CATS:
        books, entries, quiz = [], [], []
        for slug in cat['slugs']:
            meta = catalog.get(slug)
            if not meta:
                continue
            books.append({'slug': slug, 'title': meta['title']})
            data = json.load(open(os.path.join(BD, f'{slug}.json'), encoding='utf-8'))
            for e in entries_of_book(data):
                entries.append({'b': slug, 'bt': meta['title'], 't': e['t'], 'pt': e['pt'], 'g': e['g']})
            q = quiz_index.get(slug)
            if q:
                quiz.append({'slug': slug, 'count': q['count']})
        total += len(entries)
        result_cats.append({
            'key': cat['key'], 'name': cat['name'], 'icon': cat['icon'], 'desc': cat['desc'],
            'decks': TOOLS[cat['key']]['decks'], 'atlas': TOOLS.get(cat['key'], {}).get('atlas', False),
            'books': books, 'quiz': quiz, 'quizCount': sum(q['count'] for q in quiz),
            'bookCount': len(books), 'entryCount': len(entries), 'entries': entries
        })

    payload = {'version': 1, 'cats': result_cats, 'totalEntries': total, 'totalBooks': len(catalog)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))
    size_kb = os.path.getsize(OUT) / 1024
    print(f'KG OK: {len(result_cats)} 学科 · {total} 条 · {size_kb:.0f}KB → {OUT}')
    for c in result_cats:
        print(f"  {c['icon']} {c['name']}: {c['bookCount']} 书 · {c['entryCount']} 条 · 题库 {c['quizCount']}")
    assert total > 1000, f'知识条目总量异常 {total}'
    assert len(result_cats) == 9, '学科须为 9'


if __name__ == '__main__':
    main()
