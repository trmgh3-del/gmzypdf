<template>
    <!-- 脉象示意图：下方指位（寸关尺）+ 上方脉搏波形 -->
    <svg class="pulse-svg" viewBox="0 0 200 128" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <!-- 波形区网格 -->
        <line x1="8" y1="14" x2="192" y2="14" stroke="rgba(140,120,90,0.25)" stroke-dasharray="3 4" />
        <line x1="8" y1="44" x2="192" y2="44" stroke="rgba(140,120,90,0.25)" stroke-dasharray="3 4" />
        <line x1="8" y1="74" x2="192" y2="74" stroke="rgba(140,120,90,0.25)" stroke-dasharray="3 4" />
        <text x="10" y="10" class="grid-t">浅</text>
        <text x="10" y="70" class="grid-t">深</text>
        <!-- 脉搏波形 -->
        <polyline :points="wave" fill="none" :stroke="stroke" :stroke-width="width" stroke-linejoin="round" stroke-linecap="round" />
        <!-- 前臂与腕横纹 -->
        <rect x="26" y="86" width="148" height="30" rx="14" fill="#f2dfca" stroke="rgba(139,58,58,0.25)" stroke-width="1.5" />
        <line x1="150" y1="86" x2="150" y2="116" stroke="rgba(120,70,50,0.4)" stroke-width="2" />
        <!-- 三指 -->
        <g :fill="hi === i ? '#8b3a3a' : 'rgba(139,58,58,0.35)'" v-for="(fx, i) in [58, 100, 142]" :key="i">
            <circle :cx="fx" cy="101" r="9" />
        </g>
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

// 各脉象的波感参数：depth(浮沉) rate(迟数) 形(流利度) strength
const KINDS = [
    { k: '浮', depth: 20, rate: 3, jag: 0, width: 3.4, stroke: '#8b3a3a', hi: 0 },
    { k: '沉', depth: 60, rate: 3, jag: 0, width: 2.6, stroke: 'rgba(139,58,58,0.55)', hi: 2 },
    { k: '迟', depth: 44, rate: 1.6, jag: 0, width: 3, stroke: '#8b3a3a', hi: 1 },
    { k: '数', depth: 36, rate: 5.4, jag: 0, width: 2.8, stroke: '#8b3a3a', hi: 1 },
    { k: '滑', depth: 30, rate: 4, jag: 0, width: 3.2, stroke: '#4a8c5c', hi: 1 },
    { k: '涩', depth: 40, rate: 3.4, jag: 9, width: 2.4, stroke: '#7a4646', hi: 1 },
    { k: '弦', depth: 26, rate: 3.4, jag: 0, width: 4, stroke: '#8b3a3a', hi: 1 },
    { k: '细', depth: 40, rate: 3.4, jag: 0, width: 1.8, stroke: '#8b3a3a', hi: 1 },
    { k: '缓', depth: 44, rate: 2.2, jag: 0, width: 3, stroke: '#8b3a3a', hi: 1 },
    { k: '结代促', depth: 36, rate: 3.2, jag: 0, width: 3, stroke: '#8b3a3a', hi: 1, gap: true }
]

const cfg = computed(() => {
    for (const kind of KINDS) {
        if (props.term.includes(kind.k)) return kind
    }
    return KINDS[8]
})

const stroke = computed(() => cfg.value.stroke)
const width = computed(() => cfg.value.width)
const hi = computed(() => (cfg.value.hi === undefined ? 1 : cfg.value.hi))

// 生成波形点列：x=8..192，正弦带 + 迟数密度 + 涩脉锯齿 + 结代促停搏
const wave = computed(() => {
    const pts = []
    const c = cfg.value
    const y0 = 14 + c.depth * 0.5 + (c.depth >= 50 ? 46 : 22) // 浮沉：浮脉靠浅、沉脉靠深
    const base = Math.max(20, Math.min(66, y0))
    const amp = c.hi === 0 ? 14 : 10
    const n = 96
    const lambda = 184 / c.rate
    for (let i = 0; i <= n; i++) {
        const x = 8 + (184 * i) / n
        let y = base - Math.sin(((x - 8) / lambda) * Math.PI * 2) * amp
        if (c.jag) y += Math.sin(i * 3.7) * (c.jag / 3) // 涩：往来艰涩
        if (c.gap && x > 100 && x < 132) continue // 结代促：中有一止
        pts.push(`${x.toFixed(1)},${y.toFixed(1)}`)
    }
    return pts.join(' ')
})
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
