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
                        <button class="dc-btn ghost" @tap="exportCard">存图</button>
                    </view>
                </view>
            </scroll-view>
            <canvas canvas-id="dictCardCanvas" class="dict-hide-canvas" />
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

// ---- 词条卡导出图片（宣纸风 600x860 canvas） ----
function wrapText(ctx, text, x, y, maxW, lh, maxLines = 30) {
    let line = ''
    let lines = 0
    for (const ch of String(text)) {
        if (ch === '\n' || ctx.measureText(line + ch).width > maxW) {
            ctx.fillText(line, x, y)
            y += lh
            lines++
            if (lines >= maxLines) {
                ctx.fillText('…', x, y)
                return y + lh
            }
            line = ch === '\n' ? '' : ch
        } else {
            line += ch
        }
    }
    if (line) {
        ctx.fillText(line, x, y)
        y += lh
    }
    return y
}

function exportCard() {
    if (!cur.value) return
    const t = cur.value
    const W = 600
    const H = 860
    const ctx = uni.createCanvasContext('dictCardCanvas', this)
    // 底
    ctx.setFillStyle('#f7f0dd')
    ctx.fillRect(0, 0, W, H)
    // 框线
    ctx.setStrokeStyle('#c9b889')
    ctx.setLineWidth(4)
    ctx.strokeRect(18, 18, W - 36, H - 36)
    ctx.setStrokeStyle('#e0d3ab')
    ctx.setLineWidth(1)
    ctx.strokeRect(30, 30, W - 60, H - 60)
    // 卡包徽标
    ctx.setFillStyle('#8b3a3a')
    ctx.fillRect(48, 48, 64, 64)
    ctx.setFillStyle('#f3e9d2')
    ctx.setFontSize(34)
    const DK = { fangji: '方', herb: '药', point: '穴', koujue: '诀', bingz: '证', yian: '案' }
    ctx.fillText(DK[t.deck] || '卡', 66, 92)
    // 词名
    ctx.setFillStyle('#3a2e1e')
    ctx.setFontSize(44)
    ctx.fillText(t.front || t.term, 132, 92)
    ctx.setFillStyle('#a0916e')
    ctx.setFontSize(22)
    ctx.fillText((t.deckName || '') + (t.sub ? ' · ' + t.sub : ''), 48, 158)
    // 分隔
    ctx.setStrokeStyle('#e0d3ab')
    ctx.setLineWidth(1)
    ctx.beginPath()
    ctx.moveTo(48, 184)
    ctx.lineTo(W - 48, 184)
    ctx.stroke()
    // 正文
    ctx.setFillStyle('#4a4032')
    ctx.setFontSize(26)
    wrapText(ctx, t.back || '', 48, 232, W - 96, 44, 11)
    // 落款
    ctx.setFillStyle('#a0916e')
    ctx.setFontSize(20)
    ctx.fillText('光明中医文库 · 原文查词', 48, H - 70)
    const date = new Date().toISOString().slice(0, 10)
    ctx.fillText(date, W - 148, H - 70)

    ctx.draw(false, () => {
        setTimeout(() => {
            uni.canvasToTempFilePath({
                canvasId: 'dictCardCanvas',
                success: (r) => {
                    // #ifdef APP-PLUS
                    uni.saveImageToPhotosAlbum({
                        filePath: r.tempFilePath,
                        success: () => uni.showToast({ title: '已存入相册', icon: 'none' }),
                        fail: () => uni.showToast({ title: '保存失败', icon: 'none' })
                    })
                    // #endif
                    // #ifdef H5
                    const a = document.createElement('a')
                    a.href = r.tempFilePath
                    a.download = `${(t.front || t.term)}-词条卡.png`
                    a.click()
                    // #endif
                    // #ifdef MP
                    uni.saveImageToPhotosAlbum({ filePath: r.tempFilePath })
                    // #endif
                },
                fail: () => uni.showToast({ title: '导出失败', icon: 'none' })
            })
        }, 380)
    })
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

.dict-hide-canvas {
    position: fixed;
    left: -2000rpx;
    top: -2000rpx;
    width: 600px;
    height: 860px;
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
