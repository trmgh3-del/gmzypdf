<template>
    <!-- 舌象示意图（风格化 SVG，离线无资源） -->
    <svg class="tongue-svg" viewBox="0 0 120 150" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <!-- 舌体 -->
        <path :d="BODY" :fill="cfg.body" />
        <!-- 齿痕：边缘凹口（用卡面色覆盖出缺口） -->
        <g v-if="cfg.teeth" :fill="'var(--card, #fffdf7)'">
            <circle v-for="(c, i) in teethL" :key="'l' + i" :cx="c[0]" :cy="c[1]" r="7" />
            <circle v-for="(c, i) in teethR" :key="'r' + i" :cx="c[0]" :cy="c[1]" r="7" />
        </g>
        <!-- 舌苔（剥苔=斑块，其余=整片） -->
        <template v-if="cfg.coat === 'peel'">
            <circle cx="44" cy="62" r="16" fill="rgba(244,238,222,0.9)" />
            <circle cx="72" cy="96" r="18" fill="rgba(244,238,222,0.9)" />
            <circle cx="52" cy="116" r="12" fill="rgba(244,238,222,0.9)" />
        </template>
        <path v-else-if="cfg.coat" :d="COAT" :fill="cfg.coat" />
        <!-- 裂纹 -->
        <g v-if="cfg.crack" stroke="rgba(120,40,44,0.85)" stroke-width="2.4" fill="none" stroke-linecap="round">
            <path d="M60 46 L58 66 L63 84 L59 104" />
            <path d="M52 58 L58 66" />
            <path d="M63 84 L70 92" />
        </g>
        <!-- 瘀斑 -->
        <g v-if="cfg.spots" fill="rgba(90,32,60,0.75)">
            <circle cx="46" cy="70" r="4" />
            <circle cx="68" cy="60" r="3.4" />
            <circle cx="62" cy="100" r="4.4" />
        </g>
        <!-- 舌边轮廓 -->
        <path :d="BODY" fill="none" :stroke="cfg.edge" stroke-width="2" />
    </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    term: { type: String, default: '' },
    // 齿痕舌加宽
    fat: { type: Boolean, default: false }
})

const BODY_FAT = 'M60 14 C 94 14 108 52 106 86 C 104 120 86 142 60 142 C 34 142 16 120 14 86 C 12 52 26 14 60 14 Z'
const BODY_FIT = 'M60 18 C 88 18 100 54 98 86 C 96 116 82 138 60 138 C 38 138 24 116 22 86 C 20 54 32 18 60 18 Z'
const COAT_FAT = 'M60 30 C 82 30 92 58 90 84 C 88 110 76 128 60 128 C 44 128 32 110 30 84 C 28 58 38 30 60 30 Z'
const COAT_FIT = 'M60 34 C 78 34 88 60 86 84 C 84 106 74 124 60 124 C 46 124 36 106 34 84 C 32 60 42 34 60 34 Z'
const TEETH_L = [[10, 58], [14, 82], [12, 106]]
const TEETH_R = [[110, 58], [106, 82], [108, 106]]

const isFat = computed(() => props.fat || props.term.includes('齿痕') || props.term.includes('胖大'))
const BODY = computed(() => (isFat.value ? BODY_FAT : BODY_FIT))
const COAT = computed(() => (isFat.value ? COAT_FAT : COAT_FIT))
const teethL = TEETH_L
const teethR = TEETH_R

const KINDS = [
    { k: '剥苔', body: '#dd8378', coat: 'peel', crack: false, spots: false, teeth: false, edge: '#b24a3f' },
    { k: '地图', body: '#dd8378', coat: 'peel', crack: false, spots: false, teeth: false, edge: '#b24a3f' },
    { k: '黄燥', body: '#cd6d5c', coat: 'rgba(229,203,110,0.92)', crack: true, spots: false, teeth: false, edge: '#a8493c' },
    { k: '黄腻', body: '#cd6d5c', coat: 'rgba(226,203,120,0.85)', crack: false, spots: false, teeth: false, edge: '#a8493c' },
    { k: '厚腻', body: '#e2a49b', coat: 'rgba(244,238,222,0.95)', crack: false, spots: false, teeth: false, edge: '#b96a5f' },
    { k: '齿痕', body: '#eaa79f', coat: 'rgba(244,238,222,0.35)', crack: false, spots: false, teeth: true, edge: '#b96a5f' },
    { k: '胖大', body: '#eaa79f', coat: 'rgba(244,238,222,0.35)', crack: false, spots: false, teeth: true, edge: '#b96a5f' },
    { k: '裂纹', body: '#d97f72', coat: 'rgba(244,238,222,0.3)', crack: true, spots: false, teeth: false, edge: '#a8493c' },
    { k: '紫暗', body: '#6f4a6e', coat: 'rgba(244,238,222,0.25)', crack: false, spots: true, teeth: false, edge: '#4f3050' },
    { k: '绛', body: '#a63a51', coat: null, crack: false, spots: false, teeth: false, edge: '#7c2a3e', plain: true },
    { k: '红舌', body: '#d15f57', coat: null, crack: false, spots: false, teeth: false, edge: '#a8493c', plain: true },
    { k: '红', body: '#d15f57', coat: null, crack: false, spots: false, teeth: false, edge: '#a8493c', plain: true },
    { k: '淡白', body: '#f0c6c0', coat: 'rgba(244,238,222,0.55)', crack: false, spots: false, teeth: false, edge: '#c08d84' },
    { k: '淡红', body: '#e59088', coat: 'rgba(244,238,222,0.5)', crack: false, spots: false, teeth: false, edge: '#b96a5f' }
]

const cfg = computed(() => {
    for (const kind of KINDS) {
        if (props.term.includes(kind.k)) return kind
    }
    return KINDS[KINDS.length - 1] // 默认淡红
})
</script>

<style scoped>
.tongue-svg {
    width: 96rpx;
    height: 120rpx;
    flex-shrink: 0;
}
</style>
