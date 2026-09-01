// 辨证评分引擎（纯函数，无环境依赖）
// 输入：用户勾选的症状 id 数组 + static/diag/rules.json 规则库
// 输出：按匹配度排序的证型数组（含命中症状、百分比）

// 统计全部症状 id 集合与“症状 id -> 展示名”映射
export function symptomIndex(rules) {
  const map = {}
  for (const g of rules.groups) {
    for (const it of g.items) map[it.id] = it.label
  }
  return map
}

// 单证型打分：命中权重和 / 该证型总权重
export function scoreOne(selectedSet, syn) {
  let hit = 0
  let total = 0
  const matched = []
  for (const [sid, w] of Object.entries(syn.w)) {
    total += w
    if (selectedSet.has(sid)) {
      hit += w
      matched.push({ id: sid, w })
    }
  }
  matched.sort((a, b) => b.w - a.w)
  return { hit, total, matched, ratio: total ? hit / total : 0 }
}

// 全库评分排序。阈值为命中率>0；并列时命中数多者优先。
export function diagnose(selectedIds, rules, limit = 4) {
  const sel = new Set(selectedIds || [])
  if (!sel.size) return []
  const idx = symptomIndex(rules)
  return rules.syndromes
    .map(s => {
      const r = scoreOne(sel, s)
      return {
        id: s.id,
        name: s.name,
        cat: s.cat,
        bj: s.bj,
        zf: s.zf,
        fang: s.fang,
        points: s.points,
        ref: s.ref,
        hit: r.hit,
        total: r.total,
        pct: Math.round(r.ratio * 100),
        matched: r.matched.map(m => ({ ...m, label: idx[m.id] || m.id }))
      }
    })
    .filter(r => r.hit > 0)
    .sort((a, b) => b.pct - a.pct || b.hit - a.hit || a.total - b.total)
    .slice(0, limit)
}

const Diagnosis = { symptomIndex, scoreOne, diagnose }
export default Diagnosis
