// 全局状态：阅读设置、进度、历史、书签（localStorage 持久化）
import { reactive, watch } from 'vue'
import { debounce } from './util.js'

const KEY = 'gmzy-store-v1'

const defaults = {
    // 阅读器设置
    settings: {
        fontSize: 19,        // px
        lineHeight: 1.8,
        theme: 'paper',      // paper | night | eye
        serif: true
    },
    // 每本书的阅读进度: { slug: { chIdx, scrollTop, gIdx, percent, ts } }
    progress: {},
    // 最近阅读历史: [{ slug, title, chapter, gIdx, chIdx, scrollTop, percent, ts, cover }]
    history: [],
    // 书签: [{ slug, title, chapter, gIdx, chIdx, scrollTop, excerpt, ts }]
    bookmarks: [],
    // 学习系统
    learn: {
        // 记忆卡掌握度: { 'fangji_3': 2 }  0未学 1不认识 2模糊 3已掌握
        cardMastery: {},
        // 题库进度: { bookSlug: { [题号]: 1会 | 2不会 } }
        quizDone: {},
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
                if (L.cardMastery) init.learn.cardMastery = L.cardMastery
                if (L.quizDone) init.learn.quizDone = L.quizDone
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

// ---- 记忆卡掌握度 ----
export function setCardMastery(deckId, cardIdx, level) {
    store.learn.cardMastery[deckId + '_' + cardIdx] = level
    bumpActivity('cards')
}

export function cardMasteryOf(deckId, cardIdx) {
    return store.learn.cardMastery[deckId + '_' + cardIdx] || 0
}

// 卡包统计: 返回 { mastered, fuzzy, unknown, done }
export function deckStats(deckId, total) {
    const m = store.learn.cardMastery
    const s = { mastered: 0, fuzzy: 0, unknown: 0, done: 0 }
    for (let i = 0; i < total; i++) {
        const v = m[deckId + '_' + i]
        if (v === 3) s.mastered++
        else if (v === 2) s.fuzzy++
        else if (v === 1) s.unknown++
        if (v) s.done++
    }
    return s
}

export function resetDeck(deckId, total) {
    const m = store.learn.cardMastery
    for (let i = 0; i < total; i++) delete m[deckId + '_' + i]
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
    return {
        cards,
        quiz,
        activeDays: days.length,
        diagCount: store.learn.diagHistory.length
    }
}
