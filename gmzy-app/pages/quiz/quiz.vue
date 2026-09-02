<template>
    <view class="quiz" :class="{ night, elder: store.settings.elder, [themeCls]: night }">
        <view v-if="!ready" class="loading">题库加载中…</view>
        <template v-else-if="!queue.length">
            <view class="done-all">
                <text class="done-emoji serif-font">毕</text>
                <text class="done-text">该筛选下没有题目了</text>
                <button class="btn ghost" @tap="setFilter('all')">回到全部</button>
            </view>
        </template>
        <template v-else>
            <view v-if="chapMode" class="chap-tip serif-font">📖 {{ chapRange.title }}</view>
            <view class="topbar">
                <text class="counter serif-font">{{ pos + 1 }} / {{ queue.length }}</text>
                <template v-if="mockMode">
                    <text class="mock-clock serif-font" :class="{ urgent: mockLeft <= 300 }">⏱ {{ mmss }}</text>
                    <text class="mock-submit" @tap="submitMock(true)">交卷</text>
                </template>
                <view v-else class="seg">
                    <text
                        v-for="f in FILTERS"
                        :key="f.key"
                        class="seg-item"
                        :class="{ on: filter === f.key }"
                        @tap="setFilter(f.key)"
                    >{{ f.name }}</text>
                </view>
            </view>

            <!-- 模考交卷结果 -->


            <view class="qcard">
                <view class="qtag-row">
                    <text class="qtag">{{ cur.chapter }}</text>
                    <text class="qstate" :class="{ know: state === 1, dont: state === 2 }">
                        {{ state === 1 ? '已答：记住了' : state === 2 ? '已答：还没记住' : '未作答' }}
                    </text>
                </view>
                <scroll-view scroll-y class="qscroll">
                    <text class="qtext serif-font">{{ cur.idx + 1 }}. {{ cur.q }}</text>
                </scroll-view>
                <view v-if="hasAnchor" class="src-link" @tap="goSource">📖 回到教材找答案（{{ cur.chapter }}）›</view>
                <text class="qhint">先在心里作答，然后如实标记，遗忘的会自动进入"待巩固"。</text>
            </view>

            <view class="rate">
                <view class="rate-btn bad" @tap="answer(false)">
                    <text class="rate-name">还没记住</text>
                    <text class="rate-sub">进入待巩固</text>
                </view>
                <view class="rate-btn good" @tap="answer(true)">
                    <text class="rate-name">记住了</text>
                    <text class="rate-sub">默述出大意</text>
                </view>
            </view>

            <view class="nav-row">
                <text class="nav-btn" @tap="prev">‹ 上一题</text>
                <text class="nav-btn warn" v-if="stats.done && !mockMode" @tap="confirmReset">重置本书进度</text>
                <text class="nav-btn" @tap="next">下一题 ›</text>
            </view>

            <view class="foot" v-if="!mockMode">
                <view class="foot-line">
                    <text>已答 {{ stats.done || 0 }} 题 · 记住 {{ stats.know || 0 }} · 待巩固 {{ stats.dont || 0 }}</text>
                </view>
                <view class="acc-panel" v-if="daySeries.some((d) => d.total)">
                    <view class="acc-bars">
                        <view v-for="d in daySeries" :key="d.day" class="acc-col">
                            <view class="acc-stack">
                                <view class="acc-ok" :style="{ height: barOkH(d) + 'rpx' }" />
                                <view class="acc-bad" :style="{ height: barBadH(d) + 'rpx' }" />
                            </view>
                            <text class="acc-day">{{ d.day.split('-')[1] }}</text>
                        </view>
                    </view>
                    <text class="acc-legend">绿=答对 红=答错（近7日）</text>
                </view>
                <view class="weak-chip" v-if="weakChap" @tap="setFilter('weak')">
                    薄弱区间：{{ weakChap.chapter }}（错 {{ weakChap.n }} 题，点我专攻）
                </view>
            </view>

            <!-- 模考交卷结果 -->
            <view v-if="mockSubmitted" class="mock-mask">
                <view class="mock-card">
                    <text class="mk-title serif-font">交 卷</text>
                    <text class="mk-score serif-font">{{ mockResult.k }} / {{ mockResult.n }}</text>
                    <text class="mk-acc">答出率 {{ mockRate }}% · 用时 {{ mockUsedText }}</text>
                    <text class="mk-hist" v-if="pastMocks.n">历史 {{ pastMocks.n }} 场 · 场均答出率 {{ pastMocks.avg }}%</text>
                    <scroll-view scroll-y class="mk-wrong" v-if="mockWrong.length">
                        <view v-for="w in mockWrong" :key="w.u" class="mk-wrong-row">
                            <text class="mk-wrong-q">{{ w.chapter ? w.chapter + ' · ' : '' }}{{ w.q }}</text>
                            <text v-if="w.book && w.g !== null && w.g !== undefined" class="mk-wrong-src" @tap="goSourceOf(w)">📖 原文 ›</text>
                        </view>
                    </scroll-view>
                    <text v-else class="mk-perfect serif-font">满分！无一错漏</text>
                    <view class="mk-btns">
                        <text class="mk-btn ghost" @tap="goStats">成绩曲线 ›</text>
                        <text class="mk-btn ghost" @tap="exitPage">返回</text>
                        <text class="mk-btn solid" @tap="again">再来一套</text>
                    </view>
                    <text class="mk-note">本次作答已并入日常进度；未答出的题目自动进入「待巩固」</text>
                </view>
            </view>
        </template>

        <!-- 段位晋升金榜 -->
        <YuanqiCeremony :info="promoInfo" @close="promoInfo = null" />
    </view>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { onLoad, onShow, onUnload } from '@dcloudio/uni-app'
import { loadQuizBook, loadQuizIndex, loadDiagAtlas, loadDiagRules, migrateLegacyLearn } from '../../common/learn.js'
import YuanqiCeremony from '../../components/YuanqiCeremony.vue'
import {
    store,
    setQuizAnswer,
    quizStatsOf,
    resetQuiz,
    hasLegacyKeys,
    markMigrated,
    quizMistakes,
    quizDailySeries,
    pushMockResult,
    awardExamEnergy,
    bumpMockMissTerm
} from '../../common/store.js'
import { symptomIndex } from '../../common/diagnosis.js'
import { applyNavTheme } from '../../common/theme.js'

const bookKey = ref('')   // q<N>.json
const bookTitle = ref('')
const list = ref([])
const ready = ref(false)
const queue = ref([])
const pos = ref(0)
const filter = ref('all')
const stats = reactive({})
const night = ref(false)
const themeCls = computed(() => 'night-theme-' + (store.settings.nightTheme || 'warm'))
const missedCount = ref(0)
const daySeries = ref([])
const chapMode = ref(false)
const chapRange = reactive({ s: 0, e: 0, title: '' })

// ---- 综合模考 ----
const mockMode = ref(false)
const mockAns = reactive({}) // u -> 1 答出 | 2 未答出
const mockLeft = ref(0)      // 剩余秒
const mockInit = ref(0)      // 初始秒
const mockSubmitted = ref(false)
const mockResult = reactive({ n: 0, k: 0, sec: 0 })
let mockTimer = null

const mmss = computed(() => {
    const s = Math.max(0, mockLeft.value)
    return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
})
const mockRate = computed(() => (mockResult.n ? Math.round((mockResult.k / mockResult.n) * 100) : 0))
const mockUsedText = computed(() => `${String(Math.floor(mockResult.sec / 60)).padStart(2, '0')}:${String(mockResult.sec % 60).padStart(2, '0')}`)
const mockWrong = computed(() => (mockSubmitted.value ? list.value.filter((it) => mockAns[it.u] !== 1) : []))
// 交卷后，历史成绩含本场；过往场次从第 2 条起
const pastMocks = computed(() => {
    const past = store.learn.mockHistory.slice(1)
    if (!past.length) return { n: 0, avg: 0 }
    const avg = Math.round((past.reduce((s, m) => s + (m.n ? m.k / m.n : 0), 0) / past.length) * 100)
    return { n: past.length, avg }
})

async function setupMock() {
    const idx = await loadQuizIndex()
    const arr = []
    for (const meta of idx) {
        try {
            const book = await loadQuizBook(meta.f)
            book.forEach((it) => arr.push(Object.assign({}, it, { _bk: meta.f })))
        } catch (e) { /* 单卷损坏时跳过 */ }
    }
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        const t = arr[i]
        arr[i] = arr[j]
        arr[j] = t
    }
    list.value = arr.slice(0, Math.min(30, arr.length))
    queue.value = list.value.map((_, i) => i)
    pos.value = 0
    Object.keys(mockAns).forEach((k) => delete mockAns[k])
    mockSubmitted.value = false
    mockInit.value = Math.min(1500, list.value.length * 50)
    mockLeft.value = mockInit.value
}

function startMockTimer() {
    stopMockTimer()
    mockTimer = setInterval(() => {
        if (mockLeft.value > 0) {
            mockLeft.value--
            if (mockLeft.value === 0) submitMock(false)
        }
    }, 1000)
}

function stopMockTimer() {
    if (mockTimer) {
        clearInterval(mockTimer)
        mockTimer = null
    }
}

function submitMock(manual) {
    if (mockSubmitted.value) return
    if (!manual) return doSubmit()
    const unanswered = list.value.filter((it) => !mockAns[it.u]).length
    uni.showModal({
        title: '交卷',
        content: unanswered ? `还有 ${unanswered} 题未作答，未作答按未答出计。确定交卷吗？` : '确定交卷吗？',
        confirmText: '交卷',
        confirmColor: '#8b3a3a',
        success: (r) => r.confirm && doSubmit()
    })
}

function doSubmit() {
    if (mockSubmitted.value) return
    mockSubmitted.value = true
    stopMockTimer()
    let k = 0
    list.value.forEach((it) => {
        const a = mockAns[it.u] || 2
        if (a === 1) k++
        setQuizAnswer(it._bk, it.u, a === 1)
    })
    const sec = mockInit.value - mockLeft.value
    mockResult.n = list.value.length
    mockResult.k = k
    mockResult.sec = sec
    pushMockResult({ n: list.value.length, k, s: sec })
    // 跨科联动：模考按答出率灌注三科共享元气池；错题题干回流图考权重
    const rate = list.value.length ? Math.round((k / list.value.length) * 100) : 0
    showPromo(awardExamEnergy(rate >= 80 ? 6 : rate >= 60 ? 4 : 2))
    absorbMockMisses()
}

// 模考错题 → 图谱术语命中回流（与图考弱项加权共用图谱账本）
let atlasPairs = null // [[term, alias]...]
async function atlasPairsNow() {
    if (atlasPairs) return atlasPairs
    const [atlas, rules] = await Promise.all([loadDiagAtlas(), loadDiagRules()])
    const labels = {}
    for (const g of rules.groups || []) for (const it of g.items || []) labels[it.id] = it.label
    const pairs = []
    const collect = (lst) =>
        (lst || []).forEach((it) => {
            const clean = String(it.term).replace(/[（(].*/, '').replace('·', '')
            const alias = new Set()
            if (clean.length >= 3) alias.add(clean)
            ;(it.keys || []).forEach((kwd) => {
                if (labels[kwd] && labels[kwd].length >= 2) alias.add(labels[kwd])
            })
            const m = clean.match(/^([一-龥]{1,3})脉$/)
            if (m) {
                alias.add(clean) // 2 字脉名特例放行（如 滑脉/弦脉）
                const rev = '脉' + m[1]
                if (rev.length >= 3) alias.add(rev) // 脉弦/脉细数…
            }
            alias.forEach((a) => pairs.push([it.term, a]))
        })
    collect(atlas.tongue)
    collect(atlas.pulse)
    collect(atlas.wang)
    atlasPairs = pairs
    return atlasPairs
}

async function absorbMockMisses() {
    const wrong = mockWrong.value
    if (!wrong.length) return
    let pairs
    try {
        pairs = await atlasPairsNow()
    } catch (e) {
        return
    }
    for (const w of wrong) {
        const text = typeof w.q === 'string' ? w.q : ''
        if (!text) continue
        const hit = new Set()
        for (const [term, alias] of pairs) {
            if (!hit.has(term) && alias && text.includes(alias)) hit.add(term)
        }
        hit.forEach((t) => bumpMockMissTerm(t))
    }
}

// 金榜：段位晋升仪式
const promoInfo = ref(null)
let promoTimer = null
function showPromo(promo) {
    if (!promo) return
    promoInfo.value = promo
    clearTimeout(promoTimer)
    promoTimer = setTimeout(() => (promoInfo.value = null), 3200)
}

function again() {
    setupMock().then(() => startMockTimer())
}

function goStats() {
    uni.navigateTo({ url: '/pages/stats/stats' })
}

function exitPage() {
    uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/learn/learn' }) })
}

function goSourceOf(w) {
    uni.navigateTo({ url: `/pages/reader/reader?slug=${w.book}&g=${w.g}` })
}

const FILTERS = computed(() =>
    chapMode.value
        ? [
              { key: 'chap', name: '本章' },
              { key: 'all', name: '全部' },
              { key: 'new', name: '未答' },
              { key: 'weak', name: '待巩固' },
              { key: 'missed', name: `错题${missedCount.value ? ' ' + missedCount.value : ''}` }
          ]
        : [
              { key: 'all', name: '全部' },
              { key: 'new', name: '未答' },
              { key: 'weak', name: '待巩固' },
              { key: 'missed', name: `错题${missedCount.value ? ' ' + missedCount.value : ''}` }
          ]
)

onLoad(async (q) => {
    if (q && q.mock === '1') {
        mockMode.value = true
        bookKey.value = '_mock_'
        bookTitle.value = '综合模考'
        uni.setNavigationBarTitle({ title: '综合模考' })
        if (hasLegacyKeys()) await migrateLegacyLearn(store, markMigrated)
        await setupMock()
        startMockTimer()
        ready.value = true
        return
    }
    bookKey.value = decodeURIComponent(q.k || '')
    bookTitle.value = decodeURIComponent(q.title || '')
    if (q.cs !== undefined && q.ce !== undefined) {
        chapMode.value = true
        chapRange.s = +q.cs
        chapRange.e = +q.ce
        chapRange.title = decodeURIComponent(q.ctitle || '')
        filter.value = 'chap'
    }
    uni.setNavigationBarTitle({ title: bookTitle.value || '复习思考题' })
    if (hasLegacyKeys()) await migrateLegacyLearn(store, markMigrated)
    if (q.err === '1') filter.value = 'missed'
    list.value = await loadQuizBook(bookKey.value)
    daySeries.value = quizDailySeries(7)
    refreshStats()
    buildQueue()
    ready.value = true
})

onShow(() => {
    night.value = applyNavTheme()
    refreshStats()
})

onUnload(() => stopMockTimer())

function doneMap() {
    return store.learn.quizDone[bookKey.value] || {}
}

const cur = computed(() => {
    const i = queue.value[pos.value]
    if (i === undefined) return {}
    return { ...list.value[i], idx: i }
})

const state = computed(() => {
    const i = queue.value[pos.value]
    if (i === undefined) return 0
    if (mockMode.value) return mockAns[list.value[i].u] || 0
    return doneMap()[list.value[i].u] || 0
})

function refreshStats() {
    Object.assign(stats, quizStatsOf(bookKey.value, list.value.length))
    missedCount.value = quizMistakes(bookKey.value).length
}

// 薄弱章节：待巩固题最多的章节标签
const weakChap = computed(() => {
    const done = doneMap()
    const cnt = {}
    list.value.forEach((it) => {
        if (done[it.u] === 2 && it.chapter) cnt[it.chapter] = (cnt[it.chapter] || 0) + 1
    })
    const top = Object.entries(cnt).sort((a, b) => b[1] - a[1])[0]
    return top ? { chapter: top[0], n: top[1] } : null
})

function barOkH(d) {
    const max = Math.max(1, ...daySeries.value.map((x) => x.total))
    return Math.round((d.ok / max) * 56)
}

function barBadH(d) {
    const max = Math.max(1, ...daySeries.value.map((x) => x.total))
    return Math.round((d.bad / max) * 56)
}

function inChapRange(it) {
    return !!chapMode.value && it.g !== null && it.g !== undefined && it.g >= chapRange.s && it.g <= chapRange.e
}

function buildQueue() {
    const done = doneMap()
    let idx = list.value.map((_, i) => i)
    if (filter.value === 'chap') idx = idx.filter((i) => inChapRange(list.value[i]))
    else if (filter.value === 'new') idx = idx.filter((i) => !done[list.value[i].u])
    else if (filter.value === 'weak') idx = idx.filter((i) => done[list.value[i].u] === 2)
    else if (filter.value === 'missed') {
        const miss = new Set(quizMistakes(bookKey.value))
        idx = idx.filter((i) => miss.has(list.value[i].u))
    }
    queue.value = idx
    if (pos.value >= queue.value.length) pos.value = 0
}

function setFilter(f) {
    filter.value = f
    buildQueue()
}

function answer(ok) {
    if (mockMode.value) return mockAnswer(ok)
    const i = queue.value[pos.value]
    if (i === undefined) return
    setQuizAnswer(bookKey.value, list.value[i].u, ok)
    refreshStats()
    if (pos.value < queue.value.length - 1) pos.value++
    else buildQueue()
}

function mockAnswer(ok) {
    const i = queue.value[pos.value]
    if (i === undefined) return
    mockAns[list.value[i].u] = ok ? 1 : 2
    if (pos.value < queue.value.length - 1) pos.value++
    else doSubmit()
}

function prev() {
    if (pos.value > 0) pos.value--
}

function next() {
    if (pos.value < queue.value.length - 1) pos.value++
}

function confirmReset() {
    uni.showModal({
        title: '重置进度',
        content: '将清空本书全部答题记录，确定吗？',
        confirmColor: '#8b3a3a',
        success: (r) => {
            if (r.confirm) {
                resetQuiz(bookKey.value)
                refreshStats()
                buildQueue()
            }
        }
    })
}

const hasAnchor = computed(() => {
    const c = cur.value
    return c && c.book && c.g !== null && c.g !== undefined
})

function goSource() {
    const c = cur.value
    if (!c.book) return
    uni.navigateTo({ url: `/pages/reader/reader?slug=${c.book}&g=${c.g}` })
}
</script>

<style lang="scss" scoped>
.quiz {
    min-height: 100vh;
    background: #f6f1e5;
    padding: 24rpx;
    display: flex;
    flex-direction: column;
}

.loading,
.done-all {
    margin-top: 30vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20rpx;
    color: #8d8371;
    font-size: 26rpx;
}

.done-emoji {
    width: 120rpx;
    height: 120rpx;
    border-radius: 50%;
    background: #8b3a3a;
    color: #f3e9d2;
    font-size: 56rpx;
    display: flex;
    align-items: center;
    justify-content: center;
}

.chap-tip {
    font-size: 24rpx;
    color: #5c2018;
    background: rgba(139, 58, 58, 0.08);
    border-radius: 12rpx;
    padding: 14rpx 22rpx;
    margin-bottom: 16rpx;
}

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20rpx;
}

.counter {
    font-size: 28rpx;
    color: #5c2018;
    font-weight: 600;
}

.seg {
    display: flex;
    background: #efe8d6;
    border-radius: 14rpx;
    padding: 4rpx;
}

.seg-item {
    font-size: 23rpx;
    color: #8d8371;
    padding: 8rpx 22rpx;
    border-radius: 11rpx;

    &.on {
        background: #fffdf7;
        color: #8b3a3a;
        font-weight: 600;
    }
}

.qcard {
    flex: 1;
    background: #fffdf7;
    border-radius: 24rpx;
    border: 1rpx solid #e4dcc8;
    padding: 36rpx 34rpx;
    display: flex;
    flex-direction: column;
    min-height: 560rpx;
}

.qtag-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 26rpx;
}

.qtag {
    background: #efe8d6;
    color: #8d8371;
    font-size: 21rpx;
    padding: 6rpx 18rpx;
    border-radius: 999rpx;
}

.qstate {
    font-size: 21rpx;
    color: #b9ac92;

    &.know { color: #4a7c59; }
    &.dont { color: #b3543f; }
}

.qscroll {
    flex: 1;
    max-height: 720rpx;
}

.qtext {
    font-size: 34rpx;
    line-height: 1.9;
    color: #37332b;
}

.qhint {
    margin-top: 24rpx;
    font-size: 21rpx;
    color: #b9ac92;
}

.src-link {
    margin-top: 20rpx;
    padding: 16rpx 0 4rpx;
    font-size: 24rpx;
    color: #8b3a3a;
    border-top: 1rpx dashed #e4dcc8;
}

.rate {
    display: flex;
    gap: 20rpx;
    margin-top: 28rpx;
}

.rate-btn {
    flex: 1;
    border-radius: 18rpx;
    padding: 24rpx 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6rpx;

    &.bad { background: rgba(179, 84, 63, 0.12); }
    &.good { background: rgba(74, 124, 89, 0.12); }
}

.rate-name {
    font-size: 28rpx;
    font-weight: 600;
}

.bad .rate-name { color: #b3543f; }
.good .rate-name { color: #4a7c59; }

.rate-sub {
    font-size: 20rpx;
    color: #8d8371;
}

.nav-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 22rpx;
    padding: 0 10rpx;
}

.nav-btn {
    font-size: 26rpx;
    color: #8b3a3a;
    padding: 10rpx 20rpx;

    &.warn {
        color: #b3543f;
        font-size: 23rpx;
    }
}

.foot {
    margin-top: 10rpx;
}

.foot-line {
    text-align: center;
    font-size: 22rpx;
    color: #8d8371;
}

.btn.ghost {
    margin-top: 20rpx;
    border: 1rpx solid #8b3a3a;
    color: #8b3a3a;
    background: transparent;
    border-radius: 12rpx;
    font-size: 26rpx;
    padding: 0 40rpx;
    height: 72rpx;
    line-height: 72rpx;
}

/* ---- 综合模考 ---- */
.mock-clock {
    font-size: 30rpx;
    color: #5c2018;
    font-weight: 700;

    &.urgent {
        color: #b5242a;
    }
}

.mock-submit {
    font-size: 25rpx;
    color: #f3e9d2;
    background: #8b3a3a;
    border-radius: 24rpx;
    padding: 10rpx 30rpx;
}

.mock-mask {
    position: fixed;
    inset: 0;
    background: rgba(36, 24, 18, 0.55);
    z-index: 60;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40rpx;
}

.mock-card {
    width: 100%;
    max-height: 88vh;
    background: #fdfaf3;
    border-radius: 24rpx;
    padding: 40rpx 34rpx 30rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.mk-title {
    font-size: 26rpx;
    color: #8d8371;
    letter-spacing: 12rpx;
}

.mk-score {
    font-size: 88rpx;
    color: #5c2018;
    font-weight: 700;
    margin-top: 8rpx;
}

.mk-acc {
    font-size: 26rpx;
    color: #6b5d4f;
    margin-top: 6rpx;
}

.mk-hist {
    font-size: 22rpx;
    color: #a39880;
    margin-top: 4rpx;
}

.mk-wrong {
    width: 100%;
    max-height: 34vh;
    margin-top: 20rpx;
    border-top: 1rpx solid #efe8d6;
}

.mk-wrong-row {
    padding: 16rpx 4rpx;
    border-bottom: 1rpx dashed #efe8d6;
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12rpx;
}

.mk-wrong-q {
    font-size: 25rpx;
    color: #3a3226;
    flex: 1;
}

.mk-wrong-src {
    font-size: 22rpx;
    color: #8b3a3a;
    flex-shrink: 0;
}

.mk-perfect {
    font-size: 30rpx;
    color: #8b3a3a;
    margin-top: 24rpx;
}

.mk-btns {
    flex-direction: row;
    display: flex;
    gap: 18rpx;
    margin-top: 26rpx;
}

.mk-btn {
    font-size: 26rpx;
    border-radius: 14rpx;
    padding: 14rpx 30rpx;

    &.ghost {
        border: 1rpx solid #c9bfa8;
        color: #8d8371;
    }

    &.solid {
        background: #8b3a3a;
        color: #f3e9d2;
    }
}

.mk-note {
    font-size: 21rpx;
    color: #a39880;
    margin-top: 18rpx;
}
</style>
