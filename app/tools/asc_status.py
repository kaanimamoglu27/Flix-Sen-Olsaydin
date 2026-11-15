#!/usr/bin/env python3
"""App Store Connect durumu: her oyunun son TestFlight build'leri (işlenme durumu, süresi doldu mu) ve
TestFlight'tan gönderilen çökme / geri bildirim kayıtları. Sonuçlar Actions'ta notice olarak görünür."""
import json, os, time, urllib.request, urllib.error, jwt
KEY = os.environ['ASC_KEY_P8']; KID = os.environ['ASC_KEY_ID']; ISS = os.environ['ASC_ISSUER_ID']
tok = jwt.encode({'iss': ISS, 'iat': int(time.time()), 'exp': int(time.time()) + 1100, 'aud': 'appstoreconnect-v1'}, KEY, algorithm='ES256', headers={'kid': KID, 'typ': 'JWT'})
def get(path):
    r = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, headers={'Authorization': 'Bearer ' + tok})
    try: return json.load(urllib.request.urlopen(r, timeout=40))
    except urllib.error.HTTPError as e: return {'error': e.code, 'body': e.read().decode()[:300]}
def note(t, m): print('::notice title=%s::%s' % (t, m.replace('\n', ' | ')[:3000]), flush=True)
apps = get('/v1/apps?limit=50&fields[apps]=name,bundleId')
if 'error' in apps: note('ASC hata', json.dumps(apps)); raise SystemExit
for a in apps['data']:
    aid, name, bid = a['id'], a['attributes']['name'], a['attributes']['bundleId']
    b = get('/v1/builds?filter[app]=%s&sort=-uploadedDate&limit=4&include=preReleaseVersion&fields[builds]=version,processingState,expired,uploadedDate,minOsVersion&fields[preReleaseVersions]=version' % aid)
    pv = {x['id']: x['attributes']['version'] for x in b.get('included', [])}
    rows = []
    for x in b.get('data', []):
        at = x['attributes']; rel = x.get('relationships', {}).get('preReleaseVersion', {}).get('data') or {}
        rows.append('%s (%s) %s%s %s' % (pv.get(rel.get('id'), '?'), at['version'], at['processingState'], ' EXPIRED' if at.get('expired') else '', at['uploadedDate'][:16]))
    note('Build %s' % name, '%s: %s' % (bid, ' ; '.join(rows) or json.dumps(b)[:300]))
    for kind in ('betaFeedbackCrashSubmissions', 'betaFeedbackScreenshotSubmissions'):
        f = get('/v1/apps/%s/%s?limit=8' % (aid, kind))
        if 'error' in f: note('%s %s' % (kind, name), 'hata %s %s' % (f['error'], f['body'][:150])); continue
        for s in f.get('data', []):
            at = s['attributes']; note('%s %s' % ('Çökme' if 'Crash' in kind else 'Geri bildirim', name), json.dumps({k: at.get(k) for k in ('createdDate', 'comment', 'appPlatform', 'deviceModel', 'osVersion', 'buildBundleId', 'appUptimeInMilliseconds', 'batteryPercentage', 'connectionType')}, ensure_ascii=False))
            if 'Crash' in kind:
                lg = get('/v1/betaFeedbackCrashSubmissions/%s/crashLog' % s['id'])
                txt = (lg.get('data') or {}).get('attributes', {}).get('logText', '') if 'error' not in lg else ''
                if txt: note('Çökme log %s' % name, txt[:2800])
