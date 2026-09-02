// kg.js — 分类知识库学习系统数据层
// 索引静态预生成于 static/kg/index.json（tools/build_kg.py）：
//   9 学科课程分类 → 教材 → tree 拆条目（l>=3 节点，3470+ 条）
// 条目正文 = books-data 的 blocks[g..endG) 切片，运行时按书懒读
import { readJson, loadBook } from './books.js'

const KG_PATH = 'static/kg/index.json'

let kgCache = null

export async function loadKgIndex() {
    if (kgCache) return kgCache
    kgCache = await readJson(KG_PATH)
    return kgCache
}

export function getKgCats() {
    return kgCache ? kgCache.cats : []
}

export function getKgTotals() {
    return kgCache ? { entries: kgCache.totalEntries, books: kgCache.totalBooks } : { entries: 0, books: 0 }
}

export function getKgCat(key) {
    return getKgCats().find((c) => c.key === key) || null
}

// 同学科条目流（保持索引次序=书序+目录序）
export function kgEntries(key) {
    const cat = getKgCat(key)
    return cat ? cat.entries : []
}

// 条目上一个/下一个 g（同书按 g 排序切边界）
export function entryBounds(cat, b, g) {
    const sameBook = cat.entries.filter((e) => e.b === b).sort((a, z) => a.g - z.g)
    const i = sameBook.findIndex((e) => e.g === g)
    const cur = i >= 0 ? sameBook[i] : null
    const next = i >= 0 && i + 1 < sameBook.length ? sameBook[i + 1] : null
    return { cur, next, sameBook }
}

// 取条目正文块：[g, endG) 切片；endG=null 取到同书下一章节边界
export async function kgArticle(slug, g, endG) {
    const book = await loadBook(slug)
    const end = endG || book.blocks.length
    return {
        book,
        title: book.title,
        blocks: book.blocks.slice(g, end)
    }
}

// 学科内某条目的索引位置（上一篇/下一篇跨书翻页）
export function entryNeighbors(cat, b, g) {
    const i = cat.entries.findIndex((e) => e.b === b && e.g === g)
    return {
        idx: i,
        prev: i > 0 ? cat.entries[i - 1] : null,
        next: i >= 0 && i + 1 < cat.entries.length ? cat.entries[i + 1] : null
    }
}
