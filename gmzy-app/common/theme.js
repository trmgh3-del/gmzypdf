// 全局外观：夜间模式套用（页面 onShow 调用）
import { store } from './store.js'

export function applyNavTheme() {
    const night = !!store.settings.night
    try {
        uni.setNavigationBarColor({
            frontColor: '#ffffff',
            backgroundColor: night ? '#241f18' : '#5c2018'
        })
        uni.setTabBarStyle({
            color: night ? '#7d766b' : '#8A8F99',
            selectedColor: night ? '#D8B98A' : '#8B3A3A',
            backgroundColor: night ? '#241f18' : '#FBF7EC',
            borderStyle: 'black'
        })
        uni.setBackgroundColor({
            backgroundColor: night ? '#17140f' : '#F6F1E5',
            backgroundColorTop: night ? '#17140f' : '#F6F1E5',
            backgroundColorBottom: night ? '#17140f' : '#F6F1E5'
        })
    } catch (e) { /* 平台不支持时静默 */ }
    return night
}

export function isNight() {
    return !!store.settings.night
}
