// 书籍数据访问层
// 数据静态存放于 static/books-data/*.json，运行时按需读取（离线、零启动开销）。
// 读取方式按平台条件编译：
//   App 端 → plus.io 读取安装包内文件（_www/...）
//   H5 端  → fetch 静态资源

const DATA_DIR = 'static/books-data/'
const cache = new Map() // slug|catalog -> Promise/Object

// ---------------- 平台文件读取 ----------------

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
        if (!res.ok) throw new Error('HTTP ' + res.status + ' ' + path)
        return res.json()
    })
}
// #endif

// ---------------- 对外 API ----------------

let catalogCache = null

export async function loadCatalog() {
    if (catalogCache) return catalogCache
    catalogCache = await readJson(DATA_DIR + 'catalog.json')
    return catalogCache
}

export function getCatalog() {
    return catalogCache || []
}

export function getBookMeta(slug) {
    const cat = getCatalog()
    return cat.find((b) => b.slug === slug) || null
}

export async function loadBook(slug) {
    if (cache.has(slug)) return cache.get(slug)
    const p = readJson(DATA_DIR + slug + '.json')
    cache.set(slug, p)
    const book = await p
    // 回填全局块序号（渲染锚点、书签定位使用）
    for (let i = 0; i < book.blocks.length; i++) book.blocks[i].g = i
    cache.set(slug, book)
    return book
}

// 书籍分组（书架筛选）
export const CATEGORIES = [
    { key: 'all', name: '全部' },
    { key: 'intro', name: '入门基础', slugs: ['0', '1000', '5', '6', '7', '7b', '8'] },
    { key: 'classic', name: '经典方药', slugs: ['10', '11', '12', '13', '14', '25', '26', '29'] },
    { key: 'clinic', name: '临床各科', slugs: ['15', '16', '17', '18', '19', '20', '22', '23'] },
    { key: 'acu', name: '针灸', slugs: ['21', '21b', '21c'] }
]

export function booksOf(catKey) {
    const catalogData = getCatalog()
    if (catKey === 'all') return catalogData
    const cat = CATEGORIES.find((c) => c.key === catKey)
    if (!cat || !cat.slugs) return catalogData
    return cat.slugs.map((s) => catalogData.find((b) => b.slug === s)).filter(Boolean)
}
