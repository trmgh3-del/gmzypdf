// useKF.js — 口诀（方剂歌诀）↔ 方剂卡互链索引
import { loadDeck } from '../../common/learn.js'

let cache = null

/** @returns {fang2song: Map<fangUuid, [{uuid, front}]>, song2fang: Map<songUuid, [{uuid, front}]>} */
export async function koujueFangIndex() {
    if (cache) return cache
    const [fj, kj] = await Promise.all([loadDeck('fangji'), loadDeck('koujue')])
    const fangFronts = fj.map((c) => ({ name: c.front, uuid: c.meta?.uuid || '' }))
        .filter((x) => x.name && x.name.length >= 2)
        .sort((a, b) => b.name.length - a.name.length)
    const fang2song = new Map()
    const song2fang = new Map()
    for (const c of kj) {
        if (!(c.sub || '').includes('方剂')) continue
        const songUuid = c.meta?.uuid || ''
        const back = String(c.back || '')
        const hits = new Set()
        let rest = back
        for (const f of fangFronts) {
            const i = rest.indexOf(f.name)
            if (i >= 0) {
                hits.add(f)
                rest = rest.slice(i + f.name.length)
                if (hits.size >= 6) break
            }
        }
        if (!hits.size) continue
        song2fang.set(songUuid, [...hits].map((f) => ({ uuid: f.uuid, front: f.name })))
        for (const f of hits) {
            if (!fang2song.has(f.uuid)) fang2song.set(f.uuid, [])
            fang2song.get(f.uuid).push({ uuid: songUuid, front: c.front })
        }
    }
    cache = { fang2song, song2fang }
    return cache
}
