# gmzypdf

光明中医函授教材 PDF（共 26 册）及其对应的 Markdown 全文转换版。

## 目录结构

- `*.pdf` — 原始 PDF 电子书
- `md/` — 由 PDF 完整转换而来的 Markdown（书名与 PDF 一一对应）
  - `md/assets/<书名>/` — 该书配插图（封面、穴位图、示意图等）
- `gmzy-app/` — **光明中医文库·学习诊断系统**（HBuilderX + UniApp Vue3 工程，
  26 部全文离线阅读 + 记忆卡/复习思考题学习系统 + 中医辨证辅助，详见其 README）
- `tools/pdf_to_md.py` — PDF → Markdown 转换脚本
- `tools/check_md.py` — 转换结果校验脚本（字数覆盖率、标题与图片链接检查）
- `tools/build_app_data.py` — Markdown → App 数据包（`gmzy-app/static/`）编译脚本
- `tools/build_learn_data.py` — 学习数据提取（记忆卡 1110 张 + 复习思考题 1974 题，
  均带教材原文锚点 → `gmzy-app/static/learn/`、`gmzy-app/static/quiz/`）
- `tools/validate_learn_data.py` — 学习/辨证数据完整性校验（锚点、数量、规则引用闭合）

## 转换特性

- 依据 PDF 书签生成完整标题层级（`##` ~ `######`），章节结构与原版一致
- 自动折行合并为自然段（支持跨页段落），段落结构与原版一致
- 页码、页眉页脚与印刷目录页自动剔除
- 表格识别并转为 Markdown 表格（跨页长表自动合并）
- 位图插图按位置嵌入正文；书中矢量绘制的示意图渲染为图片嵌入
- `【讲解】``〔原文〕` 等段首标注自动加粗

## 重新生成

```bash
pip install pymupdf
python3 tools/pdf_to_md.py *.pdf --out md
python3 tools/check_md.py      # 校验
```
