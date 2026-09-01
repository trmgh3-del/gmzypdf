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
    return item.f // q<N>.json，唯一且全平台 ASCII 安全
}

export function loadQuizBook(key) {
    return cached(`static/quiz/${key}`)
}

// ---- 辨证规则 ----
export function loadDiagRules() {
    return cached('static/diag/rules.json')
}

// ---- 旧学习数据迁移（索引键 → uuid 稳定键） ----
// 检测由 store.hasLegacyKeys() 完成；映射表来自 static/learn/migrate-v1.json
// （由 tools/make_migrate_v1.py 用旧版数据生成）。
export async function migrateLegacyLearn(store, markMigrated) {
    try {
        const mig = await cached('static/learn/migrate-v1.json')
        const decks = await loadDecks()
        let moved = 0
        let lost = 0
        const now = Date.now()
        // ---- 卡片：旧 key = deck_index → 旧 front → 新 uuid ----
        for (const d of decks) {
            const oldFronts = (mig.decks || {})[d.id]
            if (!oldFronts) continue
            const cards = await loadDeck(d.id)
            // front → [新 uuid 按出现顺序]
            const frontMap = new Map()
            for (const c of cards) {
                const u = c.meta?.uuid
                if (!u) continue
                if (!frontMap.has(c.front)) frontMap.set(c.front, [])
                frontMap.get(c.front).push(u)
            }
            const seen = new Map() // front → 已用次数（迁移重名同序）
            for (const [k, v] of Object.entries(store.learn.cardMastery)) {
                const m = k.match(/^([a-z]+)_(\d+)$/)
                if (!m || m[1] !== d.id) continue
                const oldLv = typeof v === 'number' ? v : v.lv
                if (!oldLv) {
                    delete store.learn.cardMastery[k]
                    continue
                }
                const idx = +m[2]
                const front = oldFronts[idx]
                let uuid = null
                if (front) {
                    const occ = seen.get(front) || 0
                    seen.set(front, occ + 1)
                    const cands = frontMap.get(front) || []
                    uuid = cands[Math.min(occ, cands.length - 1)] || null
                }
                delete store.learn.cardMastery[k]
                if (uuid && !store.learn.cardMastery[uuid]) {
                    // 保守迁移：置为到期，进入复习队列重新熟悉
                    store.learn.cardMastery[uuid] = { lv: oldLv, n: oldLv === 3 ? 1 : 0, ef: 2.5, ivl: 0, next: now }
                    moved++
                } else if (!uuid) {
                    lost++
                }
            }
        }
        // ---- 题库：旧 key = slug+书名 → 新 q<N>.json；旧题 index → 题面精确匹配新 uuid ----
        const qidx = await loadQuizIndex()
        for (const [oldKey, done] of Object.entries(store.learn.quizDone)) {
            if (/^q\d+\.json$/.test(oldKey)) continue // 已是新键
            const migQ = (mig.quiz || {})[oldKey]
            const meta = qidx.find((b) => b.slug + b.book === oldKey)
            delete store.learn.quizDone[oldKey]
            if (!migQ || !meta) {
                lost++
                continue
            }
            const items = await loadQuizBook(meta.f)
            const textMap = new Map()
            items.forEach((it) => {
                if (!textMap.has(it.q)) textMap.set(it.q, [])
                textMap.get(it.q).push(it.u)
            })
            const seenT = new Map()
            for (const [idxStr, v] of Object.entries(done)) {
                const txt = migQ.qs[+idxStr]
                if (!txt) continue
                const occ = seenT.get(txt) || 0
                seenT.set(txt, occ + 1)
                const cands = textMap.get(txt) || []
                const u = cands[Math.min(occ, cands.length - 1)]
                if (!u) continue
                if (!store.learn.quizDone[meta.f]) store.learn.quizDone[meta.f] = {}
                store.learn.quizDone[meta.f][u] = v
                moved++
            }
        }
        markMigrated()
        return { moved, lost }
    } catch (e) {
        console.warn('学习数据迁移失败', e)
        markMigrated() // 避免反复重试；出错也不阻塞使用
        return { moved: 0, lost: -1 }
    }
}
