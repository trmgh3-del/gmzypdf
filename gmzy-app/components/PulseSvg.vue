<template>
    <!-- 脉象示意图：下方指位（寸关尺）+ 上方脉搏波形（浮沉深浅/迟数密度/形流利度/结代促节律） -->
    <svg class="pulse-svg" viewBox="0 0 200 128" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <!-- 波形区网格：上浅下深 -->
        <line x1="8" y1="14" x2="192" y2="14" stroke="rgba(140,120,90,0.25)" stroke-dasharray="3 4" />
        <line x1="8" y1="44" x2="192" y2="44" stroke="rgba(140,120,90,0.25)" stroke-dasharray="3 4" />
        <line x1="8" y1="74" x2="192" y2="74" stroke="rgba(140,120,90,0.25)" stroke-dasharray="3 4" />
        <text x="10" y="10" class="grid-t">浅</text>
        <text x="10" y="70" class="grid-t">深</text>
        <!-- 芤/革之「中空」影波 -->
        <polyline v-if="cfg.hollow" :points="waveH" fill="none" :stroke="stroke" :stroke-width="width * 0.7"
            stroke-opacity="0.5" stroke-linejoin="round" stroke-linecap="round" />
        <!-- 脉搏波形 -->
        <polyline :points="wave" fill="none" :stroke="stroke" :stroke-width="width"
            :stroke-opacity="cfg.dim || 1" stroke-linejoin="round" stroke-linecap="round" />
        <!-- 前臂与腕横纹 -->
        <rect x="26" y="86" width="148" height="30" rx="14" fill="#f2dfca" stroke="rgba(139,58,58,0.25)" stroke-width="1.5" />
        <line x1="150" y1="86" x2="150" y2="116" stroke="rgba(120,70,50,0.4)" stroke-width="2" />
        <!-- 三指：寸 关 尺 -->
        <circle v-for="(fx, i) in [58, 100, 142]" :key="i" :cx="fx" cy="101" r="9"
            :fill="hi === i ? '#8b3a3a' : 'rgba(139,58,58,0.35)'" />
        <text x="54" y="126" class="fp" v-if="hi === 0">寸</text>
        <text x="96" y="126" class="fp" v-if="hi === 1">关</text>
        <text x="138" y="126" class="fp" v-if="hi === 2">尺</text>
    </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    term: { type: String, default: '' }
})

// depth=浮沉(0最浅 60最深) rate=迟数 amp=振幅 width=粗细 jag=艰涩抖动 gap=停搏窗口
const KINDS = [
    { k: '浮', depth: 6, rate: 3, amp: 13, width: 3.4, stroke: '#8b3a3a', hi: 0 },
    { k: '沉', depth: 46, rate: 3, amp: 11, width: 2.8, stroke: '#8b3a3a', hi: 2 },
    { k: '伏', depth: 58, rate: 2.6, amp: 9, width: 2.2, stroke: '#8b3a3a', dim: 0.55, hi: 2 },
    { k: '芤', depth: 6, rate: 3, amp: 12, width: 2.6, stroke: '#8b3a3a', hollow: true, hi: 0 },
    { k: '迟', depth: 30, rate: 1.6, amp: 10, width: 3, stroke: '#8b3a3a', hi: 1 },
    { k: '数', depth: 22, rate: 5.4, amp: 9, width: 2.8, stroke: '#8b3a3a', hi: 1 },
    { k: '疾', depth: 20, rate: 6.6, amp: 9, width: 2.6, stroke: '#8b3a3a', hi: 1 },
    { k: '缓', depth: 32, rate: 2.2, amp: 10, width: 3, stroke: '#8b3a3a', hi: 1 },
    { k: '滑', depth: 16, rate: 4, amp: 11, width: 3.2, stroke: '#4a8c5c', hi: 1 },
    { k: '涩', depth: 28, rate: 3.4, amp: 10, width: 2.4, jag: 9, stroke: '#7a4646', hi: 1 },
    { k: '弦', depth: 12, rate: 3.4, amp: 12, width: 4, stroke: '#8b3a3a', hi: 1 },
    { k: '细', depth: 28, rate: 3.4, amp: 10, width: 1.8, stroke: '#8b3a3a', hi: 1 },
    { k: '洪', depth: 12, rate: 3, amp: 16, width: 4, stroke: '#8b3a3a', hi: 1 },
    { k: '微', depth: 30, rate: 3.2, amp: 7, width: 1.5, dim: 0.5, stroke: '#8b3a3a', hi: 1 },
    { k: '散', depth: 8, rate: 2.8, amp: 12, width: 3, jag: 5, dim: 0.55, stroke: '#8b3a3a', hi: 0 },
    { k: '虚', depth: 30, rate: 3, amp: 6, width: 2.4, dim: 0.6, stroke: '#8b3a3a', hi: 1 },
    { k: '实', depth: 20, rate: 3.2, amp: 13, width: 4, stroke: '#8b3a3a', hi: 1 },
    { k: '促', depth: 22, rate: 5, amp: 9, width: 3, stroke: '#8b3a3a', gap: [96, 124], hi: 1 },
    { k: '结', depth: 32, rate: 2.2, amp: 10, width: 3, stroke: '#8b3a3a', gap: [100, 116], hi: 1 },
    { k: '代', depth: 28, rate: 3, amp: 10, width: 3, stroke: '#8b3a3a', gap: [96, 132], hi: 1 }
]

const cfg = computed(() => {
    for (const kind of KINDS) {
        if (props.term.includes(kind.k)) return kind
    }
    return KINDS.find((x) => x.k === '缓')
})

const stroke = computed(() => cfg.value.stroke)
const width = computed(() => cfg.value.width)
const hi = computed(() => cfg.value.hi)

function genWave(shiftY) {
    const pts = []
    const c = cfg.value
    const base = Math.max(20, Math.min(68, 16 + c.depth * 0.9 + 6))
    const n = 96
    const lambda = 184 / c.rate
    for (let i = 0; i <= n; i++) {
        const x = 8 + (184 * i) / n
        let y = base + (shiftY || 0) - Math.sin(((x - 8) / lambda) * Math.PI * 2) * c.amp
        if (c.jag) y += Math.sin(i * 3.7) * (c.jag / 3) // 涩/散：往来艰涩
        if (c.gap && x > c.gap[0] && x < c.gap[1]) continue // 结代促：中有一止
        pts.push(`${x.toFixed(1)},${y.toFixed(1)}`)
    }
    return pts.join(' ')
}

const wave = computed(() => genWave(0))
const waveH = computed(() => genWave(4))
</script>

<style scoped>
.pulse-svg {
    width: 200rpx;
    height: 128rpx;
    flex-shrink: 0;
}

.grid-t {
    font-size: 14px;
    fill: rgba(141, 131, 113, 0.7);
}

.fp {
    font-size: 15px;
    fill: #5c2018;
    font-weight: 700;
}
</style>
