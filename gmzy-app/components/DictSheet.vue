<template>
    <view v-if="show" class="dict-mask" @tap="close">
        <view class="dict-sheet" @tap.stop>
            <view class="dict-head">
                <text class="dict-title serif-font">原文查词</text>
                <text class="dict-close" @tap="close">✕</text>
            </view>
            <scroll-view scroll-y class="dict-body">
                <text v-if="snippet" class="dict-snippet">{{ snippet }}</text>

                <view v-if="!terms.length" class="dict-empty">本段未命中卡片词条</view>
                <view v-else class="dict-chips">
                    <text
                        v-for="(t, i) in terms"
                        :key="t.term"
                        class="dict-chip"
                        :class="['dk-' + t.deck, { on: selIdx === i }]"
                        @tap="selIdx = i"
                    >{{ t.term }}</text>
                </view>

                <view v-if="cur" class="dict-card">
                    <view class="dc-top">
                        <text class="dc-term serif-font">{{ cur.front !== cur.term ? cur.front : cur.term }}</text>
                        <text class="dc-deck">{{ cur.deckName }} · {{ cur.sub }}</text>
                    </view>
                    <scroll-view scroll-y class="dc-scroll">
                        <text class="dc-back">{{ cur.back }}</text>
                    </scroll-view>
                    <view class="dc-actions">
                        <button class="dc-btn ghost" @tap="goCard">去背卡</button>
                        <button v-if="cur.book" class="dc-btn primary" @tap="goSource">查看原文 ›</button>
                    </view>
                </view>
            </scroll-view>
        </view>
    </view>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
    show: { type: Boolean, default: false },
    terms: { type: Array, default: () => [] },
    snippet: { type: String, default: '' }
})
const emit = defineEmits(['close'])

const selIdx = ref(0)
watch(
    () => props.terms,
    () => {
        selIdx.value = 0
    }
)

const cur = computed(() => props.terms[selIdx.value] || null)

function close() {
    emit('close')
}

function goCard() {
    if (!cur.value) return
    let url = '/pages/cards/cards?deck=' + cur.value.deck
    if (cur.value.uuid) url += '&focus=' + encodeURIComponent(cur.value.uuid)
    uni.navigateTo({ url })
}

function goSource() {
    const c = cur.value
    if (!c || !c.book || c.g === null || c.g === undefined) return
    uni.navigateTo({ url: `/pages/reader/reader?slug=${c.book}&g=${c.g}` })
}
</script>

<style scoped>
.dict-mask {
    position: fixed;
    inset: 0;
    background: rgba(20, 14, 8, 0.55);
    display: flex;
    align-items: flex-end;
    z-index: 90;
}

.dict-sheet {
    width: 100%;
    max-height: 78vh;
    background: #fffdf7;
    border-radius: 26rpx 26rpx 0 0;
    padding: 26rpx 26rpx calc(24rpx + env(safe-area-inset-bottom));
}

.dict-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14rpx;
}

.dict-title {
    font-size: 30rpx;
    font-weight: 700;
    color: #37332b;
}

.dict-close {
    font-size: 30rpx;
    color: #8d8371;
    padding: 8rpx 16rpx;
}

.dict-body {
    max-height: 64vh;
}

.dict-snippet {
    display: block;
    font-size: 22rpx;
    color: #8d8371;
    background: #f6f1e5;
    border-radius: 12rpx;
    padding: 14rpx 18rpx;
    margin-bottom: 18rpx;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}

.dict-empty {
    text-align: center;
    color: #8d8371;
    font-size: 24rpx;
    padding: 50rpx 0;
}

.dict-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 14rpx;
    margin-bottom: 20rpx;
}

.dict-chip {
    font-size: 24rpx;
    border-radius: 999rpx;
    padding: 10rpx 24rpx;
    background: #f6f1e5;
    border: 1rpx solid #e4dcc8;
    color: #6b6455;

    &.on {
        color: #fffdf7;
    }

    &.dk-fangji.on { background: #8b3a3a; border-color: #8b3a3a; }
    &.dk-herb.on { background: #4a6b3a; border-color: #4a6b3a; }
    &.dk-point.on { background: #35588b; border-color: #35588b; }
    &.dk-koujue.on { background: #8b6f35; border-color: #8b6f35; }
}

.dict-card {
    border: 1rpx solid #e4dcc8;
    border-radius: 18rpx;
    padding: 22rpx;
    background: #fefaf0;
}

.dc-top {
    display: flex;
    align-items: baseline;
    gap: 18rpx;
    margin-bottom: 14rpx;
    flex-wrap: wrap;
}

.dc-term {
    font-size: 36rpx;
    font-weight: 700;
    color: #37332b;
}

.dc-deck {
    font-size: 21rpx;
    color: #8d8371;
}

.dc-scroll {
    max-height: 300rpx;
}

.dc-back {
    font-size: 25rpx;
    line-height: 1.85;
    color: #4a453b;
    white-space: pre-line;
}

.dc-actions {
    display: flex;
    gap: 18rpx;
    margin-top: 20rpx;
}

.dc-btn {
    flex: 1;
    height: 72rpx;
    line-height: 72rpx;
    border-radius: 14rpx;
    font-size: 26rpx;
    border: none;

    &::after {
        border: none;
    }
}

.dc-btn.ghost {
    background: transparent;
    border: 1rpx solid #c9bda2;
    color: #8d8371;
}

.dc-btn.primary {
    background: linear-gradient(135deg, #8b3a3a, #5c2018);
    color: #f3e9d2;
}
</style>
