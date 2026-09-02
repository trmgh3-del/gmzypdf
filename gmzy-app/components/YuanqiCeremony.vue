<template>
    <!-- 段位晋升 · 金榜题名仪式（父组件传 info: {from,to,energy}，可控自动关闭/点屏关闭） -->
    <view v-if="info" class="promote-mask" @tap="$emit('close')">
        <view class="promote-card" @tap.stop>
            <view class="pr-lantern"><text class="pr-lt">灯</text></view>
            <view class="pr-lantern r"><text class="pr-lt">笼</text></view>
            <text class="pr-title serif-font">金榜题名</text>
            <view class="pr-from-row">
                <text class="pr-old serif-font">{{ info.from }}</text>
                <text class="pr-arrow">→</text>
                <text class="pr-old serif-font">{{ info.to }}</text>
            </view>
            <view class="pr-ring"></view>
            <text class="pr-name serif-font">{{ info.to }}</text>
            <text class="pr-line">元气盈府 · 已达 {{ info.energy }}</text>
            <text class="pr-hint">点屏敛榜归座</text>
        </view>
    </view>
</template>

<script setup>
defineProps({ info: { type: Object, default: null } })
defineEmits(['close'])
</script>

<style scoped>
.promote-mask {
    position: fixed;
    inset: 0;
    background: rgba(24, 14, 8, 0.62);
    z-index: 1200;
    display: flex;
    align-items: center;
    justify-content: center;
}

.promote-card {
    position: relative;
    width: 84%;
    max-width: 620rpx;
    background: linear-gradient(160deg, #f9ecc5, #f2d99a);
    border: 3rpx solid #8b3a3a;
    border-radius: 20rpx;
    padding: 60rpx 40rpx 44rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
    box-shadow: 0 18rpx 60rpx rgba(139, 58, 58, 0.4);
    animation: promotePop 0.5s cubic-bezier(0.2, 1.4, 0.4, 1);
}

@keyframes promotePop {
    0% {
        transform: scale(0.55);
        opacity: 0;
    }
    100% {
        transform: scale(1);
        opacity: 1;
    }
}

.pr-lantern {
    position: absolute;
    top: -34rpx;
    left: 26rpx;
    width: 64rpx;
    height: 64rpx;
    background: radial-gradient(circle, #c23232, #8b1e1e);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4rpx 14rpx rgba(194, 50, 50, 0.55);
}

.pr-lantern.r {
    left: auto;
    right: 26rpx;
}

.pr-lt {
    color: #ffe9c0;
    font-size: 26rpx;
    font-family: serif;
}

.pr-title {
    font-size: 44rpx;
    font-weight: 700;
    color: #8b1e1e;
    letter-spacing: 10rpx;
    margin-bottom: 18rpx;
}

.pr-from-row {
    display: flex;
    align-items: baseline;
    gap: 16rpx;
    margin-bottom: 16rpx;
}

.pr-old {
    font-size: 26rpx;
    color: #6e4a2a;
}

.pr-arrow {
    font-size: 30rpx;
    color: #b5242a;
    font-weight: 700;
}

.pr-ring {
    width: 100%;
    height: 2rpx;
    background: linear-gradient(90deg, transparent, #8b3a3a, transparent);
    margin: 6rpx 0 20rpx;
}

.pr-name {
    font-size: 56rpx;
    font-weight: 700;
    color: #5c2018;
    letter-spacing: 8rpx;
    text-shadow: 0 2rpx 0 #fff3d0;
    margin-bottom: 12rpx;
}

.pr-line {
    font-size: 24rpx;
    color: #7a5a30;
    margin-bottom: 6rpx;
}

.pr-hint {
    font-size: 20rpx;
    color: #a8916a;
    margin-top: 12rpx;
}
</style>
