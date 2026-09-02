<template>
    <view class="diag" :class="{ night, elder: store.settings.elder, [themeCls]: night }">
        <!-- 免责声明常驻 -->
        <view class="notice">
            <text class="notice-icon">⚠</text>
            <text class="notice-text">{{ rules.disclaimer || DEFAULT_DISCLAIMER }}</text>
        </view>

        <!-- 红旗：急重症征象提示 -->
        <view v-if="redFlags.length" class="redflag">
            <text class="redflag-icon">‼</text>
            <text class="redflag-text">已勾选急重症征象（{{ redFlags.map((f) => f.label).join('、') }}）。辨证练习可继续；<text class="redflag-bold">若为真实不适，请立即就医，切勿自我处理</text>。</text>
        </view>

        <template v-if="step === 'pick'">
            <view class="guide">
                <text class="guide-title serif-font">勾选所见症状与舌脉</text>
                <text class="guide-text">已选 {{ selectedCount }} 项 · 建议 5~12 项，舌脉尽量勾选 · 长按舌/脉可看图谱对照</text>
            </view>

            <!-- 症状搜索 -->
            <view class="symbar">
                <input v-model.trim="kw" class="sym-input" placeholder="搜索症状：如 咳嗽 / 脉浮 / 盗汗" confirm-type="search" />
            </view>
            <view v-if="kw" class="chips search-hits">
                <block v-if="kwHits.length">
                    <text
                        v-for="it in kwHits"
                        :key="it.id"
                        class="chip"
                        :class="{ on: selected[it.id] }"
                        @tap="toggleItem(it.id)"
                    ><text class="chip-g">{{ it.gname }}·</text>{{ it.label }}</text>
                </block>
                <text v-else class="search-empty">没有匹配「{{ kw }}」的症状</text>
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
                        :class="{ on: selected[it.id], hot: it.freq >= 0.45, tip: it.id in symTip }"
                        @tap="toggleItem(it.id)"
                        @longpress="showAtlasTip(it)"
                    >{{ it.label }}<text v-if="it.freq >= 0.45" class="hot-dot"> 热</text></text>
                </view>
            </view>

            <view class="actions">
                <button class="btn ghost" :disabled="!selectedCount" @tap="clearAll">清空</button>
                <button class="btn primary" :disabled="selectedCount < 3" @tap="run">
                    开始辨证{{ selectedCount < 3 ? '（再选几项）' : '' }}
                </button>
            </view>

            <!-- 医案辨证入口 -->
            <view class="case-entry" @tap="startCase">
                <view class="ce-left">
                    <text class="ce-in serif-font">🩺 医案辨证</text>
                    <text class="ce-desc">真实医案抽考：看案选证型，每次 10 题</text>
                </view>
                <text class="ce-op serif-font">开考 ›</text>
            </view>
            <text class="ce-acc" v-if="(store.learn.diagQuiz || {}).done">累计 {{ dqAcc }} 正确</text>
        </template>

        <!-- 医案辨证做题 -->
        <template v-else-if="step === 'case'">
            <view class="result-head">
                <button class="btn ghost" @tap="step = 'pick'">‹ 返回勾选</button>
                <text class="result-count serif-font">{{ casePos + 1 }} / {{ caseTotal }}</text>
                <text class="case-round serif-font">对 {{ caseOk }}</text>
            </view>
            <view class="case-card">
                <view class="case-qtag-row">
                    <text class="qtag">{{ caseCur.src || '医案' }}</text>
                    <text class="case-seq serif-font">{{ casePos + 1 }}/{{ caseTotal }}</text>
                </view>
                <scroll-view scroll-y class="case-scroll">
                    <text class="case-text serif-font">{{ caseCur.q }}</text>
                </scroll-view>
                <view class="case-choices">
                    <view
                        v-for="c in caseCur.choices"
                        :key="c"
                        class="case-choice"
                        :class="{ right: casePicked && c === caseCur.an, wrong: casePicked === c && c !== caseCur.an }"
                        @tap="pickCase(c)"
                    >
                        <text class="case-choice-t">{{ c }}</text>
                        <text v-if="casePicked && c === caseCur.an" class="case-mark">✓ 正解</text>
                        <text v-else-if="casePicked === c" class="case-mark bad">✗</text>
                    </view>
                </view>
                <view class="case-foot">
                    <text v-if="!casePicked" class="case-hint">细读医案，选出最贴合的证型</text>
                    <button v-else class="btn primary case-next" @tap="nextCase">
                        {{ casePos + 1 >= caseTotal ? '查看本组成绩' : '下一题 ›' }}
                    </button>
                </view>
            </view>

            <!-- 本组成绩 -->
            <view v-if="caseDone" class="case-mask">
                <view class="case-over">
                    <text class="co-title serif-font">本组成绩</text>
                    <text class="co-score serif-font">{{ caseOk }} / {{ caseTotal }}</text>
                    <text class="co-line">正确率 {{ Math.round((caseOk / caseTotal) * 100) }}% · 累计 {{ dqAcc }}</text>
                    <view class="co-btns">
                        <text class="co-btn ghost" @tap="step = 'pick'">返回辨证</text>
                        <text class="co-btn solid" @tap="startCase">再来一组</text>
                    </view>
                </view>
            </view>
        </template>


        <template v-else-if="step === 'result'">
            <view class="result-head">
                <button class="btn ghost" @tap="step = 'pick'">‹ 重新勾选</button>
                <text class="result-count serif-font">共 {{ results.length }} 个提示证型</text>
                <button class="btn ghost" @tap="copyResult">复制结论</button>
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
                            <text v-if="r.gang" class="gang">{{ r.gang }}</text>
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
                        <text class="rval accent" @tap="goFang(r)">{{ r.fang }} ›</text>
                    </view>
                    <view class="rrow">
                        <text class="rkey">参考穴</text>
                        <text class="rval">{{ r.points }}</text>
                    </view>
                    <view class="rrow">
                        <text class="rkey">教材出处</text>
                        <text class="rval">{{ r.ref }}</text>
                    </view>

                    <!-- 诊疗依据（教材原文证据链） -->
                    <view class="rrow rev-block" v-if="r.ev && r.ev.length">
                        <text class="rkey">诊疗依据</text>
                        <view class="ev-list">
                            <view v-for="(e, ei) in r.ev" :key="ei" class="ev-item" @tap="goEvidence(e)">
                                <view class="ev-head">
                                    <text class="ev-book">《{{ e.book.replace(/^[0-9]+/, '') }}》</text>
                                    <text class="ev-path">{{ e.path }}</text>
                                    <text class="ev-go">原文 ›</text>
                                </view>
                                <text class="ev-text">{{ e.excerpt }}</text>
                            </view>
                        </view>
                    </view>

                    <!-- 论治链：方 → 穴 → 案 -->
                    <view class="rrow rchain" v-if="chainOf(r).length">
                        <text class="rkey">论治链</text>
                        <view class="chain-chips">
                            <text v-for="c in chainOf(r)" :key="c.key" class="chain-chip"
                                :class="'cc-' + c.kind" @tap="goChain(c)">
                                {{ c.icon }} {{ c.label }}
                            </text>
                        </view>
                    </view>

                    <view class="rgo" @tap="goSearch(r.name)">在全库检索「{{ r.name }}」原文论述 ›</view>
                </view>
            </view>

            <!-- 相近证型鉴别 -->
            <view v-if="compare" class="vs-card">
                <view class="vs-head">
                    <text class="vs-tag serif-font">鉴别</text>
                    <text class="vs-names">{{ compare.nameA }} ＆ {{ compare.nameB }}</text>
                </view>
                <text class="vs-text">{{ compare.text }}</text>
                <text class="vs-ref">{{ compare.refs }}</text>
            </view>

            <view class="notice foot-notice">
                <text class="notice-icon">⚠</text>
                <text class="notice-text">{{ rules.disclaimer || DEFAULT_DISCLAIMER }}</text>
            </view>
        </template>

        <!-- 舌脉速查 -->
        <view v-if="step === 'pick'" class="sec atlas-sec">
            <view class="sec-head" @tap="toggleAtlas">
                <text class="sec-title">👁 舌脉速查（10 舌 10 脉）</text>
                <text class="sec-op">{{ atlasOpen ? '收起' : '展开' }}</text>
            </view>
            <view v-show="atlasOpen">
                <view class="seg atlas-seg">
                    <text class="seg-item" :class="{ on: atlasTab === 'she' }" @tap="atlasTab = 'she'">舌象</text>
                    <text class="seg-item" :class="{ on: atlasTab === 'mai' }" @tap="atlasTab = 'mai'">脉象</text>
                </view>
                <view v-for="it in (atlasTab === 'she' ? atlas.tongue : atlas.pulse)" :key="it.term"
                    class="atlas-item" @tap="atlasGo(it)">
                    <view class="atlas-head">
                        <text class="atlas-term serif-font">{{ it.term }}</text>
                        <text class="atlas-src">{{ it.src }} ›</text>
                    </view>
                    <text class="atlas-desc">{{ it.desc }}</text>
                </view>
                <text class="atlas-tip">内容遵循传统教材描述，仅供学习参考。</text>
            </view>
        </view>

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
import { loadDiagRules, loadDeck, loadDiagAtlas, loadDiagQuiz } from '../../common/learn.js'
import { diagnose, symptomIndex, findVs, RED_FLAGS } from '../../common/diagnosis.js'
import { store, pending, pushDiagRecord, clearDiagHistory, pushDiagQuiz } from '../../common/store.js'
import { applyNavTheme } from '../../common/theme.js'

const DEFAULT_DISCLAIMER = '本功能仅供学习辨证思路参考，不能替代执业医师面诊，如有不适请及时就医。'

const rules = ref({ groups: [] })
const selected = reactive({})
const openGroups = reactive({})
const step = ref('pick')
const results = ref([])
const atlas = ref({ tongue: [], pulse: [] })
const symTip = {} // 舌/脉症状 id -> atlas 对照文字（长按查看）
const atlasOpen = ref(false)
const atlasTab = ref('she')
const compare = ref(null)
const history = computed(() => store.learn.diagHistory)
const night = ref(false)
const themeCls = computed(() => 'night-theme-' + (store.settings.nightTheme || 'warm'))
let idxMap = {}

onLoad(async () => {
    rules.value = await loadDiagRules()
    idxMap = symptomIndex(rules.value)
    // 默认展开前两组
    if (rules.value.groups[0]) openGroups[rules.value.groups[0].id] = true
    if (rules.value.groups[1]) openGroups[rules.value.groups[1].id] = true
    // 舌/脉 长按对照（atlas 术语 ↔ 症状标签 模糊映射）
    loadDiagAtlas()
        .then((data) => {
            atlas.value = data
            for (const g of rules.value.groups) {
                const pool = g.name === '舌象' ? data.tongue : g.name === '脉象' ? data.pulse : null
                if (!pool) continue
                for (const it of g.items) {
                    let best = null
                    let bs = 0
                    for (const e of pool) {
                        let s = 0
                        for (const ch of e.term.replace(/[·（）]/g, '')) if (it.label.includes(ch)) s += 1
                        for (const ch of it.label.replace(/[、·（）或有无之沉数细]/g, '')) if (e.term.includes(ch)) s += 0.5
                        if (s > bs) {
                            bs = s
                            best = e
                        }
                    }
                    if (best && bs >= 2) symTip[it.id] = `${best.term}：${best.desc}——${best.src}`
                }
            }
        })
        .catch(() => {})
})

// ---- 症状搜索 ----
const kw = ref('')
const kwHits = computed(() => {
    const k = kw.value.trim()
    if (!k) return []
    const out = []
    for (const g of rules.value.groups) {
        for (const it of g.items) {
            if (it.label.includes(k)) out.push({ ...it, gname: g.name })
            if (out.length >= 24) return out
        }
    }
    return out
})

// ---- 红旗急重症 ----
const redFlags = computed(() => RED_FLAGS.filter((f) => selected[f.id]))

function showAtlasTip(it) {
    if (!(it.id in symTip)) return
    uni.showModal({ title: it.label, content: symTip[it.id], showCancel: false, confirmText: '知道了' })
}

onShow(() => {
    night.value = applyNavTheme()
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

async function toggleAtlas() {
    atlasOpen.value = !atlasOpen.value
    if (atlasOpen.value && !atlas.value.tongue.length) {
        try {
            atlas.value = await loadDiagAtlas()
        } catch (e) { /* 忽略 */ }
    }
}

// 速查词条 → 全库检索教材原文
function atlasGo(it) {
    uni.setStorageSync('pendingQuery', it.term.replace(/[（(].*/, ''))
    pending.keyword = it.term.replace(/[（(].*/, '')
    uni.switchTab({ url: '/pages/search/search' })
}

function clearAll() {
    for (const k of Object.keys(selected)) delete selected[k]
}

function run() {
    const out = diagnose(Object.keys(selected), rules.value, 4)
    results.value = out.map((r) => reactive({ ...r, _open: false }))
    if (results.value.length) results.value[0]._open = true
    // 异步构建论治链（方/穴/案），完成后页面自动刷新
    for (const r of results.value) {
        buildChain(r)
    }
    // 前两名接近（分差<15%）且有人工鉴别要点时，给出鉴别提示
    compare.value = null
    if (out.length >= 2 && out[0].pct - out[1].pct < 15) {
        const v = findVs(rules.value, out[0].id, out[1].id)
        if (v) compare.value = { text: v.text, refs: v.refs || '', nameA: out[0].name, nameB: out[1].name }
    }
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

// ---- 医案辨证（看案选证）----
const caseQueue = ref([])
const casePos = ref(0)
const caseOk = ref(0)
const casePicked = ref('')
const caseDone = ref(false)
const caseCur = computed(() => caseQueue.value[casePos.value] || {})
const caseTotal = computed(() => caseQueue.value.length || 10)
const dqAcc = computed(() => {
    const d = store.learn.diagQuiz || { done: 0, ok: 0 }
    return `${d.ok}/${d.done}`
})

async function startCase() {
    const quiz = await loadDiagQuiz()
    const arr = quiz.items.slice()
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        const t = arr[i]
        arr[i] = arr[j]
        arr[j] = t
    }
    caseQueue.value = arr.slice(0, 10)
    casePos.value = 0
    caseOk.value = 0
    casePicked.value = ''
    caseDone.value = false
    step.value = 'case'
    uni.pageScrollTo({ scrollTop: 0, duration: 0 })
}

function pickCase(c) {
    if (casePicked.value) return
    casePicked.value = c
    const ok = c === caseCur.value.an
    if (ok) caseOk.value++
    pushDiagQuiz(ok)
}

function nextCase() {
    if (casePos.value + 1 >= caseQueue.value.length) {
        caseDone.value = true
        return
    }
    casePos.value++
    casePicked.value = ''
    uni.pageScrollTo({ scrollTop: 0, duration: 0 })
}

// ---- 诊疗依据跳转 ----
function goEvidence(e) {
    uni.navigateTo({ url: `/pages/reader/reader?slug=${e.slug}&g=${e.g}` })
}

// ---- 论治链 chips（方/穴/案 三联一键直达） ----
let pointMap = null
let yianByUuid = null

function chainOf(r) {
    // 模板同步渲染：读取预构建的缓存
    return r._chain || []
}

async function buildChain(r) {
    const out = []
    // 方
    if (r.fang) {
        out.push({ kind: 'fang', icon: '📜', label: '代表方 ' + String(r.fang).split(/[，、；;]/)[0], r, key: 'fang' })
    }
    // 穴
    if (!pointMap) {
        pointMap = {}
        for (const c of await loadDeck('point')) pointMap[c.front] = c.meta?.uuid
    }
    const pts = String(r.points || '').split(/[、，，]/).map((x) => x.trim()).filter(Boolean).slice(0, 3)
    for (const pn of pts) {
        const u = pointMap[pn]
        if (u) out.push({ kind: 'point', icon: '📍', label: pn, uuid: u, key: 'p' + u })
    }
    // 案
    if (!yianByUuid) {
        yianByUuid = {}
        for (const c of await loadDeck('yian')) yianByUuid[c.meta?.uuid] = c
    }
    for (const mu of (r.med || []).slice(0, 2)) {
        const c = yianByUuid[mu]
        if (c) out.push({ kind: 'yian', icon: '📖', label: c.front.replace(/案$/, ''), uuid: mu, key: 'y' + mu })
    }
    r._chain = out
}

function goChain(c) {
    if (c.kind === 'fang') return goFang(c.r)
    if (c.kind === 'point') return uni.navigateTo({ url: `/pages/cards/cards?deck=point&focus=${encodeURIComponent(c.uuid)}` })
    if (c.kind === 'yian') return uni.navigateTo({ url: `/pages/cards/cards?deck=yian&focus=${encodeURIComponent(c.uuid)}` })
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

.chip.hot {
    border-color: rgba(139, 58, 58, 0.35);
}

.hot-dot {
    font-size: 18rpx;
    color: #b3543f;
    margin-left: 4rpx;
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


.atlas-sec { margin-top: 28rpx; }
.atlas-seg { margin-bottom: 16rpx; }
.atlas-item {
    background: #fffdf5;
    border-radius: 14rpx;
    padding: 20rpx 24rpx;
    margin-bottom: 14rpx;
    border: 1px solid rgba(139, 58, 58, 0.06);
}
.atlas-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 8rpx;
}
.atlas-term { font-size: 28rpx; color: #5c2018; }
.atlas-src { font-size: 20rpx; color: #a0916e; }
.atlas-desc { font-size: 25rpx; color: #5c5646; line-height: 1.7; }
.atlas-tip { font-size: 21rpx; color: #a0916e; }
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

.ev-list {
    display: flex;
    flex-direction: column;
    gap: 12rpx;
}

.ev-item {
    background: rgba(139, 58, 58, 0.05);
    border-left: 4rpx solid var(--accent, #8b3a3a);
    border-radius: 10rpx;
    padding: 14rpx 18rpx;
}

.ev-head {
    display: flex;
    align-items: baseline;
    gap: 10rpx;
    flex-wrap: wrap;
    margin-bottom: 6rpx;
}

.ev-book { font-size: 22rpx; color: var(--accent, #8b3a3a); font-weight: 600; }
.ev-path { font-size: 20rpx; color: #a0916e; flex: 1; }
.ev-go { font-size: 20rpx; color: var(--accent, #8b3a3a); }
.ev-text { font-size: 24rpx; color: #5c5646; line-height: 1.7; }

.chain-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 12rpx;
}

.chain-chip {
    font-size: 23rpx;
    border-radius: 999rpx;
    padding: 8rpx 20rpx;
    background: rgba(74, 124, 89, 0.1);
    color: #3d6248;
}
.chain-chip.cc-fang { background: rgba(139, 58, 58, 0.09); color: #8b3a3a; }
.chain-chip.cc-yian { background: rgba(42, 74, 98, 0.1); color: #2a4a62; }

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

.vs-card {
    background: linear-gradient(160deg, #6b2a20, #451611);
    border-radius: 20rpx;
    padding: 28rpx 26rpx;
    margin-bottom: 20rpx;
}

.vs-head {
    display: flex;
    align-items: center;
    gap: 16rpx;
    margin-bottom: 14rpx;
}

.vs-tag {
    background: rgba(243, 233, 210, 0.18);
    color: #f3e9d2;
    font-size: 22rpx;
    border-radius: 8rpx;
    padding: 4rpx 14rpx;
}

.vs-names {
    color: #f3e9d2;
    font-size: 26rpx;
    font-weight: 600;
}

.vs-text {
    display: block;
    color: rgba(243, 233, 210, 0.9);
    font-size: 25rpx;
    line-height: 1.8;
}

.vs-ref {
    display: block;
    margin-top: 12rpx;
    color: rgba(243, 233, 210, 0.5);
    font-size: 21rpx;
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

.qtag {
    font-size: 22rpx;
    color: #b09a77;
}

/* ---- 红旗急重症 ---- */
.redflag {
    display: flex;
    align-items: flex-start;
    gap: 12rpx;
    background: #fdeceb;
    border: 2rpx solid #e8a09a;
    border-radius: 14rpx;
    padding: 18rpx 22rpx;
    margin-bottom: 20rpx;
}

.redflag-icon { font-size: 30rpx; color: #b5242a; }

.redflag-text { font-size: 24rpx; color: #7c2f26; line-height: 1.6; flex: 1; }
.redflag-bold { color: #b5242a; font-weight: 700; }

/* ---- 症状搜索 ---- */
.symbar {
    margin-bottom: 14rpx;
}

.sym-input {
    background: #fffdf7;
    border: 2rpx solid #e4dcc8;
    border-radius: 14rpx;
    padding: 14rpx 22rpx;
    font-size: 26rpx;
    color: #3a3226;
    height: 66rpx;
}

.search-hits { margin-bottom: 20rpx; }
.chip-g { color: #b9ac92; font-size: 21rpx; }
.search-empty { font-size: 24rpx; color: #8d8371; padding: 16rpx 6rpx; }

.chip.tip { border-style: dashed; }

/* ---- 医案辨证入口 ---- */
.case-entry {
    margin-top: 22rpx;
    background: #fffdf7;
    border: 2rpx solid #e4dcc8;
    border-radius: 18rpx;
    padding: 24rpx 26rpx;
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
}

.ce-in { font-size: 30rpx; color: #5c2018; font-weight: 700; }
.ce-desc { font-size: 22rpx; color: #8d8371; margin-top: 6rpx; }
.ce-op { font-size: 26rpx; color: #8b3a3a; }
.ce-acc { font-size: 21rpx; color: #a39880; text-align: right; margin-top: 8rpx; display: block; }

/* ---- 医案辨证做题 ---- */
.case-round { font-size: 26rpx; color: #8b3a3a; }

.case-card {
    background: #fffdf7;
    border: 2rpx solid #e4dcc8;
    border-radius: 20rpx;
    padding: 26rpx 26rpx 20rpx;
    display: flex;
    flex-direction: column;
}

.case-qtag-row {
    flex-direction: row;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12rpx;
}

.case-seq { font-size: 24rpx; color: #a39880; }

.case-scroll { max-height: 46vh; }

.case-text { font-size: 29rpx; line-height: 1.95; color: #3a3226; }

.case-choices { margin-top: 22rpx; display: flex; flex-direction: column; gap: 14rpx; }

.case-choice {
    border: 2rpx solid #e4dcc8;
    border-radius: 14rpx;
    padding: 18rpx 22rpx;
    flex-direction: row;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.case-choice.right { border-color: #4a8c5c; background: rgba(74, 140, 92, 0.1); }
.case-choice.wrong { border-color: #c45454; background: rgba(196, 84, 84, 0.08); }

.case-choice-t { font-size: 27rpx; color: #3a3226; }
.case-mark { font-size: 23rpx; color: #4a8c5c; }
.case-mark.bad { color: #c45454; }

.case-foot { margin-top: 22rpx; display: flex; justify-content: center; }
.case-hint { font-size: 22rpx; color: #a39880; }
.case-next { width: 100%; }

.case-mask {
    position: fixed;
    inset: 0;
    background: rgba(36, 24, 18, 0.55);
    z-index: 60;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40rpx;
}

.case-over {
    width: 100%;
    background: #fdfaf3;
    border-radius: 24rpx;
    padding: 44rpx 34rpx 34rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.co-title { font-size: 26rpx; color: #8d8371; letter-spacing: 10rpx; }
.co-score { font-size: 92rpx; color: #5c2018; font-weight: 700; margin-top: 10rpx; }
.co-line { font-size: 25rpx; color: #6b5d4f; margin-top: 8rpx; }

.co-btns { flex-direction: row; display: flex; gap: 20rpx; margin-top: 30rpx; }

.co-btn { font-size: 27rpx; border-radius: 14rpx; padding: 16rpx 36rpx; }
.co-btn.ghost { border: 1rpx solid #c9bfa8; color: #8d8371; }
.co-btn.solid { background: #8b3a3a; color: #f3e9d2; }
</style>
