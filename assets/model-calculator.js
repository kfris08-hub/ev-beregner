(function (global) {
  'use strict';
  const core = global.EVCore;
  const consumption = core.number(document.currentScript.dataset.consumption);
  const field = id => document.getElementById(id);
  const fuel = { petrol95: 18.49, diesel: 20.19 };
  let priceStatus = 'Eksempelpris – indtast din elpris, eller afvent automatisk opdatering.';
  let fuelStatus = 'Benzin/diesel: vejledende eksempelpriser.';
  let electricRequest = 0;
  function showStatus() { field('liveNote').textContent = priceStatus + ' ' + fuelStatus; }
  const kroner = n => Math.round(n).toLocaleString('da-DK') + ' kr.';
  function calculate() {
    const km = core.number(field('km').value), price = core.number(field('ep').value);
    const validKm = Number.isFinite(km) && km >= 0;
    const validPrice = Number.isFinite(price);
    field('km').setCustomValidity(validKm ? '' : 'Indtast et kilometertal på 0 eller mere.');
    field('ep').setCustomValidity(validPrice ? '' : 'Indtast en gyldig elpris.');
    const ids = ['r100', 'rkm', 'ryear', 'rkwh', 'evAnnual', 'petAnnual', 'dieselAnnual'];
    if (!validKm || !validPrice || !Number.isFinite(consumption)) {
      ids.forEach(id => { field(id).textContent = '–'; });
      field('liveNote').textContent = 'Indtast et gyldigt kilometertal og en elpris for at beregne.';
      return false;
    }
    const kwh = km * consumption / 100;
    const annual = kwh * price;
    field('r100').textContent = (consumption * price).toFixed(2).replace('.', ',') + ' kr.';
    field('rkm').textContent = (consumption * price / 100).toFixed(2).replace('.', ',') + ' kr.';
    field('ryear').textContent = kroner(annual);
    field('rkwh').textContent = Math.round(kwh).toLocaleString('da-DK') + ' kWh';
    field('evAnnual').textContent = kroner(annual);
    field('petAnnual').textContent = kroner(km / 16 * fuel.petrol95);
    field('dieselAnnual').textContent = kroner(km / 20 * fuel.diesel);
    field('petPrice').textContent = fuel.petrol95.toFixed(2).replace('.', ',') + ' kr./l';
    field('dieselPrice').textContent = fuel.diesel.toFixed(2).replace('.', ',') + ' kr./l';
    showStatus();
    return true;
  }
  async function loadFuel() {
    try {
      const data = await core.fetchJSON('/data/fuel-prices.json', { cache: 'no-cache' });
      const petrol = core.number(data.petrol95), diesel = core.number(data.diesel);
      if (!Number.isFinite(petrol) || petrol < 0 || !Number.isFinite(diesel) || diesel < 0) throw new Error('Ugyldig brændstofpris');
      fuel.petrol95 = petrol; fuel.diesel = diesel;
      fuelStatus = 'Benzin/diesel: ' + (data.source || 'vejledende markedspris') + (data.source_date ? ' · ' + data.source_date : '') + '.';
    } catch (_) { fuelStatus = 'Brændstofpriser kunne ikke opdateres – vejledende eksempelpriser bruges.'; }
    calculate();
  }
  async function loadElectric() {
    const request = ++electricRequest;
    const area = core.setArea(field('area').value);
    priceStatus = 'Henter ' + area + '-elpris – den viste eksempelpris kan ændres manuelt.';
    showStatus();
    try {
      const data = await core.fetchJSON('https://elpriser.org/api/now?area=' + area + '&mode=inkl_alt', { cache: 'no-store' });
      const price = core.electricPrice(data);
      if (!Number.isFinite(price)) throw new Error('Ugyldig elpris');
      if (request !== electricRequest) return;
      field('ep').value = price.toFixed(2);
      priceStatus = 'Automatisk ' + area + '-elpris fra elpriser.org · hentet ' + new Date().toLocaleTimeString('da-DK', { hour: '2-digit', minute: '2-digit' }) + '.';
    } catch (_) {
      if (request !== electricRequest) return;
      priceStatus = 'Elpris kunne ikke opdateres – den viste pris bruges og kan ændres manuelt.';
    }
    calculate();
  }
  global.calculate = calculate;
  field('area').value = core.getArea();
  field('area').addEventListener('change', loadElectric);
  field('km').addEventListener('input', calculate);
  field('ep').addEventListener('input', () => {
    electricRequest++;
    priceStatus = 'Manuelt indtastet elpris.';
    calculate();
  });
  calculate();
  loadFuel();
  loadElectric();
})(window);
