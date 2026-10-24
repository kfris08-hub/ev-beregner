(function (global) {
  'use strict';
  const number = value => {
    if (value == null || String(value).trim() === '') return NaN;
    const result = Number(value);
    return Number.isFinite(result) ? result : NaN;
  };
  function getStored(key, fallback = null) {
    try { return global.localStorage.getItem(key) ?? fallback; }
    catch (_) { return fallback; }
  }
  function setStored(key, value) {
    try { global.localStorage.setItem(key, value); } catch (_) {}
  }
  function getArea() {
    return (getStored('evRegion') || getStored('evArea')) === 'DK2' ? 'DK2' : 'DK1';
  }
  function setArea(value) {
    const area = value === 'DK2' ? 'DK2' : 'DK1';
    setStored('evRegion', area);
    setStored('evArea', area);
    return area;
  }
  async function fetchJSON(url, options = {}, timeout = 8000) {
    const controller = new AbortController();
    let timer;
    try {
      return await Promise.race([
        (async () => {
          const response = await global.fetch(url, { ...options, signal: controller.signal });
          if (!response.ok) throw new Error('HTTP ' + response.status);
          return response.json();
        })(),
        new Promise((_, reject) => {
          timer = global.setTimeout(() => {
            controller.abort();
            reject(new Error('Prisopslaget tog for lang tid'));
          }, timeout);
        })
      ]);
    } finally { global.clearTimeout(timer); }
  }
  function electricPrice(data) {
    return number(typeof data === 'number' ? data : data?.price ?? data?.pris ?? data?.total ?? data?.value ?? data?.kwh);
  }
  global.EVCore = { number, getStored, setStored, getArea, setArea, fetchJSON, electricPrice };
})(window);
