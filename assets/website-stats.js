(function (win, doc) {
  'use strict';
  // Metricool's supplied be.js sends hash, u, bw, bh and ref to this pixel.
  // Keep that protocol local so calculation values and identifying URL parameters
  // never leave the site. Statistics are optional and sent without credentials.
  if (win.EVWebsiteStats) return;
  const nav = win.navigator || {};
  if (nav.webdriver === true || nav.globalPrivacyControl === true ||
      nav.doNotTrack === '1' || win.doNotTrack === '1') return;
  const KEY = 'evberegn_stats_choice_v1';
  const HASH = 'b88f7c584949360baea27864aa2e317e';
  let sent = false;
  let notice;
  let settings;
  function readChoice() {
    try { return win.localStorage.getItem(KEY); } catch (_) { return null; }
  }
  let choice = readChoice();
  function pageURL() {
    const current = new URL(win.location.href);
    const clean = new URL(current.origin + current.pathname);
    ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content'].forEach(function (key) {
      const value = current.searchParams.get(key);
      if (value && /^[a-zA-Z0-9_.-]{1,100}$/.test(value)) clean.searchParams.set(key, value);
    });
    return clean.href;
  }
  function referrer() {
    try {
      const url = new URL(doc.referrer);
      return /^https?:$/.test(url.protocol) ? url.origin + '/' : '';
    } catch (_) { return ''; }
  }
  function measure() {
    if (sent || choice !== 'allow') return;
    sent = true;
    try {
      const url = new URL('https://tracker.metricool.com/c3po.jpg');
      url.searchParams.set('hash', HASH);
      url.searchParams.set('u', pageURL());
      url.searchParams.set('bw', String(win.innerWidth));
      url.searchParams.set('bh', String(win.innerHeight));
      const source = referrer();
      if (source) url.searchParams.set('ref', source);
      if (typeof win.fetch === 'function') {
        win.fetch(url.href, {mode: 'no-cors', credentials: 'omit', referrerPolicy: 'no-referrer', cache: 'no-store', keepalive: true}).catch(function () {});
      } else {
        const pixel = new Image();
        pixel.crossOrigin = 'anonymous';
        pixel.referrerPolicy = 'no-referrer';
        pixel.src = url.href;
      }
    } catch (_) { /* Optional statistics must never interrupt a calculator. */ }
  }
  function choose(value) {
    choice = value;
    try { win.localStorage.setItem(KEY, value); } catch (_) {}
    if (notice) notice.remove();
    notice = null;
    measure();
    if (settings) settings.focus({preventScroll: true});
  }
  function showSettings() {
    if (notice) return;
    notice = doc.createElement('section');
    notice.id = 'evStatsNotice';
    notice.setAttribute('role', 'region');
    notice.setAttribute('aria-label', 'Besøgsstatistik');
    notice.innerHTML = '<p>Vil du tillade besøgsstatistik? Vi bruger Metricool til at se, hvordan hjemmesiden bliver brugt. <a href="/om/#statistik">Læs mere</a>.</p><div><button type="button" id="evStatsAllow">Tillad statistik</button><button type="button" id="evStatsDeny">Afvis statistik</button></div>';
    doc.body.appendChild(notice);
    doc.getElementById('evStatsAllow').addEventListener('click', function () { choose('allow'); });
    doc.getElementById('evStatsDeny').addEventListener('click', function () { choose('deny'); });
  }
  function start() {
    const style = doc.createElement('style');
    style.textContent = '#evStatsNotice{position:fixed;z-index:9000;left:16px;bottom:16px;width:calc(100% - 32px);max-width:620px;box-sizing:border-box;padding:16px;border:1px solid #2b5454;border-radius:16px;background:#0c1524;color:#f5f8fb;box-shadow:0 8px 30px #0007;font:14px/1.5 Arial,sans-serif}#evStatsNotice p{margin:0 0 12px}#evStatsNotice a{color:#10ddb2}#evStatsNotice>div{display:flex;flex-wrap:wrap;gap:10px}#evStatsNotice button{flex:1;min-width:120px;padding:10px 12px;border:1px solid #10ddb2;border-radius:9px;background:#0c1524;color:#10ddb2;font:700 14px Arial,sans-serif;cursor:pointer}#evStatsNotice button:focus-visible,#evStatsSettings:focus-visible{outline:2px solid #fff;outline-offset:3px}#evStatsSettings{display:inline-block;margin:12px 0 0 10px;padding:0;border:0;background:none;color:#10ddb2;font:12px Arial,sans-serif;text-decoration:underline;cursor:pointer}';
    doc.head.appendChild(style);
    settings = doc.createElement('button');
    settings.id = 'evStatsSettings';
    settings.type = 'button';
    settings.textContent = 'Statistik';
    settings.setAttribute('aria-label', 'Ændr dit valg om besøgsstatistik');
    settings.addEventListener('click', showSettings);
    (doc.querySelector('footer') || doc.querySelector('main') || doc.body).appendChild(settings);
    if (choice === 'allow') measure();
    else if (choice !== 'deny') showSettings();
  }
  win.EVWebsiteStats = {openSettings: showSettings};
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', start, {once: true});
  else start();
})(window, document);
