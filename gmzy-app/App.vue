<script>
export default {
    onLaunch() {
        // 应用启动：状态在 common/store.js 中惰性恢复
        // #ifdef H5
        // H5 离线缓存：注册数据目录 Service Worker（生产构建才启用）
        if (typeof window !== 'undefined' && 'serviceWorker' in navigator && location.hostname !== 'localhost') {
            try {
                const link = document.createElement('link')
                link.rel = 'manifest'
                link.href = 'static/pwa/manifest.webmanifest'
                document.head.appendChild(link)
                // 离线 SW: 站点根存在 /sw.js 时注册（部署指引见 README；
                // SW 作用域受路径限制，只在本文件被放到站点根才生效）
                fetch('/sw.js', { method: 'HEAD' }).then((r) => {
                    if (r.ok) navigator.serviceWorker.register('/sw.js').catch(() => {})
                }).catch(() => {})
            } catch (e) { /* noop */ }
        }
        // #endif
    },
    onShow() {},
    onHide() {}
}
</script>

<style lang="scss">
/* 全局基础样式 */
page {
    background-color: #f6f1e5;
    color: #37332b;
    font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC',
        'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
    font-size: 15px;
    line-height: 1.6;
}

view, text, scroll-view, image, input, picker, slider, button {
    box-sizing: border-box;
}

.serif-font {
    font-family: 'Songti SC', 'STSong', 'STZhongsong', 'Noto Serif CJK SC',
        'Noto Serif SC', 'SimSun', serif;
}

/* ================= 全局夜间模式（以 .night 双类名提权覆盖页面局部样式） ================= */
.night .learn.learn, .night .diag.diag, .night .cards.cards, .night .quiz.quiz,
.night .mine.mine, .night .shelf.shelf, .night .search.search {
    background: #17140f;
}

/* 通用卡片/区块底 */
.night .sec.sec, .night .group.group, .night .rcard.rcard, .night .qcard.qcard,
.night .face.face, .night .cell.cell, .night .continue-card.continue-card,
.night .intro.intro, .night .his-item.his-item, .night .bm-item.bm-item,
.night .res-item.res-item, .night .about.about {
    background: #25211a;
    border-color: #3a342a;
    color: #d9d0bf;
}

/* 主要文字 */
.night .sec-title.sec-title, .night .deck-name.deck-name, .night .group-name.group-name,
.night .rname.rname, .night .qtext.qtext, .night .card-front.card-front,
.night .cell-title.cell-title, .night .his-title.his-title, .night .bm-book.bm-book,
.night .res-text.res-text, .night .guide-title.guide-title, .night .his-top.his-top,
.night .back-title.back-title, .night .qbook-name.qbook-name, .night .res-book.res-book {
    color: #d9d0bf;
}

/* 次要文字 */
.night text, .night .deck-desc.deck-desc, .night .deck-meta.deck-meta,
.night .qbook-meta.qbook-meta, .night .qhint.qhint, .night .card-hint.card-hint,
.night .back-body.back-body, .night .rmeta.rmeta, .night .rval.rval,
.night .his-sym.his-sym, .night .his-chapter.his-chapter, .night .bm-text.bm-text,
.night .res-chapter.res-chapter, .night .guide-text.guide-text, .night .empty.empty,
.night .counter.counter, .night .card-sub.card-sub, .night .about-line.about-line {
    color: #9a8f7d;
}

/* 加重色保持 */
.night .pct.pct, .night .rname.rname, .night .nav-btn.nav-btn, .night .rgo.rgo,
.night .hit.hit, .night .rval.accent, .night .qbook-go.qbook-go {
    color: #d8b98a;
}
.night .hit.hit { background: rgba(216, 185, 138, 0.12); }
.night .hit { color: #d8b98a; }

/* 描边/分隔线 */
.night .deck.deck, .night .qbook.qbook, .night .his.his, .night .his-item.his-item,
.night .bm-item.bm-item, .night .rdetail.rdetail, .night .rgo.rgo {
    border-color: #332d23;
}

/* 胶囊/分段/进度槽 */
.night .chip.chip { background: #2b261e; border-color: #3a342a; color: #b0a796; }
.night .chip.on { background: #7d3a34; border-color: #7d3a34; color: #f3e9d2; }
.night .seg.seg { background: #2b261e; }
.night .seg-item.seg-item { color: #93897a; }
.night .seg-item.on { background: #241f18; color: #d8b98a; }
.night .qtag.qtag { background: #2b261e; color: #93897a; }
.night .cat-chip.cat-chip { background: #2b261e; color: #93897a; }
.night .hot-chip.hot-chip { background: #2b261e; color: #93897a; }

.night .deck-bar.deck-bar, .night .qbook-bar.qbook-bar, .night .pbar.pbar,
.night .his-bar.his-bar, .night .scan-bar.scan-bar {
    background: #332d23;
}

/* 评分按钮在暗底上的弱化 */
.night .rate-btn.bad { background: rgba(179, 84, 63, 0.2); }
.night .rate-btn.mid { background: rgba(200, 147, 47, 0.18); }
.night .rate-btn.good { background: rgba(74, 124, 89, 0.22); }

/* 幽灵按钮 */
.night .btn.ghost { border-color: #4a4335; color: #93897a; }

/* 提示条 */
.night .notice.notice { background: rgba(200, 147, 47, 0.14); border-color: rgba(200, 147, 47, 0.4); }
.night .notice-text.notice-text { color: #cdb27a; }

/* 搜索栏 */
.night .bar.bar .input.input { background: #25211a; color: #d9d0bf; }
.night .ph.ph { color: #6f675a; }

/* 卡片背面纹理色 */
.night .face.back { background: #221d15; }

/* 空态按钮描边 */
.night .btn.ghost { border-color: #4a4335; }
</style>
