#!/usr/bin/env python3
"""Builds app/www/index.html (Flix Director iOS app) from the web game ../index.html and adds the app-only scripts (app/native/):
head:  flix-net.js (online duels without claude.ai: window.claude.use shim, must run before the game), ads-config.js + ads.js
       (AdMob, window.FlixAds), native-bridge.js (App Store purchases, window.FlixNative)
end:   director-native.js (real ads / purchases in place of the demo ones), flix-privacy.js ("Gizlilik Seçenekleri" button)
It also swaps the texts that only make sense on the web (demo notes, "open from the Claude artifact link").
Fails loudly if a text it expects is gone, so a game update cannot silently ship a demo note. Usage: python3 tools/build_www.py"""
import pathlib, shutil, sys
app = pathlib.Path(__file__).resolve().parent.parent
src = app.parent / 'index.html'
www = app / 'www'
s = src.read_text(encoding='utf-8')

NATIVE = "(window.Capacitor&&Capacitor.isNativePlatform&&Capacitor.isNativePlatform())"
SWAPS = [
    # online: the app talks to the FLIX online server, so the failure text is about the connection
    ("Online düello, oyun Claude uygulamasındaki artifact linkinden açılınca çalışır. Arkadaşının da oynayabilmesi için linki ona <b>katılımcı</b> olarak paylaşman gerekir. Şu an bağlantı kurulamadı.",
     "Online sunucuya şu an bağlanılamadı. İnternet bağlantını kontrol edip tekrar dene."),
    # live bulletin: inside the app there is no "open it in Safari" hint
    ("${/github\\.io$/.test(location.hostname)?'':` Claude uygulamasında veri gelmiyorsa oyunu Safari'de aç:`}",
     "${(/github\\.io$/.test(location.hostname)||%s)?'':` Claude uygulamasında veri gelmiyorsa oyunu Safari'de aç:`}" % NATIVE),
    ("</p>${/github\\.io$/.test(location.hostname)?'':`", "</p>${(/github\\.io$/.test(location.hostname)||%s)?'':`" % NATIVE),
    # demo notes
    ("<small>Reklam · demo</small>", "<small>Reklam</small>"),
    ("<div class=\"note\">Demo: gerçek ödeme alınmaz. App Store sürümünde Apple ile ödenir.</div>", "<div class=\"note\">Coin paketleri App Store üzerinden satın alınır.</div>"),
    ("<small>Demo: gerçek ödeme alınmaz. App Store sürümünde Apple ile ödenir.</small>", "<small></small>"),
    ("<div class=\"note\" style=\"text-align:center\">Demo: gerçek ödeme alınmaz. İstediğin zaman iptal edebilirsin.</div>", ""),
    (" Bu sürüm demo, ödeme alınmaz.", ""),
    # App Store: in the app the Club is a one-time coin unlock and the Starter pack has no Club days (director-native.js),
    # so no monthly / yearly wording and no "7 gün Kulüp" promise that the app does not deliver
    ("${ENT.club?'Aktif':PRICE.clubM+' / ay · '+PRICE.clubY+' / yıl'}", "${ENT.club?'Aktif':PRICE.clubM+' · tek seferlik'}"),
    ("<span>1 efsane paket + 3 kıyafet + 7 gün Kulüp</span>", "<span>1 efsane paket + 3 kıyafet</span>"),
    # unlock sheet: the Club button promised "her ay 1.000 coin"; the app's Club is a one-time coin unlock with no monthly coins
    ("<small>her şey açık, her ay 1.000 coin</small>", "<small>tek seferlik, her şey açık</small>"),
    # packSheet (league/season packs): the Club line read like a monthly subscription; in the app it is a one-time coin unlock
    ("<small>bütün maçlar, her ay</small>", "<small>bütün maçlar, tek seferlik</small>"),
    ("'Avrupa geceleri paketi, Atkı, Kasket ve Kulaklık, 7 gün Direktör Kulübü.'", "'Avrupa geceleri paketi, Atkı, Kasket ve Kulaklık.'"),
]
for a, b in SWAPS:
    n = s.count(a)
    if not n: sys.exit('build_www: text not found (game changed?): %r' % a[:80])
    s = s.replace(a, b)

# Offline start (Kaan 2026-11-15 "Direktör açılmıyor"): the app must not wait for the internet to open. The Google Fonts
# stylesheet blocked the first paint and the window 'load' event (the intro waits for it), so on a slow or blocked connection
# the app stayed on the black FLIX intro. The fonts and three.js now ship inside the app (app/native/fonts, three.min.js).
import re as _re
_n = len(_re.findall(r'<link rel="(?:preconnect|stylesheet)" href="https://fonts\.(?:googleapis|gstatic)\.com[^>]*>', s))
if _n < 1: sys.exit('build_www: Google Fonts link not found (game changed?)')
s = _re.sub(r'<link rel="preconnect" href="https://fonts\.(?:googleapis|gstatic)\.com"[^>]*>\n?', '', s)
s = _re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>', '<link rel="stylesheet" href="fonts/fonts.css">', s)
_th = "const TH_URLS=['https://cdnjs"
if _th not in s: sys.exit('build_www: TH_URLS not found')
s = s.replace(_th, "const TH_URLS=['three.min.js','https://cdnjs")
shutil.rmtree(www / 'fonts', ignore_errors=True); shutil.copytree(app / 'native' / 'fonts', www / 'fonts')
shutil.copy(app / 'native' / 'three.min.js', www / 'three.min.js')
if 'fonts.googleapis.com' in s: sys.exit('build_www: Google Fonts still referenced')
HEAD = ['flix-net.js', 'ads-config.js', 'ads.js', 'native-bridge.js']
END = ['director-native.js', 'flix-privacy.js']
for f in HEAD + END: shutil.copy(app / 'native' / f, www / f)
i = s.find('<script')
if i < 0: sys.exit('build_www: no <script> in index.html')
s = s[:i] + ''.join('<script src="%s"></script>' % f for f in HEAD) + s[i:]
j = s.rfind('</body>')
if j < 0: sys.exit('build_www: no </body>')
s = s[:j] + ''.join('<script src="%s"></script>' % f for f in END) + s[j:]
left = [k for k in ('Demo: gerçek ödeme', 'Reklam · demo', 'artifact linkinden') if k in s]
if left: sys.exit('build_www: web-only text left: %s' % left)
(www / 'index.html').write_text(s, encoding='utf-8')
print('www/index.html written from', src.name, len(s), 'bytes; app scripts:', ', '.join(HEAD + END))
