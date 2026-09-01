<template>
    <view class="diag">
        <!-- 免责声明常驻 -->
        <view class="notice">
            <text class="notice-icon">⚠</text>
            <text class="notice-text">{{ rules.disclaimer || DEFAULT_DISCLAIMER }}</text>
        </view>

        <template v-if="step === 'pick'">
            <view class="guide">
                <text class="guide-title serif-font">勾选所见症状与舌脉</text>
                <text class="guide-text">已选 {{ selectedCount }} 项 · 建议 5~12 项，舌脉尽量勾选</text>
            </view>

            <view v-for="g in rules.groups" :key="g.id" class="group">
                <view class="group-head" @tap="toggleGroup(g.id)">
                    <text class="group-name">{{ g.name }}</text>
                    <view class="group-side">
                        <text v-if="groupSelCount(g)" class="group-badge serif-font">{{ groupSelCount(g) }}</text>
                        <text class="group-arrow" :class="{ open: openGroups[g.id] }">›</text>
                    </view>
                </view>
                <view v-show="openGroups[g.id]" class="chips">
                    <text
                        v-for="it in g.items"
                        :key="it.id"
                        class="chip"
                        :class="{ on: selected[it.id] }"
                        @tap="toggleItem(it.id)"
                    >{{ it.label }}</text>
                </view>
            </view>

            <view class="actions">
                <button class="btn ghost" :disabled="!selectedCount" @tap="clearAll">清空</button>
                <button class="btn primary" :disabled="selectedCount < 3" @tap="run">
                    开始辨证{{ selectedCount < 3 ? '（再选几项）' : '' }}
                </button>
            </view>
        </template>

        <template v-else>
            <view class="result-head">
                <button class="btn ghost" @tap="step = 'pick'">‹ 重新勾选</button>
                <text class="result-count serif-font">共 {{ results.length }} 个提示证型</text>
            </view>

            <view
                v-for="(r, i) in results"
                :key="r.id"
                class="rcard"
                :class="{ first: i === 0 }"
            >
                <view class="rcard-top" @tap="r._open = !r._open">
                    <view class="rank serif-font">证</view>
                    <view class="rcard-main">
                        <view class="rcard-namerow">
                            <text class="rname serif-font">{{ r.name }}</text>
                            <text class="rcat">{{ r.cat }}</text>
                        </view>
                        <view class="pbar">
                            <view class="pfill" :style="{ width: r.pct + '%' }" />
                        </view>
                        <text class="rmeta">吻合度 {{ r.pct }}% · 命中 {{ r.matched.length }} 症</text>
                    </view>
                    <view class="pct serif-font">{{ r.pct }}<text class="pct-sign">%</text></view>
                </view>

                <view v-show="r._open" class="rdetail">
                    <view class="rrow" v-if="r.matched.length">
                        <text class="rkey">命中症状</text>
                        <view class="hits">
                            <text v-for="m in r.matched" :key="m.id" class="hit">{{ m.label }}</text>
                        </view>
                    </view>
                    <view class="rrow">
                        <text class="rkey">病机</text>
                        <text class="rval">{{ r.bj }}</text>
                    </view>
                    <view class="rrow">
                        <text class="rkey">治法</text>
                        <text class="rval">{{ r.zf }}</text>
                    </view>
                    <view class="rrow">
                        <text class="rkey">代表方</text>
                        <text class="rval accent">{{ r.fang }}</text>
                    </view>
                    <view class="rrow">
                        <text class="rkey">参考穴</text>
                        <text class="rval">{{ r.points }}</text>
                    </view>
                    <view class="rrow">
                        <text class="rkey">教材出处</text>
                        <text class="rval">{{ r.ref }}</text>
                    </view>
                    <view class="rgo" @tap="goSearch(r.name)">在全库检索「{{ r.name }}」原文论述 ›</view>
                </view>
            </view>

            <view class="notice foot-notice">
                <text class="notice-icon">⚠</text>
                <text class="notice-text">{{ rules.disclaimer || DEFAULT_DISCLAIMER }}</text>
            </view>
        </template>

        <!-- 历史记录 -->
        <view v-if="step === 'pick' && history.length" class="sec">
            <view class="sec-head">
                <text class="sec-title">最近辨证</text>
                <text class="sec-op" @tap="clearHis">清空</text>
            </view>
            <view v-for="h in history" :key="h.ts" class="his" @tap="replay(h)">
                <view class="his-main">
                    <text class="his-top">提示：{{ h.top.name }}（{{ h.top.pct }}%）</text>
                    <text class="his-sym">{{ h.symptoms.join('、') }}</text>
                </view>
                <text class="his-time">{{ fmt(h.ts) }}</text>
            </view>
        </view>
    </view>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { loadDiagRules } from '../../common/learn.js'
import { diagnose, symptomIndex } from '../../common/diagnosis.js'
import { store, pending, pushDiagRecord, clearDiagHistory } from '../../common/store.js'

const DEFAULT_DISCLAIMER = '本功能仅供学习辨证思路参考，不能替代执业医师面诊，如有不适请及时就医。'

const rules = ref({ groups: [] })
const selected = reactive({})
const openGroups = reactive({})
const step = ref('pick')
const results = ref([])
const history = computed(() => store.learn.diagHistory)
let idxMap = {}

onLoad(async () => {
    rules.value = await loadDiagRules()
    idxMap = symptomIndex(rules.value)
    // 默认展开前两组
    if (rules.value.groups[0]) openGroups[rules.value.groups[0].id] = true
    if (rules.value.groups[1]) openGroups[rules.value.groups[1].id] = true
})

onShow(() => {
    if (pending.diagSymptoms) {
        for (const id of pending.diagSymptoms) selected[id] = true
        pending.diagSymptoms = null
    }
})

const selectedCount = computed(() => Object.keys(selected).length)

function toggleGroup(id) {
    openGroups[id] = !openGroups[id]
}

function groupSelCount(g) {
    return g.items.filter((it) => selected[it.id]).length
}

function toggleItem(id) {
    if (selected[id]) delete selected[id]
    else selected[id] = true
}

function clearAll() {
    for (const k of Object.keys(selected)) delete selected[k]
}

function run() {
    const out = diagnose(Object.keys(selected), rules.value, 4)
    results.value = out.map((r) => reactive({ ...r, _open: false }))
    if (results.value.length) results.value[0]._open = true
    step.value = 'result'
    if (out.length) {
        const labels = Object.keys(selected).map((id) => idxMap[id] || id)
        pushDiagRecord({
            symptoms: labels.slice(0, 10),
            count: labels.length,
            top: { name: out[0].name, pct: out[0].pct }
        })
    }
    uni.pageScrollTo({ scrollTop: 0, duration: 0 })
}

function goSearch(name) {
    pending.keyword = name.replace(/（.*）/, '')
    uni.navigateTo({ url: '/pages/search/search' })
}

function clearHis() {
    uni.showModal({
        title: '清空记录',
        content: '确定清空全部辨证练习记录吗？',
        confirmColor: '#8b3a3a',
        success: (r) => {
            if (r.confirm) clearDiagHistory()
        }
    })
}

function replay(h) {
    uni.showModal({
        title: '辨证提示：' + h.top.name,
        content: `吻合度 ${h.top.pct}%\n当时勾选 ${h.count} 项：${h.symptoms.join('、')}${h.count > 10 ? '…' : ''}`,
        showCancel: false,
        confirmColor: '#8b3a3a'
    })
}

function fmt(ts) {
    const d = new Date(ts)
    return `${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
.diag {
    min-height: 100vh;
    background: #f6f1e5;
    padding: 20rpx 24rpx 60rpx;
}

.notice {
    display: flex;
    gap: 12rpx;
    align-items: flex-start;
    background: rgba(200, 147, 47, 0.12);
    border: 1rpx solid rgba(200, 147, 47, 0.35);
    border-radius: 14rpx;
    padding: 16rpx 20rpx;
    margin-bottom: 20rpx;
}

.notice-icon {
    color: #a67619;
    font-size: 26rpx;
}

.notice-text {
    flex: 1;
    font-size: 22rpx;
    line-height: 1.6;
    color: #8a6d1c;
}

.guide {
    margin: 8rpx 4rpx 22rpx;
}

.guide-title {
    display: block;
    font-size: 34rpx;
    font-weight: 700;
    color: #37332b;
    margin-bottom: 8rpx;
}

.guide-text {
    font-size: 23rpx;
    color: #8d8371;
}

.group {
    background: #fffdf7;
    border-radius: 18rpx;
    border: 1rpx solid #e4dcc8;
    margin-bottom: 18rpx;
    overflow: hidden;
}

.group-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 24rpx;
}

.group-name {
    font-size: 28rpx;
    font-weight: 600;
    color: #37332b;
}

.group-side {
    display: flex;
    align-items: center;
    gap: 14rpx;
}

.group-badge {
    min-width: 40rpx;
    height: 40rpx;
    border-radius: 20rpx;
    background: #8b3a3a;
    color: #f3e9d2;
    font-size: 22rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 10rpx;
}

.group-arrow {
    color: #b9ac92;
    font-size: 34rpx;
    transition: transform 0.2s;

    &.open {
        transform: rotate(90deg);
    }
}

.chips {
    display: flex;
    flex-wrap: wrap;
    gap: 16rpx;
    padding: 0 24rpx 26rpx;
}

.chip {
    font-size: 24rpx;
    color: #6b6455;
    background: #f6f1e5;
    border: 1rpx solid #e4dcc8;
    border-radius: 999rpx;
    padding: 12rpx 26rpx;

    &.on {
        background: #8b3a3a;
        border-color: #8b3a3a;
        color: #f3e9d2;
    }
}

.actions {
    display: flex;
    gap: 20rpx;
    margin: 30rpx 0 10rpx;
}

.btn {
    flex: 1;
    height: 88rpx;
    line-height: 88rpx;
    border-radius: 16rpx;
    font-size: 30rpx;
    border: none;

    &::after {
        border: none;
    }
}

.btn.primary {
    background: linear-gradient(135deg, #8b3a3a, #5c2018);
    color: #f3e9d2;
    flex: 2;
    font-weight: 600;

    &[disabled] {
        opacity: 0.5;
    }
}

.btn.ghost {
    background: transparent;
    border: 1rpx solid #c9bda2;
    color: #8d8371;
}

.result-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 22rpx;
}

.result-count {
    font-size: 24rpx;
    color: #8d8371;
}

.result-head .btn.ghost {
    flex: none;
    width: auto;
    height: 64rpx;
    line-height: 64rpx;
    padding: 0 28rpx;
    font-size: 25rpx;
}

.rcard {
    background: #fffdf7;
    border: 1rpx solid #e4dcc8;
    border-radius: 20rpx;
    margin-bottom: 20rpx;
    overflow: hidden;

    &.first {
        border-color: #8b3a3a;

        .rank {
            background: linear-gradient(150deg, #8b3a3a, #5c2018);
            color: #f3e9d2;
        }
    }
}

.rcard-top {
    display: flex;
    align-items: center;
    gap: 22rpx;
    padding: 28rpx 24rpx;
}

.rank {
    width: 72rpx;
    height: 72rpx;
    border-radius: 16rpx;
    background: #efe8d6;
    color: #8d8371;
    font-size: 34rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.rcard-main {
    flex: 1;
    min-width: 0;
}

.rcard-namerow {
    display: flex;
    align-items: baseline;
    gap: 16rpx;
    margin-bottom: 12rpx;
}

.rname {
    font-size: 32rpx;
    font-weight: 700;
    color: #37332b;
}

.rcat {
    font-size: 20rpx;
    color: #8d8371;
    background: #f6f1e5;
    border-radius: 8rpx;
    padding: 4rpx 12rpx;
}

.pbar {
    height: 10rpx;
    background: #efe8d6;
    border-radius: 6rpx;
    overflow: hidden;
    margin-bottom: 8rpx;
}

.pfill {
    height: 100%;
    background: linear-gradient(90deg, #8b3a3a, #b35f4a);
    border-radius: 6rpx;
}

.rmeta {
    font-size: 21rpx;
    color: #8d8371;
}

.pct {
    font-size: 44rpx;
    color: #8b3a3a;
    font-weight: 700;
}

.pct-sign {
    font-size: 22rpx;
}

.rdetail {
    border-top: 1rpx dashed #e4dcc8;
    padding: 22rpx 24rpx 26rpx;
}

.rrow {
    display: flex;
    gap: 20rpx;
    margin-bottom: 14rpx;
}

.rkey {
    width: 120rpx;
    flex-shrink: 0;
    font-size: 23rpx;
    color: #b9ac92;
    padding-top: 3rpx;
}

.rval {
    flex: 1;
    font-size: 25rpx;
    line-height: 1.7;
    color: #4a453b;

    &.accent {
        color: #8b3a3a;
    }
}

.hits {
    flex: 1;
    display: flex;
    flex-wrap: wrap;
    gap: 10rpx;
}

.hit {
    font-size: 21rpx;
    background: rgba(139, 58, 58, 0.08);
    color: #8b3a3a;
    border-radius: 8rpx;
    padding: 4rpx 14rpx;
}

.rgo {
    margin-top: 10rpx;
    padding: 18rpx 0 4rpx;
    font-size: 25rpx;
    color: #8b3a3a;
    border-top: 1rpx dashed #e4dcc8;
}

.foot-notice {
    margin-top: 26rpx;
}

.sec {
    background: #fffdf7;
    border: 1rpx solid #e4dcc8;
    border-radius: 20rpx;
    padding: 24rpx;
    margin-top: 26rpx;
}

.sec-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12rpx;
}

.sec-title {
    font-size: 28rpx;
    font-weight: 600;
    color: #37332b;
}

.sec-op {
    font-size: 23rpx;
    color: #b3543f;
}

.his {
    display: flex;
    align-items: center;
    gap: 20rpx;
    padding: 18rpx 0;
    border-top: 1rpx solid #efe8d6;
}

.his-main {
    flex: 1;
    min-width: 0;
}

.his-top {
    display: block;
    font-size: 26rpx;
    color: #5c2018;
    font-weight: 600;
    margin-bottom: 6rpx;
}

.his-sym {
    display: block;
    font-size: 21rpx;
    color: #8d8371;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.his-time {
    font-size: 20rpx;
    color: #b9ac92;
    flex-shrink: 0;
}
</style>
