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
    bookmarks: []
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
export const pending = reactive({ keyword: '' })
