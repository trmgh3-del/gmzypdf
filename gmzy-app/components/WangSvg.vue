<template>
    <!-- 望诊示意图：面色 / 望神 / 目 / 唇 / 小儿指纹 / 舌面分部 -->
    <svg class="wang-svg" :class="{ big }" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <!-- ============ 面色 ============ -->
        <g v-if="face">
            <circle cx="60" cy="64" r="36" :fill="face.skin" />
            <path d="M24 52 C 26 26 94 26 96 52 L 96 58 C 88 42 32 42 24 58 Z" fill="#4a3a32" />
            <!-- 眉 -->
            <path d="M42 62 q 8 -3 14 0" stroke="rgba(60,40,32,0.6)" stroke-width="2.4" fill="none" stroke-linecap="round" />
            <path d="M64 62 q 8 -3 14 0" stroke="rgba(60,40,32,0.6)" stroke-width="2.4" fill="none" stroke-linecap="round" />
            <!-- 眼 -->
            <ellipse cx="49" cy="70" rx="6" ry="4" fill="#fffdf7" stroke="rgba(80,55,45,0.4)" stroke-width="1.2" />
            <ellipse cx="71" cy="70" rx="6" ry="4" fill="#fffdf7" stroke="rgba(80,55,45,0.4)" stroke-width="1.2" />
            <circle cx="49" cy="70" r="2.4" fill="#3a2a24" />
            <circle cx="71" cy="70" r="2.4" fill="#3a2a24" />
            <circle v-if="face.bright" cx="50" cy="69" r="0.9" fill="#fff" />
            <circle v-if="face.bright" cx="72" cy="69" r="0.9" fill="#fff" />
            <!-- 口 -->
            <path v-if="face.smile" d="M50 86 q 10 7 20 0" stroke="rgba(120,60,50,0.7)" stroke-width="2.2" fill="none" stroke-linecap="round" />
            <path v-else d="M52 88 q 8 3 16 0" stroke="rgba(120,60,50,0.6)" stroke-width="2.2" fill="none" stroke-linecap="round" />
            <!-- 特效 -->
            <g v-if="face.blush" :fill="'rgba(196,44,32,0.3)'">
                <circle cx="42" cy="82" r="7" />
                <circle cx="78" cy="82" r="7" />
                <ellipse cx="60" cy="60" rx="14" ry="6" fill="rgba(196,44,32,0.16)" />
            </g>
            <g v-if="face.zygo" :fill="'rgba(178,36,46,0.55)'">
                <circle cx="44" cy="80" r="4" />
                <circle cx="76" cy="80" r="4" />
            </g>
            <ellipse v-if="face.dull" cx="60" cy="64" rx="36" ry="36" fill="rgba(90,80,74,0.18)" />
            <g v-if="face.dark" fill="rgba(70,52,44,0.35)">
                <circle cx="44" cy="78" r="5" />
                <circle cx="76" cy="78" r="5" />
                <ellipse cx="60" cy="94" rx="10" ry="4" />
            </g>
        </g>

        <!-- ============ 望目 ============ -->
        <g v-if="eye === 'chi' || eye === 'huang'">
            <path d="M20 60 C 34 40 86 40 100 60 C 86 80 34 80 20 60 Z"
                :fill="eye === 'huang' ? '#ecda92' : '#fdfaf2'" stroke="rgba(90,60,50,0.5)" stroke-width="2" />
            <g v-if="eye === 'chi'" stroke="rgba(178,44,36,0.75)" stroke-width="1.8" fill="none" stroke-linecap="round">
                <path d="M30 54 q 6 4 12 4" />
                <path d="M32 66 q 5 -3 11 -2" />
                <path d="M90 54 q -6 4 -12 4" />
                <path d="M88 66 q -5 -3 -11 -2" />
            </g>
            <circle cx="60" cy="60" r="10" fill="#5b4632" />
            <circle cx="60" cy="60" r="5" fill="#241a12" />
            <circle cx="63" cy="57" r="1.8" fill="#fff" />
        </g>

        <!-- ============ 望唇 ============ -->
        <g v-if="lip">
            <path d="M28 64 C 40 52 52 56 60 62 C 68 56 80 52 92 64 C 80 74 68 75 60 72 C 52 75 40 74 28 64 Z"
                :fill="lip.fill" stroke="rgba(100,50,45,0.35)" stroke-width="1.5" />
            <path v-if="lip.crack" d="M52 60 l -2 10 M62 60 l 1 11 M70 58 l 3 10" stroke="rgba(90,30,26,0.55)" stroke-width="1.4" />
            <line x1="28" y1="64" x2="92" y2="64" stroke="rgba(90,40,36,0.4)" stroke-width="1.4" />
        </g>

        <!-- ============ 小儿指纹 ============ -->
        <g v-if="finger">
            <rect x="40" y="10" width="40" height="102" rx="20" fill="#f3dcc6" stroke="rgba(139,58,58,0.3)" stroke-width="1.5" />
            <line x1="40" y1="34" x2="80" y2="34" stroke="rgba(139,58,58,0.35)" stroke-width="1.5" stroke-dasharray="3 3" />
            <line x1="40" y1="62" x2="80" y2="62" stroke="rgba(139,58,58,0.35)" stroke-width="1.5" stroke-dasharray="3 3" />
            <text x="86" y="38" class="fz">风</text>
            <text x="86" y="66" class="fz">气</text>
            <text x="86" y="94" class="fz">命</text>
            <!-- 络脉：病轻则止於风关（鲜红），病重则逾气关达命关（紫黑） -->
            <path v-if="finger === 'light'" d="M58 12 C 60 18 60 26 60 32" stroke="#c0392b" stroke-width="3.6" fill="none" stroke-linecap="round" />
            <path v-else d="M58 12 C 60 20 60 30 59 40 C 58 58 60 80 60 100" stroke="#6e3a8c" stroke-width="3.8" fill="none" stroke-linecap="round" />
        </g>

        <!-- ============ 舌面五脏分部 ============ -->
        <g v-if="zones">
            <path d="M60 14 C 90 14 104 54 102 88 C 100 120 84 146 60 146 C 36 146 20 120 18 88 C 16 54 30 14 60 14 Z"
                fill="#e59088" stroke="#b96a5f" stroke-width="2" />
            <line x1="30" y1="52" x2="90" y2="52" stroke="rgba(124,47,38,0.55)" stroke-width="1.6" stroke-dasharray="4 4" />
            <line x1="28" y1="96" x2="92" y2="96" stroke="rgba(124,47,38,0.55)" stroke-width="1.6" stroke-dasharray="4 4" />
            <line x1="42" y1="54" x2="42" y2="94" stroke="rgba(124,47,38,0.45)" stroke-width="1.4" stroke-dasharray="4 4" />
            <line x1="78" y1="54" x2="78" y2="94" stroke="rgba(124,47,38,0.45)" stroke-width="1.4" stroke-dasharray="4 4" />
            <text x="52" y="40" class="zt">心肺</text>
            <text x="20" y="80" class="zt">肝</text>
            <text x="90" y="80" class="zt">胆</text>
            <text x="52" y="80" class="zt">脾胃</text>
            <text x="56" y="126" class="zt">肾</text>
        </g>
    </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    kind: { type: String, default: 'face-bai' },
    big: { type: Boolean, default: false }
})

const FACE = {
    'face-qing': { skin: '#96a091', blush: false, bright: false, smile: false },
    'face-chi': { skin: '#e5927c', blush: true, bright: true, smile: false },
    'face-huang': { skin: '#e0c494', blush: false, bright: false, smile: false },
    'face-bai': { skin: '#f2ece3', blush: false, bright: false, smile: false },
    'face-hei': { skin: '#a08a7e', dark: true, bright: false, smile: false },
    'shen-you': { skin: '#f0d8c4', bright: true, smile: true },
    'shen-shi': { skin: '#d8cdc4', dull: true, bright: false, smile: false },
    'shen-jia': { skin: '#e6dcd4', dull: true, zygo: true, bright: false, smile: false }
}

const LIP = {
    'lip-bai': { fill: '#ecc9c4', crack: false },
    'lip-red': { fill: '#c04536', crack: true },
    'lip-zi': { fill: '#7c5a74', crack: false }
}

const face = computed(() => FACE[props.kind] || null)
const eye = computed(() => (props.kind === 'eye-chi' ? 'chi' : props.kind === 'eye-huang' ? 'huang' : null))
const lip = computed(() => LIP[props.kind] || null)
const finger = computed(() => (props.kind === 'finger-light' ? 'light' : props.kind === 'finger-severe' ? 'severe' : null))
const zones = computed(() => props.kind === 'zones')
</script>

<style scoped>
.wang-svg {
    width: 104rpx;
    height: 104rpx;
    flex-shrink: 0;
}

.wang-svg.big {
    width: 240rpx;
    height: 240rpx;
}

.fz {
    font-size: 13px;
    fill: #5c2018;
    font-weight: 700;
}

.zt {
    font-size: 9px;
    fill: #fffdf7;
    font-weight: 700;
}
</style>
