// sharecard.js — 图谱条目「出片」：SVG 组片 → PNG dataURL → 保存
// 用法：const url = await makeSharePng(item); await savePng(url, 'xxx')
// 构图：标题（术语）· 活体图谱 SVG 嵌片 · 释义全书签款 · 出处 · 页脚
// 组片内文字类样式须注入 <style>（脱离组件 scope 后 CSS 不复戴）

const SVG_TEXT_STYLES = `
.grid-t { font-size: 14px; fill: rgba(141, 131, 113, 0.7); }
.fp { font-size: 15px; fill: #5c2018; font-weight: 700; }
.zt { font-size: 9px; fill: #fffdf7; font-weight: 700; }
.fz { font-size: 13px; fill: #5c2018; font-weight: 700; }
.num-serif { font-size: 30px; fill: #8b3a3a; font-weight: 700; text-anchor: middle; font-family: serif; }
`

// 把长描述按句读点断行（每行最多 n 字）
function wrapLines(text, n = 22) {
    const out = []
    let buf = ''
    for (const ch of String(text || '')) {
        buf += ch
        if (buf.length >= n && '。；，、：：'.includes(ch)) {
            out.push(buf)
            buf = ''
        }
    }
    if (buf) out.push(buf)
    return out
}

function escapeXml(s) {
    return String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]))
}

// 从 peek 弹层茶几取活体图谱 SVG（DOM 取整形）
export function peekFigXml() {
    const el =
        (typeof document !== 'undefined' &&
            (document.querySelector('.peek-fig svg') ||
                document.querySelector('.gq-fig svg') ||
                document.querySelector('.atlas-fig svg'))) ||
        null
    if (!el) return null
    let xml = el.outerHTML
    // 注入文字类样式（脱离 Vue scoped）
    xml = xml.replace('>', `><style>${SVG_TEXT_STYLES}</style>`)
    return xml
}

// 组片：item {term, desc, src} + 图谱 xml → 整幅 SVG 串
export function buildCardSvg(item, figXml) {
    const W = 750
    const lines = wrapLines(item.desc, 22)
    const figSize = 320
    const figTop = 110
    const descTop = figTop + figSize + 60
    const H = descTop + lines.length * 44 + 120
    const center = W / 2 - figSize / 2
    const figNode = figXml
        ? figXml.replace('<svg', `<svg width="${figSize}" height="${figSize}" x="${center}" y="${figTop}" `)
        : ''
    const esc = escapeXml
    return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <rect width="${W}" height="${H}" fill="#fdf7e8" />
    <rect x="24" y="24" width="${W - 48}" height="${H - 48}" fill="none" stroke="#b5935a" stroke-width="2" rx="18" />
    <text x="${W / 2}" y="76" text-anchor="middle" font-family="serif" font-weight="bold" font-size="40" fill="#5c2018" letter-spacing="6">${esc(item.term)}</text>
    <text x="${W / 2}" y="108" text-anchor="middle" font-size="17" fill="#a08c68" letter-spacing="4">光明中医文库 · 考举出片</text>
    ${figNode}
    ${lines
        .map(
            (ln, i) =>
                `<text x="60" y="${descTop + i * 44}" font-size="26" fill="#4b4438" font-family="serif">${esc(ln)}</text>`
        )
        .join('')}
    <text x="${W - 56}" y="${H - 74}" text-anchor="end" font-size="18" fill="#a08c68" font-family="serif">${esc(item.src || '')}</text>
    <text x="${W / 2}" y="${H - 34}" text-anchor="middle" font-size="16" fill="#c2a878" letter-spacing="4">诊法速查 · 仅供学习参考</text>
</svg>`
}

// SVG 串 → PNG dataURL（2x 分辨率）
export function svgToPngDataUrl(svgXml, w, h) {
    return new Promise((resolve) => {
        const img = new Image()
        img.onload = () => {
            try {
                const cv = document.createElement('canvas')
                cv.width = w * 2
                cv.height = h * 2
                const ctx = cv.getContext('2d')
                ctx.drawImage(img, 0, 0, cv.width, cv.height)
                resolve(cv.toDataURL('image/png'))
            } catch (e) {
                resolve(null)
            }
        }
        img.onerror = () => resolve(null)
        img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgXml)
    })
}

// 一体化：取整图 → 出片
export async function makeSharePng(item) {
    const fig = peekFigXml()
    if (!fig) return null
    const svg = buildCardSvg(item, fig)
    const H = 110 + 320 + 60 + wrapLines(item.desc, 22).length * 44 + 120
    return svgToPngDataUrl(svg, 750, H)
}

// 保存：App 走相册（plus.io 写 _doc），H5 走下载；成功返回 true
export async function savePng(dataUrl, fname) {
    if (!dataUrl) return false
    // #ifdef APP-PLUS
    try {
        const blob = await (await fetch(dataUrl)).blob()
        const fs = await new Promise((res, rej) => plus.io.requestFileSystem(plus.io.PRIVATE_DOC, res, rej))
        const file = await new Promise((res, rej) => fs.root.getFile(fname, { create: true }, res, rej))
        await new Promise((res, rej) =>
            file.createWriter(
                (w) => {
                    w.onwrite = () => res()
                    w.onerror = rej
                    w.write(blob)
                },
                rej
            )
        )
        await new Promise((res, rej) =>
            uni.saveImageToPhotosAlbum({
                filePath: file.fullPath,
                success: () => res(),
                fail: () => rej(new Error('相册拒绝'))
            })
        )
        return true
    } catch (e) {
        // 降级到分享层
    }
    // #endif
    // #ifdef H5
    try {
        const a = document.createElement('a')
        a.href = dataUrl
        a.download = fname
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        return true
    } catch (e) {
        return false
    }
    // #endif
    return false
}
