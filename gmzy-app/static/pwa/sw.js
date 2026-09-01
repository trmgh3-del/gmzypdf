// 光明中医文库 H5 离线缓存（service worker, 注册于 /static/pwa/ 作用域）
// 运行时缓存 /static/ 下全部数据目录(图书/卡包/题库/图片 ~50MB), 首次浏览后即可离线。
// 注意: SW 作用域上限为其所在目录; 想把整个应用壳也离线缓存,
// 部署时请将本文件拷贝到站点根目录并在 App.vue 中改注册为 '/sw.js'。
const CACHE = 'gmzy-data-v2'
// 预缓存关键小文件（壳需要的数据入口）
const PRECACHE = [
    'static/catalog.json',
    'static/learn/decks.json',
    'static/quiz/index.json'
]

self.addEventListener('install', (e) => {
    e.waitUntil(caches.open(CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then((ks) =>
            Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
        ).then(() => self.clients.claim())
    )
})

self.addEventListener('fetch', (e) => {
    const url = new URL(e.request.url)
    if (e.request.method !== 'GET') return
    if (!url.pathname.includes('/static/')) return
    e.respondWith(
        caches.match(e.request).then(
            (hit) =>
                hit ||
                fetch(e.request).then((resp) => {
                    if (resp && resp.status === 200 && resp.type === 'basic') {
                        const clone = resp.clone()
                        caches.open(CACHE).then((c) => c.put(e.request, clone))
                    }
                    return resp
                })
        )
    )
})
