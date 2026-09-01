#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_md.py — 校验 pdf_to_md 转换结果。
对比：PDF 提取文本字符数（去页码行）vs Markdown 文本字符数；
检查图片链接有效性、标题覆盖率。输出覆盖率报告。
"""
import os
import re
import sys
import glob
import unicodedata
import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_to_md import norm, PAGENUM_RE

def pdf_chars(doc):
    n = 0
    for i in range(len(doc)):
        t = doc[i].get_text()
        for line in t.split("\n"):
            s = line.strip().strip(" ·•-—–_.○◦●…　")
            if PAGENUM_RE.match(s):
                continue
            n += len(re.sub(r"\s+", "", line))
    return n

def md_chars(md_text):
    # 去掉 markdown 标记、图片链接、表格管线
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md_text)
    body = re.sub(r"[#*`>|]", "", body)
    body = re.sub(r"\s+", "", body)
    return len(body), body

def main():
    root = os.getcwd()
    report = []
    for pdf in sorted(glob.glob("*.pdf")):
        stem = os.path.splitext(pdf)[0]
        md_path = os.path.join("md", f"{stem}.md")
        if not os.path.exists(md_path):
            report.append((stem, "MD缺失", -1))
            continue
        doc = pymupdf.open(pdf)
        pc = pdf_chars(doc)
        toc = doc.get_toc(simple=True)
        doc.close()
        with open(md_path, encoding="utf-8") as f:
            md = f.read()
        mc, mdbody = md_chars(md)
        # 图片链接
        bad_img = 0
        for m in re.finditer(r"!\[[^\]]*\]\(([^)]*)\)", md):
            p = os.path.join("md", m.group(1))
            if not os.path.exists(p):
                bad_img += 1
        # 标题覆盖：TOC 标题（归一化）是否出现在 md 标题行中
        heads = "\n".join(l for l in md.split("\n") if l.startswith("#"))
        n_heads = re.findall(r"(?m)^#{2,6}\s*(.+)$", md)
        miss_head = sum(1 for _, t, _ in toc
                        if norm(t) not in norm(heads))
        ratio = mc / pc if pc else 0
        report.append((stem, f"chars {mc}/{pc} = {ratio:.1%}",
                       f"表头缺失{miss_head} 坏图{bad_img} TOC标题{len(toc)} md标题{len(n_heads)}"))
        print(f"{stem}: 字数覆盖率 {ratio:6.1%} | 标题缺失 {miss_head} | 坏图链 {bad_img}")
    print("\n说明：覆盖率略低于100%属正常（页眉页码、印刷目录页已按设计剔除）；过低则需排查。")

if __name__ == "__main__":
    main()
