// useHF.js — 方剂↔中药 双向索引（cards 页内部使用）
import { loadDeck } from '../../common/learn.js'

let cache = null

/** @returns {herbName2Uuid, fangByHerb} */
export async function herbfangIndex() {
    if (cache) return cache
    const [herb, fang] = await Promise.all([loadDeck('herb'), loadDeck('fangji')])
    const herbName2Uuid = {}
    for (const c of herb) herbName2Uuid[c.front] = c.meta?.uuid || ''
    const herbNames = Object.keys(herbName2Uuid).sort((a, b) => b.length - a.length)
    const fangByHerb = {}
    for (const f of fang) {
        const m = String(f.back || '').match(/[〔【]组成[〕】]\s*([^〔【〕】\n]+)/)
        if (!m) continue
        let seg = m[1]
        const hits = new Set()
        for (const nm of herbNames) {
            const i = seg.indexOf(nm)
            if (i >= 0) {
                hits.add(nm)
                seg = seg.slice(i + nm.length)
            }
        }
        for (const nm of hits) {
            if (!fangByHerb[nm]) fangByHerb[nm] = []
            fangByHerb[nm].push({ front: f.front, uuid: f.meta?.uuid || '' })
        }
    }
    cache = { herbName2Uuid, fangByHerb }
    return cache
}
