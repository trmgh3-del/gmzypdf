// selfcheck.js — 首启数据包完整性自检（离线只在本地校验 JSON 结构，不联网）
import { store } from './store.js'

async function readJson(path) {
    // #ifdef APP-PLUS
    if (typeof plus !== 'undefined') {
        const url = await new Promise((r) => plus.io.resolveLocalFileSystemURL(`_www/${path}`, (e) => r(e.fullPath), () => r(null)))
        if (!url) return null
        const text = await new Promise((r) => {
            plus.io.requestFileSystem(plus.io.PRIVATE_WWW, (fs) => {
                fs.root.getFile(path, {}, (fe) => {
                    fe.file((f) => {
                        const rd = new plus.io.FileReader()
                        rd.onloadend = (e) => r(e.target.result)
                        rd.readAsText(f)
                    }, () => r(null))
                }, () => r(null))
            }, () => r(null))
        })
        return text ? JSON.parse(text) : null
    }
    // #endif
    const [err, res] = await uni.request({ url: '/' + path, timeout: 6000 }).then((r) => [null, r], (e) => [e, null])
    if (err || res.statusCode !== 200) return null
    return typeof res.data === 'string' ? JSON.parse(res.data) : res.data
}

const CHECKS = [
    { path: 'static/books-data/catalog.json', name: '图书目录', assert: (d) => d.length >= 26 },
    { path: 'static/learn/decks.json', name: '记忆卡包索引', assert: (d) => d.length === 6 && d.every((x) => x.count > 0) },
    { path: 'static/quiz/index.json', name: '题库索引', assert: (d) => d.length === 17 && d.every((x) => x.count > 0) },
    { path: 'static/diag/rules.json', name: '辨证规则', assert: (d) => (d.syndromes || []).length >= 40 && (d.groups || []).length >= 10 }
]

export async function runSelfCheck() {
    const bad = []
    for (const c of CHECKS) {
        try {
            const d = await readJson(c.path)
            if (!d || !c.assert(d)) bad.push(c.name)
        } catch (e) {
            bad.push(c.name)
        }
    }
    store.healthWarning = bad.length ? `数据包 ${bad.join('、')} 加载异常（可能为安装包不完整）` : ''
    if (bad.length) {
        uni.showModal({
            title: '数据包自检异常',
            content: `${bad.join('、')} 未通过完整性校验。请尝试重启 App；若仍异常请联系版本维护者（进度数据均在本地，删除重装会丢失）。`,
            showCancel: false,
            confirmText: '我知道了'
        })
    }
    return store.healthWarning
}
