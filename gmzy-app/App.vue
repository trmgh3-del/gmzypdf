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
/* 三套夜间主题：CSS 变量切换。页面根 class 形如 "night night-slate" */
.night-theme-warm { --nbg: #17140f; --ncard: #25211a; --nt: #d9d0bf; --nmuted: #9a8f7d; --nline: #3a342a; --naccent: #d8b98a; --nsec: #2b261e; }
.night-theme-slate { --nbg: #17191d; --ncard: #21252b; --nt: #c9d2dc; --nmuted: #8a94a1; --nline: #2c333d; --naccent: #9dc3b8; --nsec: #20242a; }
.night-theme-amber { --nbg: #1a130d; --ncard: #261c12; --nt: #e0d2b6; --nmuted: #a5957a; --nline: #3b2c19; --naccent: #e8b168; --nsec: #221910; }

.night .learn.learn, .night .diag.diag, .night .cards.cards, .night .quiz.quiz,
.night .mine.mine, .night .shelf.shelf, .night .search.search {
    background: var(--nbg);
}

/* 通用卡片/区块底 */
.night .sec.sec, .night .group.group, .night .rcard.rcard, .night .qcard.qcard,
.night .face.face, .night .cell.cell, .night .continue-card.continue-card,
.night .intro.intro, .night .his-item.his-item, .night .bm-item.bm-item,
.night .res-item.res-item, .night .about.about, .night .wc-item.wc-item,
.night .atlas-item.atlas-item {
    background: var(--ncard);
    border-color: var(--nline);
    color: var(--nt);
}

/* 主要文字 */
.night .sec-title.sec-title, .night .deck-name.deck-name, .night .group-name.group-name,
.night .rname.rname, .night .qtext.qtext, .night .card-front.card-front,
.night .cell-title.cell-title, .night .his-title.his-title, .night .bm-book.bm-book,
.night .res-text.res-text, .night .guide-title.guide-title, .night .his-top.his-top,
.night .back-title.back-title, .night .qbook-name.qbook-name, .night .res-book.res-book,
.night .dc-term.dc-term, .night .atlas-term.atlas-term {
    color: var(--nt);
}

/* 次要文字 */
.night text, .night .deck-desc.deck-desc, .night .deck-meta.deck-meta,
.night .qbook-meta.qbook-meta, .night .qhint.qhint, .night .card-hint.card-hint,
.night .back-body.back-body, .night .rmeta.rmeta, .night .rval.rval,
.night .his-sym.his-sym, .night .his-chapter.his-chapter, .night .bm-text.bm-text,
.night .res-chapter.res-chapter, .night .guide-text.guide-text, .night .empty.empty,
.night .counter.counter, .night .card-sub.card-sub, .night .about-line.about-line,
.night .wc-label.wc-label, .night .wc-tip.wc-tip, .night .atlas-desc.atlas-desc,
.night .atlas-tip.atlas-tip, .night .term-chip.term-chip {
    color: var(--nmuted);
}

/* 加重色 */
.night .pct.pct, .night .rname.rname, .night .nav-btn.nav-btn, .night .rgo.rgo,
.night .hit.hit, .night .rval.accent, .night .qbook-go.qbook-go,
.night .wc-num.wc-num, .night .gang.gang, .night .weak-chip.weak-chip,
.night .qerr-chip.qerr-chip, .night .rate-btn .txt, .night .hit-n.hit-n {
    color: var(--naccent);
}
.night .hit.hit { background: color-mix(in srgb, var(--naccent) 12%, transparent); }
.night .gang.gang { background: color-mix(in srgb, var(--naccent) 14%, transparent); }
.night .hit-n.hit-n { background: color-mix(in srgb, var(--naccent) 16%, transparent); }

/* 描边/分隔线 */
.night .deck.deck, .night .qbook.qbook, .night .his.his, .night .his-item.his-item,
.night .bm-item.bm-item, .night .rdetail.rdetail, .night .rgo.rgo {
    border-color: var(--nline);
}

/* 胶囊/分段/进度槽 */
.night .chip.chip { background: var(--nsec); border-color: var(--nline); color: var(--nmuted); }
.night .chip.on { background: #7d3a34; border-color: #7d3a34; color: #f3e9d2; }
.night .seg.seg { background: var(--nsec); }
.night .seg-item.seg-item { color: var(--nmuted); }
.night .seg-item.on { background: var(--ncard); color: var(--naccent); }
.night .qtag.qtag, .night .cat-chip.cat-chip, .night .hot-chip.hot-chip,
.night .term-chip.term-chip {
    background: var(--nsec);
    color: var(--nmuted);
}

.night .deck-bar.deck-bar, .night .qbook-bar.qbook-bar, .night .pbar.pbar,
.night .his-bar.his-bar, .night .scan-bar.scan-bar {
    background: var(--nline);
}

/* 评分按钮在暗底上的弱化 */
.night .rate-btn.bad { background: rgba(179, 84, 63, 0.2); }
.night .rate-btn.mid { background: rgba(200, 147, 47, 0.18); }
.night .rate-btn.good { background: rgba(74, 124, 89, 0.22); }

/* 幽灵按钮 */
.night .btn.ghost { border-color: var(--nline); color: var(--nmuted); }

/* 提示条 */
.night .notice.notice { background: rgba(200, 147, 47, 0.14); border-color: rgba(200, 147, 47, 0.4); }
.night .notice-text.notice-text { color: #cdb27a; }
.night .chap-tip.chap-tip { background: color-mix(in srgb, var(--naccent) 10%, transparent); color: var(--naccent); }

/* 搜索栏 */
.night .bar.bar .input.input { background: var(--ncard); color: var(--nt); }
.night .ph.ph { color: var(--nmuted); }

/* 卡片背面纹理色 */
.night .face.back { background: var(--nsec); }
.night .hf-chip.hf-chip { background: color-mix(in srgb, var(--naccent) 16%, transparent); color: var(--naccent); }

/* 空态按钮描边 */
.night .btn.ghost { border-color: var(--nline); }

</style>
