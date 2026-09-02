<template>
    <view class="reader" :class="themeClass" :style="cssVars" v-if="book">
        <!-- 顶部栏 -->
        <view
            class="nav"
            :style="{ paddingTop: statusBar + 'px', transition: 'opacity .2s' }"
            v-show="showBars"
        >
            <view class="nav-btn" @tap="goBack"><text class="nav-btn-t">‹ 书架</text></view>
            <text class="nav-title serif-font">{{ book.title }}</text>
            <view class="nav-btn nav-btn-r" @tap="showDrawer = true"><text class="nav-btn-t">目录</text></view>
        </view>

        <!-- 正文 -->
        <scroll-view
            class="content"
            :class="{ serif: settings.serif }"
            scroll-y
            :scroll-top="scrollTopVal"
            :scroll-into-view="scrollIntoId"
            :scroll-with-animation="false"
            :show-scrollbar="false"
            @scroll="onScroll"
            @scrolltolower="appendNext"
            :lower-threshold="500"
            @tap="toggleBars"
        >
            <view
                class="content-inner"
                :class="{ 'turn-l': turnDir === 'l', 'turn-r': turnDir === 'r' }"
                @touchstart="csStart"
                @touchend="csEnd"
            >
                <template v-for="ci in renderedIdx" :key="ci">
                    <BlocksView
                        :blocks="chapterBlocks(ci)"
                        :slug="slug"
                        :dict-mode="dictMode"
                        @img="previewImg"
                        @blk="onDictBlk"
                        @ref="onRefLink"
                    />
                    <view class="chapter-sep">
                        <text class="chapter-sep-t">{{ chapters[ci].title }}</text>
                    </view>
                    <view class="ch-quiz" v-if="chapQuiz(ci).length">
                        <view v-for="qb in chapQuiz(ci)" :key="qb.f" class="ch-quiz-row" @click.stop="goQuiz(qb, ci)">
                            <text class="ch-quiz-t">📝 本章复习思考题 {{ qb.n }} 道</text>
                            <text class="ch-quiz-a">开始作答 ›</text>
                        </view>
                    </view>
                </template>
                <view class="load-hint" v-if="hasNext">上拉继续阅读 · {{ nextTitle }}</view>
                <view class="load-hint load-end" v-else>— 全书完 —</view>
                <view class="bottom-space" />
            </view>
        </scroll-view>

        <!-- 底部栏 -->
        <view class="foot" v-show="showBars" :style="{ paddingBottom: 'calc(10rpx + env(safe-area-inset-bottom))' }">
            <view class="foot-row1">
                <view class="foot-btn" @tap="prevChapter"><text :class="{ disabled: !canPrev }">上一章</text></view>
                <slider
                    class="foot-slider"
                    :min="0"
                    :max="chapters.length - 1"
                    :value="visualChIdx"
                    :block-size="16"
                    :activeColor="sliderActive"
                    :backgroundColor="sliderBg"
                    @change="onSlider"
                />
                <view class="foot-btn" @tap="nextChapter"><text :class="{ disabled: !hasNext }">下一章</text></view>
            </view>
            <view class="foot-row2">
                <text class="foot-meta">{{ chapters[visualChIdx] ? chapters[visualChIdx].title : '' }}</text>
                <text class="foot-meta">{{ percentText }}</text>
                <view class="foot-act" :class="{ 'act-on': dictMode }" @tap="toggleDict">{{ dictMode ? '查词中…' : '查词' }}</view>
                <view class="foot-act" @tap="bookmarkHere">＋书签</view>
                <view class="foot-act" @tap="showSettings = true">设置</view>
            </view>
        </view>

        <ChapterDrawer
            v-model:show="showDrawer"
            :tree="book.tree"
            :currentG="currentG"
            @jump="jumpToG"
        />
        <SettingsPanel v-model:show="showSettings" />
        <!-- 图片缩放遮罩 -->
        <view v-if="zoomImg" class="zoom-mask" @tap="closeZoom">
            <movable-area class="zoom-area">
                <movable-view
                    class="zoom-view"
                    direction="all"
                    :scale="true"
                    :scale-min="0.6"
                    :scale-max="4"
                    :scale-value="zoomInit"
                    out-of-bounds
                    @scale="onZoomScale"
                    @tap.stop="zoomTap"
                >
                    <image class="zoom-img" :src="zoomImg.src" mode="widthFix" />
                </movable-view>
            </movable-area>
            <text v-if="zoomImg.cap" class="zoom-cap">{{ zoomImg.cap }}</text>
            <text class="zoom-close">轻点空白关闭 · 双击 2×</text>
        </view>

        <DictSheet :show="dictOpen" :terms="dictTerms" :snippet="dictSnippet" @close="dictOpen = false" />

        <view class="toast" v-if="toast">{{ toast }}</view>
    </view>
    <view class="loading" v-else>
        <text class="loading-t">载入书籍…</text>
    </view>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, getCurrentInstance } from 'vue'
import { onLoad, onUnload, onBackPress, onShareAppMessage } from '@dcloudio/uni-app'
import { loadBook, getBookMeta } from '../../common/books.js'
import { store, saveProgress, pushHistory, addBookmark, pending } from '../../common/store.js'
import {
    statusBarHeight, debounce, chapterOf, excerptText
} from '../../common/util.js'
import BlocksView from '../../components/BlocksView.vue'
import ChapterDrawer from '../../components/ChapterDrawer.vue'
import SettingsPanel from '../../components/SettingsPanel.vue'
import DictSheet from '../../components/DictSheet.vue'
import { findTerms } from '../../common/termdict.js'

const THEMES = {
    paper: { bg: '#f6f1e5', fg: '#37332b', muted: '#8d8371', card: '#fffdf7', line: '#e4dcc8', accent: '#8b3a3a', thBg: 'rgba(139,58,58,.06)' },
    eye: { bg: '#d3e4cd', fg: '#2e3a2c', muted: '#6f7f6a', card: '#e6f2e0', line: '#bfd8b8', accent: '#4a6b46', thBg: 'rgba(74,107,70,.08)' },
    night: { bg: '#17191d', fg: '#b9bec7', muted: '#6b7280', card: '#1e2126', line: '#2a2e35', accent: '#c08766', thBg: 'rgba(192,135,102,.10)' }
}

const settings = store.settings
const statusBar = ref(statusBarHeight())

const slug = ref('')
const book = ref(null)
const chapters = computed(() => (book.value ? book.value.chapters : []))
const totalBlocks = computed(() => (book.value ? book.value.blocks.length : 1))

// 渲染窗口：从 startIdx 章开始，连续 renderedIdx.length 章
const startIdx = ref(0)
const windowLen = ref(1)
const renderedIdx = computed(() => {
    const arr = []
    for (let i = 0; i < windowLen.value && startIdx.value + i < chapters.value.length; i++) {
        arr.push(startIdx.value + i)
    }
    return arr
})

const scrollTopVal = ref(0)
const visualChIdx = ref(0)
const currentG = ref(0)
const showBars = ref(true)
const showDrawer = ref(false)
const showSettings = ref(false)
const toast = ref('')

let pendingRestore = null // {scrollTop}
let toastTimer = null

const themeClass = computed(() => 'theme-' + settings.theme + (settings.serif ? ' serif-mode' : ''))
const cssVars = computed(() => {
    const t = THEMES[settings.theme] || THEMES.paper
    return {
        '--bg': t.bg,
        '--fg': t.fg,
        '--muted': t.muted,
        '--card': t.card,
        '--line': t.line,
        '--accent': t.accent,
        '--th-bg': t.thBg,
        '--fs': settings.fontSize + 'px',
        '--lh': settings.lineHeight
    }
})

const hasNext = computed(() => startIdx.value + windowLen.value < chapters.value.length)
const canPrev = computed(() => visualChIdx.value > 0)
const nextTitle = computed(() => {
    const n = chapters.value[startIdx.value + windowLen.value]
    return n ? n.title : ''
})
const percentText = computed(() => {
    const p = Math.min(100, (currentG.value / totalBlocks.value) * 100)
    return p.toFixed(1) + '%'
})
const sliderActive = computed(() => (THEMES[settings.theme] || THEMES.paper).accent)
const sliderBg = computed(() => (THEMES[settings.theme] || THEMES.paper).line)

// ---- 章末复习思考题入口 ----
const quizAll = ref([]) // [{f, book(slug), bookTitle, items:[{g,...}]}]

async function ensureQuizAll() {
    if (quizAll.value.length || quizAll.value.loading) return
    quizAll.value.loading = true
    try {
        const idx = await loadQuizIndex()
        const mine = idx.filter((b) => b.slug === slug.value)
        const loaded = []
        for (const b of mine) {
            const items = await loadQuizBook(b.f)
            loaded.push({ f: b.f, bookTitle: b.book, items })
        }
        quizAll.value = loaded
    } catch (e) { /* 无题库时忽略 */ }
}

function chapQuiz(ci) {
    const ch = chapters.value[ci]
    if (!ch) return []
    const out = []
    for (const b of quizAll.value) {
        const n = b.items.reduce(
            (c, it) => c + (it.g !== null && it.g !== undefined && it.g >= ch.s && it.g <= ch.e ? 1 : 0),
            0
        )
        if (n) out.push({ ...b, n })
    }
    return out
}

function goQuiz(qb, ci) {
    const ch = chapters.value[ci]
    uni.navigateTo({
        url: `/pages/quiz/quiz?k=${encodeURIComponent(qb.f)}&title=${encodeURIComponent(qb.bookTitle)}&cs=${ch.s}&ce=${ch.e}&ctitle=${encodeURIComponent(ch.title)}`
    })
}

function chapterBlocks(ci) {
    const c = chapters.value[ci]
    return book.value.blocks.slice(c.s, c.e)
}

function showToast(t, ms = 1600) {
    toast.value = t
    if (toastTimer) clearTimeout(toastTimer)
    toastTimer = setTimeout(() => (toast.value = ''), ms)
}

async function bootstrap(slugStr, opt) {
    slug.value = slugStr
    try {
        book.value = await loadBook(slugStr)
        ensureQuizAll()
    } catch (e) {
        showToast('书籍载入失败')
        console.error(e)
        return
    }
    const meta = getBookMeta(slugStr)
    pushHistory({
        slug: slugStr,
        title: book.value.title,
        cover: meta ? meta.cover : '',
        chapter: '',
        gIdx: 0,
        chIdx: 0,
        scrollTop: 0,
        percent: 0
    })
    let ch = 0
    let g = opt.g !== undefined && opt.g !== null ? Number(opt.g) : null
    if (g !== null && !Number.isNaN(g)) {
        ch = chapterOf(book.value, g)
    } else {
        g = null
    }
    if (g === null && opt.resume) {
        const p = store.progress[slugStr]
        if (p && typeof p.chIdx === 'number') {
            ch = Math.min(p.chIdx, chapters.value.length - 1)
            pendingRestore = { scrollTop: p.scrollTop || 0 }
        }
    }
    renderFrom(ch)
    if (g !== null) {
        const target = g
        await nextTick()
        setTimeout(() => scrollToBlock(target), 250)
    }
}

function renderFrom(ch, keepScroll = 0) {
    startIdx.value = Math.max(0, ch)
    windowLen.value = 1
    visualChIdx.value = startIdx.value
    currentG.value = chapters.value[startIdx.value].s
    scrollTopVal.value = 0
    if (keepScroll > 0 || pendingRestore) {
        const st = keepScroll || (pendingRestore && pendingRestore.scrollTop) || 0
        pendingRestore = null
        nextTick(() => {
            setTimeout(() => {
                scrollTopVal.value = st
            }, 120)
        })
    }
}

function appendNext() {
    if (hasNext.value) windowLen.value += 1
}

function prevChapter() {
    if (!canPrev.value) return
    renderFrom(visualChIdx.value - 1)
    recordJump()
}

function nextChapter() {
    const nxt = Math.min(visualChIdx.value + 1, chapters.value.length - 1)
    renderFrom(nxt)
    recordJump()
}

function onSlider(e) {
    const v = Number(e.detail.value)
    if (v === visualChIdx.value) return
    renderFrom(v)
}

function jumpToG(g) {
    const ch = chapterOf(book.value, g)
    renderFrom(ch)
    setTimeout(() => scrollToBlock(g), 250)
    recordJump()
}

// 通过 scroll-view 的 scroll-into-view 特性滚动到指定块
const scrollIntoId = ref('')

function scrollToBlock(g) {
    currentG.value = g
    scrollIntoId.value = ''
    nextTick(() => {
        setTimeout(() => {
            scrollIntoId.value = 'blk-' + g
        }, 30)
    })
}

// 滚动处理：估算当前可视位置（块序号 g）
const lastScroll = { scrollTop: 0, scrollHeight: 1 }

function onScroll(e) {
    lastScroll.scrollTop = e.detail.scrollTop
    lastScroll.scrollHeight = e.detail.scrollHeight || 1
    scheduleEstimate()
}

const scheduleEstimate = debounce(() => {
    // 估算：渲染窗口内块数，按滚动比例折算全局位置
    const chs = renderedIdx.value
    if (!chs.length || !book.value) return
    let spanBlocks = 0
    for (const ci of chs) spanBlocks += chapters.value[ci].e - chapters.value[ci].s
    const frac = Math.min(1, Math.max(0, lastScroll.scrollTop / Math.max(lastScroll.scrollHeight, 1)))
    const within = Math.floor(frac * spanBlocks)
    let acc = 0
    let chIdx = chs[0]
    for (const ci of chs) {
        const len = chapters.value[ci].e - chapters.value[ci].s
        if (within < acc + len) {
            chIdx = ci
            break
        }
        acc += len
    }
    visualChIdx.value = chIdx
    currentG.value = chapters.value[chIdx].s + Math.max(0, within - acc)
    persistProgress()
}, 160)

function persistProgress() {
    if (!book.value) return
    saveProgress(slug.value, {
        chIdx: startIdx.value,
        scrollTop: lastScroll.scrollTop,
        gIdx: currentG.value,
        percent: currentG.value / totalBlocks.value
    })
}

function recordJump() {
    if (!book.value) return
    const ch = chapters.value[visualChIdx.value]
    pushHistory({
        slug: slug.value,
        title: book.value.title,
        cover: getBookMeta(slug.value)?.cover || '',
        chapter: ch ? ch.title : '',
        gIdx: currentG.value,
        chIdx: startIdx.value,
        scrollTop: 0,
        percent: currentG.value / totalBlocks.value
    })
}

function toggleBars() {
    showBars.value = !showBars.value
}

function goBack() {
    uni.navigateBack({ delta: 1 })
}

// ---- 查词 ----
const dictMode = ref(false)
const dictOpen = ref(false)
const dictTerms = ref([])
const dictSnippet = ref('')

function toggleDict() {
    dictMode.value = !dictMode.value
    showToast(dictMode.value ? '查词模式：点按段落匹配卡片词条' : '已退出查词模式')
}

function blockFullText(b) {
    if (b.t === 'h') return b.x || ''
    if (b.t === 'p') return (b.segs || []).map((s) => s.x).join('')
    return ''
}

async function onDictBlk(b) {
    const text = blockFullText(b)
    dictSnippet.value = text.length > 60 ? text.slice(0, 60) + '…' : text
    const hits = await findTerms(text)
    dictTerms.value = hits
    dictOpen.value = true
    if (!hits.length) showToast('本段未命中卡片词条')
}

// ---- 图片双指缩放 ----
const zoomImg = ref(null) // {src, cap}
const zoomScale = ref(1)
const zoomInit = ref(1)
let lastTapZoom = 0

function previewImg(b) {
    zoomImg.value = { src: `/static/books/${slug.value}/${b.s}`, cap: b.a || '' }
    zoomScale.value = 1
    zoomInit.value = 1
}

function closeZoom() {
    zoomImg.value = null
}

function onZoomScale(e) {
    zoomScale.value = e.detail.scale
}

function zoomTap() {
    const now = Date.now()
    if (now - lastTapZoom < 300) {
        zoomScale.value = zoomScale.value > 1 ? 1 : 2
        zoomInit.value = zoomScale.value
    }
    lastTapZoom = now
}

// ---- 左右滑翻章 + 动画 ----
const turnDir = ref('')
const csX = ref(0)
const csY = ref(0)

function csStart(e) {
    const t = e.changedTouches[0]
    csX.value = t.clientX
    csY.value = t.clientY
}

function csEnd(e) {
    const t = e.changedTouches[0]
    const dx = t.clientX - csX.value
    const dy = Math.abs(t.clientY - csY.value)
    if (Math.abs(dx) < 110 || dy > 90 || dictMode.value) return
    if (dx < 0 && nextChapterAvail()) {
        flash('l')
        nextChapter()
    } else if (dx > 0 && canPrev.value) {
        flash('r')
        prevChapter()
    }
}

function nextChapterAvail() {
    return visualChIdx.value < chapters.value.length - 1 || hasNext.value
}

function flash(d) {
    turnDir.value = d
    setTimeout(() => (turnDir.value = ''), 320)
}

// ---- 正文互链跳转 ----
const HN = '一二三四五六七八九十'

function han2num(x) {
    x = x.replace(/[零〇]/g, '')
    if (/^\d+$/.test(x)) return +x
    if (x === '十') return 10
    let n = 0
    if (x.includes('百')) {
        const [h, r] = x.split('百')
        n += (Math.max(0, HN.indexOf(h)) + 1) * 100
        x = r || ''
    }
    if (x.includes('十')) {
        const [a, b] = x.split('十')
        n += (a ? Math.max(0, HN.indexOf(a)) + 1 : 1) * 10 + (b ? Math.max(0, HN.indexOf(b)) + 1 : 0)
        return n
    }
    const i = HN.indexOf(x)
    return n + (i >= 0 ? i + 1 : 0)
}

let catCache = null
async function catOf() {
    if (!catCache) catCache = await loadCatalog()
    return catCache
}

function onRefLink(ref) {
    if (ref.startsWith('《')) {
        const core = ref
            .replace(/[《》]/g, '')
            .replace(/(讲解|浅释|备要|辑要|订|指南|浅说|新版|重印)/g, '')
            .trim()
        catOf().then((list) => {
            const hits = list.filter(
                (c) => core.length >= 2 && (c.title.includes(core) || core.includes(c.title))
            )
            if (hits.length === 1) {
                showToast('→ ' + hits[0].title)
                uni.navigateTo({ url: `/pages/reader/reader?slug=${hits[0].slug}` })
            } else {
                showToast(hits.length > 1 ? `有 ${hits.length} 本书相关，已改为检索` : '未找到对应书目，已改为检索')
                pending.keyword = core
                uni.switchTab({ url: '/pages/search/search' })
            }
        })
        return
    }
    const m = ref.match(/^第([一二三四五六七八九十百〇零0-9]{1,6})(章|节|篇)/)
    if (!m) return
    const n = han2num(m[1])
    if (n <= 0) return
    const kind = m[2]
    const ci = chapters.value.findIndex(
        (c) => c.title.startsWith(`第${m[1]}${kind}`) || c.title.startsWith(`第${n}${kind}`)
    )
    if (ci >= 0) {
        renderFrom(ci)
        recordJump()
        showToast('→ ' + chapters.value[ci].title)
    } else {
        showToast(`本书目录中未收录「第${m[1]}${kind}」`)
    }
}



const inst = getCurrentInstance()
function bookmarkHere() {
    if (!book.value) return
    // 定位视口内第一个块
    const q = uni.createSelectorQuery().in(inst.proxy)
    q.selectAll('.blk').boundingClientRect()
    q.exec((res) => {
        let g = currentG.value
        const nodes = (res && res[0]) || []
        for (const nd of nodes) {
            if (nd.top > (statusBar.value + 60)) {
                const dg = nd.dataset && nd.dataset.g
                if (dg !== undefined) g = Number(dg)
                break
            }
        }
        const ch = chapters.value[visualChIdx.value]
        const ok = addBookmark({
            slug: slug.value,
            title: book.value.title,
            chapter: ch ? ch.title : '',
            gIdx: g,
            chIdx: startIdx.value,
            scrollTop: lastScroll.scrollTop,
            excerpt: excerptText(book.value, g)
        })
        showToast(ok ? '已添加书签' : '该处已有书签')
    })
}

// 页面生命周期
onLoad((opt) => {
    const s = (opt && opt.slug) || ''
    bootstrap(s, {
        g: opt && opt.g !== undefined ? opt.g : null,
        resume: opt && opt.resume === '1'
    })
})

onUnload(() => {
    persistProgress()
})

onBackPress(() => {
    if (showDrawer.value) {
        showDrawer.value = false
        return true
    }
    if (showSettings.value) {
        showSettings.value = false
        return true
    }
    return false
})

onShareAppMessage(() => {
    return {
        title: book.value ? `《${book.value.title}》光明中医文库` : '光明中医文库',
        path: '/pages/index/index'
    }
})
</script>

<style lang="scss" scoped>
.reader {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: var(--bg, #f6f1e5);
    transition: background 0.2s;
}

.nav {
    position: fixed;
    left: 0;
    right: 0;
    top: 0;
    z-index: 50;
    display: flex;
    align-items: center;
    padding: 8px 16rpx 14rpx;
    background: var(--bg, #f6f1e5);
    border-bottom: 1rpx solid var(--line, #e4dcc8);
}

.nav-btn {
    min-width: 130rpx;
}

.nav-btn-r {
    text-align: right;
}

.nav-btn-t {
    font-size: 27rpx;
    color: var(--accent, #8b3a3a);
    padding: 10rpx 16rpx;
}

.nav-title {
    flex: 1;
    text-align: center;
    font-size: 30rpx;
    font-weight: 700;
    color: var(--fg, #37332b);
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.content {
    flex: 1;
    height: 100%;
}

.turn-l { animation: turnL .3s ease; }
.turn-r { animation: turnR .3s ease; }
@keyframes turnL {
    from { transform: translateX(56px); opacity: 0.3; }
    to   { transform: translateX(0);    opacity: 1; }
}
@keyframes turnR {
    from { transform: translateX(-56px); opacity: 0.3; }
    to   { transform: translateX(0);     opacity: 1; }
}

.zoom-mask {
    position: fixed;
    inset: 0;
    background: rgba(12, 10, 8, 0.92);
    z-index: 260;
}

.zoom-area {
    position: absolute;
    inset: 0;
}

.zoom-view {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
}

.zoom-img {
    width: 100%;
    max-height: 90vh;
    object-fit: contain;
}

.zoom-cap {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 90rpx;
    text-align: center;
    color: #e8ddc8;
    font-size: 26rpx;
}

.zoom-close {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 40rpx;
    text-align: center;
    color: #8a8070;
    font-size: 22rpx;
}

.content-inner {
    padding: 110px 40rpx 40rpx;
}

.serif .para, .serif-mode .blk-p {
    font-family: 'Songti SC', 'STSong', 'STZhongsong', 'Noto Serif CJK SC',
        'Noto Serif SC', 'SimSun', serif;
}

.chapter-sep {
    margin: 60rpx 0 30rpx;
    text-align: center;
}

.chapter-sep-t {
    font-size: 22rpx;
    color: var(--muted, #8d8371);
    letter-spacing: 4rpx;
}

.ch-quiz {
    margin: 8rpx 40rpx 48rpx;
}

.ch-quiz-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 16rpx;
    padding: 24rpx 30rpx;
}

.ch-quiz-t {
    font-size: 27rpx;
    color: var(--fg);
}

.ch-quiz-a {
    font-size: 25rpx;
    color: var(--accent);
}

.load-hint {
    margin: 50rpx 0;
    text-align: center;
    font-size: 24rpx;
    color: var(--muted, #8d8371);
}

.load-end {
    letter-spacing: 8rpx;
}

.bottom-space {
    height: 180rpx;
}

.foot {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 50;
    background: var(--bg, #f6f1e5);
    border-top: 1rpx solid var(--line, #e4dcc8);
    padding: 10rpx 24rpx;
}

.foot-row1 {
    display: flex;
    align-items: center;
}

.foot-btn {
    width: 150rpx;
    text-align: center;
    font-size: 26rpx;
    color: var(--accent, #8b3a3a);
    padding: 8rpx 0;
}

.disabled {
    color: var(--muted, #8d8371);
    opacity: 0.5;
}

.foot-slider {
    flex: 1;
    margin: 0 10rpx;
}

.foot-row2 {
    display: flex;
    align-items: center;
    margin-top: 4rpx;
}

.foot-meta {
    flex: 1;
    font-size: 21rpx;
    color: var(--muted, #8d8371);
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.foot-act {
    margin-left: 22rpx;
    font-size: 25rpx;
    color: var(--accent, #8b3a3a);
    padding: 6rpx 14rpx;
}

.foot-act.act-on {
    background: var(--accent, #8b3a3a);
    color: #f3e9d2;
    border-radius: 999rpx;
}

.toast {
    position: fixed;
    left: 50%;
    top: 45%;
    transform: translate(-50%, -50%);
    background: rgba(30, 22, 18, 0.85);
    color: #fff8ec;
    font-size: 26rpx;
    padding: 18rpx 40rpx;
    border-radius: 40rpx;
    z-index: 99;
}

.loading {
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f6f1e5;
}

.loading-t {
    color: #8d8371;
    font-size: 28rpx;
    letter-spacing: 6rpx;
}

.theme-night .fig-img {
    opacity: 0.92;
}
</style>
