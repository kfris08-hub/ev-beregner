/* Small, local enhancements. No tracking, storage, or additional price service. */
(function () {
  'use strict';
  const panel = document.getElementById('carOverview');
  if (!panel || typeof selectCar !== 'function') return;
  const byId = id => document.getElementById(id);
  const format = (value, digits = 0) => new Intl.NumberFormat('da-DK', {
    minimumFractionDigits: digits, maximumFractionDigits: digits
  }).format(value);
  const photos = new Map();
  let priceEdited = false, photoRequest = 0, opener = null, modalOpen = false;
  let previousOverflow = '';
  const fields = ['overviewKm', 'overviewConsumption', 'overviewPrice', 'overviewHomeShare', 'overviewPublicPrice'];
  const definitions = {
    2: 'pris-pr-km', 6: 'koeretur', 9: 'stroemforbrug-elbil'
  };
  function slug() { return selectedCar ? modelSlugs[selectedCar[0] + '|||' + selectedCar[1]] : ''; }
  function linked(id, values) {
    const base = location.origin + '/beregnere/' + definitions[id] + '/';
    if (!window.EVCalculationShare) return base + (slug() ? '#bil=' + slug() : '');
    return EVCalculationShare.encode(base, id, Object.keys(values), values, slug(), energyPrices.region);
  }
  function update() {
    const values = Object.fromEntries(fields.map(id => [id, EVCore.number(byId(id).value)]));
    let valid = true;
    for (const id of fields) {
      const used = byId('overviewMix').checked || !['overviewHomeShare', 'overviewPublicPrice'].includes(id);
      const value = values[id];
      const bad = used && (!Number.isFinite(value) ||
        (['overviewKm', 'overviewConsumption', 'overviewHomeShare'].includes(id) && value < 0) ||
        (id === 'overviewHomeShare' && value > 100));
      byId(id).setAttribute('aria-invalid', bad ? 'true' : 'false');
      if (bad) valid = false;
    }
    const price = byId('overviewMix').checked
      ? values.overviewPrice * values.overviewHomeShare / 100 + values.overviewPublicPrice * (1 - values.overviewHomeShare / 100)
      : values.overviewPrice;
    const per100 = values.overviewConsumption * price, yearlyKwh = values.overviewConsumption * values.overviewKm / 100;
    const yearly = yearlyKwh * price;
    valid = valid && [price, per100, yearlyKwh, yearly].every(Number.isFinite);
    byId('overviewResults').hidden = !valid;
    byId('overviewError').textContent = valid ? '' : 'Indtast gyldige tal. Kilometer og forbrug skal være 0 eller større, og hjemmeandelen skal være 0–100 %.';
    byId('overviewDetailLinks').hidden = !valid;
    if (!valid) return;
    byId('overviewPerKm').textContent = format(per100 / 100, 2) + ' kr.';
    byId('overviewPer100').textContent = format(per100, 2) + ' kr.';
    byId('overviewYear').textContent = format(yearly) + ' kr.';
    byId('overviewMonth').textContent = format(yearly / 12) + ' kr.';
    byId('overviewBasis').textContent = format(values.overviewKm) + ' km/år · ' + format(yearlyKwh) + ' kWh/år · ' + format(price, 2) + ' kr./kWh' + (byId('overviewMix').checked ? ' i vægtet gennemsnit.' : '.');
    byId('overviewCostLink').href = linked(2, {consumption: values.overviewConsumption, electricPrice: price});
    byId('overviewTripLink').href = linked(6, {km: 100, consumption: values.overviewConsumption, electricPrice: price});
    byId('overviewEnergyLink').href = linked(9, {annualKm: values.overviewKm, consumption: values.overviewConsumption});
  }
  async function photo(carSlug) {
    const token = ++photoRequest, figure = byId('overviewPhoto');
    figure.hidden = true; figure.replaceChildren();
    if (!carSlug) return;
    try {
      let markup = photos.get(carSlug);
      if (markup === undefined) {
        const response = await fetch('/elbil/' + encodeURIComponent(carSlug) + '/', {credentials: 'omit'});
        if (!response.ok) return;
        markup = await response.text(); photos.set(carSlug, markup);
      }
      if (token !== photoRequest) return;
      const doc = new DOMParser().parseFromString(markup, 'text/html');
      const source = doc.getElementById('carPhoto'), credit = doc.getElementById('photoCredit');
      if (!source || !credit || !/^\/assets\/cars\/[a-z0-9-]+\.webp$/.test(source.getAttribute('src') || '')) return;
      const image = document.createElement('img');
      image.src = source.getAttribute('src'); image.alt = source.alt;
      image.width = Number(source.getAttribute('width')); image.height = Number(source.getAttribute('height'));
      image.decoding = 'async'; image.loading = 'lazy';
      image.addEventListener('error', () => { if (token === photoRequest) figure.hidden = true; });
      const caption = document.createElement('figcaption');
      // Reuse the reviewed credit, licence, original link and variant caveat.
      for (const node of credit.childNodes) caption.appendChild(document.importNode(node, true));
      figure.append(image, caption); figure.hidden = false;
    } catch (_) { /* The overview remains usable without a photo. */ }
  }
  function show() {
    panel.hidden = false;
    byId('overviewTitle').textContent = selectedCar ? selectedCar[0] + ' ' + selectedCar[1] : 'Din strømøkonomi';
    byId('overviewConsumption').value = selectedCar ? (Number.isFinite(selectedCar[5]) ? selectedCar[5] : '') : '16';
    if (!priceEdited) byId('overviewPrice').value = energyPrices.electric.toFixed(2);
    byId('overviewPriceNote').textContent = priceEdited ? 'Din egen elpris.' : energyState.electric === 'ready'
      ? 'Aktuel timepris · ' + energyPrices.region + '. Brug din samlede aftalepris; lokal nettarif og leverandørtillæg kan afvige.'
      : 'Eksempelpris. Indtast din egen samlede elpris.';
    const currentSlug = slug();
    byId('overviewBudgetLink').href = '/beregnere/samlet-biloekonomi/' + (currentSlug ? '#bil=' + currentSlug : '');
    byId('overviewLeaseLink').href = '/beregnere/leasing-vs-koeb/' + (currentSlug ? '#bil=' + currentSlug : '');
    photo(currentSlug); update();
  }
  const originalSelect = selectCar, originalRemove = removeSelectedCar, originalMode = setMode;
  selectCar = function (car) { originalSelect(car); show(); };
  removeSelectedCar = function () { originalRemove(); panel.hidden = true; photoRequest++; };
  setMode = function (mode) {
    originalMode(mode);
    byId('carModeBtn').setAttribute('aria-pressed', mode === 'car' ? 'true' : 'false');
    byId('generalModeBtn').setAttribute('aria-pressed', mode === 'car' ? 'false' : 'true');
    if (mode !== 'car') { show(); panel.scrollIntoView({block: 'start'}); }
    else if (!selectedCar) panel.hidden = true;
  };
  const originalPrices = loadElectricPrice;
  loadElectricPrice = async function () {
    await originalPrices();
    if (!panel.hidden) {
      if (!priceEdited) byId('overviewPrice').value = energyPrices.electric.toFixed(2);
      byId('overviewPriceNote').textContent = priceEdited ? 'Din egen elpris.' : energyState.electric === 'ready'
        ? 'Aktuel timepris · ' + energyPrices.region + '. Din samlede aftalepris kan afvige.' : 'Eksempelpris. Indtast din egen samlede elpris.';
      update();
    }
  };
  for (const id of fields) byId(id).addEventListener('input', () => {
    if (id === 'overviewPrice') { priceEdited = true; byId('overviewPriceNote').textContent = 'Din egen elpris.'; }
    update();
  });
  byId('overviewMix').addEventListener('change', () => { byId('overviewMixFields').hidden = !byId('overviewMix').checked; update(); });
  // Initial price requests can finish before or after this deferred enhancement.
  window.addEventListener('ev-prices-updated', () => {
    if (!panel.hidden && !priceEdited) {
      byId('overviewPrice').value = energyPrices.electric.toFixed(2);
      byId('overviewPriceNote').textContent = energyState.electric === 'ready' ? 'Aktuel timepris · ' + energyPrices.region + '. Din samlede aftalepris kan afvige.' : 'Eksempelpris. Indtast din egen samlede elpris.';
      update();
    }
  });
  const modal = byId('calculator'), originalOpen = openCalculator, originalClose = closeCalculator;
  function focusModal() {
    if (!modalOpen) {
      opener = document.activeElement;
      previousOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden'; modalOpen = true;
      modal.scrollTop = 0;
      (modal.querySelector('input') || modal.querySelector('button')).focus({preventScroll: true});
    }
  }
  openCalculator = function (id, fromURL) { originalOpen(id, fromURL); if (modal.style.display === 'block') focusModal(); };
  closeCalculator = function () {
    originalClose();
    if (modalOpen) {
      document.body.style.overflow = previousOverflow; modalOpen = false;
      if (opener && opener.isConnected) opener.focus({preventScroll: true});
    }
  };
  modal.addEventListener('keydown', event => {
    if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); closeCalculatorFromButton(); return; }
    if (event.key === 'Enter' && event.target.matches('input')) { event.preventDefault(); calculate(); }
    if (event.key !== 'Tab') return;
    const nodes = [...modal.querySelectorAll('button,input,a[href]')].filter(node => !node.disabled && node.getClientRects().length);
    const first = nodes[0], last = nodes[nodes.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
  if (selectedCar) show();
  if (modal.style.display === 'block') focusModal();
})();
