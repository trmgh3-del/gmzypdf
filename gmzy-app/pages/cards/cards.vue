<template>
    <view class="cards">
        <view v-if="!ready" class="loading">卡片加载中…</view>
        <template v-else-if="!queue.length">
            <view class="done-all">
                <text class="done-emoji serif-font">毕</text>
                <text class="done-text">该筛选下没有卡片了</text>
                <button class="btn ghost" @tap="resetFilter(false)">回到全部</button>
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
                        @tap="resetFilter(f.key)"
                    >{{ f.name }}</text>
                </view>
                <text class="shuffle" :class="{ on: shuffled }" @tap="toggleShuffle">乱序</text>
            </view>

            <view class="stage" @tap="flip">
                <view class="card" :class="{ flipped, ['lv' + mastery] : !flipped }">
                    <view class="face front">
                        <text class="card-sub">{{ cur.sub }}</text>
                        <text class="card-front serif-font">{{ cur.front }}</text>
                        <text class="card-hint">点击卡片查看释义</text>
                    </view>
                    <view class="face back">
                        <text class="back-title serif-font">{{ cur.front }}</text>
                        <scroll-view scroll-y class="back-scroll">
                            <text class="back-body">{{ cur.back }}</text>
                        </scroll-view>
                    </view>
                </view>
            </view>

            <view class="rate">
                <view class="rate-btn bad" @tap.stop="rate(1)">
                    <text class="rate-name">不认识</text>
                    <text class="rate-sub">稍后再见</text>
                </view>
                <view class="rate-btn mid" @tap.stop="rate(2)">
                    <text class="rate-name">模糊</text>
                    <text class="rate-sub">还需巩固</text>
                </view>
                <view class="rate-btn good" @tap.stop="rate(3)">
                    <text class="rate-name">已掌握</text>
                    <text class="rate-sub">下次跳过</text>
                </view>
            </view>

            <view class="nav-row">
                <text class="nav-btn" @tap="prev">‹ 上一张</text>
                <text class="nav-btn" @tap="next">下一张 ›</text>
            </view>
        </template>
    </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { loadDecks, loadDeck } from '../../common/learn.js'
import { setCardMastery, cardMasteryOf } from '../../common/store.js'

const FILTERS = [
    { key: 'all', name: '全部' },
    { key: 'new', name: '未学' },
    { key: 'weak', name: '待巩固' }
]

const deckId = ref('')
const cards = ref([])
const deckMeta = ref({})
const ready = ref(false)
const queue = ref([]) // 原 cards 的索引序列
const pos = ref(0)
const flipped = ref(false)
const shuffled = ref(false)
const filter = ref('all')
const mastery = ref(0)

onLoad(async (q) => {
    deckId.value = q.deck || 'fangji'
    const [decks, list] = await Promise.all([loadDecks(), loadDeck(deckId.value)])
    deckMeta.value = decks.find((d) => d.id === deckId.value) || {}
    cards.value = list
    uni.setNavigationBarTitle({ title: deckMeta.value.name || '记忆卡' })
    buildQueue()
    ready.value = true
})

const cur = computed(() => cards.value[queue.value[pos.value]] || {})

function buildQueue() {
    let idx = cards.value.map((_, i) => i)
    if (filter.value === 'new') idx = idx.filter((i) => !cardMasteryOf(deckId.value, i))
    if (filter.value === 'weak') {
        idx = idx.filter((i) => {
            const v = cardMasteryOf(deckId.value, i)
            return v === 1 || v === 2
        })
    }
    if (shuffled.value) {
        for (let i = idx.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1))
            ;[idx[i], idx[j]] = [idx[j], idx[i]]
        }
    }
    queue.value = idx
    pos.value = 0
    flipped.value = false
    syncMastery()
}

function syncMastery() {
    mastery.value = cardMasteryOf(deckId.value, queue.value[pos.value] ?? -1)
}

function flip() {
    flipped.value = !flipped.value
}

function rate(level) {
    const real = queue.value[pos.value]
    if (real === undefined) return
    setCardMastery(deckId.value, real, level)
    const nextPos = pos.value + 1
    if (nextPos < queue.value.length) {
        pos.value = nextPos
    } else {
        // 到达末尾：重新构建队列（掌握后的新状态会刷新待巩固）
        buildQueue()
    }
    flipped.value = false
    syncMastery()
}

function prev() {
    if (pos.value > 0) {
        pos.value--
        flipped.value = false
        syncMastery()
    }
}

function next() {
    if (pos.value < queue.value.length - 1) {
        pos.value++
        flipped.value = false
        syncMastery()
    }
}

function resetFilter(f) {
    filter.value = f || 'all'
    buildQueue()
}

function toggleShuffle() {
    shuffled.value = !shuffled.value
    buildQueue()
}
</script>

<style lang="scss" scoped>
.cards {
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
    width: 150rpx;
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

.shuffle {
    width: 150rpx;
    text-align: right;
    font-size: 23rpx;
    color: #8d8371;

    &.on {
        color: #8b3a3a;
        font-weight: 600;
    }
}

.stage {
    flex: 1;
    perspective: 1200rpx;
    min-height: 640rpx;
}

.card {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 640rpx;
    transform-style: preserve-3d;
    transition: transform 0.45s ease;

    &.flipped {
        transform: rotateY(180deg);
    }
}

.face {
    position: absolute;
    inset: 0;
    backface-visibility: hidden;
    border-radius: 24rpx;
    background: #fffdf7;
    border: 1rpx solid #e4dcc8;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 60rpx 40rpx;

    &.back {
        transform: rotateY(180deg);
        align-items: stretch;
        background: #fefaf0;
    }
}

.card.lv1 .front { border-top: 8rpx solid #b3543f; }
.card.lv2 .front { border-top: 8rpx solid #c8932f; }
.card.lv3 .front { border-top: 8rpx solid #4a7c59; }

.card-sub {
    font-size: 24rpx;
    color: #8d8371;
    margin-bottom: 30rpx;
}

.card-front {
    font-size: 64rpx;
    font-weight: 700;
    color: #37332b;
    text-align: center;
    line-height: 1.4;
}

.card-hint {
    position: absolute;
    bottom: 40rpx;
    font-size: 22rpx;
    color: #b9ac92;
}

.back-title {
    font-size: 34rpx;
    font-weight: 700;
    color: #5c2018;
    margin-bottom: 20rpx;
    text-align: center;
}

.back-scroll {
    flex: 1;
    height: 480rpx;
}

.back-body {
    font-size: 27rpx;
    line-height: 1.9;
    color: #4a453b;
    white-space: pre-line;
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
    &.mid { background: rgba(200, 147, 47, 0.12); }
    &.good { background: rgba(74, 124, 89, 0.12); }
}

.rate-name {
    font-size: 28rpx;
    font-weight: 600;
}

.bad .rate-name { color: #b3543f; }
.mid .rate-name { color: #a67619; }
.good .rate-name { color: #4a7c59; }

.rate-sub {
    font-size: 20rpx;
    color: #8d8371;
}

.nav-row {
    display: flex;
    justify-content: space-between;
    margin-top: 22rpx;
    padding: 0 10rpx;
}

.nav-btn {
    font-size: 26rpx;
    color: #8b3a3a;
    padding: 10rpx 20rpx;
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
