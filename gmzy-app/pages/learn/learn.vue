<template>
    <view class="learn" :class="{ night, [themeCls]: night }">
        <!-- 学习总览 -->
        <view class="hero-op" @tap="goStats">详表 ›</view>
        <view class="hero">
            <view class="hero-row">
                <view class="hero-cell">
                    <text class="hero-num serif-font">{{ ov.streak }}</text>
                    <text class="hero-label">连续学习(天)</text>
                </view>
                <view class="hero-div" />
                <view class="hero-cell">
                    <text class="hero-num serif-font">{{ dueTotal }}</text>
                    <text class="hero-label">今日待复习</text>
                </view>
                <view class="hero-div" />
                <view class="hero-cell">
                    <text class="hero-num serif-font">{{ ov.todayCards + ov.todayQuiz }}</text>
                    <text class="hero-label">今日已学</text>
                </view>
                <view class="hero-div" />
                <view class="hero-cell">
                    <text class="hero-num serif-font">{{ ov.cards + ov.quiz }}</text>
                    <text class="hero-label">累计学习量</text>
                </view>
            </view>
            <!-- 近 7 日学习量 -->
            <view class="week">
                <view v-for="d in week" :key="d.day" class="week-col">
                    <view class="week-bars">
                        <view class="week-bar c" :style="{ height: barH(d.cards) }" />
                        <view class="week-bar q" :style="{ height: barH(d.quiz) }" />
                    </view>
                    <text class="week-day">{{ d.day }}</text>
                </view>
            </view>
            <view class="week-legend">
                <text class="lg"><text class="dot c" />识记卡片</text>
                <text class="lg"><text class="dot q" />自测题目</text>
            </view>
        </view>

        <view v-if="migrating" class="mig-tip">正在升级旧学习记录，请稍候…</view>

        <!-- 本周学习报告 -->
        <view class="sec weekly">
            <view class="sec-head">
                <text class="sec-title">本周战报</text>
                <text class="sec-op wc-mood">{{ weeklyMood }}</text>
            </view>
            <view class="week-compare">
                <view class="wc-item">
                    <text class="wc-num serif-font">{{ wa.cards.cur }}</text>
                    <text class="wc-label">背卡</text>
                    <text class="wc-delta" :class="deltaCls(wa.cards)">{{ deltaText(wa.cards) }}</text>
                </view>
                <view class="wc-item">
                    <text class="wc-num serif-font">{{ wa.quiz.cur }}</text>
                    <text class="wc-label">答题</text>
                    <text class="wc-delta" :class="deltaCls(wa.quiz)">{{ deltaText(wa.quiz) }}</text>
                </view>
                <view class="wc-item">
                    <text class="wc-num serif-font">{{ wa.diag.cur }}</text>
                    <text class="wc-label">辨证</text>
                    <text class="wc-delta" :class="deltaCls(wa.diag)">{{ deltaText(wa.diag) }}</text>
                </view>
            </view>
            <text class="wc-tip">对比上周同一 7 天 · 正数为进步</text>
        </view>

        <!-- 记忆卡包 -->
        <view class="sec">
            <view class="sec-head"><text class="sec-title">记忆卡</text></view>
            <view v-for="d in decks" :key="d.id" class="deck" @tap="openDeck(d)">
                <image class="deck-cover" :src="coverOf(d.id)" mode="aspectFill" />
                <view class="deck-fade" />
                <view class="deck-icon serif-font" :class="'deck-' + d.id">{{ d.icon }}</view>
                <view class="deck-info">
                    <view class="deck-top">
                        <text class="deck-name">{{ d.name }}</text>
                        <view class="deck-topside">
                            <text v-if="statOf(d).due" class="due-badge serif-font">{{ statOf(d).due }} 到期</text>
                            <text class="deck-count serif-font">{{ d.count }} 张</text>
                        </view>
                    </view>
                    <text class="deck-desc">{{ d.desc }}</text>
                    <view class="deck-bar">
                        <view class="deck-fill m3" :style="{ width: pctOf(d, 'mastered') + '%' }" />
                        <view class="deck-fill m2" :style="{ width: pctOf(d, 'fuzzy') + '%' }" />
                        <view class="deck-fill m1" :style="{ width: pctOf(d, 'unknown') + '%' }" />
                    </view>
                    <text class="deck-meta">
                        已掌握 {{ statOf(d).mastered }} · 待巩固 {{ statOf(d).fuzzy + statOf(d).unknown }} · 未学 {{ d.count - statOf(d).done }}
                    </text>
                    <text class="deck-meta new-line" v-if="statOf(d).done">今日新卡 {{ nt(d) }}/{{ newLimit }}</text>
                </view>
            </view>
        </view>

        <!-- 复习思考题 -->
        <view class="sec">
            <view class="sec-head">
                <text class="sec-title">复习思考题</text>
                <text class="sec-total serif-font">共 {{ totalQuiz }} 题</text>
            </view>
            <view v-for="b in quizBooks" :key="b.slug + b.book" class="qbook" @tap="openQuiz(b)">
                <text class="qbook-name serif-font">{{ b.book }}</text>
                <text v-if="qerr(b) > 0" class="qerr-chip" @tap.stop="openQuizErr(b)">错 {{ qerr(b) }}</text>
                <view class="qbook-side">
                    <view class="qbook-bar">
                        <view class="qbook-fill" :style="{ width: qpct(b) + '%' }" />
                    </view>
                    <text class="qbook-meta">{{ qstat(b).done }}/{{ b.count }}</text>
                    <text class="qbook-go">›</text>
                </view>
            </view>
            <view v-if="!quizBooks.length" class="empty">题库载入中…</view>
        </view>
    </view>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { onShow, onLoad } from '@dcloudio/uni-app'
import { loadDecks, loadQuizIndex, quizKey, migrateLegacyLearn } from '../../common/learn.js'
import {
    store,
    deckStats,
    quizStatsOf,
    weeklyCompare,
    quizMistakeCount,
    learnOverview,
    weekSeries,
    newPerDayLimit,
    newTodayCount,
    hasLegacyKeys,
    markMigrated
} from '../../common/store.js'
import { applyNavTheme } from '../../common/theme.js'
import { maybeToastH5Reminder } from '../../common/remind.js'

const decks = ref([])
const quizBooks = ref([])
const stats = reactive({})
const qstats = reactive({})
const ov = reactive({ cards: 0, quiz: 0, activeDays: 0, diagCount: 0, todayCards: 0, todayQuiz: 0, streak: 0 })
const week = ref([])
const night = ref(false)
const themeCls = computed(() => 'night-theme-' + (store.settings.nightTheme || 'warm'))
const totalQuiz = ref(0)

const dueTotal = computed(() => decks.value.reduce((s, d) => s + (statOf(d).due || 0), 0))
const weekMax = computed(() => Math.max(8, ...week.value.map((d) => d.cards + d.quiz)))

const newLimit = ref(20)
const wa = ref({ cards: { cur: 0, prev: 0 }, quiz: { cur: 0, prev: 0 }, diag: { cur: 0, prev: 0 } })

function deltaText(d) {
    const diff = d.cur - d.prev
    if (!diff && !d.cur) return '—'
    if (diff > 0) return '+' + diff
    return String(diff || 0)
}

function deltaCls(d) {
    const diff = d.cur - d.prev
    return diff > 0 ? 'up' : diff < 0 ? 'down' : 'flat'
}

const weeklyMood = computed(() => {
    const t = wa.value.cards.cur + wa.value.quiz.cur
    return t >= 100 ? '状态极佳 🔥' : t >= 40 ? '保持不错' : t > 0 ? '加油赶超上周' : '本周还未开始'
})
const migrating = ref(false)

onLoad(async () => {
    newLimit.value = newPerDayLimit()
    if (hasLegacyKeys()) {
        migrating.value = true
        await migrateLegacyLearn(store, markMigrated)
        migrating.value = false
    }
    loadDecks().then((list) => {
        decks.value = list
        refreshDeckStats()
    })
    loadQuizIndex().then((list) => {
        quizBooks.value = list
        totalQuiz.value = list.reduce((s, b) => s + b.count, 0)
        refreshQuizStats()
    })
})

onShow(() => {
    night.value = applyNavTheme()
    wa.value = weeklyCompare()
    maybeToastH5Reminder()
    Object.assign(ov, learnOverview())
    week.value = weekSeries()
    refreshDeckStats()
    refreshQuizStats()
})

function coverOf(id) {
    return `/static/learn/cover-${id}.jpg`
}

function goStats() {
    uni.navigateTo({ url: '/pages/stats/stats' })
}

function nt(d) {
    return newTodayCount(d.id)
}

function barH(v) {
    return Math.round((v / weekMax.value) * 110) + 'rpx'
}

function refreshDeckStats() {
    for (const d of decks.value) stats[d.id] = deckStats(d.id, d.count)
}

function refreshQuizStats() {
    for (const b of quizBooks.value) qstats[quizKey(b)] = quizStatsOf(quizKey(b), b.count)
}

function statOf(d) {
    return stats[d.id] || { mastered: 0, fuzzy: 0, unknown: 0, done: 0, due: 0 }
}

function qstat(b) {
    return qstats[quizKey(b)] || { done: 0 }
}

function pctOf(d, k) {
    const s = statOf(d)
    return d.count ? Math.round((s[k] / d.count) * 100) : 0
}

function qpct(b) {
    const s = qstat(b)
    return b.count ? Math.round(((s.done || 0) / b.count) * 100) : 0
}

function openDeck(d) {
    const due = statOf(d).due
    uni.navigateTo({ url: '/pages/cards/cards?deck=' + d.id + (due ? '&due=1' : '') })
}

function qerr(b) {
    return quizMistakeCount(quizKey(b))
}

function openQuizErr(b) {
    uni.navigateTo({
        url: `/pages/quiz/quiz?k=${encodeURIComponent(quizKey(b))}&title=${encodeURIComponent(b.book)}&err=1`
    })
}

function openQuiz(b) {
    uni.navigateTo({ url: '/pages/quiz/quiz?k=' + encodeURIComponent(quizKey(b)) + '&title=' + encodeURIComponent(b.book) })
}
</script>

<style lang="scss" scoped>
.learn {
    min-height: 100vh;
    background: #f6f1e5;
    padding: 24rpx 24rpx 60rpx;
}

.hero-op {
    position: absolute;
    top: 24rpx;
    right: 30rpx;
    font-size: 22rpx;
    color: rgba(243, 233, 210, 0.7);
    z-index: 2;
}

.hero {
    position: relative;
    background: linear-gradient(160deg, #6b2a20, #451611);
    border-radius: 22rpx;
    padding: 34rpx 12rpx 24rpx;
    margin-bottom: 28rpx;
}

.hero-row {
    display: flex;
    align-items: center;
}

.hero-cell {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8rpx;
}

.hero-num {
    font-size: 44rpx;
    color: #f3e9d2;
    font-weight: 600;
}

.hero-label {
    font-size: 21rpx;
    color: rgba(243, 233, 210, 0.6);
}

.hero-div {
    width: 1rpx;
    height: 52rpx;
    background: rgba(243, 233, 210, 0.25);
}

.week {
    display: flex;
    justify-content: space-around;
    margin-top: 30rpx;
    padding: 0 10rpx;
}

.week-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8rpx;
}

.week-bars {
    height: 120rpx;
    display: flex;
    align-items: flex-end;
    gap: 6rpx;
}

.week-bar {
    width: 12rpx;
    border-radius: 4rpx;
    min-height: 4rpx;

    &.c { background: rgba(243, 233, 210, 0.9); }
    &.q { background: #c8932f; }
}

.week-day {
    font-size: 19rpx;
    color: rgba(243, 233, 210, 0.55);
}

.week-legend {
    display: flex;
    justify-content: center;
    gap: 30rpx;
    margin-top: 14rpx;
}

.lg {
    font-size: 19rpx;
    color: rgba(243, 233, 210, 0.55);
    display: flex;
    align-items: center;
    gap: 8rpx;
}

.dot {
    display: inline-block;
    width: 14rpx;
    height: 14rpx;
    border-radius: 4rpx;

    &.c { background: rgba(243, 233, 210, 0.9); }
    &.q { background: #c8932f; }
}

.sec {
    background: #fffdf7;
    border-radius: 22rpx;
    padding: 26rpx 24rpx;
    margin-bottom: 28rpx;
    border: 1rpx solid #e4dcc8;
}

.sec-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 22rpx;
}

.sec-title {
    font-size: 30rpx;
    font-weight: 600;
    color: #37332b;
}

.sec-total {
    font-size: 22rpx;
    color: #8d8371;
}

.deck {
    position: relative;
    overflow: hidden;
    display: flex;
    gap: 22rpx;
    padding: 22rpx 0;
    border-top: 1rpx solid #e4dcc8;

    &:first-of-type {
        border-top: none;
    }
}

.deck-icon {
    position: relative;
    z-index: 1;
    width: 88rpx;
    height: 88rpx;
    border-radius: 18rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40rpx;
    color: #fffdf7;
    flex-shrink: 0;
}

.deck-fangji { background: linear-gradient(150deg, #8b3a3a, #5c2018); }
.deck-herb { background: linear-gradient(150deg, #4a6b3a, #2d4520); }
.deck-point { background: linear-gradient(150deg, #35588b, #1e3054); }
.deck-koujue { background: linear-gradient(150deg, #8b6f35, #54451e); }
.deck-bingz { background: linear-gradient(150deg, #7a5a8b, #4a3060); }
.deck-yian { background: linear-gradient(150deg, #4a7a70, #2a4a44); }

.weekly .wc-mood { color: #4a7c59; }

.week-compare {
    display: flex;
    gap: 20rpx;
    margin-top: 16rpx;
}

.wc-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6rpx;
    background: #fffdf5;
    border-radius: 14rpx;
    padding: 20rpx 10rpx;
    border: 1px solid rgba(139, 58, 58, 0.06);
}

.wc-num { font-size: 40rpx; color: #5c2018; }
.wc-label { font-size: 23rpx; color: #8a8070; }
.wc-delta { font-size: 21rpx; }
.wc-delta.up { color: #4a7c59; }
.wc-delta.down { color: #b3543f; }
.wc-delta.flat { color: #a0916e; }

.wc-tip {
    font-size: 20rpx;
    color: #a0916e;
    margin-top: 12rpx;
}

.deck-cover {
    position: absolute;
    top: 0;
    bottom: 0;
    right: 0;
    width: 58%;
    z-index: 0;
    opacity: 0.92;
}

.deck-fade {
    position: absolute;
    top: 0;
    bottom: 0;
    right: 0;
    left: 0;
    z-index: 0;
    background: linear-gradient(90deg, #faf6ea 34%, rgba(250, 246, 234, 0.75) 52%, transparent 82%);
}

.night-theme-warm .deck-fade { background: linear-gradient(90deg, #25211a 34%, rgba(37, 33, 26, 0.75) 52%, transparent 82%); }
.night-theme-slate .deck-fade { background: linear-gradient(90deg, #21252b 34%, rgba(33, 37, 43, 0.75) 52%, transparent 82%); }
.night-theme-amber .deck-fade { background: linear-gradient(90deg, #261c12 34%, rgba(38, 28, 18, 0.75) 52%, transparent 82%); }

.mig-tip {
    background: rgba(200, 147, 47, 0.12);
    color: #8a6d1c;
    font-size: 24rpx;
    border-radius: 14rpx;
    padding: 18rpx 24rpx;
    margin-bottom: 20rpx;
}

.new-line {
    color: #b3543f;
}

.deck-info {
    flex: 1;
    min-width: 0;
}

.deck-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.deck-name {
    font-size: 30rpx;
    font-weight: 600;
    color: #37332b;
}

.deck-topside {
    display: flex;
    align-items: center;
    gap: 12rpx;
}

.due-badge {
    font-size: 20rpx;
    background: #8b3a3a;
    color: #f3e9d2;
    border-radius: 999rpx;
    padding: 4rpx 16rpx;
}

.deck-count {
    font-size: 22rpx;
    color: #8d8371;
}

.deck-desc {
    font-size: 23rpx;
    color: #8d8371;
    margin: 6rpx 0 14rpx;
}

.deck-bar {
    height: 10rpx;
    background: #efe8d6;
    border-radius: 6rpx;
    overflow: hidden;
    display: flex;
}

.deck-fill {
    height: 100%;
}

.m3 { background: #4a7c59; }
.m2 { background: #c8932f; }
.m1 { background: #b3543f; }

.deck-meta {
    margin-top: 10rpx;
    font-size: 21rpx;
    color: #8d8371;
}

.qbook {
    display: flex;
    align-items: center;
    gap: 24rpx;
    padding: 20rpx 0;
    border-top: 1rpx solid #e4dcc8;

    &:first-of-type {
        border-top: none;
    }
}

.qerr-chip {
    font-size: 22rpx;
    color: #b3543f;
    background: rgba(179, 84, 63, 0.12);
    border-radius: 999rpx;
    padding: 6rpx 16rpx;
    margin-right: 12rpx;
    flex-shrink: 0;
}

.qbook-name {
    width: 260rpx;
    flex-shrink: 0;
    font-size: 27rpx;
    color: #37332b;
}

.qbook-side {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 16rpx;
}

.qbook-bar {
    flex: 1;
    height: 8rpx;
    background: #efe8d6;
    border-radius: 5rpx;
    overflow: hidden;
}

.qbook-fill {
    height: 100%;
    background: linear-gradient(90deg, #8b3a3a, #b35f4a);
}

.qbook-meta {
    font-size: 21rpx;
    color: #8d8371;
    white-space: nowrap;
}

.qbook-go {
    color: #b9ac92;
    font-size: 34rpx;
}

.empty {
    padding: 40rpx 0;
    text-align: center;
    color: #8d8371;
    font-size: 24rpx;
}
</style>
