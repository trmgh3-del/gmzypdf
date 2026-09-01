<template>
    <view class="quiz" :class="{ night }">
        <view v-if="!ready" class="loading">题库加载中…</view>
        <template v-else-if="!queue.length">
            <view class="done-all">
                <text class="done-emoji serif-font">毕</text>
                <text class="done-text">该筛选下没有题目了</text>
                <button class="btn ghost" @tap="setFilter('all')">回到全部</button>
            </view>
        </template>
        <template v-else>
            <view class="topbar">
                <text class="counter serif-font">{{ pos + 1 }} / {{ queue.length }}</text>
                <view class="seg">
                    <text
                        v-for="f in FILTERS"
                        :key="f.key"
                        class="seg-item"
                        :class="{ on: filter === f.key }"
                        @tap="setFilter(f.key)"
                    >{{ f.name }}</text>
                </view>
            </view>

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
                <text class="nav-btn warn" v-if="stats.done" @tap="confirmReset">重置本书进度</text>
                <text class="nav-btn" @tap="next">下一题 ›</text>
            </view>

            <view class="foot">
                <view class="foot-line">
                    <text>已答 {{ stats.done || 0 }} 题 · 记住 {{ stats.know || 0 }} · 待巩固 {{ stats.dont || 0 }}</text>
                </view>
            </view>
        </template>
    </view>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { loadQuizBook } from '../../common/learn.js'
import { setQuizAnswer, quizStatsOf, resetQuiz, store } from '../../common/store.js'
import { applyNavTheme } from '../../common/theme.js'

const FILTERS = [
    { key: 'all', name: '全部' },
    { key: 'new', name: '未答' },
    { key: 'weak', name: '待巩固' }
]

const bookKey = ref('')
const bookTitle = ref('')
const list = ref([])
const ready = ref(false)
const queue = ref([])
const pos = ref(0)
const filter = ref('all')
const stats = reactive({})
const night = ref(false)

onLoad(async (q) => {
    bookKey.value = decodeURIComponent(q.k || '')
    bookTitle.value = decodeURIComponent(q.title || '')
    uni.setNavigationBarTitle({ title: bookTitle.value || '复习思考题' })
    list.value = await loadQuizBook(bookKey.value)
    refreshStats()
    buildQueue()
    ready.value = true
})

onShow(() => {
    night.value = applyNavTheme()
    refreshStats()
})

const hasAnchor = computed(() => {
    const c = cur.value
    return c && c.book && c.g !== null && c.g !== undefined
})

function goSource() {
    const c = cur.value
    if (!c.book) return
    uni.navigateTo({ url: `/pages/reader/reader?slug=${c.book}&g=${c.g}` })
}

const cur = computed(() => {
    const i = queue.value[pos.value]
    if (i === undefined) return {}
    return { ...list.value[i], idx: i }
})

const state = computed(() => {
    const d = store.learn.quizDone[bookKey.value] || {}
    const i = queue.value[pos.value]
    return i === undefined ? 0 : d[i] || 0
})

function refreshStats() {
    Object.assign(stats, quizStatsOf(bookKey.value, list.value.length))
}

function buildQueue() {
    const done = store.learn.quizDone[bookKey.value] || {}
    let idx = list.value.map((_, i) => i)
    if (filter.value === 'new') idx = idx.filter((i) => !done[i])
    if (filter.value === 'weak') idx = idx.filter((i) => done[i] === 2)
    queue.value = idx
    if (pos.value >= queue.value.length) pos.value = 0
}

function setFilter(f) {
    filter.value = f
    buildQueue()
}

function answer(ok) {
    const i = queue.value[pos.value]
    if (i === undefined) return
    setQuizAnswer(bookKey.value, i, ok)
    refreshStats()
    if (pos.value < queue.value.length - 1) pos.value++
    else buildQueue()
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
</style>
