<template>
    <view class="shelf" :class="{ night, elder: store.settings.elder, [themeCls]: night }">
        <!-- 顶部横幅 -->
        <view class="hero">
            <view class="hero-inner">
                <text class="hero-title serif-font">光明中医文库</text>
                <text class="hero-sub">光明中医函授教材 {{ catalog.length }} 部 · 全文离线阅读</text>
                <view class="hero-stats">
                    <text class="hero-stat">{{ totalWan }} 万字</text>
                    <text class="hero-stat-dot">·</text>
                    <text class="hero-stat">{{ totalChapters }} 章节</text>
                    <text class="hero-stat-dot">·</text>
                    <text class="hero-stat">双色精排</text>
                </view>
                <view class="search-bar" @tap="goSearch">
                    <text class="search-ico">⌕</text>
                    <text class="search-ph">搜索书名、条文、方药、穴位…</text>
                </view>
            </view>
        </view>

        <!-- 继续阅读 -->
        <view class="continue" v-if="latest">
            <view class="continue-head">
                <text class="sec-title">继续阅读</text>
                <text class="sec-more" @tap="goMine">全部记录 ›</text>
            </view>
            <view class="continue-card" @tap="openBook(latest.slug, 'resume')">
                <BookCover :title="latest.title" :cover="latest.cover" :width="150" />
                <view class="continue-info">
                    <text class="continue-title serif-font">{{ latest.title }}</text>
                    <text class="continue-chapter">{{ latest.chapter || '卷首' }}</text>
                    <view class="pbar">
                        <view class="pbar-fill" :style="{ width: percentOf(latest.slug) + '%' }" />
                    </view>
                    <text class="continue-pct">{{ (percentOf(latest.slug) * 100).toFixed(1) }}% · {{ formatTime(latest.ts) }}</text>
                </view>
            </view>
        </view>

        <!-- 分类 -->
        <scroll-view class="cats" scroll-x :show-scrollbar="false">
            <view class="cats-row">
                <view
                    v-for="c in CATEGORIES"
                    :key="c.key"
                    class="cat-chip"
                    :class="{ on: catKey === c.key }"
                    @tap="catKey = c.key"
                >{{ c.name }}</view>
            </view>
        </scroll-view>

        <!-- 书架网格 -->
        <view class="grid">
            <view
                v-for="b in books"
                :key="b.slug"
                class="cell"
                @tap="tapBook(b)"
                @longpress="showIntro(b)"
            >
                <BookCover :title="b.title" :cover="b.cover" :width="210" />
                <text class="cell-title">{{ b.title }}</text>
                <text class="cell-meta">{{ b.chapters }}章 · {{ formatChars(b.chars) }}</text>
                <view v-if="storeProgress(b.slug)" class="read-dot" />
            </view>
        </view>

        <!-- 书籍简介弹层 -->
        <view class="mask" v-show="introBook" @tap="introBook = null" />
        <view class="intro" :class="{ 'intro-show': introBook }" v-if="introBook">
            <view class="intro-card">
                <BookCover :title="introBook.title" :cover="introBook.cover" :width="190" />
                <view class="intro-body">
                    <text class="intro-title serif-font">{{ introBook.title }}</text>
                    <text class="intro-meta">{{ introBook.stem }}</text>
                    <text class="intro-meta">{{ introBook.chapters }} 章 · {{ formatChars(introBook.chars) }}</text>
                    <text class="intro-text">{{ introBook.excerpt || '光明中医函授教材' }}</text>
                </view>
            </view>
            <view class="intro-actions">
                <view class="intro-btn intro-btn-ghost" @tap="openBook(introBook.slug, 'restart')">从头阅读</view>
                <view class="intro-btn" @tap="openBook(introBook.slug, 'resume')">{{ storeProgress(introBook.slug) ? '继续阅读' : '开始阅读' }}</view>
            </view>
        </view>
    </view>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { loadCatalog, CATEGORIES, booksOf } from '../../common/books.js'
import { store, pending } from '../../common/store.js'
import { applyNavTheme } from '../../common/theme.js'
import { formatChars, formatTime } from '../../common/util.js'
import BookCover from '../../components/BookCover.vue'

const catalog = ref([])
const catKey = ref('all')
const introBook = ref(null)
const totalWan = computed(() => (catalog.value.reduce((a, b) => a + b.chars, 0) / 10000).toFixed(0))
const totalChapters = computed(() => catalog.value.reduce((a, b) => a + b.chapters, 0))

onMounted(async () => {
    try {
        catalog.value = await loadCatalog()
    } catch (e) {
        console.error('书目载入失败', e)
        uni.showToast({ title: '书目载入失败', icon: 'none' })
    }
})

const showTick = ref(0)
const night = computed(() => (showTick.value, store.settings.night))
const themeCls = computed(() => 'night-theme-' + (store.settings.nightTheme || 'warm'))
onShow(() => {
    showTick.value++
    applyNavTheme()
})

const books = computed(() => {
    showTick.value
    catalog.value
    return booksOf(catKey.value)
})

const latest = computed(() => {
    showTick.value
    return store.history.length ? store.history[0] : null
})

function storeProgress(slug) {
    showTick.value
    return store.progress[slug] || null
}

function percentOf(slug) {
    const p = store.progress[slug]
    return p && p.percent ? Math.min(1, p.percent) : 0
}

function goSearch() {
    pending.keyword = ''
    uni.navigateTo({ url: '/pages/search/search' })
}

function goMine() {
    uni.switchTab({ url: '/pages/mine/mine' })
}

function tapBook(b) {
    const p = store.progress[b.slug]
    if (p && p.percent > 0.001) {
        uni.showActionSheet({
            itemList: [`继续阅读（${(p.percent * 100).toFixed(1)}%）`, '从头开始'],
            success: (r) => {
                openBook(b.slug, r.tapIndex === 0 ? 'resume' : 'restart')
            }
        })
    } else {
        openBook(b.slug, 'restart')
    }
}

function showIntro(b) {
    introBook.value = b
}

function openBook(slug, mode) {
    introBook.value = null
    uni.navigateTo({
        url: `/pages/reader/reader?slug=${slug}${mode === 'resume' ? '&resume=1' : ''}`
    })
}
</script>

<style lang="scss" scoped>
.shelf {
    min-height: 100vh;
    background: #f6f1e5;
    padding-bottom: 40rpx;
}

/* 顶部 */
.hero {
    background: linear-gradient(160deg, #6b2a20 0%, #5c2018 55%, #451611 100%);
    padding: 46rpx 36rpx 40rpx;
    border-radius: 0 0 32rpx 32rpx;
}

.hero-title {
    display: block;
    color: #f3e9d2;
    font-size: 52rpx;
    font-weight: 800;
    letter-spacing: 10rpx;
}

.hero-sub {
    display: block;
    margin-top: 14rpx;
    color: rgba(243, 233, 210, 0.65);
    font-size: 24rpx;
    letter-spacing: 3rpx;
}

.hero-stats {
    margin-top: 22rpx;
    display: flex;
    align-items: center;
}

.hero-stat {
    color: #d9b98a;
    font-size: 23rpx;
    letter-spacing: 2rpx;
}

.hero-stat-dot {
    color: rgba(217, 185, 138, 0.5);
    margin: 0 18rpx;
}

.search-bar {
    margin-top: 30rpx;
    display: flex;
    align-items: center;
    background: rgba(255, 250, 235, 0.94);
    border-radius: 44rpx;
    padding: 18rpx 30rpx;
}

.search-ico {
    font-size: 32rpx;
    color: #8b3a3a;
    margin-right: 14rpx;
}

.search-ph {
    color: #a39478;
    font-size: 25rpx;
}

/* 继续阅读 */
.continue {
    margin: 30rpx 30rpx 0;
}

.continue-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 18rpx;
}

.sec-title {
    font-size: 32rpx;
    font-weight: 700;
    color: #37332b;
}

.sec-more {
    font-size: 24rpx;
    color: #8d8371;
}

.continue-card {
    display: flex;
    background: #fffdf7;
    border-radius: 18rpx;
    padding: 24rpx;
    box-shadow: 0 6rpx 24rpx rgba(90, 60, 30, 0.1);
}

.continue-info {
    flex: 1;
    margin-left: 26rpx;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.continue-title {
    font-size: 32rpx;
    font-weight: 700;
    color: #37332b;
}

.continue-chapter {
    margin-top: 10rpx;
    font-size: 24rpx;
    color: #8d8371;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.pbar {
    margin-top: 24rpx;
    height: 8rpx;
    border-radius: 8rpx;
    background: #efe7d3;
    overflow: hidden;
}

.pbar-fill {
    height: 100%;
    background: linear-gradient(90deg, #b9724f, #8b3a3a);
    border-radius: 8rpx;
}

.continue-pct {
    margin-top: 12rpx;
    font-size: 22rpx;
    color: #a39478;
}

/* 分类 */
.cats {
    margin: 34rpx 0 6rpx;
    white-space: nowrap;
}

.cats-row {
    display: flex;
    padding: 0 24rpx;
}

.cat-chip {
    flex-shrink: 0;
    margin: 0 8rpx;
    padding: 12rpx 34rpx;
    border-radius: 36rpx;
    font-size: 26rpx;
    color: #6d6455;
    background: #efe8d5;
    border: 1rpx solid #e2d8bd;
}

.cat-chip.on {
    background: #8b3a3a;
    color: #fff8ec;
    border-color: #8b3a3a;
    font-weight: 600;
}

/* 网格 */
.grid {
    display: flex;
    flex-wrap: wrap;
    padding: 10rpx 18rpx;
}

.cell {
    width: 33.33%;
    padding: 14rpx;
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.cell-title {
    margin-top: 14rpx;
    font-size: 25rpx;
    color: #37332b;
    text-align: center;
    line-height: 1.3;
    height: 66rpx;
    overflow: hidden;
}

.cell-meta {
    font-size: 20rpx;
    color: #a39478;
}

.read-dot {
    position: absolute;
    top: 22rpx;
    right: 22rpx;
    width: 16rpx;
    height: 16rpx;
    border-radius: 50%;
    background: #8b3a3a;
    box-shadow: 0 0 0 4rpx rgba(139, 58, 58, 0.16);
}

/* 简介弹层 */
.mask {
    position: fixed;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background: rgba(20, 12, 8, 0.45);
    z-index: 60;
}

.intro {
    position: fixed;
    left: 6%;
    right: 6%;
    top: 50%;
    transform: translateY(-50%);
    z-index: 61;
    background: #fffdf7;
    border-radius: 24rpx;
    padding: 36rpx;
    box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.3);
}

.intro-card {
    display: flex;
}

.intro-body {
    flex: 1;
    margin-left: 26rpx;
    display: flex;
    flex-direction: column;
}

.intro-title {
    font-size: 34rpx;
    font-weight: 800;
    color: #37332b;
}

.intro-meta {
    margin-top: 8rpx;
    font-size: 22rpx;
    color: #a39478;
}

.intro-text {
    margin-top: 16rpx;
    font-size: 24rpx;
    color: #6d6455;
    line-height: 1.7;
    display: -webkit-box;
    -webkit-line-clamp: 5;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.intro-actions {
    margin-top: 30rpx;
    display: flex;
}

.intro-btn {
    flex: 1;
    height: 76rpx;
    line-height: 76rpx;
    text-align: center;
    border-radius: 44rpx;
    background: #8b3a3a;
    color: #fff8ec;
    font-size: 28rpx;
    font-weight: 600;
    letter-spacing: 4rpx;
}

.intro-btn-ghost {
    background: #efe8d5;
    color: #6d6455;
    margin-right: 20rpx;
}
</style>
