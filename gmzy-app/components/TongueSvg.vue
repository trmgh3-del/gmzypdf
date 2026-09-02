<template>
    <!-- 舌象示意图（风格化 SVG，离线无资源）：舌色/舌形/舌态/苔色/苔质 -->
    <svg class="tongue-svg" :viewBox="'0 0 120 ' + vbh" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <g :transform="cfg.tilt ? `rotate(${cfg.tilt} 60 40)` : ''">
            <!-- 舌体 -->
            <path :d="bodyPath" :fill="cfg.body" />
            <!-- 齿痕：边缘凹口（用卡面色覆盖出缺口） -->
            <g v-if="cfg.teeth" fill="var(--card, #fffdf7)">
                <circle v-for="(c, i) in teethL" :key="'l' + i" :cx="c[0]" :cy="c[1]" r="8" />
                <circle v-for="(c, i) in teethR" :key="'r' + i" :cx="c[0]" :cy="c[1]" r="8" />
            </g>
            <!-- 舌苔：剥苔=斑块，腐苔=颗粒，其余=整片 -->
            <template v-if="cfg.coat === 'peel'">
                <circle cx="44" cy="62" r="15" fill="rgba(244,238,222,0.9)" />
                <circle cx="73" cy="94" r="17" fill="rgba(244,238,222,0.9)" />
                <circle cx="52" cy="114" r="11" fill="rgba(244,238,222,0.9)" />
            </template>
            <g v-else-if="cfg.coat === 'bean'" fill="rgba(244,238,222,0.92)">
                <circle cx="46" cy="54" r="6" />
                <circle cx="66" cy="60" r="7" />
                <circle cx="52" cy="80" r="6.4" />
                <circle cx="72" cy="84" r="7" />
                <circle cx="56" cy="106" r="6" />
                <circle cx="70" cy="110" r="5.4" />
            </g>
            <path v-else-if="cfg.coat" :d="coatPath" :fill="cfg.coat" />
            <!-- 裂纹 -->
            <g v-if="cfg.crack" stroke="rgba(120,40,44,0.85)" stroke-width="2.2" fill="none" stroke-linecap="round">
                <path d="M60 46 L58 66 L63 84 L59 104" />
                <path d="M52 58 L58 66" />
                <path d="M63 84 L70 92" />
            </g>
            <!-- 瘀斑（暗色点） -->
            <g v-if="cfg.spots" :fill="cfg.spots">
                <circle cx="46" cy="70" r="4" />
                <circle cx="68" cy="60" r="3.4" />
                <circle cx="62" cy="100" r="4.4" />
                <circle cx="52" cy="88" r="2.6" />
            </g>
            <!-- 点刺（红刺凸起） -->
            <g v-if="cfg.prick" :fill="'#b3242e'">
                <circle cx="58" cy="34" r="3.6" />
                <circle cx="50" cy="48" r="4.4" />
                <circle cx="70" cy="46" r="3.8" />
                <circle cx="58" cy="62" r="5" />
                <circle cx="72" cy="72" r="4.2" />
                <circle cx="44" cy="72" r="3.8" />
            </g>
            <!-- 镜面高光 -->
            <ellipse v-if="cfg.gloss" cx="46" cy="58" rx="14" ry="22" fill="rgba(255,255,255,0.42)" transform="rotate(-22 46 58)" />
            <!-- 强硬中线 -->
            <path v-if="cfg.rigid" d="M60 30 L60 126" stroke="rgba(110,44,40,0.5)" stroke-width="3" stroke-linecap="round" />
        </g>
        <!-- 颤动示意（抖动残影弧线） -->
        <g v-if="cfg.wiggle" stroke="rgba(139,58,58,0.55)" stroke-width="2.4" fill="none" stroke-linecap="round">
            <path d="M14 64 q -6 10 0 20" />
            <path d="M106 64 q 6 10 0 20" />
            <path d="M20 40 q -5 8 0 16" />
            <path d="M100 40 q 5 8 0 16" />
        </g>
        <!-- 舌边轮廓 -->
        <path :d="bodyPath" fill="none" :stroke="cfg.edge" :stroke-width="cfg.old ? 3.2 : 2" :transform="cfg.tilt ? `rotate(${cfg.tilt} 60 40)` : ''" />
    </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    term: { type: String, default: '' }
})

// 舌体变体
const V = {
    std: {
        body: 'M60 18 C 88 18 100 54 98 86 C 96 116 82 138 60 138 C 38 138 24 116 22 86 C 20 54 32 18 60 18 Z',
        coat: 'M60 34 C 78 34 88 60 86 84 C 84 106 74 124 60 124 C 46 124 36 106 34 84 C 32 60 42 34 60 34 Z',
        h: 150
    },
    fat: {
        body: 'M60 14 C 94 14 108 52 106 86 C 104 120 86 142 60 142 C 34 142 16 120 14 86 C 12 52 26 14 60 14 Z',
        coat: 'M60 30 C 82 30 92 58 90 84 C 88 110 76 128 60 128 C 44 128 32 110 30 84 C 28 58 38 30 60 30 Z',
        h: 152
    },
    slim: {
        body: 'M60 20 C 80 20 90 56 88 88 C 86 116 74 136 60 136 C 46 136 34 116 32 88 C 30 56 40 20 60 20 Z',
        coat: 'M60 36 C 74 36 82 62 80 86 C 78 106 70 122 60 122 C 50 122 42 106 40 86 C 38 62 46 36 60 36 Z',
        h: 148
    },
    droop: {
        body: 'M60 16 C 94 16 108 58 106 96 C 104 130 88 162 60 162 C 32 162 16 130 14 96 C 12 58 26 16 60 16 Z',
        coat: 'M60 32 C 80 32 92 64 90 94 C 88 124 76 146 60 146 C 44 146 32 124 30 94 C 28 64 40 32 60 32 Z',
        h: 168
    },
    short: {
        body: 'M60 34 C 86 34 98 62 96 84 C 94 106 80 118 60 118 C 40 118 26 106 24 84 C 22 62 34 34 60 34 Z',
        coat: 'M60 48 C 76 48 86 68 84 84 C 82 100 72 108 60 108 C 48 108 38 100 36 84 C 34 68 44 48 60 48 Z',
        h: 130
    },
    rigid: {
        body: 'M60 14 C 88 14 100 50 102 84 C 104 118 86 142 60 142 C 34 142 16 118 18 84 C 20 50 32 14 60 14 Z',
        coat: 'M60 32 C 82 32 92 60 90 84 C 88 108 76 126 60 126 C 44 126 32 108 30 84 C 28 60 38 32 60 32 Z',
        h: 152
    },
    long: {
        body: 'M60 10 C 90 10 102 52 100 92 C 98 128 84 160 60 160 C 36 160 22 128 20 92 C 18 52 30 10 60 10 Z',
        coat: 'M60 26 C 80 26 90 58 88 88 C 86 118 74 140 60 140 C 46 140 34 118 32 88 C 30 58 40 26 60 26 Z',
        h: 166
    }
}

const TEETH_L = [[10, 56], [14, 84], [12, 110]]
const TEETH_R = [[110, 56], [106, 84], [108, 110]]
const teethL = TEETH_L
const teethR = TEETH_R

// 关键字 → 图样（顺序即优先级：先特后泛）
const KINDS = [
    { k: '镜面', body: '#cf7a70', coat: null, edge: '#a8493c', gloss: true },
    { k: '无苔', body: '#cf7a70', coat: null, edge: '#a8493c', gloss: true },
    { k: '剥苔', body: '#dd8378', coat: 'peel', edge: '#b24a3f' },
    { k: '地图', body: '#dd8378', coat: 'peel', edge: '#b24a3f' },
    { k: '腐', body: '#dd9a8f', coat: 'bean', edge: '#b96a5f' },
    { k: '灰黑', body: '#c98d82', coat: 'rgba(84,74,66,0.88)', crack: true, edge: '#a8493c' },
    { k: '黄厚', body: '#cd6d5c', coat: 'rgba(226,204,104,0.96)', edge: '#a8493c' },
    { k: '黄腻', body: '#cd6d5c', coat: 'rgba(224,200,112,0.85)', edge: '#a8493c' },
    { k: '黄燥', body: '#cd6d5c', coat: 'rgba(229,203,110,0.9)', crack: true, edge: '#a8493c' },
    { k: '白润', body: '#e59088', coat: 'rgba(244,238,222,0.5)', edge: '#b96a5f' },
    { k: '白干', body: '#de9890', coat: 'rgba(240,232,214,0.8)', crack: true, edge: '#b96a5f' },
    { k: '齿痕', body: '#eaa79f', coat: 'rgba(244,238,222,0.35)', teeth: true, edge: '#b96a5f', v: 'fat' },
    { k: '胖大', body: '#eaa79f', coat: 'rgba(244,238,222,0.35)', teeth: true, edge: '#b96a5f', v: 'fat' },
    { k: '瘦薄', body: '#e8b2aa', coat: null, edge: '#c08d84', v: 'slim' },
    { k: '点刺', body: '#cf6557', coat: 'rgba(244,238,222,0.25)', prick: true, edge: '#a8493c' },
    { k: '嫩舌', body: '#f0b8b0', coat: 'rgba(244,238,222,0.3)', edge: '#d09a92', v: 'slim' },
    { k: '嫩', body: '#f0b8b0', coat: 'rgba(244,238,222,0.3)', edge: '#d09a92', v: 'slim' },
    { k: '老舌', body: '#c68f83', coat: null, crack: true, edge: '#8f4a40', old: true },
    { k: '强硬', body: '#c66f60', coat: 'rgba(244,238,222,0.3)', rigid: true, edge: '#8f4a40', v: 'rigid' },
    { k: '歪斜', body: '#d97f72', coat: 'rgba(244,238,222,0.3)', tilt: 14, edge: '#a8493c' },
    { k: '颤动', body: '#d97f72', coat: 'rgba(244,238,222,0.3)', wiggle: true, edge: '#a8493c' },
    { k: '痿软', body: '#e4b0a8', coat: 'rgba(244,238,222,0.4)', edge: '#c08d84', v: 'droop' },
    { k: '短缩', body: '#d27f74', coat: 'rgba(244,238,222,0.35)', edge: '#a8493c', v: 'short' },
    { k: '吐弄', body: '#dd867e', coat: 'rgba(244,238,222,0.3)', edge: '#b24a3f', v: 'long' },
    { k: '青紫', body: '#5c4358', coat: 'rgba(244,238,222,0.2)', spots: 'rgba(40,20,40,0.8)', edge: '#442f42' },
    { k: '紫暗', body: '#6f4a6e', coat: 'rgba(244,238,222,0.25)', spots: 'rgba(70,32,60,0.75)', edge: '#4f3050' },
    { k: '绛', body: '#a63a51', coat: null, edge: '#7c2a3e' },
    { k: '淡白', body: '#f0c6c0', coat: 'rgba(244,238,222,0.55)', edge: '#c08d84' },
    { k: '淡红', body: '#e59088', coat: 'rgba(244,238,222,0.5)', edge: '#b96a5f' },
    { k: '红', body: '#d15f57', coat: null, edge: '#a8493c' },
    { k: '裂纹', body: '#d97f72', coat: 'rgba(244,238,222,0.3)', crack: true, edge: '#a8493c' },
    { k: '厚腻', body: '#e2a49b', coat: 'rgba(244,238,222,0.95)', edge: '#b96a5f' },
    { k: '腻', body: '#e2a49b', coat: 'rgba(244,238,222,0.9)', edge: '#b96a5f' }
]

const cfg = computed(() => {
    for (const kind of KINDS) {
        if (props.term.includes(kind.k)) return kind
    }
    return KINDS.find((x) => x.k === '淡红')
})

const variant = computed(() => V[cfg.value.v || 'std'])
const bodyPath = computed(() => variant.value.body)
const coatPath = computed(() => variant.value.coat)
const vbh = computed(() => variant.value.h)
</script>

<style scoped>
.tongue-svg {
    width: 96rpx;
    height: 132rpx;
    flex-shrink: 0;
}
</style>
