<template>
    <view class="shelf" :class="{ night, elder: store.settings.elder, [themeCls]: night }">
        <!-- 顶部横幅 -->
        <view class="hero">
            <view class="hero-inner">
                <text class="hero-title serif-font">光明中医知识库</text>
                <text class="hero-sub">分类知识库学习系统 · {{ totals.books }} 部教材全文拆解 {{ totals.entries }} 知识条目</text>
                <view class="hero-stats">
                    <text class="hero-stat">9 学科</text>
                    <text class="hero-stat-dot">·</text>
                    <text class="hero-stat">{{ totals.entries }} 条目</text>
                    <text class="hero-stat-dot">·</text>
                    <text class="hero-stat">已读 {{ kgReadTotal }}</text>
                    <text class="hero-stat-dot">·</text>
                    <text class="hero-stat">今日 {{ todayKg }}</text>
                </view>
                <view class="search-bar" @tap="goSearch">
                    <text class="search-ico">⌕</text>
                    <text class="search-ph">检索条目、条文、方药、穴位…</text>
                </view>
            </view>
        </view>

        <!-- 继续学习 -->
        <view class="continue" v-if="lastRead">
            <view class="continue-head">
                <text class="sec-title">继续学习</text>
                <text class="sec-more" @tap="goCatOfLast">进学科 ›</text>
            </view>
            <view class="continue-card" @tap="goArticle(lastRead)">
                <view class="learn-badge serif-font">学</view>
                <view class="continue-info">
                    <text class="continue-title serif-font">{{ lastRead.title }}</text>
                    <text class="continue-chapter">{{ lastRead.bookTitle }} · {{ lastRead.parentTitle || '条目' }}</text>
                    <text class="continue-pct">{{ lastRead.read ? '✓ 已读毕' : '上次学到此处' }} · {{ formatTime(lastRead.ts) }}</text>
                </view>
            </view>
        </view>

        <!-- 九学科 -->
        <view class="kg-sec">
            <text class="sec-title kg-sec-title">📚 九大学科</text>
            <view class="kg-grid">
                <view v-for="c in cats" :key="c.key" class="kg-cat" @tap="goCat(c.key)">
                    <view class="kg-cat-top">
                        <text class="kg-icon serif-font">{{ c.icon }}</text>
                        <text class="kg-pct" v-if="readPct(c) > 0">{{ readPct(c) }}%</text>
                    </view>
                    <text class="kg-name serif-font">{{ c.name }}</text>
                    <text class="kg-meta">{{ c.bookCount }} 部 · {{ c.entryCount }} 条</text>
                    <view class="kg-bar"><view class="kg-fill" :style="{ width: readPct(c) + '%' }" /></view>
                </view>
            </view>
        </view>

        <!-- 资料室（附录入口：全文阅读器） -->
        <view class="archive" @tap="goShelf">
            <view class="archive-l">
                <text class="archive-t serif-font">📖 全文资料室</text>
                <text class="archive-s">26 部教材原书与阅读器（附录）</text>
            </view>
            <text class="archive-go">›</text>
        </view>
    </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { store, kgReadCount, kgLastRead } from '../../common/store.js'
import { loadKgIndex, getKgCats, getKgTotals, getKgCat } from '../../common/kg.js'
import { applyNavTheme } from '../../common/theme.js'
import { formatTime } from '../../common/util.js'

const cats = ref([])
const totals = ref({ entries: 0, books: 0 })
const night = computed(() => store.settings.night)
const themeCls = computed(() => 'night-theme-' + (store.settings.nightTheme || 'warm'))

onLoad(async () => {
    await loadKgIndex()
    cats.value = getKgCats()
    totals.value = getKgTotals()
})

onShow(() => applyNavTheme())

const kgReadTotal = computed(() => kgReadCount())
const todayKg = computed(() => {
    const d = new Date()
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    return (store.learn.activity[key] || {}).kg || 0
})

const lastRead = computed(() => {
    const lr = kgLastRead()
    if (!lr) return null
    // 反向查条目元数据
    for (const c of cats.value) {
        const e = c.entries.find((x) => x.b === lr.slug && x.g === lr.g)
        if (e) {
            return { ...lr, title: e.t, bookTitle: e.bt, parentTitle: e.pt, catKey: c.key, read: true }
        }
    }
    return null
})

function readPct(c) {
    const kd = store.learn.kgDone || {}
    const n = c.entries.reduce((s, e) => s + (kd[e.b + ':' + e.g] ? 1 : 0), 0)
    return c.entryCount ? +((n / c.entryCount) * 100).toFixed(1) : 0
}

function goCat(key) {
    uni.navigateTo({ url: '/pages/kg/kg?key=' + key })
}

function goArticle(lr) {
    uni.navigateTo({ url: `/pages/kgarticle/kgarticle?key=${lr.catKey}&s=${lr.slug}&g=${lr.g}` })
}

function goCatOfLast() {
    if (lastRead.value) goCat(lastRead.value.catKey)
}

function goSearch() {
    uni.navigateTo({ url: '/pages/search/search' })
}

function goShelf() {
    uni.navigateTo({ url: '/pages/shelf/shelf' })
}
</script>

<style scoped>
.shelf {
    min-height: 100vh;
    background: #f6f1e5;
}

.night .shelf {
    background: #1a1611;
}

/* 顶部 */
.hero {
    background: linear-gradient(180deg, #8b3a3a, #6b2a20);
    padding: 56rpx 30rpx 44rpx;
    border-radius: 0 0 32rpx 32rpx;
}

.hero-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.hero-title {
    font-size: 52rpx;
    font-weight: 700;
    color: #fdf7e8;
    letter-spacing: 6rpx;
}

.hero-sub {
    font-size: 22rpx;
    color: #e3cfa8;
    margin-top: 14rpx;
    text-align: center;
}

.hero-stats {
    display: flex;
    align-items: center;
    gap: 12rpx;
    margin-top: 18rpx;
}

.hero-stat {
    font-size: 24rpx;
    color: #f3e9d2;
}

.hero-stat-dot {
    font-size: 24rpx;
    color: #c2a878;
}

.search-bar {
    margin-top: 28rpx;
    width: 100%;
    background: rgba(255, 253, 247, 0.94);
    border-radius: 999rpx;
    height: 74rpx;
    display: flex;
    align-items: center;
    padding: 0 28rpx;
}

.search-ico {
    font-size: 30rpx;
    color: #8b3a3a;
    margin-right: 14rpx;
}

.search-ph {
    font-size: 25rpx;
    color: #8d8371;
}

/* 通用小节 */
.sec-title {
    font-size: 30rpx;
    font-weight: 700;
    color: #3a342a;
}

.night .sec-title {
    color: #e8dfc8;
}

/* 继续学习 */
.continue {
    margin: 26rpx 30rpx 0;
}

.continue-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 12rpx;
}

.sec-more {
    font-size: 23rpx;
    color: #8b3a3a;
}

.continue-card {
    display: flex;
    align-items: center;
    gap: 22rpx;
    background: #fffdf7;
    border: 1px solid rgba(139, 58, 58, 0.15);
    border-radius: 18rpx;
    padding: 22rpx;
}

.night .continue-card {
    background: #241f18;
}

.learn-badge {
    width: 76rpx;
    height: 76rpx;
    line-height: 76rpx;
    text-align: center;
    font-size: 40rpx;
    color: #fffdf7;
    background: linear-gradient(150deg, #b5935a, #8b3a3a);
    border-radius: 16rpx;
    flex-shrink: 0;
}

.continue-info {
    flex: 1;
    min-width: 0;
}

.continue-title {
    display: block;
    font-size: 31rpx;
    font-weight: 700;
    color: #2e2921;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.night .continue-title {
    color: #e8dfc8;
}

.continue-chapter {
    display: block;
    font-size: 22rpx;
    color: #8d8371;
    margin-top: 5rpx;
}

.continue-pct {
    display: block;
    font-size: 21rpx;
    color: #557a46;
    margin-top: 6rpx;
}

/* 九学科 */
.kg-sec {
    margin: 30rpx 30rpx 0;
}

.kg-sec-title {
    display: block;
    margin-bottom: 16rpx;
}

.kg-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16rpx;
}

.kg-cat {
    background: #fffdf7;
    border: 1px solid rgba(139, 58, 58, 0.12);
    border-radius: 18rpx;
    padding: 22rpx 18rpx 16rpx;
    display: flex;
    flex-direction: column;
}

.night .kg-cat {
    background: #241f18;
    border-color: rgba(232, 223, 200, 0.1);
}

.kg-cat-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.kg-icon {
    font-size: 42rpx;
    color: #8b3a3a;
}

.kg-pct {
    font-size: 20rpx;
    color: #557a46;
    font-weight: 700;
}

.kg-name {
    font-size: 27rpx;
    font-weight: 700;
    color: #2e2921;
    margin-top: 10rpx;
    letter-spacing: 1rpx;
}

.night .kg-name {
    color: #e8dfc8;
}

.kg-meta {
    font-size: 20rpx;
    color: #a0937a;
    margin-top: 5rpx;
}

.kg-bar {
    height: 6rpx;
    background: rgba(181, 147, 90, 0.2);
    border-radius: 999rpx;
    overflow: hidden;
    margin-top: 12rpx;
}

.kg-fill {
    height: 100%;
    background: #557a46;
    border-radius: 999rpx;
}

/* 资料室 */
.archive {
    margin: 30rpx;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(181, 147, 90, 0.12);
    border: 1px dashed rgba(181, 147, 90, 0.55);
    border-radius: 16rpx;
    padding: 22rpx 26rpx;
}

.archive-t {
    display: block;
    font-size: 28rpx;
    color: #6b5d4f;
    font-weight: 700;
}

.night .archive-t {
    color: #e8dfc8;
}

.archive-s {
    display: block;
    font-size: 21rpx;
    color: #a0937a;
    margin-top: 4rpx;
}

.archive-go {
    font-size: 40rpx;
    color: #b5935a;
}
</style>
