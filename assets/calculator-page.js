(function (global) {
  'use strict';
  const api = global.EVCalculators, core = global.EVCore;
  const form = document.getElementById('calculatorForm');
  if (!api || !core || !form) return;
  const id = Number(form.dataset.calculator), definition = api.definitions[id];
  if (!definition) return;
  const field = key => form.elements.namedItem(key);
  const result = document.getElementById('answer');
  const message = document.getElementById('calcMessage');
  const selection = document.getElementById('carSelect');
  const modelNote = document.getElementById('modelNote');
  const priceStatus = document.getElementById('priceStatus');
  const priceButton = document.getElementById('loadPrices');
  const area = document.getElementById('priceArea');
  const dirtyPrices = new Set(), dirtyFields = new Set();
  let catalogue = [], chosen = null, requestToken = 0;
  let electricStatus = 'Elpris: eksempelværdi.', fuelStatus = 'Benzin: eksempelpris.';
  const values = () => Object.fromEntries(definition.fields.map(([key]) => [key, field(key).value]));
  function calculate(report) {
    const inputs = values(), errors = api.validate(id, inputs);
    for (const [key] of definition.fields) {
      field(key).setCustomValidity(errors[key] || '');
      field(key).setAttribute('aria-invalid', errors[key] ? 'true' : 'false');
      document.getElementById('error_' + key).textContent = errors[key] || '';
    }
    if (Object.keys(errors).length) {
      message.textContent = 'Kontrollér de markerede felter.';
      result.innerHTML = '<p>Ret de markerede felter for at få et gyldigt resultat.</p>';
      if (report) { const first = field(Object.keys(errors)[0]); first.focus(); first.reportValidity(); }
      return;
    }
    try {
      result.innerHTML = api.render(id, api.compute(id, inputs));
      message.textContent = '';
    } catch (_) {
      message.textContent = 'Tallene er for store til en gyldig beregning. Prøv mindre værdier.';
      result.textContent = 'Resultatet kunne ikke beregnes.';
    }
  }
  function showPriceStatus() {
    if (priceStatus) priceStatus.textContent = [field('electricPrice') ? electricStatus : '', field('fuelPrice') ? fuelStatus : ''].filter(Boolean).join(' ');
  }
  function requestedCar() {
    const query = new URLSearchParams(global.location.search).get('car');
    const fragment = new URLSearchParams(global.location.hash.slice(1)).get('bil');
    const slug = query || fragment || '';
    return slug === 'hyundai-ioniq-7-standard' ? 'hyundai-ioniq-9-rwd-advanced' : slug;
  }
  function carryCar() {
    document.querySelectorAll('[data-carry-car]').forEach(link => {
      const url = new URL(link.href, global.location.href);
      url.hash = chosen ? 'bil=' + encodeURIComponent(chosen.slug) : '';
      link.href = url.href;
    });
  }
  function selectCar(slug, updateURL, preserveManual = false) {
    chosen = catalogue.find(car => car.slug === slug) || null;
    selection.value = chosen ? chosen.slug : '';
    if (chosen) {
      const keys = { battery: 'battery', consumption: 'consumption', price: 'price' };
      const inserted = [];
      for (const [inputName, carName] of Object.entries(keys)) {
        if (!field(inputName) || (preserveManual && dirtyFields.has(inputName))) continue;
        if (Number.isFinite(chosen[carName])) { field(inputName).value = chosen[carName]; inserted.push(inputName); }
        else field(inputName).value = field(inputName).defaultValue;
      }
      const hasData = Object.entries(keys).some(([inputName, carName]) => field(inputName) && Number.isFinite(chosen[carName]));
      modelNote.textContent = hasData ? 'Bildata valgt. Ret tallene efter behov.' : 'Producentdata er ikke bekræftet. Tilpas eksempelværdierne.';
      if (id === 8) modelNote.textContent += ' Angiv selv gennemsnitlig ladeeffekt.';
    } else {
      for (const key of ['battery','consumption','price']) if (field(key) && !(preserveManual && dirtyFields.has(key))) field(key).value = field(key).defaultValue;
      modelNote.textContent = slug ? 'Modellen er ikke i biloversigten. Brug egne tal.' : '';
    }
    if (updateURL) {
      const url = new URL(global.location.href); url.searchParams.delete('car');
      url.hash = chosen ? 'bil=' + encodeURIComponent(chosen.slug) : '';
      global.history.replaceState(null, '', url.href);
    }
    carryCar(); calculate(false);
  }
  form.addEventListener('submit', event => { event.preventDefault(); calculate(true); });
  form.addEventListener('input', event => {
    if(event.target.name) dirtyFields.add(event.target.name);
    if (['electricPrice', 'fuelPrice'].includes(event.target.name)) {
      dirtyPrices.add(event.target.name);
      if (event.target.name === 'electricPrice') electricStatus = 'Elpris: egen indtastning.';
      else fuelStatus = 'Benzin: egen indtastning.';
      showPriceStatus();
    }
    calculate(false);
  });
  document.getElementById('calculateButton').disabled = false;
  document.querySelectorAll('[data-js-only]').forEach(node => { node.hidden = false; });
  selection.addEventListener('change', () => selectCar(selection.value, true));
  global.addEventListener('hashchange', () => { if (catalogue.length) selectCar(requestedCar(), false); });
  if (area) {
    area.value = core.getArea();
    area.addEventListener('change', () => {
      core.setArea(area.value); requestToken++;
      electricStatus = 'Elområde ændret. Hent en ny pris, eller brug din egen.';
      showPriceStatus();
      if (priceButton) { priceButton.disabled = false; priceButton.textContent = 'Hent vejledende priser'; }
    });
  }
  if (priceButton) priceButton.addEventListener('click', async () => {
    const token = ++requestToken, region = core.setArea(area.value);
    dirtyPrices.clear(); priceButton.disabled = true; priceButton.textContent = 'Henter priser…';
    const tasks = [
      (async () => {
        try {
          const data = await core.fetchJSON('https://elpriser.org/api/now?area=' + region + '&mode=inkl_alt', { cache: 'no-store' });
          const value = core.electricPrice(data); if (!Number.isFinite(value)) throw new Error('invalid');
          if (token !== requestToken || dirtyPrices.has('electricPrice')) return;
          field('electricPrice').value = value.toFixed(2);
          electricStatus = region + ' · elpriser.org · ' + new Date().toLocaleTimeString('da-DK', {hour:'2-digit',minute:'2-digit'}) + '. Din aftale kan afvige.';
        } catch (_) { if (token === requestToken && !dirtyPrices.has('electricPrice')) electricStatus = 'Elprisen kunne ikke hentes. Brug din egen pris.'; }
      })()
    ];
    if (field('fuelPrice')) tasks.push((async () => {
      try {
        const data = await core.fetchJSON('/data/fuel-prices.json', { cache: 'no-cache' });
        const value = core.number(data.petrol95); if (!Number.isFinite(value) || value < 0) throw new Error('invalid');
        if (token !== requestToken || dirtyPrices.has('fuelPrice')) return;
        field('fuelPrice').value = value.toFixed(2);
        fuelStatus = 'Benzin: ' + (data.source || 'markedspris') + (data.source_date ? ' · ' + data.source_date : '') + '.';
      } catch (_) { if (token === requestToken && !dirtyPrices.has('fuelPrice')) fuelStatus = 'Benzinprisen kunne ikke hentes. Brug din egen pris.'; }
    })());
    await Promise.allSettled(tasks);
    if (token === requestToken) {
      priceButton.disabled = false; priceButton.textContent = 'Hent vejledende priser';
      showPriceStatus(); calculate(false);
    }
  });
  core.fetchJSON('/assets/calculator-cars.json?v=20261024-pages1', { cache: 'force-cache' }).then(data => {
    catalogue = data.models.filter(car => /^[a-z0-9-]+$/.test(car.slug));
    for (const car of catalogue) { const option = document.createElement('option'); option.value = car.slug; option.textContent = car.label; selection.appendChild(option); }
    selection.disabled = false; selectCar(requestedCar(), false, true);
  }).catch(() => { modelNote.textContent = 'Biloversigten kunne ikke hentes. Beregneren virker med dine egne tal.'; });
  showPriceStatus(); calculate(false);
})(window);
