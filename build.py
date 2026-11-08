#!/usr/bin/env python3
"""Bygger iPad-appen (docs/) fra src/tangenta.html.

src/tangenta.html er samme fil som publiseres som Claude-artefakt.
Her pakkes den inn i et fullt HTML-dokument med manifest, ikoner og
service worker, slik at den kan legges på Hjem-skjermen og virke uten nett.

Kjør:  python3 build.py
"""
import hashlib
import json
from datetime import datetime
import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / 'src' / 'tangenta.html'
OUT = ROOT / 'docs'

HEAD = """<!doctype html>
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Tangenta">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#edf0f6" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#12142a" media="(prefers-color-scheme: dark)">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-192.png">
<style>html{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}</style>
"""

# Service workeren gir bare offline-støtte. Beskjeden om ny versjon kommer fra appens egen
# sjekk mot version.json, så den vises bare når versjonen faktisk er nyere enn den som kjører.
SW_REGISTER = """<script>
if ('serviceWorker' in navigator) addEventListener('load', () => {
  navigator.serviceWorker.register('sw.js').then(reg => reg.update()).catch(() => {});
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') navigator.serviceWorker.getRegistration().then(r => r && r.update()).catch(() => {});
  });
});
</script>
"""

SW = """// Tangenta offline: selve siden hentes fra nettet først (lageret er reserve uten nett),
// resten vises fra lageret med en gang og fornyes i bakgrunnen. version.json går alltid til nettet.
const CACHE = 'tangenta-%s';
const SHELL = ['./', 'index.html', 'manifest.webmanifest', 'icon-180.png', 'icon-192.png', 'icon-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL.map(u => new Request(u, { cache: 'reload' })))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  if (new URL(e.request.url).pathname.endsWith('version.json')) return;
  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request, { cache: 'no-store' }).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put('./', copy)); }
      return res;
    }).catch(() => caches.match('./').then(hit => hit || caches.match('index.html'))));
    return;
  }
  e.respondWith(caches.match(e.request, { ignoreSearch: true }).then(hit => {
    const net = fetch(e.request).then(res => {
      if (res.ok || res.type === 'opaque') { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
      return res;
    }).catch(() => hit);
    return hit || net;
  }));
});
"""

MANIFEST = {
    'name': 'Tangenta',
    'short_name': 'Tangenta',
    'description': 'Lær å spille piano og lese noter med enkle sanger.',
    'lang': 'nb',
    'start_url': './',
    'scope': './',
    'display': 'standalone',
    'orientation': 'any',
    'background_color': '#12142a',
    'theme_color': '#12142a',
    'icons': [
        {'src': 'icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
        {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
        {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
    ],
}


def png(path, w, h, pixels):
    raw = b''.join(b'\x00' + bytes(pixels[y * w * 3:(y + 1) * w * 3]) for y in range(h))
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def icon(size):
    """Tre pianotangenter i notefarger (C, E, G) under en filtstripe, med svarte tangenter."""
    bg, felt, white = (18, 20, 42), (155, 35, 53), (253, 253, 255)
    cols = [(229, 72, 77), white, (229, 176, 0), white, (15, 159, 163)]
    px = bytearray(size * size * 3)
    s = size / 100
    for y in range(size):
        for x in range(size):
            u, v = x / s, y / s
            c = bg
            if 18 <= v < 24 and 10 <= u < 90:
                c = felt
            elif 24 <= v < 86 and 10 <= u < 90:
                k = int((u - 10) // 16)
                if (u - 10) % 16 >= 1.5:
                    c = cols[min(k, 4)]
                    # avrundede hjørner nederst
                    if v > 82 and ((u - 10) % 16 < 4 or (u - 10) % 16 > 13.5):
                        c = bg
                for bx in (26, 42, 74):
                    if bx - 5 <= u < bx + 5 and v < 62:
                        c = (28, 31, 51)
            i = (y * size + x) * 3
            px[i:i + 3] = bytes(c)
    return px


def main():
    src = SRC.read_text(encoding='utf-8')
    split = src.index('<div id="app">')
    head, body = src[:split], src[split:]
    version = hashlib.sha1(src.encode()).hexdigest()[:7]
    label = datetime.now().strftime('%d.%m.%Y %H:%M')
    stamp = '<script>window.TANGENTA_VERSION = %s;</script>\n' % json.dumps({'id': version, 'label': label})
    html = HEAD + stamp + head + '</head>\n<body>\n' + body + SW_REGISTER + '</body>\n</html>\n'
    OUT.mkdir(exist_ok=True)
    (OUT / 'index.html').write_text(html, encoding='utf-8')
    (OUT / 'sw.js').write_text(SW % version, encoding='utf-8')
    (OUT / 'version.json').write_text(json.dumps({'id': version, 'label': label}), encoding='utf-8')
    (OUT / 'manifest.webmanifest').write_text(json.dumps(MANIFEST, ensure_ascii=False, indent=2), encoding='utf-8')
    for n in (180, 192, 512):
        f = OUT / f'icon-{n}.png'
        if not f.exists():
            png(f, n, n, icon(n))
    print(f'Bygget docs/ (versjon {label}, {version})')


if __name__ == '__main__':
    main()
