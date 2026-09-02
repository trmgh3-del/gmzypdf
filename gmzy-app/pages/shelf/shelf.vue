<template>
    <view class="shelf-p" :class="{ night, elder: store.settings.elder, [themeCls]: night }">
        <view class="slp-head">
            <text class="slp-title serif-font">📚 全文资料室</text>
            <text class="slp-sub">光明中医函授教材 {{ catalog.length }} 部 · 全文离线阅读（附录形态，学习请回知识库）</text>
        </view>

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

        <view class="grid">
            <view v-for="b in books" :key="b.slug" class="book" @tap="openBook(b.slug)">
                <BookCover :title="b.title" :cover="b.cover" :width="100" />
                <text class="book-title">{{ b.title }}</text>
                <text class="book-meta">{{ b.chapters }} 章节</text>
            </view>
        </view>
    </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { store } from '../../common/store.js'
import { loadCatalog, CATEGORIES, booksOf } from '../../common/books.js'
import { applyNavTheme } from '../../common/theme.js'
import BookCover from '../../components/BookCover.vue'

const catalog = ref([])
const catKey = ref('all')
const night = computed(() => store.settings.night)
const themeCls = computed(() => 'night-theme-' + (store.settings.nightTheme || 'warm'))

onLoad(async () => {
    uni.setNavigationBarTitle({ title: '全文资料室' })
    catalog.value = await loadCatalog()
})

onShow(() => applyNavTheme())

const books = computed(() => booksOf(catKey.value))

function openBook(slug) {
    uni.navigateTo({ url: `/pages/reader/reader?slug=${slug}` })
}
</script>

<style scoped>
.shelf-p {
    min-height: 100vh;
    background: #f6f1e5;
    padding: 24rpx 30rpx 40rpx;
}

.night .shelf-p {
    background: #1a1611;
}

.slp-head {
    padding: 12rpx 6rpx 22rpx;
}

.slp-title {
    display: block;
    font-size: 40rpx;
    font-weight: 700;
    color: #5c2018;
    letter-spacing: 4rpx;
}

.night .slp-title {
    color: #e8b0a0;
}

.slp-sub {
    display: block;
    font-size: 22rpx;
    color: #8d8371;
    margin-top: 10rpx;
}

.cats {
    white-space: nowrap;
    margin-bottom: 24rpx;
}

.cats-row {
    display: flex;
    gap: 16rpx;
    padding: 4rpx 2rpx;
}

.cat-chip {
    padding: 12rpx 28rpx;
    border-radius: 999rpx;
    font-size: 25rpx;
    background: rgba(139, 58, 58, 0.07);
    color: #5c2018;
    border: 1px solid rgba(139, 58, 58, 0.2);
}

.cat-chip.on {
    background: #8b3a3a;
    color: #fffdf7;
}

.night .cat-chip {
    color: #e8dfc8;
    background: rgba(232, 223, 200, 0.08);
    border-color: rgba(232, 223, 200, 0.2);
}

.night .cat-chip.on {
    background: #8b3a3a;
}

.grid {
    display: flex;
    flex-wrap: wrap;
    gap: 28rpx 30rpx;
}

.book {
    width: 200rpx;
    display: flex;
    flex-direction: column;
}

.book-title {
    font-size: 25rpx;
    color: #3a342a;
    margin-top: 12rpx;
    font-weight: 600;
    line-height: 1.35;
}

.night .book-title {
    color: #e8dfc8;
}

.book-meta {
    font-size: 21rpx;
    color: #a0937a;
    margin-top: 3rpx;
}
</style>
