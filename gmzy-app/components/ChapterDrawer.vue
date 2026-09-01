<template>
    <view>
        <view class="mask" v-show="show" @tap="close" :class="{ 'mask-show': show }" />
        <view class="drawer" :class="{ 'drawer-show': show }">
            <view class="drawer-head" :style="{ paddingTop: statusBar + 'px' }">
                <text class="drawer-title">目录</text>
                <text class="drawer-count">{{ flatCount }} 节</text>
                <view class="drawer-close" @tap="close">✕</view>
            </view>
            <scroll-view class="drawer-body" scroll-y :scroll-top="scrollTop">
                <view
                    v-for="n in flatTree"
                    :key="n.g"
                    class="node"
                    :class="{
                        current: n.g === currentG,
                        'node-lvl-1': n.l <= 1,
                        'node-lvl-2': n.l === 2,
                        'node-lvl-3': n.l === 3,
                        'node-lvl-deep': n.l >= 4
                    }"
                    :style="{ paddingLeft: 24 + (n.l - 1) * 30 + 'rpx' }"
                    @tap="jump(n)"
                >
                    <text
                        v-if="n.hasChild"
                        class="expander"
                        @tap.stop="toggle(n)"
                    >{{ expanded[n.g] ? '▾' : '▸' }}</text>
                    <text v-else class="expander exp-empty">·</text>
                    <text class="node-title">{{ n.x }}</text>
                </view>
            </scroll-view>
        </view>
    </view>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { statusBarHeight } from '../common/util.js'

const props = defineProps({
    show: { type: Boolean, default: false },
    tree: { type: Array, default: () => [] },
    currentG: { type: Number, default: -1 }
})
const emit = defineEmits(['update:show', 'jump'])

const statusBar = ref(statusBarHeight())
const expanded = reactive({})
let expandedInit = false

function close() {
    emit('update:show', false)
}

function toggle(n) {
    expanded[n.g] = !expanded[n.g]
}

watch(
    () => props.tree,
    () => {
        // 换书时清空展开状态，避免旧书的折叠状态误伤新树
        for (const k of Object.keys(expanded)) delete expanded[k]
        expandedInit = false
    }
)

const flatTree = computed(() => {
    const out = []
    const walk = (nodes) => {
        for (const n of nodes) {
            const hasChild = n.c && n.c.length > 0
            if (!expandedInit && n.l <= 2) expanded[n.g] = true
            out.push({ x: n.x, l: n.l, g: n.g, hasChild })
            if (hasChild && expanded[n.g] !== false) walk(n.c)
        }
    }
    walk(props.tree || [])
    expandedInit = true
    return out
})

const flatCount = computed(() => flatTree.value.length)
const scrollTop = ref(0)

watch(
    () => props.show,
    async (v) => {
        if (!v) return
        // 展开后滚动到当前节
        const idx = flatTree.value.findIndex((n) => n.g === props.currentG)
        if (idx > 6) {
            scrollTop.value = 0
            await new Promise((r) => setTimeout(r, 60))
            scrollTop.value = (idx - 4) * 44
        }
    }
)

function jump(n) {
    emit('jump', n.g)
    close()
}
</script>

<style lang="scss" scoped>
.mask {
    position: fixed;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background: rgba(20, 12, 8, 0.45);
    z-index: 90;
    opacity: 0;
    transition: opacity 0.25s;
}

.mask-show {
    opacity: 1;
}

.drawer {
    position: fixed;
    left: 0;
    top: 0;
    height: 100%;
    width: 76%;
    max-width: 620rpx;
    background: var(--bg, #fbf7ec);
    z-index: 91;
    transform: translateX(-102%);
    transition: transform 0.25s ease-out;
    display: flex;
    flex-direction: column;
    box-shadow: 4rpx 0 24rpx rgba(0, 0, 0, 0.15);
}

.drawer-show {
    transform: translateX(0);
}

.drawer-head {
    padding: 12px 30rpx 18rpx;
    display: flex;
    align-items: baseline;
    border-bottom: 1rpx solid var(--line, #e4dcc8);
}

.drawer-title {
    font-size: 34rpx;
    font-weight: 700;
    color: var(--fg, #37332b);
}

.drawer-count {
    margin-left: 16rpx;
    font-size: 22rpx;
    color: var(--muted, #8d8371);
}

.drawer-close {
    margin-left: auto;
    padding: 6rpx 16rpx;
    font-size: 28rpx;
    color: var(--muted, #8d8371);
}

.drawer-body {
    flex: 1;
}

.node {
    display: flex;
    align-items: center;
    padding: 18rpx 20rpx 18rpx 0;
    border-bottom: 1rpx solid var(--line-soft, rgba(228, 220, 200, 0.5));
}

.node-lvl-1 .node-title { font-size: 30rpx; font-weight: 700; }
.node-lvl-2 .node-title { font-size: 28rpx; font-weight: 600; }
.node-lvl-3 .node-title { font-size: 26rpx; }
.node-lvl-deep .node-title { font-size: 24rpx; color: var(--muted, #8d8371); }

.node-title {
    color: var(--fg, #37332b);
    line-height: 1.4;
    flex: 1;
}

.current .node-title {
    color: var(--accent, #8b3a3a);
    font-weight: 700;
}

.expander {
    width: 40rpx;
    text-align: center;
    color: var(--muted, #8d8371);
    font-size: 24rpx;
}

.exp-empty {
    opacity: 0.4;
    font-size: 20rpx;
}
</style>
