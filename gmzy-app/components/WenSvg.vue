<template>
    <!-- 闻诊/问诊示意图：ting=声波，xiu=气味，ask=气泡+数序 -->
    <svg class="wen-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <!-- 听声音 -->
        <g v-if="kind === 'ting'">
            <path d="M28 42 v16 h14 l18 14 V28 L42 42 Z" fill="#8b3a3a" />
            <path d="M68 36 q 10 14 0 28" stroke="#8b3a3a" stroke-width="4" fill="none" stroke-linecap="round" />
            <path d="M78 28 q 16 22 0 44" stroke="rgba(139,58,58,0.6)" stroke-width="4" fill="none" stroke-linecap="round" />
        </g>
        <!-- 嗅气味 -->
        <g v-else-if="kind === 'xiu'">
            <!-- 碗/盏 -->
            <path d="M28 62 h44 a 22 22 0 0 1 -44 0 Z" fill="#8b3a3a" />
            <rect x="24" y="58" width="52" height="5" rx="2" fill="#6e2626" />
            <!-- 上升香气 -->
            <path d="M38 46 q -5 -8 0 -14 q 5 -6 0 -14" stroke="rgba(139,58,58,0.65)" stroke-width="3.4" fill="none" stroke-linecap="round" />
            <path d="M52 48 q -5 -8 0 -14 q 5 -6 0 -14" stroke="rgba(139,58,58,0.85)" stroke-width="3.4" fill="none" stroke-linecap="round" />
            <path d="M66 46 q -5 -8 0 -14 q 5 -6 0 -14" stroke="rgba(139,58,58,0.65)" stroke-width="3.4" fill="none" stroke-linecap="round" />
        </g>
        <!-- 问诊：气泡+数序 -->
        <g v-else>
            <path d="M18 22 h64 a 10 10 0 0 1 10 10 v26 a 10 10 0 0 1 -10 10 H44 l -14 14 v -14 h -12 a 10 10 0 0 1 -10 -10 V32 a 10 10 0 0 1 10 -10 Z"
                fill="#fffdf7" stroke="#b5935a" stroke-width="3" />
            <text x="50" y="60" class="num-serif">{{ num || '问' }}</text>
        </g>
    </svg>
</template>

<script setup>
defineProps({
    kind: { type: String, default: 'ask' },
    num: { type: String, default: '' }
})
</script>

<style scoped>
.wen-svg {
    width: 96rpx;
    height: 96rpx;
    flex-shrink: 0;
}

.num-serif {
    font-size: 30px;
    fill: #8b3a3a;
    font-weight: 700;
    text-anchor: middle;
    font-family: serif;
}
</style>
