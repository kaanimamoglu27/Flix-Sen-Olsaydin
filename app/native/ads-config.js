/* Flix Director: the one place for AdMob ids and switches (app only; the web build never loads AdMob).
   Real ids come from AdMob (apps.admob.com > Apps > Flix Director > App settings / Ad units).
   An id left empty (or not in the ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX form) falls back to Google's TEST ad unit.
   IOS_APP_ID also goes into Info.plist (GADApplicationIdentifier) via tools/ios_admob.py.
   Ad pacing is a game rule (index.html interAdG: every 3rd match, none for Director Club members). */
window.FLIX_ADS_CONFIG = {
  forceTestAds: false,
  ids: {
    IOS_APP_ID: 'ca-app-pub-9939733946730095~1768089142',        // ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX
    IOS_REWARDED: 'ca-app-pub-9939733946730095/2730971979',      // rewarded: +40 coin (5 a day), undo a decision, sponsor money
    IOS_INTERSTITIAL: 'ca-app-pub-9939733946730095/1417890305',  // interstitial: before every 3rd match (none for Director Club)
    IOS_BANNER: '',
    ANDROID_REWARDED: '',
    ANDROID_INTERSTITIAL: '',
    ANDROID_BANNER: ''
  },
  bannerEnabled: false,
  // Asks the iPhone's "Allow tracking?" question once. If false, also update App Store Connect > App Privacy.
  requestTracking: true,
  testDevices: []
};
