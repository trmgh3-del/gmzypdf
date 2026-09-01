<template>
    <view class="blocks">
        <view
            v-for="b in blocks"
            :key="b.g"
            :id="'blk-' + b.g"
            :data-g="b.g"
            class="blk"
            :class="blockClass(b)"
        >
            <!-- 标题 -->
            <view v-if="b.t === 'h'" class="hd-wrap">
                <text class="hd serif-font">{{ b.x }}</text>
                <view class="hd-line" v-if="b.l <= 2" />
            </view>
            <!-- 段落 -->
            <view v-else-if="b.t === 'p'" class="para">
                <text
                    v-for="(s, si) in b.segs"
                    :key="si"
                    class="pt"
                    :class="{ 'pt-bold': s.b }"
                    :user-select="true"
                >{{ s.x }}</text>
            </view>
            <!-- 图片 -->
            <view v-else-if="b.t === 'img'" class="fig" @tap.stop="$emit('img', b)">
                <image
                    class="fig-img"
                    :src="imgSrc(b)"
                    mode="widthFix"
                    :lazy-load="true"
                    :show-menu-by-longpress="true"
                />
                <text v-if="b.a && b.a !== '插图'" class="fig-cap">{{ b.a }}</text>
            </view>
            <!-- 表格 -->
            <scroll-view v-else-if="b.t === 'tbl'" class="tbl-wrap" scroll-x :show-scrollbar="true">
                <view class="tbl" :style="{ minWidth: tableMinWidth(b) }">
                    <view class="tr tr-head">
                        <text v-for="(c, ci) in b.h" :key="ci" class="td th">{{ c }}</text>
                    </view>
                    <view v-for="(r, ri) in b.r" :key="ri" class="tr">
                        <text v-for="(c, ci) in r" :key="ci" class="td">{{ c }}</text>
                    </view>
                </view>
            </scroll-view>
        </view>
    </view>
</template>

<script setup>
const props = defineProps({
    blocks: { type: Array, default: () => [] }, // 每块带 g 全局序号
    slug: { type: String, default: '' }
})

defineEmits(['img'])

function blockClass(b) {
    if (b.t === 'h') return 'blk-h lvl-' + b.l
    return 'blk-' + b.t
}

function imgSrc(b) {
    return `/static/books/${props.slug}/${b.s}`
}

function tableMinWidth(b) {
    const cols = Math.max((b.h || []).length, 1)
    return Math.min(Math.max(cols * 150, 320), cols * 260) + 'rpx'
}
</script>

<style lang="scss" scoped>
.blk {
    margin: 0;
}

/* 标题 */
.hd-wrap {
    margin: 1.1em 0 0.7em;
}

.hd {
    color: var(--accent, #8b3a3a);
    font-weight: 700;
    line-height: 1.4;
    display: block;
}

.hd-line {
    height: 2px;
    margin-top: 10rpx;
    background: linear-gradient(90deg, var(--accent, #8b3a3a) 0%, transparent 80%);
    opacity: 0.35;
    border-radius: 2px;
}

.lvl-1 .hd { font-size: 1.5em; }
.lvl-2 .hd { font-size: 1.32em; }
.lvl-3 .hd { font-size: 1.16em; }
.lvl-4 .hd { font-size: 1.06em; }
.lvl-5 .hd, .lvl-6 .hd { font-size: 1em; }

/* 段落 */
.para {
    margin: 0.65em 0;
    font-size: var(--fs, 19px);
    line-height: var(--lh, 1.8);
    color: var(--fg, #37332b);
    text-align: justify;
    text-indent: 2em;
    letter-spacing: 0.01em;
    word-break: break-all;
}

.pt-bold {
    font-weight: 700;
    color: var(--accent, #8b3a3a);
}

/* 图片 */
.fig {
    margin: 0.8em auto;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.fig-img {
    max-width: 100%;
    border-radius: 8rpx;
    background: var(--card, #fff);
    box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.08);
}

.fig-cap {
    margin-top: 10rpx;
    font-size: 0.8em;
    color: var(--muted, #8d8371);
}

/* 表格 */
.tbl-wrap {
    margin: 0.8em 0;
    max-width: 100%;
}

.tbl {
    border-top: 1px solid var(--line, #e4dcc8);
    border-left: 1px solid var(--line, #e4dcc8);
    border-radius: 6rpx;
    overflow: hidden;
    display: inline-block;
}

.tr {
    display: flex;
}

.td {
    flex: 1 0 0;
    min-width: 120rpx;
    padding: 12rpx 18rpx;
    font-size: 0.78em;
    line-height: 1.55;
    color: var(--fg, #37332b);
    border-right: 1px solid var(--line, #e4dcc8);
    border-bottom: 1px solid var(--line, #e4dcc8);
    word-break: break-all;
}

.th {
    font-weight: 700;
    color: var(--accent, #8b3a3a);
    background: var(--th-bg, rgba(139, 58, 58, 0.06));
}
</style>
