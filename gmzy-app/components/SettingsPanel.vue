<template>
    <view>
        <view class="mask" v-show="show" @tap="close" />
        <view class="panel" :class="{ 'panel-show': show }">
            <view class="panel-title">阅读设置</view>

            <view class="row">
                <text class="label">字号</text>
                <view class="font-ctl">
                    <view class="font-btn" @tap="setFont(settings.fontSize - 1)">A−</view>
                    <text class="font-num">{{ settings.fontSize }}</text>
                    <view class="font-btn font-btn-big" @tap="setFont(settings.fontSize + 1)">A＋</view>
                </view>
            </view>

            <view class="row">
                <text class="label">行距</text>
                <view class="seg">
                    <view
                        v-for="opt in lineHeights"
                        :key="opt.v"
                        class="seg-item"
                        :class="{ on: settings.lineHeight === opt.v }"
                        @tap="settings.lineHeight = opt.v"
                    >{{ opt.n }}</view>
                </view>
            </view>

            <view class="row">
                <text class="label">字体</text>
                <view class="seg">
                    <view
                        class="seg-item serif-font"
                        :class="{ on: settings.serif }"
                        @tap="settings.serif = true"
                    >宋体</view>
                    <view
                        class="seg-item"
                        :class="{ on: !settings.serif }"
                        @tap="settings.serif = false"
                    >黑体</view>
                </view>
            </view>

            <view class="row">
                <text class="label">主题</text>
                <view class="themes">
                    <view
                        v-for="t in themes"
                        :key="t.key"
                        class="theme-card"
                        :class="{ on: settings.theme === t.key }"
                        :style="{ background: t.bg, color: t.fg, borderColor: settings.theme === t.key ? '#8b3a3a' : t.line }"
                        @tap="settings.theme = t.key"
                    >
                        <text class="theme-name" :style="{ color: t.fg }">{{ t.name }}</text>
                    </view>
                </view>
            </view>
        </view>
    </view>
</template>

<script setup>
import { reactive } from 'vue'
import { store } from '../common/store.js'

const props = defineProps({
    show: { type: Boolean, default: false }
})
const emit = defineEmits(['update:show'])

const settings = store.settings

const lineHeights = [
    { n: '紧凑', v: 1.6 },
    { n: '适中', v: 1.8 },
    { n: '宽松', v: 2.05 }
]

const themes = [
    { key: 'paper', name: '宣纸', bg: '#f6f1e5', fg: '#37332b', line: '#e4dcc8' },
    { key: 'eye', name: '护眼', bg: '#d3e4cd', fg: '#2e3a2c', line: '#bfd8b8' },
    { key: 'night', name: '夜读', bg: '#17191d', fg: '#b9bec7', line: '#2a2e35' }
]

function setFont(v) {
    settings.fontSize = Math.min(28, Math.max(14, Math.round(v)))
}

function close() {
    emit('update:show', false)
}
</script>

<style lang="scss" scoped>
.mask {
    position: fixed;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    z-index: 92;
    background: rgba(20, 12, 8, 0.35);
}

.panel {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 93;
    background: var(--bg, #fbf7ec);
    border-radius: 24rpx 24rpx 0 0;
    padding: 30rpx 36rpx calc(36rpx + env(safe-area-inset-bottom));
    transform: translateY(102%);
    transition: transform 0.25s ease-out;
    box-shadow: 0 -6rpx 30rpx rgba(0, 0, 0, 0.18);
}

.panel-show {
    transform: translateY(0);
}

.panel-title {
    font-size: 30rpx;
    font-weight: 700;
    color: var(--fg, #37332b);
    margin-bottom: 24rpx;
    text-align: center;
}

.row {
    display: flex;
    align-items: center;
    margin: 26rpx 0;
}

.label {
    width: 96rpx;
    font-size: 26rpx;
    color: var(--muted, #8d8371);
}

.font-ctl {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: space-around;
}

.font-btn {
    width: 180rpx;
    height: 64rpx;
    line-height: 64rpx;
    text-align: center;
    border: 1rpx solid var(--line, #e4dcc8);
    border-radius: 32rpx;
    color: var(--fg, #37332b);
    font-size: 30rpx;
    background: var(--card, #fffdf7);
}

.font-num {
    font-size: 28rpx;
    color: var(--fg, #37332b);
}

.seg {
    flex: 1;
    display: flex;
    border: 1rpx solid var(--line, #e4dcc8);
    border-radius: 32rpx;
    overflow: hidden;
    background: var(--card, #fffdf7);
}

.seg-item {
    flex: 1;
    height: 62rpx;
    line-height: 62rpx;
    text-align: center;
    font-size: 26rpx;
    color: var(--fg, #37332b);
}

.seg-item.on {
    background: var(--accent, #8b3a3a);
    color: #fff8ec;
}

.themes {
    flex: 1;
    display: flex;
    justify-content: space-between;
}

.theme-card {
    width: 31%;
    height: 84rpx;
    border-radius: 12rpx;
    border: 3rpx solid transparent;
    display: flex;
    align-items: center;
    justify-content: center;
}

.theme-card.on {
    border-width: 3rpx;
}

.theme-name {
    font-size: 26rpx;
}
</style>
