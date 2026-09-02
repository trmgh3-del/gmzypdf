<template>
    <!-- 闻诊/问诊示意图：ting=声波，xiu=气味，ask=气泡+数序 -->
    <svg class="wen-svg" :class="{ big }" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
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
        <g v-else-if="kind === 'ask'">
            <path d="M18 22 h64 a 10 10 0 0 1 10 10 v26 a 10 10 0 0 1 -10 10 H44 l -14 14 v -14 h -12 a 10 10 0 0 1 -10 -10 V32 a 10 10 0 0 1 10 -10 Z"
                fill="#fffdf7" stroke="#b5935a" stroke-width="3" />
            <text x="50" y="60" class="num-serif">{{ num || '问' }}</text>
        </g>
        <!-- 按诊：手 -->
        <g v-else>
            <!-- 胸腹（虚里/脘腹/胁） -->
            <g v-if="kind === 'an-belly'">
                <ellipse cx="50" cy="72" rx="34" ry="22" fill="#f3dcc6" stroke="rgba(139,58,58,0.35)" stroke-width="2" />
                <path d="M30 46 q 20 -14 40 0" stroke="rgba(139,58,58,0.5)" stroke-width="3" fill="none" stroke-linecap="round" />
                <path d="M36 38 q 14 -10 28 0" stroke="rgba(139,58,58,0.35)" stroke-width="3" fill="none" stroke-linecap="round" />
                <path d="M42 30 q 8 -6 16 0" stroke="rgba(139,58,58,0.2)" stroke-width="3" fill="none" stroke-linecap="round" />
            </g>
            <!-- 肌肤/尺肤/手足 -->
            <g v-else-if="kind === 'an-skin'">
                <path d="M18 70 q 12 -14 22 -6 q 10 8 20 0 q 10 -8 20 6" stroke="#8b3a3a" stroke-width="4" fill="none" stroke-linecap="round" />
                <path d="M28 56 q 6 6 6 10" stroke="rgba(139,58,58,0.45)" stroke-width="3" fill="none" stroke-linecap="round" />
                <path d="M58 52 q 6 8 4 12" stroke="rgba(139,58,58,0.45)" stroke-width="3" fill="none" stroke-linecap="round" />
                <path d="M78 56 q -5 7 -3 11" stroke="rgba(139,58,58,0.45)" stroke-width="3" fill="none" stroke-linecap="round" />
            </g>
            <!-- 俞穴/囟门 -->
            <g v-else-if="kind === 'an-acu'">
                <circle cx="50" cy="62" r="8" fill="#fffdf7" stroke="#8b3a3a" stroke-width="3" />
                <circle cx="50" cy="62" r="2.6" fill="#8b3a3a" />
                <circle cx="50" cy="62" r="16" stroke="rgba(139,58,58,0.5)" stroke-width="2" fill="none" stroke-dasharray="3 4" />
                <circle cx="50" cy="62" r="26" stroke="rgba(139,58,58,0.25)" stroke-width="2" fill="none" stroke-dasharray="3 5" />
                <path d="M46 26 h10 v18 q -5 5 -10 0 Z" fill="#8b3a3a" />
            </g>
        </g>
    </svg>
</template>

<script setup>
defineProps({
    kind: { type: String, default: 'ask' },
    num: { type: String, default: '' },
    big: { type: Boolean, default: false }
})
</script>

<style scoped>
.wen-svg {
    width: 96rpx;
    height: 96rpx;
    flex-shrink: 0;
}

.wen-svg.big {
    width: 220rpx;
    height: 220rpx;
}

.num-serif {
    font-size: 30px;
    fill: #8b3a3a;
    font-weight: 700;
    text-anchor: middle;
    font-family: serif;
}
</style>
