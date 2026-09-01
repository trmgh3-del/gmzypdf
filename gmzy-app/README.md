# 光明中医文库（UniApp Vue3）

基于 **HBuilderX + UniApp（Vue3 语法）** 开发的跨平台离线电子书 App，
收录光明中医函授教材 **26 部**全文精排内容（约 1300 万字、900+ 插图），
全部数据打包在应用内，完全离线可用。

## 功能

- **书架**：封面网格、分类筛选（入门 / 经典方药 / 临床 / 针灸）、书籍简介卡
- **阅读器**：
  - 三种主题：宣纸 / 护眼绿 / 夜读；宋体 / 黑体切换；字号、行距调节
  - 目录抽屉（完整章节树，定位跳转）、进度条章节滑杆
  - 段内加粗标注、宽表格横向滚动、图片点击放大
  - 自动保存阅读进度，书签随记随取，点击空白处唤出/隐藏工具栏
- **搜索**：全库 / 单书全文检索，关键字高亮，结果直达原文位置
- **我的**：在读统计、阅读历史（带进度条）、书签管理、清空/删除
- **分享**：微信内可分享当前书籍

## 用 HBuilderX 运行

1. 安装 HBuilderX 3.6+（建议最新版），打开 “文件 → 打开目录”，选择本目录（`gmzy-app`）。
2. 首次打开时，点击 `manifest.json`，在 **基础配置** 中点 “重新获取” 自动生成 AppID。
3. 运行：
   - **运行 → 运行到内置浏览器**：即开即见的 H5 预览。
   - **运行 → 运行到手机或模拟器 → Android/iOS**：真机调试（基座）。
4. 打包安装包：**发行 → 原生App-云打包**，选 Android（apk）/iOS（ipa）即可。

## 目录结构

```
gmzy-app/
├── App.vue / main.js / pages.json / manifest.json / uni.scss
├── static/
│   ├── books-data/      # 26 部书的结构化内容 JSON（运行时按需读取）
│   │   ├── catalog.json #   书目总录（标题/封面/章节数/字数/摘要）
│   │   └── <slug>.json  #   每本书：章节区间 + 标题树 + 内容块
│   ├── books/<slug>/    # 每本书的全部插图（原位嵌入正文）
│   └── tabbar/          # 底部导航图标
├── common/              # 数据访问层、全局状态（进度/书签/设置持久化）、工具
├── components/          # BookCover / BlocksView / ChapterDrawer / SettingsPanel
└── pages/
    ├── index/           # 书架
    ├── reader/          # 阅读器
    ├── search/          # 全文搜索
    └── mine/            # 我的（历史/书签/关于）
```

## 附：用 Vue CLI 构建（已通过真实构建验证）

本目录为 HBuilderX 目录结构，可直接用 HBuilderX 打开。若偏好命令行：

```bash
npm create uni@latest my-app          # 选择 Vue3 模板
cd my-app && npm install
rm -rf src && cp -r <本目录> src      # 用本目录内容替换脚手架 src
npx unh build h5                      # H5（已验证通过）
npx unh build app                     # App 打包资源（已验证通过）
# 输出在 dist/build/<platform>，App 资源可导入 HBuilderX 云打包
```

验证环境：vite 5.2.8 + @dcloudio 3.0.0-5000720260410001 + vue 3.4.21。

## 数据管线（可选，仓库 tools/ 内）

```bash
python3 tools/pdf_to_md.py *.pdf --out md       # PDF → Markdown
python3 tools/build_app_data.py                 # Markdown → App 数据包
```

## 说明

- 目标平台：**Android / iOS App** 与 **H5**。微信小程序因包体限制（主包 2MB）
  需将 `books/` 与图片迁至 CDN 并将 `common/books.js` 改为网络加载，暂未默认开启。
- 字体（宋体）依赖设备系统字体，未内置字体文件。
