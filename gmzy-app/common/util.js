// 通用工具
export function statusBarHeight() {
    try {
        if (uni.getWindowInfo && uni.getWindowInfo().statusBarHeight !== undefined) {
            return uni.getWindowInfo().statusBarHeight
        }
    } catch (e) {}
    try {
        const info = uni.getSystemInfoSync()
        return info.statusBarHeight || 0
    } catch (e) {
        return 0
    }
}

export function debounce(fn, wait = 300) {
    let timer = null
    return function (...args) {
        if (timer) clearTimeout(timer)
        timer = setTimeout(() => fn.apply(this, args), wait)
    }
}

export function formatChars(n) {
    if (n >= 10000) return (n / 10000).toFixed(1) + ' 万字'
    return n + ' 字'
}

export function formatTime(ts) {
    const d = new Date(ts)
    const now = Date.now()
    const pad = (x) => (x < 10 ? '0' + x : '' + x)
    if (now - ts < 60 * 1000) return '刚刚'
    if (now - ts < 3600 * 1000) return Math.floor((now - ts) / 60000) + ' 分钟前'
    if (now - ts < 86400 * 1000) return Math.floor((now - ts) / 3600000) + ' 小时前'
    if (now - ts < 7 * 86400 * 1000) return Math.floor((now - ts) / 86400000) + ' 天前'
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function excerptText(book, g, len = 60) {
    // 从块 g 起提取首个非空文本片段作为书签/历史摘要
    if (!book || !book.blocks) return ''
    for (let i = g; i < book.blocks.length && i < g + 8; i++) {
        const b = book.blocks[i]
        if (b.t === 'p') {
            const t = b.segs.map((s) => s.x).join('').trim()
            if (t) return t.slice(0, len) + (t.length > len ? '…' : '')
        }
        if (b.t === 'h' && i > g) {
            return '《' + b.x + '》'
        }
    }
    return ''
}

// 在块数组上拼接纯文本（搜索用）
export function blockText(b) {
    if (b.t === 'p') return b.segs.map((s) => s.x).join('')
    if (b.t === 'h') return b.x
    if (b.t === 'tbl') {
        const rows = [b.h].concat(b.r || [])
        return rows.map((r) => r.join(' ')).join(' ')
    }
    if (b.t === 'img') return b.a || ''
    return ''
}

// 定位块 g 所属章节
export function chapterOf(book, g) {
    const chs = book.chapters
    let lo = 0, hi = chs.length - 1, ans = 0
    while (lo <= hi) {
        const mid = (lo + hi) >> 1
        if (chs[mid].s <= g) {
            ans = mid
            lo = mid + 1
        } else {
            hi = mid - 1
        }
    }
    return ans
}
