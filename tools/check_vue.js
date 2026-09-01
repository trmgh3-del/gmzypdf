#!/usr/bin/env node
// check_vue.js — 快速校验 .vue SFC：模板标签配对 + <script> 语法编译
// 依赖均从同仓工程沙箱解析（默认 /home/user/uicheck/node_modules，
// 可用 CHECK_DEPS=/path/to/node_modules 覆盖）。
// 用法: node tools/check_vue.js <file.vue> [...more.vue]

const fs = require('fs')
const path = require('path')
const { createRequire } = require('module')

const DEPS = process.env.CHECK_DEPS || '/home/user/uicheck/node_modules'
const req = createRequire(path.join(DEPS, '.x.js'))
let sfc, esbuild
try {
    sfc = req('@vue/compiler-sfc')
    esbuild = req('esbuild')
} catch (e) {
    console.error('缺少构建依赖：请先准备沙箱工程并设 CHECK_DEPS 指向其 node_modules')
    console.error('  例: CHECK_DEPS=/home/user/uicheck/node_modules node tools/check_vue.js a.vue')
    process.exit(2)
}

const files = process.argv.slice(2)
let bad = 0

function checkTemplate(html, file) {
    // 简单配平（忽略自闭合/文本干扰）
    const stack = []
    const re = /<\/?([a-zA-Z][\w-]*)((?:"[^"]*"|'[^']*'|[^>"'])*)>/g
    let m
    while ((m = re.exec(html))) {
        const open = !m[1].startsWith('/') && !html.substr(m.index, 5).startsWith('<!--')
        const tag = m[1]
        const close = m[0].startsWith('</')
        const selfClose = /\/\s*>$/.test(m[0]) || ['image', 'img', 'input', 'br', 'hr'].includes(tag)
        if (html.startsWith('<!--', m.index)) continue
        if (close) {
            const top = stack.pop()
            if (top !== tag) return `标签不配对: </${tag}>（栈顶 ${top || '空'}）`
        } else if (!selfClose) {
            stack.push(tag)
        }
    }
    if (stack.length) return `有未闭合标签: ${stack.slice(-3).join(',')}`
    return null
}

async function main() {
    for (const f of files) {
        const src = fs.readFileSync(f, 'utf-8')
        const { descriptor, errors } = sfc.parse(src, { filename: f })
        const errs = []
        if (errors.length) errs.push(...errors.map((e) => e.message))
        for (const b of [descriptor.script, descriptor.scriptSetup]) {
            if (!b) continue
            try {
                const code = sfc.compileScript(descriptor, { id: 'x' }).content
                await esbuild.transform(code, { loader: 'js' })
            } catch (e) {
                errs.push('script: ' + String(e.message || e).slice(0, 300))
            }
        }
        if (descriptor.template) {
            const terr = checkTemplate(descriptor.template.content, f)
            if (terr) errs.push('template: ' + terr)
        }
        if (errs.length) {
            bad++
            console.error('✗', f)
            errs.forEach((e) => console.error('   -', e))
        }
    }
    if (bad) {
        console.error(` FAILED: ${bad}/${files.length}`)
        process.exit(1)
    }
    console.log('ALL VUE OK:', files.length)
}

main()
