/* Flix Director (Sen Olsaydın): app-only layer, loaded after the game. The web build never loads it.
   - Ads: the game's demo adShow / rewardAd become AdMob (window.FlixAds, ads.js): rewarded ads only give their reward
     after AdMob's reward callback, interstitials keep the game's own pacing (every 3rd match, none for Club members).
   - Purchases (App Store, window.FlixNative, native-bridge.js): only the 5 Flix Coin packs and the Starter pack are real
     in-app purchases. Everything else (seasons, archive, packs, leagues, outfits, Director Club) is bought with Flix Coin:
     the game's TL prices are shown and charged as coins here (COIN_PER_TL), the Club is a one-time coin unlock on this device.
   Purchases are delivered through window.__dirGrant(id, tx) once per transaction, so a purchase finished after a restart still arrives. */
(function () {
  var Cap = window.Capacitor;
  if (!Cap || !Cap.isNativePlatform || !Cap.isNativePlatform()) return;

  var COIN_IDS = ['director_coins_500', 'director_coins_1200', 'director_coins_2800', 'director_coins_6500', 'director_coins_15000'];
  var STARTER_ID = 'director_starter';
  var COIN_PER_TL = 20;     // 39,99 TL season -> 800 coin (the game's own coin prices use 15-22 coin per TL)
  var CLUB_COINS = 9000;    // Director Club, one time, this device

  var coinsFor = function (tl) {
    var m = String(tl).match(/(\d+)(?:[.,](\d+))?\s*TL/); if (!m) return null;
    var v = parseFloat(m[1] + '.' + (m[2] || '0'));
    return Math.max(100, Math.round(v * COIN_PER_TL / 50) * 50);
  };
  var asCoin = function (n) { return n.toLocaleString('tr-TR') + ' coin'; };
  var fmt = function (n) { return Number(n).toLocaleString('tr-TR'); };

  // ---------- prices: TL -> coin everywhere except the real in-app purchases ----------
  try {
    // where the game already has a coin price (CPRICE) the TL label shows that same coin price
    Object.keys(TPRICE).forEach(function (k) { var c = CPRICE[k] || coinsFor(TPRICE[k]); if (c) TPRICE[k] = asCoin(c); });
    ['pack'].forEach(function (k) { var c = coinsFor(PRICE[k]); if (c) PRICE[k] = asCoin(c); });
    PRICE.clubM = asCoin(CLUB_COINS); PRICE.clubY = asCoin(CLUB_COINS);
    [ACC_PRICE, OUTFIT_PRICE].forEach(function (arr) { for (var i = 0; i < arr.length; i++) { var c = typeof arr[i] === 'string' && coinsFor(arr[i]); if (c) arr[i] = asCoin(c); } });
  } catch (e) { console.warn('director prices', e); }
  // store prices (localized, from Apple) for the real products once the store has loaded
  function syncStorePrices() {
    var N = window.FlixNative; if (!N || !N.price) return;
    COIN_IDS.forEach(function (id, i) { var p = N.price(id); if (p && COINPK[i]) COINPK[i][1] = p; });
    var s = N.price(STARTER_ID); if (s) PRICE.start = s;
  }
  window.addEventListener('flixprices', syncStorePrices);

  // ---------- purchase delivery (once per transaction id) ----------
  var seen = []; try { seen = JSON.parse(localStorage.getItem('fdIapTx') || '[]'); } catch (e) {}
  window.__dirGrant = function (id, tx) {
    if (tx) { if (seen.indexOf(tx) >= 0) return; seen.push(tx); if (seen.length > 80) seen.shift(); try { localStorage.setItem('fdIapTx', JSON.stringify(seen)); } catch (e) {} }
    var i = COIN_IDS.indexOf(id);
    if (i >= 0) { coinAdd(COINPK[i][0], 'Satın alındı'); return; }
    if (id === STARTER_ID && !ENT.start) {
      ENT.start = true; ENT.packs.avrupa = true; ['acc:1', 'acc:2', 'acc:3'].forEach(function (k) { ENT.items[k] = true; });
      saveEnt(); toast('Başlangıç paketi açıldı');
      if (!$('#shop').hidden) shopScreen();
    }
  };

  function iap(id) {
    var N = window.FlixNative;
    if (!N || !N.buy) { toast('App Store şu an açılamadı'); return; }
    N.buy(id).then(function (r) {
      if (r === 'pending') toast('Onay bekleniyor, gelince eklenecek');
      else if (!r) toast('Satın alma tamamlanmadı');
    }, function () { toast('Satın alma tamamlanmadı'); });
  }

  function coinSheet(title, cost, desc, onBuy) {
    var sh = document.createElement('div'); sh.className = 'sheet';
    sh.innerHTML = '<div class="in"><h3 class="disp">' + esc(title) + '</h3><div class="note">' + esc(desc) + '</div>' +
      '<div class="buyp"><b>' + coinTxt(cost) + '</b><small>Sende ' + fmt(coins()) + '</small></div>' +
      '<div class="foot"><button class="btn ghost" data-x>Vazgeç</button><button class="btn" data-ok>Coin ile aç</button></div></div>';
    sh.onclick = function (e) { if (e.target === sh || e.target.closest('[data-x]')) sh.remove(); };
    sh.querySelector('[data-ok]').onclick = function () {
      sh.remove();
      if (coins() < cost) { toast('Coin yetmiyor'); coinShop(); return; }
      coinSpend(cost, function () { onBuy(); saveEnt(); toast('Açıldı'); });
    };
    $('#app').appendChild(sh);
  }

  // the game's purchase sheet: real purchase for coin packs / Starter, coins for everything else
  window.buySheet = function (title, price, desc, onBuy) {
    var i = COINPK.findIndex(function (p) { return title === fmt(p[0]) + ' Flix Coin'; });
    if (i >= 0) return iap(COIN_IDS[i]);
    if (title === 'Başlangıç paketi') { if (ENT.start) { toast('Sende'); return; } return iap(STARTER_ID); }
    var m = String(price).match(/([\d.]+)\s*coin/);
    var cost = m ? parseInt(m[1].replace(/\./g, ''), 10) : coinsFor(price);
    if (!cost) { toast('Bu ürün şu an satışta değil'); return; }
    coinSheet(title, cost, desc, onBuy);
  };

  // Director Club: one-time coin unlock on this device instead of a subscription
  window.clubSheet = function (onDone) {
    if (ENT.club) { onDone && onDone(); return; }
    var sh = document.createElement('div'); sh.className = 'sheet';
    sh.innerHTML = '<div class="in"><h3 class="disp">Direktör Kulübü</h3>' +
      '<ul class="perks"><li>2010\'dan bugüne bütün Süper Lig sezonları</li><li>Bütün efsane maçlar ve haftanın bütün maçları</li><li>Hikaye modunun tamamı</li><li>Bütün hoca kıyafetleri</li><li>Ödüllü özellikler reklamsız, ara reklam yok</li></ul>' +
      '<div class="plans"><button class="card plan best" data-p><b>Kalıcı üyelik</b><em>' + coinTxt(CLUB_COINS) + '</em><small>tek seferlik, bu cihazda</small></button></div>' +
      '<div class="note" style="text-align:center">Flix Coin ile açılır. Coin maç kazanarak, kupa toplayarak, reklam izleyerek ya da mağazadan alınır.</div>' +
      '<div class="foot"><span></span><button class="btn ghost" data-x>Şimdi değil</button></div></div>';
    sh.onclick = function (e) { if (e.target === sh || e.target.closest('[data-x]')) sh.remove(); };
    sh.querySelector('[data-p]').onclick = function () {
      sh.remove();
      if (coins() < CLUB_COINS) { toast('Coin yetmiyor'); coinShop(); return; }
      coinSpend(CLUB_COINS, function () { ENT.club = true; saveEnt(); toast('Kulübe hoş geldin'); onDone && onDone(); });
    };
    $('#app').appendChild(sh);
  };

  // ---------- ads ----------
  window.adShow = function (cb, reward) {
    var F = window.FlixAds;
    if (!F) { cb(); return; }
    if (reward) {
      F.showRewarded(6000).then(function (r) {
        if (r === 'rewarded') cb();
        else if (r === 'unavailable') toast('Şu an reklam yok, biraz sonra tekrar dene');
      }, function () { toast('Şu an reklam yok, biraz sonra tekrar dene'); });
    } else {
      F.showInterstitial().then(function () { cb(); }, function () { cb(); });
    }
  };
  window.rewardAd = function (cb) { if (ENT.club) { cb(); return; } window.adShow(cb, true); };
  if (ENT.club && window.FlixAds) window.FlixAds.setAdsRemoved(true);

  // TL buttons in the unlock sheet buy the same thing with coins here, so only the coin button is shown
  var css = document.createElement('style');
  css.textContent = '.ulk [data-t]{display:none!important}.ulk{grid-template-columns:1fr!important}';
  document.head.appendChild(css);
})();
