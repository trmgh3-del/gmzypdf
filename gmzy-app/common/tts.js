// tts.js — 本地朗读（H5 Web Speech API；App 端尽力而为，不可用则回退提示）
// 纯离线：不调用任何云端 TTS 服务。
export const state = { current: null, queue: [], playing: false }

function synthAvailable() {
    return typeof window !== 'undefined' && 'speechSynthesis' in window
}

function zhVoice() {
    const voices = window.speechSynthesis.getVoices()
    return voices.find((v) => /zh|Chinese|Yue|月|中/.test(v.lang + v.name)) || voices[0] || null
}

/** 朗读一段文本。返回 true=已开始，false=环境不支持 */
export function speak(text, { rate = 0.95, pitch = 1, onend } = {}) {
    if (!synthAvailable()) return false
    try {
        window.speechSynthesis.cancel()
        const u = new SpeechSynthesisUtterance(String(text).slice(0, 2400))
        u.lang = 'zh-CN'
        u.rate = rate
        u.pitch = pitch
        const v = zhVoice()
        if (v) u.voice = v
        if (onend) u.onend = onend
        window.speechSynthesis.speak(u)
        state.current = u
        return true
    } catch (e) {
        return false
    }
}

export function stopSpeak() {
    if (synthAvailable()) window.speechSynthesis.cancel()
    state.current = null
    state.queue = []
    state.playing = false
}

/** 连续播放：连续朗读若干段（口诀卡沉浸模式） */
export function speakQueue(texts, { gapMs = 400, onEach, onDone } = {}) {
    if (!synthAvailable() || !texts.length) return false
    stopSpeak()
    state.queue = texts.slice()
    state.playing = true
    const step = () => {
        if (!state.playing) return
        const t = state.queue.shift()
        if (t === undefined) {
            state.playing = false
            if (onDone) onDone()
            return
        }
        if (onEach) onEach(t, texts.length - state.queue.length - 1, texts.length)
        speak(t, {
            onend: () => {
                setTimeout(step, gapMs)
            }
        })
    }
    step()
    return true
}

export function isSpeaking() {
    return synthAvailable() && window.speechSynthesis.speaking
}
