// 词条内容索引：把 4 个记忆卡包的正名建成可查词典
// 懒加载，长按/点段查词时在原文段落中做最长词匹配。
import { loadDecks, loadDeck } from './learn.js'

let ready = null // Promise<Map<term, entry>> | null
// entry: { term, back, sub, deck, deckName, book, g }

const PRIORITY = { point: 0, fangji: 1, herb: 2, koujue: 3, bingz: 4 }

export function loadDict() {
    if (ready) return ready
    ready = (async () => {
        const decks = await loadDecks()
        const map = new Map()
        const lists = await Promise.all(decks.map((d) => loadDeck(d.id)))
        decks.forEach((d, di) => {
            for (const c of lists[di]) {
                // 病证卡 front=病·证，取病名做词条（至少3字才收，防误命中）
                let term = (c.front || '').trim()
                if (d.id === 'bingz') {
                    term = term.split('·')[0]
                    if (term.length < 3) continue
                } else if (term.length < 2 || term.length > 8) {
                    continue
                }
                const entry = {
                    term,
                    front: c.front,
                    back: c.back,
                    sub: c.sub,
                    deck: d.id,
                    deckName: d.name,
                    book: c.meta?.book || '',
                    g: c.meta?.g,
                    uuid: c.meta?.uuid || ''
                }
                const old = map.get(term)
                if (!old || PRIORITY[d.id] < PRIORITY[old.deck]) map.set(term, entry)
            }
        })
        return map
    })()
    return ready
}

// 在一段原文中找命中的词条（最长优先、去重、限量）
export async function findTerms(text, limit = 10) {
    const dict = await loadDict()
    if (!text) return []
    const hits = []
    for (const [term, entry] of dict) {
        if (entry.deck === 'koujue' && term.length < 3) continue // 口诀类目名短词易误命中
        if (text.includes(term)) hits.push(entry)
    }
    hits.sort((a, b) => b.term.length - a.term.length || PRIORITY[a.deck] - PRIORITY[b.deck])
    // 同名去重 + 包含关系裁剪（如“当归”命中后不再显示“归”）
    const seen = new Set()
    const out = []
    for (const h of hits) {
        if (seen.has(h.term)) continue
        seen.add(h.term)
        out.push(h)
        if (out.length >= limit) break
    }
    return out
}
