<template>
    <view class="mine" :class="{ night }">
        <!-- 统计卡 -->
        <view class="stats">
            <view class="stat">
                <text class="stat-num serif-font">{{ history.length }}</text>
                <text class="stat-label">在读</text>
            </view>
            <view class="stat-div" />
            <view class="stat">
                <text class="stat-num serif-font">{{ bookmarks.length }}</text>
                <text class="stat-label">书签</text>
            </view>
            <view class="stat-div" />
            <view class="stat">
                <text class="stat-num serif-font">{{ finishedCount }}</text>
                <text class="stat-label">已读完</text>
            </view>
        </view>

        <!-- 阅读历史 -->
        <view class="sec">
            <view class="sec-head">
                <text class="sec-title">阅读历史</text>
                <text class="sec-op" v-if="history.length" @tap="clearHis">清空</text>
            </view>
            <view v-if="!history.length" class="empty">还没有阅读记录，去书架挑一本吧</view>
            <view
                v-for="h in history"
                :key="h.slug"
                class="his-item"
                @tap="openResume(h)"
                @longpress="removeHis(h.slug)"
            >
                <BookCover :title="h.title" :cover="h.cover" :width="110" />
                <view class="his-info">
                    <text class="his-title">{{ h.title }}</text>
                    <text class="his-chapter">{{ h.chapter || '卷首' }}</text>
                    <view class="his-bar"><view class="his-fill" :style="{ width: pct(h.slug) + '%' }" /></view>
                    <text class="his-meta">{{ pct(h.slug) }}% · {{ formatTime(h.ts) }}</text>
                </view>
                <text class="his-go">继续 ›</text>
            </view>
        </view>

        <!-- 书签 -->
        <view class="sec">
            <view class="sec-head">
                <text class="sec-title">我的书签</text>
                <text class="sec-op" v-if="bookmarks.length" @tap="clearBm">清空</text>
            </view>
            <view v-if="!bookmarks.length" class="empty">阅读时点右上角＋书签即可收藏</view>
            <view
                v-for="(m, i) in bookmarks"
                :key="i"
                class="bm-item"
                @tap="openG(m)"
                @longpress="removeBm(i)"
            >
                <view class="bm-mark serif-font">签</view>
                <view class="bm-info">
                    <view class="bm-top">
                        <text class="bm-book">《{{ m.title }}》{{ m.chapter }}</text>
                        <text class="bm-time">{{ formatTime(m.ts) }}</text>
                    </view>
                    <text class="bm-text">{{ m.excerpt }}</text>
                </view>
            </view>
        </view>

        <!-- 关于 -->
        <view class="sec">
            <view class="sec-head"><text class="sec-title">设置</text></view>
            <view class="set-row" @tap="toggleNight">
                <view class="set-info">
                    <text class="set-name">夜间模式</text>
                    <text class="set-desc">书架、学习、辨证、查询等界面整体转暗</text>
                </view>
                <switch :checked="night" color="#8b3a3a" @change="toggleNight" @tap.stop />
            </view>
        </view>
        <view class="sec">
            <view class="sec-head"><text class="sec-title">关于</text></view>
            <view class="about">
                <text class="about-title serif-font">光明中医文库·学习诊断系统</text>
                <text class="about-line">收录光明中医函授教材 26 部，全文离线精排。</text>
                <text class="about-line">内置记忆卡 1110 张、复习思考题 1974 题与中医辨证辅助。</text>
                <text class="about-line">辨证功能仅供学习参考，不能替代执业医师面诊。</text>
                <text class="about-line">内容来源：光明中医网校（gmzy 系列教材电子化）。</text>
                <text class="about-line">版本 v2.1.0 · 仅供学习研究使用</text>
            </view>
        </view>
    </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { store, removeHistory, clearHistory, removeBookmark, clearBookmarks, setNight } from '../../common/store.js'
import { applyNavTheme } from '../../common/theme.js'
import { formatTime } from '../../common/util.js'
import BookCover from '../../components/BookCover.vue'

const history = computed(() => store.history)
const bookmarks = computed(() => store.bookmarks)
const tick = ref(0)
const night = computed(() => store.settings.night)
onShow(() => {
    tick.value++
    applyNavTheme()
})

function toggleNight() {
    setNight(!store.settings.night)
    applyNavTheme()
}

const finishedCount = computed(() => {
    tick.value
    return Object.values(store.progress).filter((p) => p.percent >= 0.995).length
})

function pct(slug) {
    const p = store.progress[slug]
    return p && p.percent ? Math.min(100, Math.round(p.percent * 1000) / 10) : 0
}

function openResume(h) {
    uni.navigateTo({
        url: `/pages/reader/reader?slug=${h.slug}&g=${h.gIdx || 0}`
    })
}

function openG(m) {
    uni.navigateTo({
        url: `/pages/reader/reader?slug=${m.slug}&g=${m.gIdx}`
    })
}

function removeHis(slug) {
    uni.showActionSheet({
        itemList: ['删除该记录'],
        success: (r) => {
            if (r.tapIndex === 0) removeHistory(slug)
        }
    })
}

function clearHis() {
    uni.showModal({
        title: '清空阅读历史？',
        content: '此操作不可恢复',
        success: (r) => {
            if (r.confirm) clearHistory()
        }
    })
}

function removeBm(i) {
    uni.showActionSheet({
        itemList: ['删除该书签'],
        success: (r) => {
            if (r.tapIndex === 0) removeBookmark(i)
        }
    })
}

function clearBm() {
    uni.showModal({
        title: '清空全部书签？',
        content: '此操作不可恢复',
        success: (r) => {
            if (r.confirm) clearBookmarks()
        }
    })
}
</script>

<style lang="scss" scoped>
.mine {
    min-height: 100vh;
    background: #f6f1e5;
    padding-bottom: 60rpx;
}

.stats {
    margin: 30rpx;
    background: linear-gradient(160deg, #6b2a20, #451611);
    border-radius: 22rpx;
    padding: 36rpx 0;
    display: flex;
    align-items: center;
}

.stat {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.stat-num {
    font-size: 44rpx;
    font-weight: 800;
    color: #f3e9d2;
}

.stat-label {
    margin-top: 8rpx;
    font-size: 22rpx;
    color: rgba(243, 233, 210, 0.6);
    letter-spacing: 4rpx;
}

.stat-div {
    width: 1rpx;
    height: 60rpx;
    background: rgba(243, 233, 210, 0.25);
}

.sec {
    margin: 26rpx 30rpx 0;
}

.sec-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 18rpx;
}

.sec-title {
    font-size: 31rpx;
    font-weight: 700;
    color: #37332b;
}

.sec-op {
    font-size: 23rpx;
    color: #a39478;
}

.empty {
    background: #fffdf7;
    border-radius: 16rpx;
    padding: 46rpx 0;
    text-align: center;
    color: #b6a98d;
    font-size: 25rpx;
}

.his-item {
    display: flex;
    align-items: center;
    background: #fffdf7;
    border-radius: 16rpx;
    padding: 20rpx;
    margin-bottom: 16rpx;
    box-shadow: 0 4rpx 14rpx rgba(90, 60, 30, 0.06);
}

.his-info {
    flex: 1;
    margin-left: 20rpx;
}

.his-title {
    font-size: 27rpx;
    font-weight: 600;
    color: #37332b;
}

.his-chapter {
    display: block;
    margin-top: 6rpx;
    font-size: 22rpx;
    color: #8d8371;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.his-bar {
    margin-top: 12rpx;
    height: 6rpx;
    border-radius: 6rpx;
    background: #efe7d3;
    overflow: hidden;
}

.his-fill {
    height: 100%;
    background: linear-gradient(90deg, #b9724f, #8b3a3a);
}

.his-meta {
    display: block;
    margin-top: 8rpx;
    font-size: 20rpx;
    color: #a39478;
}

.his-go {
    color: #8b3a3a;
    font-size: 24rpx;
    padding: 10rpx 6rpx;
}

.bm-item {
    display: flex;
    background: #fffdf7;
    border-radius: 16rpx;
    padding: 22rpx;
    margin-bottom: 16rpx;
    box-shadow: 0 4rpx 14rpx rgba(90, 60, 30, 0.06);
}

.bm-mark {
    width: 56rpx;
    height: 56rpx;
    border-radius: 12rpx;
    background: #8b3a3a;
    color: #fff8ec;
    text-align: center;
    line-height: 56rpx;
    font-size: 28rpx;
}

.bm-info {
    flex: 1;
    margin-left: 20rpx;
}

.bm-top {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
}

.bm-book {
    flex: 1;
    font-size: 24rpx;
    color: #8b3a3a;
    font-weight: 600;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.bm-time {
    margin-left: 16rpx;
    font-size: 20rpx;
    color: #a39478;
}

.bm-text {
    display: block;
    margin-top: 10rpx;
    font-size: 25rpx;
    color: #4a443a;
    line-height: 1.6;
}

.about {
    background: #fffdf7;
    border-radius: 16rpx;
    padding: 30rpx;
}

.about-title {
    display: block;
    font-size: 32rpx;
    font-weight: 800;
    color: #37332b;
}

.about-line {
    display: block;
    margin-top: 12rpx;
    font-size: 24rpx;
    color: #6d6455;
    line-height: 1.7;
}

.set-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10rpx 0;
    gap: 20rpx;
}

.set-info {
    flex: 1;
}

.set-name {
    display: block;
    font-size: 28rpx;
    color: #37332b;
    font-weight: 600;
    margin-bottom: 4rpx;
}

.set-desc {
    display: block;
    font-size: 22rpx;
    color: #8d8371;
}
</style>
