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
  function fuelPrices(data, now = Date.now()) {
    if (data?.price_type !== 'pump_average' || data?.currency !== 'DKK' || data?.unit !== 'DKK/l' || data?.source_chain !== 'OK') throw new Error('Ingen dokumenterede pumpepriser');
    const petrol95 = number(data.petrol95), diesel = number(data.diesel);
    if (![petrol95, diesel].every(value => Number.isFinite(value) && value >= 5 && value <= 60)) throw new Error('Ugyldige pumpepriser');
    const checked = Date.parse(data.checked_at || data.updated);
    if (!Number.isFinite(checked) || checked > now + 600000 || now - checked > 48 * 3600000) throw new Error('Pumpepriserne er forældede');
    for (const key of ['petrol95', 'diesel']) if (!Number.isInteger(data.coverage?.[key]) || data.coverage[key] < 1) throw new Error('Manglende prisdækning');
    return { ...data, petrol95, diesel };
  }
  function fuelLabel(data, type, now = Date.now()) {
    const snapshot = fuelPrices(data, now);
    const time = new Intl.DateTimeFormat('da-DK', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Copenhagen' }).format(new Date(snapshot.checked_at || snapshot.updated));
    const label = type ? 'Gns. fra ' + snapshot.coverage[type] + ' OK-stationer' : 'OK-pumpepriser · gennemsnit';
    return label + ' · kontrolleret ' + time;
  }
  global.EVCore = { number, getStored, setStored, getArea, setArea, fetchJSON, electricPrice, fuelPrices, fuelLabel };
})(window);
