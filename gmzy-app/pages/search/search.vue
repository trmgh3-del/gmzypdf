<template>
    <view class="search" :class="{ night }">
        <!-- 搜索栏 -->
        <view class="bar">
            <view class="bar-input">
                <text class="bar-ico">⌕</text>
                <input
                    class="input"
                    v-model="keyword"
                    :focus="autoFocus"
                    confirm-type="search"
                    placeholder="输入关键字，如：桂枝汤、足三里、脉浮"
                    placeholder-class="ph"
                    @confirm="doSearch"
                />
                <text v-if="keyword" class="bar-clear" @tap="keyword = ''; results = []">✕</text>
            </view>
            <view class="bar-btn" @tap="doSearch">搜索</view>
        </view>

        <!-- 范围选择 -->
        <view class="scope">
            <picker mode="selector" :range="scopeNames" :value="scopeIdx" @change="scopeIdx = Number($event.detail.value)">
                <view class="scope-picker">
                    <text class="scope-t">范围：{{ scopeNames[scopeIdx] }}</text>
                    <text class="scope-arrow">▾</text>
                </view>
            </picker>
            <text class="scope-hint" v-if="scopeIdx === 0">全库检索需逐本扫描，稍候片刻</text>
        </view>

        <!-- 热门关键词 -->
        <view class="hot" v-if="!searched">
            <text class="hot-title">常用检索</text>
            <view class="hot-row">
                <view v-for="w in hotWords" :key="w" class="hot-chip" @tap="quick(w)">{{ w }}</view>
            </view>
        </view>

        <!-- 进度 -->
        <view class="scanning" v-if="scanning">
            <view class="scan-bar"><view class="scan-fill" :style="{ width: scanPct + '%' }" /></view>
            <text class="scan-t">正在扫描 {{ scanBook }}（{{ scanPct }}%）…</text>
        </view>

        <!-- 结果 -->
        <view class="res-head" v-if="searched && !scanning">
            <text class="res-count">共 {{ results.length }} 条结果{{ truncated ? '（已截断，请缩小范围）' : '' }}</text>
        </view>
        <scroll-view class="res" scroll-y>
            <view
                v-for="(r, i) in results"
                :key="i"
                class="res-item"
                @tap="openResult(r)"
            >
                <view class="res-top">
                    <text class="res-book">《{{ r.bookTitle }}》</text>
                    <text class="res-chapter">{{ r.chapter }}</text>
                </view>
                <view class="res-text">
                    <text v-for="(seg, si) in r.segments" :key="si" class="res-seg" :class="{ hl: seg.hl }">{{ seg.x }}</text>
                </view>
            </view>
            <view class="res-empty" v-if="searched && !scanning && !results.length">
                <text class="res-empty-t">未找到「{{ lastKeyword }}」相关内容</text>
            </view>
        </scroll-view>
    </view>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { loadCatalog, loadBook } from '../../common/books.js'
import { pending, store } from '../../common/store.js'
import { applyNavTheme } from '../../common/theme.js'
import { blockText, chapterOf } from '../../common/util.js'

const catalog = ref([])
onMounted(async () => {
    try {
        catalog.value = await loadCatalog()
    } catch (e) {
        console.error('书目载入失败', e)
    }
})
const keyword = ref('')
const lastKeyword = ref('')
const scopeIdx = ref(0)
const scopeNames = computed(() => ['全部书库'].concat(catalog.value.map((b) => b.title)))
const results = ref([])
const searched = ref(false)
const scanning = ref(false)
const scanBook = ref('')
const scanPct = ref(0)
const truncated = ref(false)
const autoFocus = ref(true)

const hotWords = ['桂枝汤', '小柴胡汤', '足三里', '三阴交', '脉浮紧', '肾阴虚', '六经辨证', '卫气营血', '四君子汤', '活血化瘀']

const MAX_RESULTS = 300

const night = computed(() => store.settings.night)
onShow(() => {
    applyNavTheme()
    if (pending.keyword) {
        keyword.value = pending.keyword
        pending.keyword = ''
        doSearch()
    }
})

function quick(w) {
    keyword.value = w
    doSearch()
}

function makeSegments(text, kw, maxLen = 96) {
    const idx = text.indexOf(kw)
    if (idx < 0) return [{ x: text.slice(0, maxLen) }]
    const half = Math.floor((maxLen - kw.length) / 2)
    const start = Math.max(0, idx - half)
    const end = Math.min(text.length, idx + kw.length + half)
    const segs = []
    if (start > 0) segs.push({ x: (start > 3 ? '…' : '') + text.slice(start, idx) })
    segs.push({ x: kw, hl: true })
    if (idx + kw.length < end) segs.push({ x: text.slice(idx + kw.length, end) + (end < text.length ? '…' : '') })
    return segs
}

async function doSearch() {
    const kw = keyword.value.trim()
    if (!kw || scanning.value) return
    if (kw.length < 1) return
    searched.value = true
    lastKeyword.value = kw
    results.value = []
    truncated.value = false
    scanning.value = true
    scanPct.value = 0

    const targets = scopeIdx.value === 0
        ? catalog.value
        : [catalog.value[scopeIdx.value - 1]]

    const found = []
    for (let i = 0; i < targets.length; i++) {
        const meta = targets[i]
        if (!meta) continue
        scanBook.value = meta.title
        scanPct.value = Math.round((i / targets.length) * 100)
        await new Promise((r) => setTimeout(r, 10))
        try {
            const book = await loadBook(meta.slug)
            for (let g = 0; g < book.blocks.length; g++) {
                const t = blockText(book.blocks[g])
                if (t && t.indexOf(kw) >= 0) {
                    const ch = book.chapters[chapterOf(book, g)]
                    found.push({
                        slug: meta.slug,
                        bookTitle: meta.title,
                        chapter: ch ? ch.title : '',
                        g,
                        segments: makeSegments(t, kw)
                    })
                    if (found.length >= MAX_RESULTS) {
                        truncated.value = true
                        break
                    }
                }
            }
        } catch (e) {
            console.error('搜索失败', meta.slug, e)
        }
        if (truncated.value) break
    }
    scanPct.value = 100
    scanning.value = false
    results.value = found
}

function openResult(r) {
    uni.navigateTo({
        url: `/pages/reader/reader?slug=${r.slug}&g=${r.g}`
    })
}
</script>

<style lang="scss" scoped>
.search {
    min-height: 100vh;
    background: #f6f1e5;
    display: flex;
    flex-direction: column;
}

.bar {
    display: flex;
    align-items: center;
    padding: 20rpx 24rpx 12rpx;
}

.bar-input {
    flex: 1;
    display: flex;
    align-items: center;
    background: #fffdf7;
    border: 1rpx solid #e4dcc8;
    border-radius: 44rpx;
    padding: 14rpx 26rpx;
}

.bar-ico {
    font-size: 30rpx;
    color: #8b3a3a;
    margin-right: 12rpx;
}

.input {
    flex: 1;
    font-size: 28rpx;
    color: #37332b;
}

.ph {
    color: #b6a98d;
    font-size: 26rpx;
}

.bar-clear {
    color: #b6a98d;
    font-size: 26rpx;
    padding: 4rpx 10rpx;
}

.bar-btn {
    margin-left: 18rpx;
    background: #8b3a3a;
    color: #fff8ec;
    font-size: 27rpx;
    padding: 14rpx 34rpx;
    border-radius: 40rpx;
    font-weight: 600;
}

.scope {
    padding: 8rpx 34rpx 4rpx;
    display: flex;
    align-items: center;
}

.scope-picker {
    display: flex;
    align-items: center;
}

.scope-t {
    font-size: 24rpx;
    color: #6d6455;
}

.scope-arrow {
    font-size: 22rpx;
    color: #a39478;
    margin-left: 6rpx;
}

.scope-hint {
    margin-left: 20rpx;
    font-size: 20rpx;
    color: #b6a98d;
}

.hot {
    padding: 40rpx 34rpx;
}

.hot-title {
    font-size: 28rpx;
    font-weight: 700;
    color: #37332b;
}

.hot-row {
    margin-top: 22rpx;
    display: flex;
    flex-wrap: wrap;
}

.hot-chip {
    margin: 0 16rpx 16rpx 0;
    padding: 12rpx 30rpx;
    background: #fffdf7;
    border: 1rpx solid #e4dcc8;
    border-radius: 36rpx;
    font-size: 25rpx;
    color: #6d6455;
}

.scanning {
    padding: 30rpx 34rpx;
}

.scan-bar {
    height: 8rpx;
    border-radius: 8rpx;
    background: #efe7d3;
    overflow: hidden;
}

.scan-fill {
    height: 100%;
    background: linear-gradient(90deg, #b9724f, #8b3a3a);
    transition: width 0.15s;
}

.scan-t {
    display: block;
    margin-top: 14rpx;
    font-size: 23rpx;
    color: #8d8371;
}

.res-head {
    padding: 22rpx 34rpx 10rpx;
}

.res-count {
    font-size: 24rpx;
    color: #8d8371;
}

.res {
    flex: 1;
}

.res-item {
    margin: 0 24rpx 20rpx;
    background: #fffdf7;
    border-radius: 16rpx;
    padding: 24rpx 26rpx;
    box-shadow: 0 4rpx 16rpx rgba(90, 60, 30, 0.07);
}

.res-top {
    display: flex;
    align-items: baseline;
}

.res-book {
    font-size: 26rpx;
    font-weight: 700;
    color: #8b3a3a;
}

.res-chapter {
    margin-left: 14rpx;
    flex: 1;
    font-size: 22rpx;
    color: #a39478;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.res-text {
    margin-top: 12rpx;
    line-height: 1.65;
}

.res-seg {
    font-size: 26rpx;
    color: #4a443a;
}

.hl {
    color: #c0392b;
    font-weight: 700;
    background: rgba(192, 57, 43, 0.1);
}

.res-empty {
    padding: 120rpx 0;
    text-align: center;
}

.res-empty-t {
    color: #a39478;
    font-size: 26rpx;
}
</style>
