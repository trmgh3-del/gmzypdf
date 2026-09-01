<script>
export default {
    onLaunch() {
        // 应用启动：状态在 common/store.js 中惰性恢复
    },
    onShow() {},
    onHide() {}
}
</script>

<style lang="scss">
/* 全局基础样式 */
page {
    background-color: #f6f1e5;
    color: #37332b;
    font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC',
        'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
    font-size: 15px;
    line-height: 1.6;
}

view, text, scroll-view, image, input, picker, slider, button {
    box-sizing: border-box;
}

.serif-font {
    font-family: 'Songti SC', 'STSong', 'STZhongsong', 'Noto Serif CJK SC',
        'Noto Serif SC', 'SimSun', serif;
}
</style>
