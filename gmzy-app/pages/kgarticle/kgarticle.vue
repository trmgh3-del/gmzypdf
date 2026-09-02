<template>
    <view class="art" :class="{ night, elder, [themeCls]: night }">
        <!-- 条目题头 -->
        <view class="art-head">
            <text class="art-bt">{{ bookTitle }} · {{ cat.name }}</text>
            <text class="art-t serif-font">{{ entryTitle }}</text>
            <text class="art-pt" v-if="parentTitle">{{ parentTitle }}</text>
        </view>

        <!-- 正文（复用全书 BlocksView 渲染器） -->
        <view class="art-body">
            <BlocksView :blocks="blocks" :slug="slug" />
        </view>

        <!-- 条目动作条 -->
        <view class="art-bar">
            <text class="ab-btn" :class="{ off: !prevEntry }" @tap="goPrev">« 上一条</text>
            <text class="ab-btn ab-read" :class="{ done: read }" @tap="markRead">{{ read ? '✓ 已读毕' : '读毕标记' }}</text>
            <text class="ab-btn" :class="{ off: !nextEntry }" @tap="goNext">下一条 »</text>
        </view>
    </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { store, markKgRead, isKgRead } from '../../common/store.js'
import { loadKgIndex, getKgCat, entryBounds, entryNeighbors, kgArticle } from '../../common/kg.js'
import { applyNavTheme } from '../../common/theme.js'
import BlocksView from '../../components/BlocksView.vue'

const cat = ref({ name: '', icon: '', entries: [] })
const slug = ref('')
const g = ref(0)
const entryTitle = ref('')
const parentTitle = ref('')
const bookTitle = ref('')
const blocks = ref([])
const prevEntry = ref(null)
const nextEntry = ref(null)
const read = ref(false)

const night = computed(() => store.settings.night)
const elder = computed(() => store.settings.elder)
const themeCls = computed(() => 'night-theme-' + (store.settings.nightTheme || 'warm'))

let catKey = ''

async function loadEntry(b, gi) {
    const { cur, next } = entryBounds(cat.value, b, gi)
    if (!cur) return
    const art = await kgArticle(b, gi, next ? next.g : null)
    slug.value = b
    g.value = gi
    entryTitle.value = cur.t
    parentTitle.value = cur.pt
    bookTitle.value = art.title
    blocks.value = art.blocks
    read.value = isKgRead(b, gi)
    const nb = entryNeighbors(cat.value, b, gi)
    prevEntry.value = nb.prev
    nextEntry.value = nb.next
    uni.setNavigationBarTitle({ title: cur.t })
}

onLoad(async (q) => {
    catKey = q.key || 'basics'
    await loadKgIndex()
    const c = getKgCat(catKey)
    if (!c) return
    cat.value = c
    await loadEntry(q.s, +q.g)
})

onShow(() => applyNavTheme())

function markRead() {
    if (markKgRead(slug.value, g.value)) {
        read.value = true
        // 自动顺推下一条
        if (nextEntry.value) {
            setTimeout(() => loadEntry(nextEntry.value.b, nextEntry.value.g), 350)
        } else {
            uni.showToast({ icon: 'none', title: '本科目条目已至卷末' })
        }
    }
}

function goPrev() {
    if (prevEntry.value) loadEntry(prevEntry.value.b, prevEntry.value.g)
}
function goNext() {
    if (nextEntry.value) loadEntry(nextEntry.value.b, nextEntry.value.g)
}
</script>

<style scoped>
.art {
    min-height: 100vh;
    background: #f6f1e5;
    display: flex;
    flex-direction: column;
}

.night .art {
    background: #1a1611;
}

.art-head {
    margin: 24rpx 30rpx 0;
    padding: 24rpx 26rpx 18rpx;
    background: #fffdf7;
    border: 1px solid rgba(139, 58, 58, 0.12);
    border-radius: 18rpx 18rpx 0 0;
    border-bottom: none;
}

.night .art-head {
    background: #241f18;
}

.art-bt {
    display: block;
    font-size: 21rpx;
    color: #a0937a;
    margin-bottom: 8rpx;
}

.art-t {
    display: block;
    font-size: 40rpx;
    font-weight: 700;
    color: #5c2018;
    letter-spacing: 2rpx;
}

.night .art-t {
    color: #e8b0a0;
}

.art-pt {
    display: block;
    font-size: 23rpx;
    color: #8d8371;
    margin-top: 8rpx;
}

.art-body {
    margin: 0 30rpx;
    padding: 6rpx 26rpx 30rpx;
    background: #fffdf7;
    border: 1px solid rgba(139, 58, 58, 0.12);
    border-top: none;
    border-radius: 0 0 18rpx 18rpx;
}

.night .art-body {
    background: #241f18;
}

.art-bar {
    display: flex;
    justify-content: space-between;
    gap: 14rpx;
    margin: 26rpx 30rpx 46rpx;
}

.ab-btn {
    flex: 1;
    text-align: center;
    background: rgba(139, 58, 58, 0.08);
    border: 1px solid rgba(139, 58, 58, 0.2);
    color: #5c2018;
    border-radius: 12rpx;
    padding: 18rpx 0;
    font-size: 25rpx;
}

.night .ab-btn {
    color: #e8dfc8;
    background: rgba(232, 223, 200, 0.08);
    border-color: rgba(232, 223, 200, 0.2);
}

.ab-btn.off {
    opacity: 0.3;
}

.ab-read {
    background: #8b3a3a;
    color: #fffdf7;
}

.ab-read.done {
    background: #557a46;
}
</style>
