// 全局状态：阅读设置、进度、历史、书签（localStorage 持久化）
import { reactive, watch } from 'vue'
import { debounce } from './util.js'

const KEY = 'gmzy-store-v1'

const defaults = {
    // 阅读器设置
    settings: {
        fontSize: 19,        // px
        lineHeight: 1.8,
        theme: 'paper',      // paper | night | eye（阅读器内）
        serif: true,
        night: false         // 全局夜间模式
    },
    // 每本书的阅读进度: { slug: { chIdx, scrollTop, gIdx, percent, ts } }
    progress: {},
    // 最近阅读历史: [{ slug, title, chapter, gIdx, chIdx, scrollTop, percent, ts, cover }]
    history: [],
    // 书签: [{ slug, title, chapter, gIdx, chIdx, scrollTop, excerpt, ts }]
    bookmarks: [],
    // 学习系统
    learn: {
        // key 方案版本：1=索引键（旧），2=uuid 稳定键
        keyV: 2,
        // 记忆卡状态: { 'fangji:827d96bd': {lv,n,ef,ivl,next} }
        cardMastery: {},
        // 题库进度: { 'q0.json': { 'q:xxxx': 1会 | 2不会 } }
        quizDone: {},
        // 每日新卡计数: { '2026-09-01': { fangji: 12 } }
        newDaily: {},
        // 每日活跃: { '2026-09-01': { cards: 10, quiz: 5, done: 1 } }
        activity: {},
        // 辨证记录: [{ ts, symptoms: [label...], top: { name, pct }, count }]
        diagHistory: []
    }
}

function loadInitial() {
    const init = JSON.parse(JSON.stringify(defaults))
    try {
        const raw = uni.getStorageSync(KEY)
        if (raw) {
            const saved = typeof raw === 'string' ? JSON.parse(raw) : raw
            if (saved.settings) Object.assign(init.settings, saved.settings)
            if (saved.progress) init.progress = saved.progress
            if (Array.isArray(saved.history)) init.history = saved.history
            if (Array.isArray(saved.bookmarks)) init.bookmarks = saved.bookmarks
            if (saved.learn) {
                const L = saved.learn
                init.learn.keyV = L.keyV || 1
                if (L.cardMastery) init.learn.cardMastery = L.cardMastery
                if (L.quizDone) init.learn.quizDone = L.quizDone
                if (L.newDaily) init.learn.newDaily = L.newDaily
                if (L.activity) init.learn.activity = L.activity
                if (Array.isArray(L.diagHistory)) init.learn.diagHistory = L.diagHistory
            }
        }
    } catch (e) {
        console.warn('读取本地状态失败', e)
    }
    return init
}

export const store = reactive(loadInitial())

const persist = debounce(() => {
    try {
        uni.setStorageSync(KEY, JSON.stringify(store))
    } catch (e) {
        console.warn('保存本地状态失败', e)
    }
}, 400)

watch(store, persist, { deep: true })

// ---- 进度 ----
export function saveProgress(slug, info) {
    store.progress[slug] = Object.assign({}, store.progress[slug], info, { ts: Date.now() })
}

// ---- 历史 ----
export function pushHistory(entry) {
    const arr = store.history
    const i = arr.findIndex((x) => x.slug === entry.slug)
    if (i >= 0) arr.splice(i, 1)
    arr.unshift(Object.assign({ ts: Date.now() }, entry))
    if (arr.length > 60) arr.length = 60
}

export function removeHistory(slug) {
    const i = store.history.findIndex((x) => x.slug === slug)
    if (i >= 0) store.history.splice(i, 1)
}

export function clearHistory() {
    store.history = []
}

// ---- 书签 ----
export function addBookmark(entry) {
    const dup = store.bookmarks.some(
        (x) => x.slug === entry.slug && x.gIdx === entry.gIdx
    )
    if (dup) return false
    store.bookmarks.unshift(Object.assign({ ts: Date.now() }, entry))
    return true
}

export function removeBookmark(idx) {
    store.bookmarks.splice(idx, 1)
}

export function clearBookmarks() {
    store.bookmarks = []
}

// ---- 搜索暂存（tabBar 跳页不能带参数）----
export const pending = reactive({ keyword: '', diagSymptoms: null })

// ================= 学习系统 =================

function todayStr() {
    const d = new Date()
    const p = (n) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

function bumpActivity(kind) {
    const t = todayStr()
    if (!store.learn.activity[t]) store.learn.activity[t] = { cards: 0, quiz: 0, done: 0 }
    const a = store.learn.activity[t]
    a[kind] = (a[kind] || 0) + 1
}

// ---- 记忆卡（SM-2 间隔重复，uuid 稳定键） ----
// 卡片状态: { lv: 1|2|3, n: 连续答对次数, ef: 难度因子, ivl: 间隔天数, next: 到期时间戳 }
// keyV=2 起 key 为卡片数据内嵌 uuid（卡组增补不再错位）；旧索引键由 migrateLegacyLearn 迁移。
function cardState(uuid) {
    const v = store.learn.cardMastery[uuid]
    return v && typeof v === 'object' ? v : null
}

const DAY = 86400000

export function setCardMastery(uuid, level) {
    const prev = cardState(uuid) || { lv: 0, n: 0, ef: 2.5, ivl: 0, next: 0 }
    const q = level === 3 ? 5 : level === 2 ? 3 : 1
    let { n, ef, ivl } = prev
    const now = Date.now()
    const isNew = !prev.lv
    if (q < 3) {
        n = 0
        ivl = 0
        const next = level === 1 ? now + 30 * 60000 : now + DAY
        ef = Math.max(1.3, ef - 0.2)
        store.learn.cardMastery[uuid] = { lv: level, n, ef, ivl, next }
    } else {
        n += 1
        ivl = n === 1 ? 1 : n === 2 ? 3 : Math.max(4, Math.round(ivl * ef))
        ef = Math.max(1.3, ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
        store.learn.cardMastery[uuid] = { lv: level, n, ef, ivl, next: now + ivl * DAY }
    }
    if (isNew) markNewCardUsed(uuid)
    bumpActivity('cards')
}

export function cardMasteryOf(uuid) {
    const s = cardState(uuid)
    return s ? s.lv : 0
}

export function cardStateRef(uuid) {
    return cardState(uuid)
}

export function isCardDue(uuid, now = Date.now()) {
    const s = cardState(uuid)
    return !!s && s.next <= now
}

// 卡包统计: { mastered, fuzzy, unknown, done, due }（按 uuid 前缀扫描，卡组变化不受影响）
export function deckStats(deckId, total) {
    const now = Date.now()
    const s = { mastered: 0, fuzzy: 0, unknown: 0, done: 0, due: 0 }
    const prefix = deckId + ':'
    for (const k of Object.keys(store.learn.cardMastery)) {
        if (!k.startsWith(prefix)) continue
        const st = store.learn.cardMastery[k]
        if (!st || typeof st !== 'object') continue
        s.done++
        if (st.lv === 3) s.mastered++
        else if (st.lv === 2) s.fuzzy++
        else if (st.lv === 1) s.unknown++
        if (st.next <= now) s.due++
    }
    return s
}

// 到期卡片 uuid（先到期先排，其次按 lv 升序——不认识的排前）
export function dueCardUuids(deckId) {
    const now = Date.now()
    const arr = []
    const prefix = deckId + ':'
    for (const k of Object.keys(store.learn.cardMastery)) {
        if (!k.startsWith(prefix)) continue
        const st = store.learn.cardMastery[k]
        if (st && typeof st === 'object' && st.next <= now) arr.push([k, st])
    }
    arr.sort((a, b) => a[1].lv - b[1].lv || a[1].next - b[1].next)
    return arr.map((x) => x[0])
}

export function resetDeck(deckId) {
    const m = store.learn.cardMastery
    const prefix = deckId + ':'
    for (const k of Object.keys(m)) if (k.startsWith(prefix)) delete m[k]
}

// ---- 每日新卡配额 ----
export function newPerDayLimit() {
    return store.settings.newPerDay || 20
}

export function newTodayCount(deckId) {
    const t = todayStr()
    return (store.learn.newDaily?.[t] || {})[deckId] || 0
}

export function quotaRemaining(deckId) {
    return Math.max(0, newPerDayLimit() - newTodayCount(deckId))
}

export function markNewCardUsed(uuid) {
    if (!store.learn.newDaily) store.learn.newDaily = {}
    const t = todayStr()
    if (!store.learn.newDaily[t]) store.learn.newDaily[t] = {}
    const deck = uuid.split(':')[0]
    store.learn.newDaily[t][deck] = (store.learn.newDaily[t][deck] || 0) + 1
}

// ---- 题库 ----
export function setQuizAnswer(bookSlug, qIdx, ok) {
    if (!store.learn.quizDone[bookSlug]) store.learn.quizDone[bookSlug] = {}
    store.learn.quizDone[bookSlug][qIdx] = ok ? 1 : 2
    bumpActivity('quiz')
}

export function quizStatsOf(bookSlug, total) {
    const done = store.learn.quizDone[bookSlug] || {}
    let know = 0
    let dont = 0
    for (const k of Object.keys(done)) {
        if (done[k] === 1) know++
        else if (done[k] === 2) dont++
    }
    return { know, dont, done: know + dont, total }
}

export function resetQuiz(bookSlug) {
    delete store.learn.quizDone[bookSlug]
}

// ---- 辨证记录 ----
export function pushDiagRecord(rec) {
    const arr = store.learn.diagHistory
    arr.unshift(Object.assign({ ts: Date.now() }, rec))
    if (arr.length > 30) arr.length = 30
    bumpActivity('done')
}

export function clearDiagHistory() {
    store.learn.diagHistory = []
}

// ---- 学习总览 ----
export function learnOverview() {
    const act = store.learn.activity || {}
    const days = Object.keys(act)
    let cards = 0
    let quiz = 0
    for (const d of days) {
        cards += act[d].cards || 0
        quiz += act[d].quiz || 0
    }
    const t = todayStr()
    const today = act[t] || { cards: 0, quiz: 0 }
    return {
        cards,
        quiz,
        activeDays: days.length,
        diagCount: store.learn.diagHistory.length,
        todayCards: today.cards || 0,
        todayQuiz: today.quiz || 0,
        streak: streakDays()
    }
}

export function streakDays() {
    const act = store.learn.activity || {}
    let cur = new Date()
    // 今天还没学：允许从昨天起算
    const pad = (n) => String(n).padStart(2, '0')
    const key = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
    let streak = 0
    if (!act[key(cur)]) cur = new Date(cur.getTime() - DAY)
    while (act[key(cur)]) {
        streak++
        cur = new Date(cur.getTime() - DAY)
    }
    return streak
}

// 近 7 日学习量（含今天），用于柱状图
export function weekSeries() {
    const act = store.learn.activity || {}
    const out = []
    for (let i = 6; i >= 0; i--) {
        const d = new Date(Date.now() - i * DAY)
        const p = (n) => String(n).padStart(2, '0')
        const k = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
        const a = act[k] || {}
        out.push({
            day: i === 0 ? '今' : `${d.getMonth() + 1}/${d.getDate()}`,
            cards: a.cards || 0,
            quiz: a.quiz || 0
        })
    }
    return out
}

// 全部卡包到期总数
export function totalDue(decks) {
    return decks.reduce((s, d) => s + deckStats(d.id, d.count).due, 0)
}

// ---- 全局外观 ----
export function setNight(on) {
    store.settings.night = !!on
}

// ================= 数据备份 / 恢复 =================

export function backupBundle() {
    return JSON.stringify({
        app: 'gmzy',
        v: 2,
        ts: Date.now(),
        settings: store.settings,
        progress: store.progress,
        history: store.history,
        bookmarks: store.bookmarks,
        learn: store.learn
    })
}

// 导入校验：字段齐全才覆盖；返回错误信息或 null
export function restoreBundle(jsonText) {
    let obj
    try {
        obj = JSON.parse(jsonText)
    } catch (e) {
        return '备份文件解析失败'
    }
    if (!obj || obj.app !== 'gmzy' || !obj.learn) return '不是有效的备份文件'
    if (obj.settings) Object.assign(store.settings, obj.settings)
    if (obj.progress) store.progress = obj.progress
    if (Array.isArray(obj.history)) store.history = obj.history
    if (Array.isArray(obj.bookmarks)) store.bookmarks = obj.bookmarks
    if (obj.learn) {
        store.learn = Object.assign(store.learn, obj.learn)
    }
    // 立即持久化（跳过 debounce）
    try {
        uni.setStorageSync(KEY, JSON.stringify(store))
    } catch (e) { /* 忽略 */ }
    return null
}

// 检测并存在旧索引键（迁移由 common/learn.js 的 migrateLegacyLearn 完成）
export function hasLegacyKeys() {
    if (store.learn.keyV === 2) return false
    for (const k of Object.keys(store.learn.cardMastery)) {
        if (/^[a-z]+_\d+$/.test(k)) return true
    }
    for (const k of Object.keys(store.learn.quizDone)) {
        if (!/^q\d+\.json$/.test(k)) return true
    }
    return false
}

export function markMigrated() {
    store.learn.keyV = 2
}

export function isNight() {
    return !!store.settings.night
}
