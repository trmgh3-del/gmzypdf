<template>
    <view class="stats-page" :class="{ night, elder: store.settings.elder, [themeCls]: night }">
        <!-- 总览 -->
        <view class="hero">
            <view class="hero-block serif-font">{{ totals.studyDays }}</view>
            <text class="hero-label">学习天数</text>
            <view class="hero-div" />
            <view class="hero-block serif-font">{{ totals.answers }}</view>
            <text class="hero-label">背卡+答题</text>
            <view class="hero-div" />
            <view class="hero-block serif-font">{{ totals.quizLeft }}</view>
            <text class="hero-label">未答题目</text>
        </view>

        <!-- 各卡包掌握度 -->
        <view class="sec">
            <text class="sec-title">各卡包掌握度</text>
            <view v-for="d in decks" :key="d.id" class="row">
                <text class="row-name">{{ d.name }}</text>
                <view class="row-bar">
                    <view class="row-fill" :style="{ width: masterPct(d) + '%' }" />
                </view>
                <text class="row-pct">{{ masterPct(d) }}%</text>
            </view>
        </view>

        <!-- 辨证画像 -->
        <view class="sec portrait">
            <view class="sec-head">
                <text class="sec-title">我的辨证画像</text>
                <text class="sec-op">{{ diagHistory.length }} 次记录</text>
            </view>
            <view v-if="!diagHistory.length" class="empty">还没有辨证记录，去辨证页体验一次吧</view>
            <template v-else>
                <view class="pt-block">
                    <text class="pt-key">近期常反映症状</text>
                    <view class="chips">
                        <text v-for="s_ in topSymptoms" :key="s_" class="chip on">{{ s_ }}</text>
                    </view>
                </view>
                <view class="pt-block">
                    <text class="pt-key">最常匹配证型</text>
                    <view v-for="t in topSyndromes" :key="t.name" class="pt-row">
                        <text class="pt-name">{{ t.name }}</text>
                        <text class="pt-n">{{ t.n }} 次</text>
                    </view>
                </view>
                <text class="pt-note">
                    提示：常组团出现的症状组合，就是你体质倾向的教材侧写。仅供学习参考。
                </text>
            </template>
        </view>

        <!-- 错题命中率 -->
        <view class="sec">
            <text class="sec-title">答题效度</text>
            <view class="acc-grid">
                <view class="acc-cell">
                    <text class="acc-num serif-font">{{ accKnow }}</text>
                    <text class="acc-label">已掌握</text>
                </view>
                <view class="acc-cell">
                    <text class="acc-num mid serif-font">{{ accWeak }}</text>
                    <text class="acc-label">待巩固</text>
                </view>
                <view class="acc-cell">
                    <text class="acc-num serif-font">{{ accRate }}%</text>
                    <text class="acc-label">正确率</text>
                </view>
                <view class="acc-cell">
                    <text class="acc-num serif-font">{{ errLeft }}</text>
                    <text class="acc-label">错题待练</text>
                </view>
            </view>
        </view>

        <!-- 模考战绩 -->
        <view class="sec" v-if="mocks.length">
            <view class="sec-head-row">
                <text class="sec-title">模考战绩</text>
                <text class="mk-sub">共 {{ mocks.length }} 场 · 场均 {{ mockAvg }}% · 最佳 {{ mockBest }}%</text>
            </view>
            <view class="mk-chart">
                <view v-for="m in mocksChart" :key="m.t" class="mk-col">
                    <text class="mk-col-v">{{ m.acc }}</text>
                    <view class="mk-col-bar serif-font" :style="{ height: m.h + 'rpx' }" />
                    <text class="mk-col-d">{{ m.d }}</text>
                </view>
            </view>
            <text class="hm-legend">近 {{ mocksChart.length }} 场答出率（柱上所标为百分数）</text>
        </view>

        <!-- 近 30 日学习热力 -->
        <!-- 本周奏报（7 日热图 + 拟签） -->
        <view class="sec weekly">
            <view class="sec-head">
                <text class="sec-title">📜 本周奏报</text>
                <text class="sec-op" @tap="copyWeekly">誊抄 ›</text>
            </view>
            <text class="wk-range serif-font">{{ wkRange }}</text>
            <view class="wk-heat">
                <view v-for="d in wkHeat" :key="d.day" class="wk-cell" :class="{ zero: !d.n }" :style="{ opacity: wkOpacity(d.n) }">
                    <text class="wk-dd">{{ d.wd }}</text>
                    <text class="wk-n">{{ d.n || '·' }}</text>
                </view>
            </view>
            <view class="wk-totals">
                <text class="wk-t">记卡 {{ wk.cards }} · 研题 {{ wk.quiz }} · 辨证 {{ wk.done }} · 元气 +{{ wk.yuanqi }}</text>
            </view>
            <view class="wk-note">
                <text class="wk-note-body serif-font">{{ wkNote }}</text>
            </view>
        </view>

        <view class="sec">
            <text class="sec-title">近 30 日学习热力</text>
            <view class="heatmap">
                <view v-for="d in heat" :key="d.day" class="hm-cell" :data-n="d.n" :style="{ opacity: hmOpacity(d.n) }"
                    >{{ d.dd }}</view>
            </view>
            <text class="hm-legend">越亮 = 学得越多</text>
        </view>
    </view>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { loadDecks, loadQuizIndex } from '../../common/learn.js'
import { store, deckStats, quizStatsOf, gqRank, wenguList } from '../../common/store.js'
import { applyNavTheme } from '../../common/theme.js'

const decks = ref([])
const quizIdx = ref([])
const night = computed(() => store.settings.night)
const themeCls = computed(() => 'night-theme-' + (store.settings.nightTheme || 'warm'))
const totals = reactive({ studyDays: 0, answers: 0, quizLeft: 0 })

onShow(() => applyNavTheme())

onLoad(async () => {
    uni.setNavigationBarTitle({ title: '学习总览' })
    ;[decks.value, quizIdx.value] = await Promise.all([loadDecks(), loadQuizIndex()])
    // 学习天数 & 总动作量
    const act = store.learn.activity
    totals.studyDays = Object.values(act).filter((a) => (a.cards || 0) + (a.quiz || 0) + (a.done || 0) + (a.kg || 0) > 0).length
    totals.answers = Object.values(act).reduce((s, a) => s + (a.cards || 0) + (a.quiz || 0), 0)
    totals.quizLeft = quizIdx.value.reduce((s, b) => {
        const done = store.learn.quizDone[b.f] || {}
        return s + (b.count - Object.keys(done).length)
    }, 0)
    // 错题数
    let k = 0
    let w = 0
    for (const b of quizIdx.value) {
        for (const v of Object.values(store.learn.quizDone[b.f] || {})) {
            if (v === 1) k++
            else if (v === 2) w++
        }
    }
    accKnow.value = k
    accWeak.value = w
    errLeft.value = Object.values(store.learn.qErr || {}).reduce(
        (s, errs) => s + Object.values(errs).filter((e) => e.m >= 2).length,
        0
    )
})

const accKnow = ref(0)
const accWeak = ref(0)
const errLeft = ref(0)
// ---- 模考战绩 ----
const mocks = computed(() => store.learn.mockHistory || [])
const mockAvg = computed(() => {
    if (!mocks.value.length) return 0
    const s = mocks.value.reduce((a, m) => a + (m.n ? m.k / m.n : 0), 0)
    return Math.round((s / mocks.value.length) * 100)
})
const mockBest = computed(() => Math.round(Math.max(0, ...mocks.value.map((m) => (m.n ? m.k / m.n : 0))) * 100))
const mocksChart = computed(() =>
    mocks.value
        .slice(0, 10)
        .reverse()
        .map((m) => {
            const acc = m.n ? Math.round((m.k / m.n) * 100) : 0
            const dt = new Date(m.t)
            return { t: m.t, acc, h: 12 + Math.round(acc * 1.1), d: `${dt.getMonth() + 1}/${dt.getDate()}` }
        })
)

const accRate = computed(() => {
    const t = accKnow.value + accWeak.value
    return t ? Math.round((accKnow.value / t) * 100) : 0
})

function masterPct(d) {
    const st = deckStats(d.id, d.count)
    return st.done ? Math.round((st.mastered / st.done) * 100) : 0
}

// ---- 辨证画像 ----
const diagHistory = computed(() => store.learn.diagHistory || [])
const topSymptoms = computed(() => {
    const cnt = {}
    for (const h of diagHistory.value.slice(0, 30)) {
        for (const s of h.symptoms || []) cnt[s] = (cnt[s] || 0) + 1
    }
    return Object.entries(cnt).sort((a, b) => b[1] - a[1]).slice(0, 6).map((x) => x[0])
})
const topSyndromes = computed(() => {
    const cnt = {}
    for (const h of diagHistory.value) {
        const nm = h.top?.name
        if (nm) cnt[nm] = (cnt[nm] || 0) + 1
    }
    return Object.entries(cnt).map(([name, n]) => ({ name, n })).sort((a, b) => b.n - a.n).slice(0, 5)
})

// ---- 30 日热力 ----
const heat = computed(() => {
    const out = []
    const now = Date.now()
    for (let i = 29; i >= 0; i--) {
        const d = new Date(now - i * 86400000)
        const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
        const a = store.learn.activity[key] || { cards: 0, quiz: 0, done: 0 }
        out.push({ day: key, dd: key.slice(8), n: (a.cards || 0) + (a.quiz || 0) + (a.done || 0) + (a.kg || 0) })
    }
    return out
})

function hmOpacity(n) {
    if (!n) return 0.18
    return Math.min(1, 0.28 + n / 26)
}

// ---- 本周奏报（近 7 日） ----
const WD = ['日', '一', '二', '三', '四', '五', '六']
function dayKey(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
const wkHeat = computed(() => {
    const out = []
    const now = Date.now()
    for (let i = 6; i >= 0; i--) {
        const d = new Date(now - i * 86400000)
        const key = dayKey(d)
        const a = store.learn.activity[key] || {}
        const n = (a.cards || 0) + (a.quiz || 0) + (a.done || 0) + (a.yuanqi || 0) + (a.kg || 0)
        out.push({ day: key, wd: i === 0 ? '今' : WD[d.getDay()], n })
    }
    return out
})
const wk = computed(() => {
    const s = { cards: 0, quiz: 0, done: 0, yuanqi: 0, days: 0 }
    const now = Date.now()
    for (let i = 6; i >= 0; i--) {
        const a = store.learn.activity[dayKey(new Date(now - i * 86400000))] || {}
        s.cards += a.cards || 0
        s.quiz += a.quiz || 0
        s.done += a.done || 0
        s.yuanqi += a.yuanqi || 0
        if ((a.cards || 0) + (a.quiz || 0) + (a.done || 0) + (a.yuanqi || 0) + (a.kg || 0) > 0) s.days++
    }
    return s
})
const wkRange = computed(() => {
    const a = wkHeat.value
    return `${a[0].day} — ${a[a.length - 1].day} · 共 ${wk.value.days} 日有状`
})
function wkOpacity(n) {
    if (!n) return 0.2
    return Math.min(1, 0.35 + n / 22)
}

const wkRank = computed(() => gqRank((store.learn.gqYuanqi || {}).energy || 0))
const wenguDueNow = computed(() => wenguList().filter((w) => w.dueIn === 0).length)

// 拟签：按实绩定制签语
const wkNote = computed(() => {
    const w = wk.value
    if (!w.cards && !w.quiz && !w.yuanqi && !w.done) {
        return '这一旬未曾起笔，书页积尘。不必正襟危坐——三五分钟亦行：图考开一局，或卡库校十张。'
    }
    const parts = []
    parts.push(`一旬七日，筋骨有状 ${w.days} 日，积元气 ${w.yuanqi} · 记卡 ${w.cards} 张 · 研题 ${w.quiz} 道`)
    const dom = [
        ['cards', w.cards, '温书勤谨，卡片为本'],
        ['quiz', w.quiz, '开卷攻题，笔耕不辍'],
        ['yuanqi', w.yuanqi, '勤考上进，元气见长']
    ].sort((a, b) => b[1] - a[1])[0]
    if (dom[1] > 0) parts.push(dom[2])
    parts.push(`今阶「${wkRank.value.name}」${wkRank.value.next ? `，下一阶尚差元气 ${wkRank.value.need}` : '，已至顶峰'}`)
    parts.push(wenguDueNow.value ? `温故席尚欠 ${wenguDueNow.value} 题到日，宜先还账再扬帆。` : '无待温之账，可放胆再闯。')
    return parts.join('；') + '。'
})

function weeklyText() {
    return [
        `📜 光明文库 · 本周奏报（${wkRange.value}）`,
        `段位：${wkRank.value.name}（元气 ${(store.learn.gqYuanqi || {}).energy || 0}）`,
        `周绩：记卡 ${wk.value.cards} · 研题 ${wk.value.quiz} · 辨证 ${wk.value.done} · 元气 +${wk.value.yuanqi}`,
        `拟签：${wkNote.value}`
    ].join('\n')
}

function copyWeekly() {
    uni.setClipboardData({
        data: weeklyText(),
        success: () => uni.showToast({ title: '奏报已誊抄', icon: 'none' })
    })
}
</script>

<style lang="scss" scoped>
.stats-page {
    min-height: 100vh;
    padding: 30rpx;
    background: #f6f1e5;
}

.hero {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 28rpx 30rpx;
    background: linear-gradient(135deg, #8b3a3a, #5c2018);
    border-radius: 20rpx;
    text-align: center;

    .hero-block { font-size: 44rpx; color: #f3e9d2; }
    .hero-label { font-size: 22rpx; color: rgba(243, 233, 210, 0.75); margin-top: 4rpx; }
    .hero-div { width: 1rpx; height: 52rpx; background: rgba(243, 233, 210, 0.2); }
}

.sec {
    margin-top: 28rpx;
    background: #fffdf5;
    border-radius: 18rpx;
    padding: 26rpx;
}

.sec-title { font-size: 27rpx; color: #5c5646; font-weight: 600; }
.sec-head-row { display: flex; flex-direction: row; align-items: baseline; justify-content: space-between; }
.mk-sub { font-size: 21rpx; color: #a39880; }
.mk-chart { flex-direction: row; display: flex; align-items: flex-end; justify-content: space-around; margin-top: 18rpx; }
.mk-col { display: flex; flex-direction: column; align-items: center; width: 58rpx; }
.mk-col-v { font-size: 19rpx; color: #8b3a3a; }
.mk-col-bar { width: 26rpx; min-height: 12rpx; border-radius: 8rpx 8rpx 0 0; background: linear-gradient(180deg, #8b3a3a, #b5735a); margin: 6rpx 0; }
.mk-col-d { font-size: 19rpx; color: #a39880; }

.row {
    display: flex;
    align-items: center;
    gap: 16rpx;
    margin-top: 16rpx;
}

.row-name { width: 132rpx; font-size: 25rpx; color: #5c5646; }

.row-bar { flex: 1; height: 14rpx; background: #eadfc4; border-radius: 7rpx; overflow: hidden; }
.row-fill { height: 100%; background: #8b3a3a; border-radius: 7rpx; }
.row-pct { width: 76rpx; text-align: right; font-size: 23rpx; color: #8a8070; }

.chips { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 12rpx; }

.pt-block { margin-top: 16rpx; }
.pt-key { font-size: 23rpx; color: #a0916e; }

.pt-row {
    display: flex;
    justify-content: space-between;
    padding: 10rpx 0;
    border-bottom: 1rpx dashed rgba(139, 58, 58, 0.12);
    font-size: 25rpx;
    color: #5c5646;
}

.pt-name { font-weight: 600; }
.pt-n { color: #8b3a3a; }
.pt-note { font-size: 20rpx; color: #a0916e; margin-top: 14rpx; display: block; }

.acc-grid { display: flex; gap: 14rpx; margin-top: 16rpx; }
.acc-cell {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6rpx;
    background: rgba(139, 58, 58, 0.06);
    border-radius: 14rpx;
    padding: 18rpx 0;
}
.acc-num { font-size: 36rpx; color: #8b3a3a; }
.acc-num.mid { color: #c8922f; }
.acc-label { font-size: 22rpx; color: #8a8070; }

/* 本周奏报 */
.weekly {
    background: linear-gradient(135deg, #fffdf5, #fbf2dd);
    border: 1px solid rgba(181, 147, 90, 0.5);
}

.wk-range {
    display: block;
    text-align: center;
    font-size: 22rpx;
    color: #a08c68;
    margin-bottom: 14rpx;
    letter-spacing: 2rpx;
}

.wk-heat {
    display: flex;
    gap: 10rpx;
    margin-bottom: 12rpx;
}

.wk-cell {
    flex: 1;
    height: 88rpx;
    background: #8b3a3a;
    border-radius: 12rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.wk-cell.zero {
    background: #d8ccb0;
}

.wk-dd {
    font-size: 20rpx;
    color: #f3e9d2;
}

.wk-n {
    font-size: 26rpx;
    color: #fffdf7;
    font-weight: 700;
}

.wk-cell.zero .wk-dd,
.wk-cell.zero .wk-n {
    color: #a08c68;
}

.wk-totals {
    margin: 4rpx 0 14rpx;
}

.wk-t {
    font-size: 22rpx;
    color: #6b5d4f;
}

.wk-note {
    border-top: 1px dashed rgba(181, 147, 90, 0.5);
    padding-top: 14rpx;
}

.wk-note-body {
    display: block;
    font-size: 25rpx;
    color: #5c2018;
    line-height: 1.9;
}

.heatmap {
    display: grid;
    grid-template-columns: repeat(10, 1fr);
    gap: 8rpx;
    margin-top: 16rpx;
}

.hm-cell {
    aspect-ratio: 1;
    background: #8b3a3a;
    color: #f3e9d2;
    font-size: 18rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6rpx;
}

.hm-legend { font-size: 20rpx; color: #a0916e; margin-top: 10rpx; display: block; }

.empty { font-size: 24rpx; color: #a0916e; padding: 20rpx 0; }
</style>
