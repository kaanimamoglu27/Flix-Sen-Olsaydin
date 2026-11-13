#!/usr/bin/env python3
"""Info.plist for AdMob after `npx cap add ios`: app id (from native/ads-config.js, env ADMOB_APP_ID overrides; Google's TEST id
when empty or malformed, since a bad id crashes the app at launch), tracking prompt text and SKAdNetwork ids."""
import os, pathlib, plistlib, re
app = pathlib.Path(__file__).resolve().parent.parent
pl_path = app / 'ios' / 'App' / 'App' / 'Info.plist'
cfg = (app / 'native' / 'ads-config.js').read_text(encoding='utf-8')
m = re.search(r"\bIOS_APP_ID:\s*'([^']*)'", cfg)
app_id = (os.environ.get('ADMOB_APP_ID') or '').strip() or (m.group(1).strip() if m else '')
if app_id and not re.fullmatch(r'ca-app-pub-\d{16}~\d{10}', app_id):
    print('WARNING: malformed AdMob app id %r, using the TEST app id' % app_id); app_id = ''
with open(pl_path, 'rb') as f: pl = plistlib.load(f)
pl['GADApplicationIdentifier'] = app_id or 'ca-app-pub-3940256099942544~1458002511'
pl['NSUserTrackingUsageDescription'] = 'Reklamları sana daha uygun göstermek için kullanılır. Hayır dersen oyun aynı şekilde çalışır.'
pl['SKAdNetworkItems'] = [{'SKAdNetworkIdentifier': i} for i in ['cstr6suwn9.skadnetwork', '4fzdc2evr5.skadnetwork', '2fnua5tdw4.skadnetwork', 'ydx93a7ass.skadnetwork', 'p78axxw29g.skadnetwork', 'v72qych5uu.skadnetwork', 'ludvb6z3bs.skadnetwork', 'cp8zw746q7.skadnetwork', '3sh42y64q3.skadnetwork', 'c6k4g5qg8m.skadnetwork', 's39g8k73mm.skadnetwork', '3qy4746246.skadnetwork', 'hs6bdukanm.skadnetwork', 'mlmmfzh3r3.skadnetwork', 'v4nxqhlyqp.skadnetwork', 'wzmmz9fp6w.skadnetwork', 'su67r6k2v3.skadnetwork', 'yclnxrl5pm.skadnetwork', '7ug5zh24hu.skadnetwork', 'gta9lk7p23.skadnetwork', 'vutu7akeur.skadnetwork', 'y5ghdn5j9k.skadnetwork', 'v9wttpbfk9.skadnetwork', 'n38lu8286q.skadnetwork', '47vhws6wlr.skadnetwork', 'kbd757ywx3.skadnetwork', '9t245vhmpl.skadnetwork', 'a2p9lx4jpn.skadnetwork', '22mmun2rn5.skadnetwork', '4468km3ulz.skadnetwork', '2u9pt9hc89.skadnetwork', '8s468mfl3y.skadnetwork', 'ppxm28t8ap.skadnetwork', 'uw77j35x4d.skadnetwork', 'pwa73g5rt2.skadnetwork', '578prtvx9j.skadnetwork', '4dzt52r2t5.skadnetwork', 'tl55sbb4fm.skadnetwork', 'e5fvkxwrpn.skadnetwork', '8c4e2ghe7u.skadnetwork', '3rd42ekr43.skadnetwork', '3qcr597p9d.skadnetwork']]
with open(pl_path, 'wb') as f: plistlib.dump(pl, f)
print('Info.plist: AdMob app id', pl['GADApplicationIdentifier'])
