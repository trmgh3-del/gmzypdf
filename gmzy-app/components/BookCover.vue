<template>
    <view class="cover" :style="{ width: width + 'rpx' }">
        <image
            v-if="cover && !loadError"
            class="cover-img"
            :src="'/' + cover"
            mode="aspectFill"
            :lazy-load="true"
            @error="loadError = true"
        />
        <view v-else class="cover-fallback serif-font">
            <text class="fb-title">{{ shortTitle }}</text>
            <text class="fb-sub">光明中医文库</text>
        </view>
        <view class="cover-gloss" />
    </view>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
    title: { type: String, default: '' },
    cover: { type: String, default: '' },
    width: { type: Number, default: 210 }
})

const loadError = ref(false)
const shortTitle = computed(() => {
    return props.title.replace(/[《》]/g, '').slice(0, 8)
})
</script>

<style lang="scss" scoped>
.cover {
    position: relative;
    aspect-ratio: 3 / 4;
    border-radius: 12rpx;
    overflow: hidden;
    box-shadow: 0 6rpx 18rpx rgba(60, 40, 20, 0.18);
    background: linear-gradient(150deg, #78423a 0%, #5c2018 70%, #451611 100%);
}

.cover-img {
    width: 100%;
    height: 100%;
    display: block;
}

.cover-fallback {
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    bottom: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 18rpx;
}

.fb-title {
    color: #f3e9d2;
    font-size: 30rpx;
    font-weight: 700;
    letter-spacing: 4rpx;
    text-align: center;
    line-height: 1.5;
}

.fb-sub {
    margin-top: 16rpx;
    color: rgba(243, 233, 210, 0.55);
    font-size: 18rpx;
    letter-spacing: 6rpx;
}

.cover-gloss {
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    bottom: 0;
    background: linear-gradient(112deg, rgba(255, 255, 255, 0.14) 0%, rgba(255, 255, 255, 0) 30%);
    pointer-events: none;
}
</style>
