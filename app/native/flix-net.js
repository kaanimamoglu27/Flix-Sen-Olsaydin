/* FLIX online client: provides window.claude.use('db' | 'user' | 'room') on top of the FLIX online server,
   Lazy: nothing connects at app launch; the first claude.use('db' | 'room') (Online screen, real-match crowd stats) opens the socket.
   so the same online code runs inside the iOS app (where the claude.ai artifact services do not exist).
   If window.claude.use already exists (game opened from its claude.ai link) nothing is changed.
   Server: flix-kick-up/server/src/net.js (Render service flix-kick-up-online, path /net). Shared by Flix Direktör (db, user) and FLIX Bomb (room). */
(function () {
  if (window.claude && window.claude.use) return;
  var URL = window.FLIX_NET_URL || 'wss://flix-kick-up-online.onrender.com/net';

  // stable anonymous player id for this install
  var uid = null;
  try { uid = localStorage.getItem('flixNetUid'); } catch (e) {}
  if (!uid || !/^[a-z0-9]{8,40}$/.test(uid)) {
    uid = ''; var c = 'abcdefghijklmnopqrstuvwxyz0123456789';
    for (var i = 0; i < 20; i++) uid += c[Math.floor(Math.random() * c.length)];
    try { localStorage.setItem('flixNetUid', uid); } catch (e) {}
  }

  var ws = null, open = false, seq = 0, pending = {}, queue = [], backoff = 500, opening = null;
  var docSubs = {};   // sid -> {path, fn}
  var roomState = {}; // room -> {peer, presence, peers, listeners:Set}

  function connect() {
    if (opening) return opening;
    opening = new Promise(function (resolve) {
      try { ws = new WebSocket(URL); } catch (e) { opening = null; retry(); return resolve(false); }
      var done = false;
      var to = setTimeout(function () { if (!done) { done = true; try { ws.close(); } catch (e) {} resolve(false); } }, 12000);
      ws.onopen = function () {
        open = true; backoff = 500;
        raw({ op: 'hello', uid: uid });
        // restore subscriptions and rooms after a reconnect
        for (var sid in docSubs) raw({ op: 'sub', sid: sid, path: docSubs[sid].path });
        for (var r in roomState) rejoin(r);
        var q = queue; queue = []; q.forEach(function (m) { ws.send(JSON.stringify(m)); });
        if (!done) { done = true; clearTimeout(to); resolve(true); }
      };
      ws.onmessage = function (e) {
        var m; try { m = JSON.parse(e.data); } catch (x) { return; }
        if (m.id && pending[m.id]) { var p = pending[m.id]; delete pending[m.id]; clearTimeout(p.t); if (m.error) p.rej(new Error(m.error)); else p.res(m); return; }
        if (m.ev === 'doc' && docSubs[m.sid]) { var d = m.data; docSubs[m.sid].fn(snap(d)); }
        if (m.ev === 'peers' && roomState[m.room]) { roomState[m.room].peers = m.peers; roomState[m.room].listeners.forEach(function (f) { try { f(); } catch (x) {} }); }
      };
      ws.onclose = function () {
        open = false; opening = null;
        for (var id in pending) { pending[id].rej(new Error('disconnected')); clearTimeout(pending[id].t); } pending = {};
        if (!done) { done = true; clearTimeout(to); resolve(false); }
        retry();
      };
      ws.onerror = function () {};
    });
    return opening;
  }
  // reconnect on its own only while something is listening (a duel / live room / queued message). Otherwise the next
  // call() connects again, so an offline app does not keep dialing the server in the background.
  function busy() { for (var k in docSubs) return true; for (var r in roomState) return true; return queue.length > 0; }
  function retry() { if (!busy()) return; setTimeout(function () { if (!open && busy()) connect(); }, backoff); backoff = Math.min(backoff * 2, 15000); }
  function raw(m) { if (open && ws && ws.readyState === 1) ws.send(JSON.stringify(m)); else queue.push(m); }
  function call(op, args) {
    return connect().then(function () {
      return new Promise(function (res, rej) {
        var id = 'c' + (++seq);
        var t = setTimeout(function () { delete pending[id]; rej(new Error('timeout')); }, 10000);
        pending[id] = { res: res, rej: rej, t: t };
        raw(Object.assign({ id: id, op: op }, args || {}));
      });
    });
  }
  function snap(d) { return { exists: d != null, data: function () { return d == null ? undefined : d; } }; }

  // ---------- db: doc(path).get/set/update/onSnapshot, collection(name).where(f,'==',v).limit(n).get() ----------
  var db = {
    doc: function (path) {
      return {
        get: function () { return call('get', { path: path }).then(function (m) { return snap(m.data); }); },
        set: function (data) { return call('set', { path: path, data: data }).then(function () {}); },
        update: function (data) { return call('update', { path: path, data: data }).then(function () {}); },
        onSnapshot: function (fn, err) {
          var sid = 's' + (++seq); docSubs[sid] = { path: path, fn: fn };
          connect().then(function (ok) { if (!ok && err) err(new Error('offline')); raw({ op: 'sub', sid: sid, path: path }); });
          return function () { delete docSubs[sid]; raw({ op: 'unsub', sid: sid }); };
        }
      };
    },
    collection: function (coll) {
      var where = [], lim = 50;
      var q = {
        where: function (f, op, v) { where.push([f, op, v]); return q; },
        limit: function (n) { lim = n; return q; },
        get: function () {
          return call('query', { coll: coll, where: where, limit: lim }).then(function (m) {
            var docs = (m.docs || []).map(function (d) { return { id: d.id, data: function () { return d.data; } }; });
            return { docs: docs, empty: !docs.length, size: docs.length, forEach: function (f) { docs.forEach(f); } };
          });
        }
      };
      return q;
    }
  };

  // ---------- user: id(), profiles([ids]), setName(name) ----------
  var user = {
    id: function () { return Promise.resolve(uid); },
    profiles: function (ids) { return call('profiles', { ids: ids }).then(function (m) { return m.profiles || {}; }); },
    setName: function (name) { return call('profile', { name: name }).then(function () {}); }
  };

  // ---------- room: join(name) -> {presence(obj), peers(), onPeers(fn, err), leave()} ----------
  function rejoin(name) {
    var st = roomState[name];
    call('join', { room: name }).then(function (m) {
      st.peer = m.peer; st.peers = m.peers;
      if (st.presence) raw({ op: 'presence', room: name, data: st.presence });
      st.listeners.forEach(function (f) { try { f(); } catch (x) {} });
    }, function () {});
  }
  var room = {
    join: function (name) {
      return call('join', { room: name }).then(function (m) {
        var st = roomState[name] = { peer: m.peer, presence: null, peers: m.peers || [], listeners: new Set() };
        return {
          presence: function (data) {
            st.presence = Object.assign({}, st.presence || {}, data || {});
            return call('presence', { room: name, data: data }).then(function () {});
          },
          peers: function () {
            return st.peers.map(function (p) { return { peer: p.peer, presence: p.presence, isMe: p.peer === st.peer, sameTab: p.peer === st.peer, kind: 'user' }; });
          },
          onPeers: function (fn, err) { st.listeners.add(fn); return function () { st.listeners.delete(fn); }; },
          leave: function () { delete roomState[name]; return call('leave', { room: name }).then(function () {}, function () {}); }
        };
      });
    }
  };

  window.claude = window.claude || {};
  window.claude.use = function (name) {
    if (name === 'db') return connect().then(function (ok) { return ok ? db : null; });
    if (name === 'user') return Promise.resolve(user);
    if (name === 'room') return connect().then(function (ok) { return ok ? room : null; });
    return Promise.resolve(null);
  };
})();
