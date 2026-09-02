<template>
    <view class="cards" :class="{ night, [themeCls]: night }" @touchstart="ts" @touchend="te">
        <view v-if="!ready" class="loading">卡片加载中…</view>
        <template v-else-if="!queue.length">
            <view class="done-all">
                <text class="done-emoji serif-font">毕</text>
                <text class="done-text">{{ emptyText }}</text>
                <button v-if="!dueMode" class="btn ghost" @tap="resetFilter('all')">回到全部</button>
                <button v-else class="btn ghost" @tap="goNormal">进入顺序学习</button>
            </view>
        </template>
        <template v-else>
            <view class="topbar">
                <text class="counter serif-font">{{ pos + 1 }} / {{ queue.length }}</text>
                <view v-if="dueMode" class="due-tag serif-font">复习到期的 {{ queue.length }} 张</view>
                <view v-else-if="quotaLeft >= 0" class="due-tag serif-font">今日新卡余 {{ quotaLeft }}</view>
                <view v-else class="seg">
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
                <view class="card" :class="{ flipped, ['lv' + mastery]: !flipped }">
                    <view class="face front">
                        <text class="card-sub">{{ cur.sub }}</text>
                        <text class="card-front serif-font">{{ cur.front }}</text>
                        <text v-if="dueInfo" class="card-due">{{ dueInfo }}</text>
                        <text class="card-hint">点击卡片查看释义 · 左右滑动切换</text>
                    </view>
                    <view class="face back">
                        <text class="back-title serif-font">{{ cur.front }}</text>
                        <scroll-view scroll-y class="back-scroll">
                            <text class="back-body">{{ cur.back }}</text>
                        </scroll-view>
                        <view v-if="hasAnchor" class="src-link" @tap.stop="goSource">📖 查看教材原文 ›</view>
                    </view>
                </view>
            </view>

            <view class="rate">
                <view class="rate-btn bad" @tap.stop="rate(1)">
                    <text class="rate-name">不认识</text>
                    <text class="rate-sub">30 分钟后重现</text>
                </view>
                <view class="rate-btn mid" @tap.stop="rate(2)">
                    <text class="rate-name">模糊</text>
                    <text class="rate-sub">明日再复习</text>
                </view>
                <view class="rate-btn good" @tap.stop="rate(3)">
                    <text class="rate-name">已掌握</text>
                    <text class="rate-sub">间隔逐渐拉长</text>
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
import { onLoad, onShow } from '@dcloudio/uni-app'
import { loadDecks, loadDeck, migrateLegacyLearn } from '../../common/learn.js'
import { herbfangIndex } from './useHF.js'
import { koujueFangIndex } from './useKF.js'
import {
    store,
    setCardMastery,
    cardMasteryOf,
    cardStateRef,
    dueCardUuids,
    quotaRemaining,
    newPerDayLimit,
    hasLegacyKeys,
    markMigrated
} from '../../common/store.js'
import { applyNavTheme } from '../../common/theme.js'

const FILTERS = [
    { key: 'all', name: '全部' },
    { key: 'new', name: '未学' },
    { key: 'weak', name: '待巩固' },
    { key: 'due', name: '到期' }
]

const deckId = ref('')
const cards = ref([])
const ready = ref(false)
const queue = ref([])
const pos = ref(0)
const flipped = ref(false)
const shuffled = ref(false)
const filter = ref('all')
const mastery = ref(0)
const dueMode = ref(false)
const night = ref(false)
const themeCls = computed(() => 'night-theme-' + (store.settings.nightTheme || 'warm'))
const touchX = ref(0)
const quotaLeft = ref(0)
const focusUuid = ref('')

const herbName2Uuid = ref({})     // 中药名 → herb deck 的 uuid（方剂卡药味用）
const fangByHerb = ref({})        // 中药名 → [{front, uuid}]（中药卡反查用）
const hfReady = ref(false)
const kfSong = ref({})            // 方剂卡 front → 对应口诀卡（歌诀对照）
const kfFang = ref({})            // 口诀卡 uuid → 含方剂的方剂卡列表
const kfReady = ref(false)

onLoad(async (q) => {
    deckId.value = q.deck || 'fangji'
    if (hasLegacyKeys()) await migrateLegacyLearn(store, markMigrated)
    const [decks, list] = await Promise.all([loadDecks(), loadDeck(deckId.value)])
    const meta = decks.find((d) => d.id === deckId.value) || {}
    cards.value = list
    uni.setNavigationBarTitle({ title: meta.name || '记忆卡' })
    if (q.due === '1') {
        dueMode.value = true
        filter.value = 'due'
    }
    if (q.focus) focusUuid.value = decodeURIComponent(q.focus)
    buildQueue()
    ready.value = true
    if (deckId.value === 'fangji' || deckId.value === 'herb') {
        herbfangIndex().then(({ herbName2Uuid: h, fangByHerb: f }) => {
            herbName2Uuid.value = h
            fangByHerb.value = f
            hfReady.value = true
        })
    }
    if (deckId.value === 'fangji' || deckId.value === 'koujue') {
        koujueFangIndex().then(({ fang2song, song2fang }) => {
            kfSong.value = fang2song
            kfFang.value = song2fang
            kfReady.value = true
        })
    }
})

onShow(() => {
    night.value = applyNavTheme()
})

const emptyText = computed(() => {
    if (dueMode.value) return '今日到期卡片已全部复习完，继续保持！'
    if (filter.value === 'all' || filter.value === 'new')
        return `今日新卡已达上限 ${newPerDayLimit()} 张，可在"我的 → 设置"调整；到期复习不受影响`
    return '该筛选下没有卡片了'
})

const cur = computed(() => cards.value[queue.value[pos.value]] || {})
const hasAnchor = computed(() => {
    const m = cur.value.meta
    return m && m.book && m.g !== null && m.g !== undefined
})
const dueInfo = computed(() => {
    const real = queue.value[pos.value]
    if (real === undefined || !dueMode.value) return ''
    const st = cardStateRef(uuidOf(real))
    if (!st || !st.lv) return ''
    return ['', '尚未记住 · 今日强化', '模糊 · 间隔复习', '巩固中'][st.lv] || ''
})

function uuidOf(i) {
    return cards.value[i]?.meta?.uuid || ''
}

function buildQueue() {
    quotaLeft.value = quotaRemaining(deckId.value)
    let idx = cards.value.map((_, i) => i)
    if (filter.value === 'due') {
        const dueSet = new Set(dueCardUuids(deckId.value))
        idx = idx.filter((i) => dueSet.has(uuidOf(i)))
    } else {
        let budget = quotaLeft.value
        idx = idx.filter((i) => {
            const lv = cardMasteryOf(uuidOf(i))
            if (filter.value === 'new') {
                if (lv) return false
                if (budget-- > 0) return true
                return false
            }
            if (filter.value === 'weak') return lv === 1 || lv === 2
            // all：学过的全放行，未学的受新卡配额限制
            if (lv) return true
            return budget-- > 0
        })
    }
    if (shuffled.value && filter.value !== 'due') {
        for (let i = idx.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1))
            ;[idx[i], idx[j]] = [idx[j], idx[i]]
        }
    }
    queue.value = idx
    pos.value = 0
    // 定位到指定卡片（查词跳转）
    if (focusUuid.value) {
        const fi = idx.findIndex((i) => uuidOf(i) === focusUuid.value)
        if (fi >= 0) pos.value = fi
        focusUuid.value = ''
    }
    flipped.value = false
    syncMastery()
}

function syncMastery() {
    const i = queue.value[pos.value]
    mastery.value = i === undefined ? 0 : cardMasteryOf(uuidOf(i))
}

function flip() {
    flipped.value = !flipped.value
}

function rate(level) {
    const real = queue.value[pos.value]
    if (real === undefined) return
    setCardMastery(uuidOf(real), level)
    quotaLeft.value = quotaRemaining(deckId.value)
    if (pos.value < queue.value.length - 1) {
        pos.value++
    } else {
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
    filter.value = f
    dueMode.value = f === 'due'
    buildQueue()
}

function goNormal() {
    resetFilter('all')
}

function toggleShuffle() {
    shuffled.value = !shuffled.value
    buildQueue()
}

/** 方剂卡：解析【组成】里的药味 chip（取书名命中的前 10 个） */
const compChips = computed(() => {
    if (deckId.value !== 'fangji' || !flipped.value || !hfReady.value) return []
    const m = String(cur.value.back || '').match(/[〔【]组成[〕】]\s*([^〔【〕】\n]+)/)
    if (!m) return []
    const seg = m[1]
    const names = Object.keys(herbName2Uuid.value).sort((a, b) => b.length - a.length)
    const out = []
    let rest = seg
    for (const nm of names) {
        if (out.length >= 10) break
        const i = rest.indexOf(nm)
        if (i >= 0) {
            out.push({ name: nm, uuid: herbName2Uuid.value[nm] })
            rest = rest.slice(i + nm.length)
        }
    }
    return out
})

/** 方剂卡：可对照的歌诀卡 */
const songChips = computed(() => {
    if (deckId.value !== 'fangji' || !flipped.value || !kfReady.value) return []
    const arr = kfSong.value.get(curUuid()) || []
    return arr.slice(0, 6)
})

/** 口诀卡：本诀涉及的方剂卡 */
const fangKChips = computed(() => {
    if (deckId.value !== 'koujue' || !flipped.value || !kfReady.value) return []
    const arr = kfFang.value.get(curUuid()) || []
    return arr.slice(0, 6)
})

function curUuid() {
    return uuidOf(queue.value[pos.value]) || ''
}

function goSongChip(c) {
    uni.navigateTo({ url: `/pages/cards/cards?deck=koujue&focus=${encodeURIComponent(c.uuid)}` })
}

function goFangKChip(c) {
    uni.navigateTo({ url: `/pages/cards/cards?deck=fangji&focus=${encodeURIComponent(c.uuid)}` })
}

/** 中药卡：含该药的方剂 chip */
const fangChips = computed(() => {
    if (deckId.value !== 'herb' || !flipped.value || !hfReady.value) return []
    return (fangByHerb.value[cur.value.front] || []).slice(0, 10)
})

function goHerbChip(c) {
    uni.navigateTo({ url: `/pages/cards/cards?deck=herb&focus=${encodeURIComponent(c.uuid)}` })
}

function goFangChip(c) {
    uni.navigateTo({ url: `/pages/cards/cards?deck=fangji&focus=${encodeURIComponent(c.uuid)}` })
}

function goSource() {
    const m = cur.value.meta
    if (!m || !m.book) return
    uni.navigateTo({ url: `/pages/reader/reader?slug=${m.book}&g=${m.g}` })
}

// ---- 手势切换 ----
function ts(e) {
    touchX.value = e.changedTouches?.[0]?.clientX ?? 0
}

function te(e) {
    const dx = (e.changedTouches?.[0]?.clientX ?? 0) - touchX.value
    if (dx < -70) next()
    else if (dx > 70) prev()
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

.due-tag {
    font-size: 22rpx;
    color: #8b3a3a;
    background: rgba(139, 58, 58, 0.1);
    padding: 8rpx 20rpx;
    border-radius: 999rpx;
}

.seg {
    display: flex;
    background: #efe8d6;
    border-radius: 14rpx;
    padding: 4rpx;
}

.seg-item {
    font-size: 22rpx;
    color: #8d8371;
    padding: 8rpx 18rpx;
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

.card-due {
    margin-top: 26rpx;
    font-size: 22rpx;
    color: #b3543f;
}

.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 12rpx;
    margin-top: 18rpx;
    align-items: center;
}

.chip-label {
    font-size: 22rpx;
    color: #e0c79a;
    opacity: 0.8;
}

.hf-chip {
    font-size: 24rpx;
    padding: 8rpx 18rpx;
    border-radius: 999rpx;
    background: rgba(224, 199, 154, 0.16);
    color: #f2e3bd;
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
    height: 440rpx;
}

.back-body {
    font-size: 27rpx;
    line-height: 1.9;
    color: #4a453b;
    white-space: pre-line;
}

.src-link {
    text-align: center;
    margin-top: 18rpx;
    padding: 16rpx 0 4rpx;
    font-size: 24rpx;
    color: #8b3a3a;
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
