// 学习/辨证数据访问层
// 静态存放：static/learn/*.json（记忆卡）、static/quiz/*.json（题库）、static/diag/rules.json（辨证规则）
// 读取方式与 books.js 一致：App 端 plus.io，H5 端 fetch。

const cache = new Map()

// #ifdef APP-PLUS
function readTextFile(path) {
    return new Promise((resolve, reject) => {
        plus.io.resolveLocalFileSystemURL(
            '_www/' + path,
            (entry) => {
                entry.file(
                    (file) => {
                        const reader = new plus.io.FileReader()
                        reader.onloadend = (e) => resolve(e.target.result)
                        reader.onerror = (err) => reject(err)
                        reader.readAsText(file, 'utf-8')
                    },
                    reject
                )
            },
            reject
        )
    })
}

function readJson(path) {
    return readTextFile(path).then((t) => JSON.parse(t))
}
// #endif

// #ifdef H5
function readJson(path) {
    return fetch('/' + path).then((res) => {
        if (!res.ok) throw new Error('读取失败: ' + path)
        return res.json()
    })
}
// #endif

function cached(path) {
    if (!cache.has(path)) cache.set(path, readJson(path))
    return cache.get(path)
}

// ---- 记忆卡 ----
export function loadDecks() {
    return cached('static/learn/decks.json')
}

export function loadDeck(deckId) {
    return cached(`static/learn/deck-${deckId}.json`)
}

// ---- 题库 ----
export function loadQuizIndex() {
    return cached('static/quiz/index.json')
}

export function quizKey(item) {
    return item.slug + item.book
}

export function loadQuizBook(key) {
    return cached(`static/quiz/${encodeURIComponent(key)}.json`)
}

// ---- 辨证规则 ----
export function loadDiagRules() {
    return cached('static/diag/rules.json')
}
