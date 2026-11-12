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
  const sharing = global.EVCalculationShare, shareStatus = document.getElementById('shareStatus');
  const shareButton = document.getElementById('shareCalculation'), shareURL = document.getElementById('shareURL');
  const keys = definition.fields.map(([key]) => key);
  const diesel = definition.fields.some(field => field[3] === 'liveDiesel'), fuelKind = diesel ? 'diesel' : 'petrol95', fuelName = diesel ? 'Diesel' : 'Benzin';
  let catalogue = [], chosen = null, requestToken = 0, resultValid = true, pdfURL = '';
  let electricStatus = 'Elpris: eksempelværdi.', fuelStatus = fuelName + ': eksempelpris.';
  const values = () => Object.fromEntries(definition.fields.map(([key]) => [key, field(key).value]));
  function calculate(report) {
    clearPDF();
    const inputs = values(), errors = api.validate(id, inputs);
    resultValid = false;
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
      message.textContent = ''; resultValid = true;
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
        else field(inputName).value = inputName === 'price' && chosen.availability === 'discontinued' ? '' : field(inputName).defaultValue;
      }
      const hasData = Object.entries(keys).some(([inputName, carName]) => field(inputName) && Number.isFinite(chosen[carName]));
      modelNote.textContent = hasData ? 'Bildata valgt. Ret tallene efter behov.' : 'Producentdata er ikke bekræftet. Tilpas eksempelværdierne.';
      if (chosen.price_status === 'catalogue' && field('price')) modelNote.textContent += ' Katalogpris – ret til din købspris.';
      if (chosen.availability === 'discontinued') modelNote.textContent = 'Tidligere model (' + chosen.model_year + ').' + (field('price') ? ' Indtast egen købspris.' : ' Ret tallene efter behov.');
      if (field('battery') && !['net','netto'].includes(chosen.battery_basis)) modelNote.textContent += ' Kontrollér brugbar batterikapacitet.';
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
    if (shareStatus) shareStatus.textContent = ''; if (shareURL) shareURL.hidden = true;
    if (['electricPrice', 'fuelPrice'].includes(event.target.name)) {
      dirtyPrices.add(event.target.name);
      if (event.target.name === 'electricPrice') electricStatus = 'Elpris: egen indtastning.';
      else fuelStatus = fuelName + ': egen indtastning.';
      showPriceStatus();
    }
    calculate(false);
  });
  document.getElementById('calculateButton').disabled = false;
  document.querySelectorAll('[data-js-only]').forEach(node => { node.hidden = false; });
  selection.addEventListener('change', () => { shareStatus.textContent = ''; shareURL.hidden = true; selectCar(selection.value, true); });
  global.addEventListener('hashchange', () => { if (catalogue.length) selectCar(requestedCar(), false); restoreShared(); calculate(false); });
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
    shareStatus.textContent = ''; shareURL.hidden = true;
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
        const snapshot = core.fuelPrices(data), value = snapshot[fuelKind];
        if (token !== requestToken || dirtyPrices.has('fuelPrice')) return;
        field('fuelPrice').value = value.toFixed(2);
        fuelStatus = fuelName + ': ' + core.fuelLabel(data, fuelKind) + '.';
      } catch (_) { if (token === requestToken && !dirtyPrices.has('fuelPrice')) fuelStatus = fuelName + 'prisen kunne ikke hentes. Brug din egen pris.'; }
    })());
    await Promise.allSettled(tasks);
    if (token === requestToken) {
      priceButton.disabled = false; priceButton.textContent = 'Hent vejledende priser';
      showPriceStatus(); calculate(false);
    }
  });
  function restoreShared() {
    if (!sharing) return;
    const saved = sharing.decode(global.location.hash, id, keys);
    if (!saved) return;
    if (saved.error || Object.keys(api.validate(id, saved.values)).length) {
      shareStatus.textContent = 'Linkets tal kunne ikke indlæses. Brug eksempelværdier eller dine egne tal.'; return;
    }
    for (const [key, value] of Object.entries(saved.values)) { field(key).value = value; dirtyFields.add(key); if (['electricPrice','fuelPrice'].includes(key)) dirtyPrices.add(key); }
    requestToken++; if (priceButton) { priceButton.disabled = false; priceButton.textContent = 'Hent vejledende priser'; }
    if (saved.area && area) { area.value = saved.area; core.setArea(saved.area); }
    if (field('electricPrice')) electricStatus = 'Elpris: fra delt beregning.';
    if (field('fuelPrice')) fuelStatus = fuelName + ': fra delt beregning.';
    shareStatus.textContent = 'Tal fra en delt beregning. Priser kan have ændret sig.';
    showPriceStatus();
  }
  if (shareButton && sharing) shareButton.addEventListener('click', async () => {
    calculate(false); if (!resultValid) { shareStatus.textContent = 'Ret tallene, før du deler beregningen.'; return; }
    try {
      const base = document.querySelector('link[rel="canonical"]').href;
      const url = sharing.encode(base, id, keys, values(), chosen ? chosen.slug : requestedCar(), area ? area.value : '');
      if (typeof navigator.share === 'function') {
        await navigator.share({title: document.title, text: 'Min beregning på EV Beregner', url});
        shareStatus.textContent = 'Linket til beregningen er klar.';
      } else if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
        await navigator.clipboard.writeText(url); shareStatus.textContent = 'Link kopieret. Modtageren får de samme indtastede tal.';
      } else { shareURL.hidden = false; shareURL.value = url; shareURL.focus(); shareURL.select(); shareStatus.textContent = 'Kopiér linket nedenfor.'; }
    } catch (error) {
      if (error.name === 'AbortError') { shareStatus.textContent = 'Deling annulleret.'; return; }
      shareURL.hidden = false;
      try { shareURL.value = sharing.encode(document.querySelector('link[rel="canonical"]').href, id, keys, values(), chosen ? chosen.slug : requestedCar(), area ? area.value : ''); } catch (_) { shareURL.hidden = true; }
      shareStatus.textContent = 'Brug linkfeltet til at kopiere beregningen.'; if (!shareURL.hidden) { shareURL.focus(); shareURL.select(); }
    }
  });
  function clearPDF() {
    const link = document.getElementById('pdfDownload');
    if (link) { link.hidden = true; link.removeAttribute('href'); }
    if (pdfURL) { global.URL.revokeObjectURL(pdfURL); pdfURL = ''; }
  }
  function resultLines() {
    const lines = []; let current = '';
    const flush = () => { const text = current.replace(/\s+/g, ' ').trim(); if (text) lines.push(text); current = ''; };
    function visit(node) {
      if (node.nodeType === 3) { current += node.textContent; return; }
      if (node.nodeType !== 1) return;
      if (node.tagName === 'TABLE') { flush(); for (const row of node.rows) lines.push(Array.from(row.cells, cell => cell.textContent.trim()).join(': ')); return; }
      if (node.tagName === 'BR') { flush(); return; }
      const block = ['P','DIV','LI','H2','H3'].includes(node.tagName);
      if (block) flush();
      for (const child of node.childNodes) visit(child);
      if (block) flush();
    }
    visit(result); flush(); return lines;
  }
  const pdfButton = document.getElementById('downloadCalculation');
  if (pdfButton) pdfButton.addEventListener('click', () => {
    calculate(false);
    if (!resultValid) { shareStatus.textContent = 'Ret tallene, før du gemmer en PDF.'; return; }
    try {
      const source = document.querySelector('link[rel="canonical"]').href;
      const report = {
        title: document.querySelector('h1').textContent, savedAt: new Date().toLocaleString('da-DK'),
        car: chosen ? chosen.label : 'Egne tal',
        fields: definition.fields.map(([key, label]) => ({ label, value: field(key).value.replace('.', ',') })),
        result: resultLines(), notes: [modelNote.textContent, priceStatus ? priceStatus.textContent : ''], source,
        shareURL: sharing ? sharing.encode(source, id, keys, values(), chosen ? chosen.slug : requestedCar(), area ? area.value : '') : ''
      };
      const bytes = global.EVCalculationPDF.build(report);
      pdfURL = global.URL.createObjectURL(new Blob([bytes], { type: 'application/pdf' }));
      const link = document.getElementById('pdfDownload');
      link.href = pdfURL; link.download = 'evberegner-' + new URL(source).pathname.split('/').filter(Boolean).pop() + '-' + new Date().toISOString().slice(0, 10) + '.pdf';
      link.hidden = false; link.click();
      shareStatus.textContent = 'PDF-filen er klar. Brug Åbn PDF, hvis download ikke starter.';
    } catch (_) { clearPDF(); shareStatus.textContent = 'PDF-filen kunne ikke oprettes. Prøv igen, eller brug Print i browseren.'; }
  });
  const printButton = document.getElementById('printCalculation');
  if (printButton) printButton.addEventListener('click', () => {
    calculate(false);
    if (!resultValid) { shareStatus.textContent = 'Ret tallene, før du printer.'; return; }
    shareStatus.textContent = 'Hvis printdialogen ikke åbner, kan du bruge Gem PDF.';
    try { if (typeof global.print === 'function') global.print(); }
    catch (_) { shareStatus.textContent = 'Print kunne ikke åbnes i denne browser. Brug Gem PDF.'; }
  });
  restoreShared();
  core.fetchJSON('/assets/calculator-cars.json', { cache: 'no-cache' }).then(data => {
    catalogue = data.models.filter(car => /^[a-z0-9-]+$/.test(car.slug));
    for (const car of catalogue) { const option = document.createElement('option'); option.value = car.slug; option.textContent = car.label; selection.appendChild(option); }
    selection.disabled = false; selectCar(requestedCar(), false, true);
  }).catch(() => { modelNote.textContent = 'Biloversigten kunne ikke hentes. Beregneren virker med dine egne tal.'; });
  showPriceStatus(); calculate(false);
})(window);


