#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_migrate_v1.py — 从 v1（20525b7）旧学习数据生成迁移映射表。

旧方案：卡片 key = <deck>_<index>，题库 key = <slug+书名>，题 key = index。
本脚本把旧数据的「位置 → 名称/题面」映射固化为 static/learn/migrate-v1.json，
App 端用它把老用户进度无损迁移到 uuid 稳定键。
"""
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = "20525b7"  # 旧学习数据所在提交
OUT = os.path.join(ROOT, "gmzy-app", "static", "learn", "migrate-v1.json")


def git_show(path):
    r = subprocess.run(["git", "show", f"{REV}:{path}"], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git show 失败: {path}: {r.stderr[:200]}")
    return json.loads(r.stdout)


mig = {"from": REV, "decks": {}, "quiz": {}}
for did in ("fangji", "herb", "point", "koujue"):
    cards = git_show(f"gmzy-app/static/learn/deck-{did}.json")
    mig["decks"][did] = [c["front"] for c in cards]
    print(f"deck {did}: {len(cards)} fronts")

# 用旧提交中的文件名（磁盘上可能已是新命名的文件；中文名需 -z 防转义）
tree = subprocess.run(["git", "ls-tree", "-r", "-z", "--name-only", REV, "--", "gmzy-app/static/quiz"],
                      cwd=ROOT, capture_output=True, check=True)
for full in sorted(tree.stdout.decode("utf-8").split("\0")):
    if not full.endswith(".json") or full.endswith("index.json"):
        continue
    name = os.path.basename(full)
    key = os.path.splitext(name)[0]
    qs = git_show(full)
    mig["quiz"][key] = {"qs": [q["q"] for q in qs]}
    print(f"quiz {key}: {len(qs)} texts")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(mig, f, ensure_ascii=False, separators=(",", ":"))
print("->", OUT, os.path.getsize(OUT), "bytes")
