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

// 单证型打分：命中权重和 / 该证型总权重（负权重=反证，勾选即扣整证分、不计入总分母）
export function scoreOne(selectedSet, syn) {
  let hit = 0
  let total = 0
  const matched = []
  const against = []
  for (const [sid, w] of Object.entries(syn.w)) {
    if (w > 0) {
      total += w
      if (selectedSet.has(sid)) {
        hit += w
        matched.push({ id: sid, w })
      }
    } else if (selectedSet.has(sid)) {
      hit += w
      against.push({ id: sid, w })
    }
  }
  matched.sort((a, b) => b.w - a.w)
  return { hit, total, matched, against, ratio: total ? Math.max(0, hit) / total : 0 }
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

// 查找两个证型之间的鉴别要点（rules.vs 人工编写，顺序无关）
export function findVs(rules, idA, idB) {
    for (const v of rules.vs || []) {
        if ((v.a === idA && v.b === idB) || (v.a === idB && v.b === idA)) return v
    }
    return null
}

// 急重症红旗症状：勾选即应提示「真实不适请立即就医」（本系统仅供辨证学习）
export const RED_FLAGS = [
    { id: 'shenhun', label: '神昏谵语' },
    { id: 'er_jingfeng', label: '惊风抽搐' },
    { id: 'er_jire', label: '小儿高热骤起' },
    { id: 'chu_xue', label: '出血不止' },
    { id: 'dh_br', label: '高热不退' }
]

const Diagnosis = { symptomIndex, scoreOne, diagnose, findVs, RED_FLAGS }
export default Diagnosis
