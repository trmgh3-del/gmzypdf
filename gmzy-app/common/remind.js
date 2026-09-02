// remind.js — 本地学习提醒（纯离线）
// App 端：plus.push 系统级本地定时通知（App 被杀死仍弹出）。
// H5 端：打开应用时若今日未学且有到期卡，弹一次 toast。
import { store, deckStats, quizMistakeCount, wenguList } from './store.js'

export function todayLearnedCount() {
    const d = new Date()
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    const a = store.learn.activity[key] || {}
    return (a.cards || 0) + (a.quiz || 0) + (a.done || 0) + (a.kg || 0)
}

export function remindEnabledHour() {
    return store.settings.remind ?? 20 // 20=晚8点，-1=关，7=早7点，21=晚9点
}

function secondsUntil(hour) {
    const now = new Date()
    const next = new Date(now)
    next.setHours(hour, 0, 0, 0)
    if (next <= now) next.setDate(next.getDate() + 1)
    return Math.round((next - now) / 1000)
}

function computeMessageText() {
    const decks = ['fangji', 'herb', 'point', 'koujue', 'bingz', 'yian']
    const due = decks.reduce((s, id) => s + deckStats(id, 0).due, 0)
    const errs = (store.learn.qErr ? Object.values(store.learn.qErr) : []).reduce(
        (s, errs) => s + Object.values(errs || {}).filter((e) => e.m >= 2).length, 0)
    const wg = wenguList().filter((w) => w.dueIn === 0).length
    const bits = []
    if (due) bits.push(`${due} 张卡到期`)
    if (errs) bits.push(`${errs} 道错题重练`)
    if (wg) bits.push(`温故 ${wg} 题到日`)
    if (!bits.length) return null
    return bits.join('，') + '，温故而知新'
}

/** 排入次日/当日 20:00 提醒（App 端系统级；无内容则清空） */
export function scheduleAppReminder() {
    // #ifdef APP-PLUS
    try {
        const hour = remindEnabledHour()
        plus.push.clear()
        if (hour < 0) return
        const text = computeMessageText()
        if (!text) return
        plus.push.createMessage(
            text,
            JSON.stringify({ title: '📚 光明中医 学习提醒' }),
            { delay: secondsUntil(hour), sound: 'none', cover: false }
        )
        store.settings.remindPlanned = { hour, text, ts: Date.now() }
    } catch (e) {
        console.warn('学习提醒排程失败', e)
    }
    // #endif
}

/** H5 端会话提醒：每天最多弹一次 */
export function maybeToastH5Reminder() {
    // #ifdef H5
    const today = new Date().toISOString().slice(0, 10)
    if (store.settings.h5RemindOnDate === today) return
    if (todayLearnedCount() > 0) return
    const text = computeMessageText()
    if (!text) return
    store.settings.h5RemindOnDate = today
    uni.showToast({ title: text, icon: 'none', duration: 3200 })
    // #endif
}

/** 供设置页调用：切换提醒时间并立即重排 */
export function setRemindHour(hour) {
    store.settings.remind = hour
    scheduleAppReminder()
}
