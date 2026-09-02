#!/usr/bin/env python3
# H5 离线化（PWA）：在 uni build -p h5 产物上注入 Service Worker + Web App Manifest。
# 用法：python3 tools/build_pwa.py [dist_h5_dir]
# 默认目录：/home/user/uicheck/dist/build/h5
#
# 策略（纯离线、零外联）：
#   - 预缓存：index.html、assets/**（应用壳 JS/CSS）、static/**/*.json（全部书目与学习数据）
#   - 运行时缓存：其余同源 GET（封面图、舌脉图等）首次访问后入缓存，断网可回看
#   - 导航请求断网时回落到 /index.html
import json
import os
import re
import struct
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIR = '/home/user/uicheck/dist/build/h5'


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    if head[:8] == b'\x89PNG\r\n\x1a\n':
        w, h = struct.unpack('>II', head[16:24])
        return w, h
    return 512, 512


def collect_precache(root):
    """收集预缓存清单（相对 URL，以 / 开头）。"""
    out = []
    for base, _dirs, files in os.walk(root):
        for fn in files:
            full = os.path.join(base, fn)
            rel = '/' + os.path.relpath(full, root).replace(os.sep, '/')
            if rel in ('/sw.js', '/manifest.webmanifest'):
                continue
            if rel == '/index.html' or rel.startswith('/assets/'):
                out.append(rel)
            elif rel.startswith('/static/') and rel.endswith('.json'):
                out.append(rel)
    return sorted(set(out))


SW_TMPL = """// 光明中医文库 H5 离线缓存（tools/build_pwa.py 自动生成于 {ts}）
const CACHE = 'gmzy-h5-{ver}';
const PRECACHE = {precache};

self.addEventListener('install', (e) => {{
    e.waitUntil(
        caches.open(CACHE)
            .then((c) => c.addAll(PRECACHE))
            .then(() => self.skipWaiting())
    );
}});

self.addEventListener('activate', (e) => {{
    e.waitUntil(
        caches.keys()
            .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
            .then(() => self.clients.claim())
    );
}});

self.addEventListener('fetch', (e) => {{
    const req = e.request;
    if (req.method !== 'GET' || !req.url.startsWith(self.location.origin)) return;
    e.respondWith(
        caches.match(req).then((hit) => {{
            const fetched = fetch(req).then((res) => {{
                if (res && res.ok && res.type === 'basic') {{
                    const cp = res.clone();
                    caches.open(CACHE).then((c) => c.put(req, cp));
                }}
                return res;
            }});
            if (hit) return hit;
            return fetched.catch(() => {{
                if (req.mode === 'navigate') return caches.match('/index.html');
                throw new Error('offline');
            }});
        }})
    );
}});
"""

REGISTER_SCRIPT = """<script>
// PWA 离线缓存注册（tools/build_pwa.py 注入）
if ('serviceWorker' in navigator && /^https?:/.test(location.protocol)) {
    window.addEventListener('load', function () {
        navigator.serviceWorker.register('/sw.js');
    });
}
</script>"""


def inject_index(root, app_name, theme):
    ipath = os.path.join(root, 'index.html')
    html = open(ipath, encoding='utf-8').read()
    if 'gmzy-pwa-marker' in html:
        return False  # 已注入
    head_add = (
        '<!-- gmzy-pwa-marker -->\n'
        '<link rel="manifest" href="/manifest.webmanifest">\n'
        '<meta name="theme-color" content="%s">\n'
        '<meta name="mobile-web-app-capable" content="yes">\n'
        '<meta name="apple-mobile-web-app-title" content="%s">' % (theme, app_name)
    )
    html = re.sub(r'</head>', head_add + '\n</head>', html, count=1)
    html = re.sub(r'</body>', REGISTER_SCRIPT + '\n</body>', html, count=1)
    open(ipath, 'w', encoding='utf-8').write(html)
    return True


def main():
    root = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DIR
    if not os.path.isfile(os.path.join(root, 'index.html')):
        print('PWA FAIL: %s 下没有 index.html（先执行 npm run build:h5）' % root)
        return 1

    # manifest.json 为 JSONC（允许注释），用正则抽取
    mtxt = open(os.path.join(REPO, 'gmzy-app', 'manifest.json'), encoding='utf-8').read()
    mver = re.search(r'"versionName":\s*"([^"]+)"', mtxt)
    ver = mver.group(1) if mver else '0.0.0'
    mname = re.search(r'"name":\s*"([^"]+)"', mtxt)
    app_name = mname.group(1) if mname else '光明中医文库'

    precache = collect_precache(root)
    sw = SW_TMPL.format(ts=time.strftime('%Y-%m-%d %H:%M:%S'), ver='%s-%d' % (ver, len(precache)),
                        precache=json.dumps(precache, ensure_ascii=False, indent=2))
    open(os.path.join(root, 'sw.js'), 'w', encoding='utf-8').write(sw)

    icon = os.path.join(root, 'static', 'icon.png')
    w, h = png_size(icon) if os.path.isfile(icon) else (512, 512)
    webmanifest = {
        'name': app_name,
        'short_name': app_name,
        'start_url': '/',
        'scope': '/',
        'display': 'standalone',
        'background_color': '#f6f1e5',
        'theme_color': '#5c2018',
        'icons': [
            {'src': '/static/icon.png', 'sizes': '%dx%d' % (w, h), 'type': 'image/png', 'purpose': 'any'}
        ]
    }
    open(os.path.join(root, 'manifest.webmanifest'), 'w', encoding='utf-8').write(
        json.dumps(webmanifest, ensure_ascii=False, indent=2))

    changed = inject_index(root, app_name, '#5c2018')
    print('PWA OK: %s | v%s | 预缓存 %d 个文件 | index.html %s' % (
        root, ver, len(precache), '已注入' if changed else '（早前已注入）'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
