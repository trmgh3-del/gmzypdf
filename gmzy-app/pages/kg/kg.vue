<template>
    <view class="kgp" :class="{ night, elder: store.settings.elder, [themeCls]: night }">
        <!-- 学科枢纽卡 -->
        <view class="hub">
            <view class="hub-top">
                <text class="hub-icon serif-font">{{ cat.icon }}</text>
                <view class="hub-txt">
                    <text class="hub-name serif-font">{{ cat.name }}</text>
                    <text class="hub-desc">{{ cat.desc }}</text>
                </view>
            </view>
            <view class="hub-stats">
                <text class="hs">藏书 {{ cat.bookCount }} 部</text>
                <text class="hs">条目 {{ cat.entryCount }} 条</text>
                <text class="hs" v-if="cat.quizCount">题库 {{ cat.quizCount }} 题</text>
                <text class="hs" v-if="readInCat">已读 {{ readInCat }}</text>
            </view>
            <view class="hub-progress" v-if="cat.entryCount">
                <view class="hp-fill" :style="{ width: catPct + '%' }" />
            </view>
            <!-- 学习工具枢纽 -->
            <view class="hub-tools">
                <view v-for="d in cat.decks" :key="d" class="tool" @tap="goDeck(d)">
                    <text class="tool-name">记忆卡 · {{ deckName(d) }}</text>
                    <text class="tool-meta">{{ deckDue(d) }} 张到期 ›</text>
                </view>
                <view v-if="cat.atlas" class="tool" @tap="goAtlas">
                    <text class="tool-name">六诊图谱考举</text>
                    <text class="tool-meta">入闱 ›</text>
                </view>
                <view v-for="q in cat.quiz" :key="q.slug" class="tool" @tap="goQuiz(q.slug)">
                    <text class="tool-name">复习思考 · {{ bookTitle(q.slug) }}</text>
                    <text class="tool-meta">{{ q.count }} 题 ›</text>
                </view>
            </view>
        </view>

        <!-- 条目流（按书分组） -->
        <view class="entries">
            <view class="en-head">
                <text class="sec-title">📖 知识条目</text>
                <text class="en-count">{{ filteredEntries.length }} 条</text>
            </view>
            <view class="en-search">
                <input v-model="kw" class="en-kw" placeholder="学科内检索条目名…" confirm-type="search" />
            </view>
            <view v-for="bk in groupedEntries" :key="bk.b" class="en-book">
                <text class="en-bt serif-font">{{ bk.bt }}</text>
                <view
                    v-for="e in bk.list"
                    :key="e.b + ':' + e.g"
                    class="en-item"
                    @tap="goArticle(e)"
                >
                    <view class="en-item-main">
                        <text class="en-t serif-font">{{ e.t }}</text>
                        <text class="en-pt" v-if="e.pt">{{ e.pt }}</text>
                    </view>
                    <text class="en-read" :class="{ done: isRead(e) }">{{ isRead(e) ? '✓ 已读' : '›' }}</text>
                </view>
            </view>
            <text class="en-empty" v-if="!filteredEntries.length">未检索到条目</text>
        </view>
    </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { store, isKgRead, deckStats } from '../../common/store.js'
import { loadKgIndex, getKgCat } from '../../common/kg.js'
import { loadDecks } from '../../common/learn.js'
import { applyNavTheme } from '../../common/theme.js'

const cat = ref({ key: '', name: '', icon: '', desc: '', books: [], quiz: [], decks: [], entries: [], entryCount: 0, bookCount: 0, quizCount: 0 })
const decks = ref([])
const kw = ref('')
const night = computed(() => store.settings.night)
const themeCls = computed(() => 'night-theme-' + (store.settings.nightTheme || 'warm'))

let catKey = ''
onLoad(async (q) => {
    catKey = q.key || 'basics'
    await Promise.all([loadKgIndex(), loadDecks()])
    const c = getKgCat(catKey)
    if (!c) return
    cat.value = c
    decks.value = (await loadDecks()) || []
    uni.setNavigationBarTitle({ title: c.name })
})

onShow(() => applyNavTheme())

const filteredEntries = computed(() => {
    const list = cat.value.entries || []
    const k = kw.value.trim()
    if (!k) return list
    return list.filter((e) => (e.t || '').includes(k) || (e.pt || '').includes(k) || (e.bt || '').includes(k))
})

// 按书分组（索引次序）
const groupedEntries = computed(() => {
    const map = new Map()
    for (const e of filteredEntries.value) {
        if (!map.has(e.b)) map.set(e.b, { b: e.b, bt: e.bt, list: [] })
        map.get(e.b).list.push(e)
    }
    return [...map.values()]
})

const readInCat = computed(() => {
    const kd = store.learn.kgDone || {}
    return (cat.value.entries || []).reduce((n, e) => n + (kd[e.b + ':' + e.g] ? 1 : 0), 0)
})
const catPct = computed(() => (cat.value.entryCount ? ((readInCat.value / cat.value.entryCount) * 100).toFixed(1) : 0))

function isRead(e) {
    return isKgRead(e.b, e.g)
}

function bookTitle(slug) {
    const bk = (cat.value.books || []).find((b) => b.slug === slug)
    return bk ? bk.title : slug
}

function deckName(id) {
    const d = (decks.value || []).find((x) => x.id === id)
    return d ? d.name : id
}
function deckDue(id) {
    return deckStats(id, 0).due
}

function goArticle(e) {
    uni.navigateTo({ url: `/pages/kgarticle/kgarticle?key=${catKey}&s=${e.b}&g=${e.g}` })
}
function goDeck(id) {
    uni.navigateTo({ url: '/pages/cards/cards?deck=' + id })
}
function goQuiz(slug) {
    uni.navigateTo({ url: '/pages/quiz/quiz?k=' + slug })
}
function goAtlas() {
    uni.switchTab({ url: '/pages/diag/diag' })
}
</script>

<style scoped>
.kgp {
    min-height: 100vh;
    background: #f6f1e5;
}
.night .kgp {
    background: #1a1611;
}

/* 学科枢纽卡 */
.hub {
    margin: 24rpx 30rpx;
    padding: 28rpx;
    background: linear-gradient(150deg, #fffdf5, #f7ead0);
    border: 1px solid rgba(181, 147, 90, 0.55);
    border-radius: 20rpx;
}

.hub-top {
    display: flex;
    align-items: center;
    gap: 20rpx;
    margin-bottom: 8rpx;
}

.hub-icon {
    font-size: 56rpx;
    color: #8b3a3a;
    width: 76rpx;
    height: 76rpx;
    line-height: 76rpx;
    text-align: center;
    background: rgba(139, 58, 58, 0.08);
    border-radius: 18rpx;
}

.hub-name {
    display: block;
    font-size: 38rpx;
    font-weight: 700;
    color: #2e2921;
    letter-spacing: 3rpx;
}

.night .hub-name {
    color: #e8dfc8;
}

.hub-desc {
    display: block;
    font-size: 23rpx;
    color: #8d8371;
    margin-top: 4rpx;
}

.hub-stats {
    display: flex;
    flex-wrap: wrap;
    gap: 14rpx;
    margin: 14rpx 0 10rpx;
}

.hs {
    font-size: 22rpx;
    color: #6b5d4f;
    background: rgba(181, 147, 90, 0.16);
    border-radius: 8rpx;
    padding: 5rpx 14rpx;
}

.hub-progress {
    height: 8rpx;
    background: rgba(181, 147, 90, 0.22);
    border-radius: 999rpx;
    overflow: hidden;
    margin-bottom: 18rpx;
}

.hp-fill {
    height: 100%;
    background: #8b3a3a;
    border-radius: 999rpx;
}

.hub-tools {
    display: flex;
    flex-direction: column;
    gap: 12rpx;
}

.tool {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(139, 58, 58, 0.07);
    border: 1px solid rgba(139, 58, 58, 0.18);
    border-radius: 12rpx;
    padding: 16rpx 20rpx;
}

.tool-name {
    font-size: 26rpx;
    color: #5c2018;
    font-weight: 600;
}

.tool-meta {
    font-size: 22rpx;
    color: #8d6244;
}

/* 条目流 */
.entries {
    margin: 0 30rpx 40rpx;
}

.en-head {
    display: flex;
    align-items: baseline;
    gap: 14rpx;
    margin-bottom: 12rpx;
}

.sec-title {
    font-size: 30rpx;
    font-weight: 700;
    color: #3a342a;
}

.night .sec-title {
    color: #e8dfc8;
}

.en-count {
    font-size: 22rpx;
    color: #a0937a;
}

.en-search {
    background: rgba(139, 58, 58, 0.06);
    border-radius: 12rpx;
    padding: 4rpx 20rpx;
    margin-bottom: 18rpx;
}

.en-kw {
    height: 66rpx;
    font-size: 26rpx;
    color: #3a342a;
}

.night .en-kw {
    color: #e8dfc8;
}

.en-book {
    margin-bottom: 20rpx;
}

.en-bt {
    display: block;
    font-size: 26rpx;
    color: #8b3a3a;
    font-weight: 700;
    margin: 20rpx 0 8rpx;
    letter-spacing: 2rpx;
}

.en-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20rpx 22rpx;
    background: #fffdf7;
    border: 1px solid rgba(139, 58, 58, 0.1);
    border-radius: 12rpx;
    margin-bottom: 10rpx;
}

.night .en-item {
    background: #241f18;
    border-color: rgba(232, 223, 200, 0.1);
}

.en-item-main {
    flex: 1;
    min-width: 0;
}

.en-t {
    display: block;
    font-size: 28rpx;
    color: #3a342a;
}

.night .en-t {
    color: #e8dfc8;
}

.en-pt {
    display: block;
    font-size: 21rpx;
    color: #a0937a;
    margin-top: 3rpx;
}

.en-read {
    font-size: 22rpx;
    color: #a0937a;
    padding-left: 12rpx;
}

.en-read.done {
    color: #557a46;
}

.en-empty {
    display: block;
    text-align: center;
    font-size: 24rpx;
    color: #a0937a;
    padding: 60rpx 0;
}
</style>
