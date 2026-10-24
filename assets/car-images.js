(function (global) {
  'use strict';
  const core = global.EVCore, config = document.currentScript.dataset;
  const brand = config.brand, model = config.model;
  const image = document.getElementById('carPhoto');
  const loading = document.getElementById('photoLoading');
  const credit = document.getElementById('photoCredit');
  if (!image || !brand || !model) return;
  const normalise = value => String(value || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  const words = normalise(brand + ' ' + model).split(/\s+/).filter(Boolean);
  const bad = /interior|inside|cockpit|dashboard|steering|seats?|cabin|console|infotainment|engine|badge|logo|wheel|rim|headlight|taillight|cutaway|diagram|crash|accident|brochure|manual|toy|scale.model/i;
  const exterior = /side.view|sideview|side.profile|profile|lateral|three.?quarter|3.?4|exterior|outside|front.?side|rear.?side/i;
  const clean = value => String(value || '').replace(/<[^>]*>/g, '').replace(/&[^;]+;/g, ' ').trim();
  const safeURL = value => { try { return new URL(value).protocol === 'https:'; } catch (_) { return false; } };
  const modelMatches = text => {
    const tokens = new Set(normalise(text).split(/\s+/));
    return words.every(word => tokens.has(word));
  };
  const key = 'evModelPhoto:v2:' + normalise(brand + ' ' + model);
  function show(photo) {
    if (!safeURL(photo.url) || !safeURL(photo.page) || !photo.author || !photo.license) return false;
    image.onload = () => { if (loading) loading.style.display = 'none'; };
    image.onerror = unavailable;
    image.alt = brand + ' ' + model + ' – udvendigt modelbillede';
    image.src = photo.url;
    image.style.display = 'block';
    credit.textContent = 'Foto: ' + photo.author + ' · ';
    const license = document.createElement('a');
    license.textContent = photo.license;
    license.href = safeURL(photo.licenseURL) ? photo.licenseURL : photo.page;
    license.target = '_blank'; license.rel = 'noopener noreferrer';
    credit.appendChild(license);
    credit.appendChild(document.createTextNode(' · '));
    const source = document.createElement('a');
    source.href = photo.page; source.textContent = 'Wikimedia Commons';
    source.target = '_blank'; source.rel = 'noopener noreferrer';
    credit.appendChild(source);
    return true;
  }
  function unavailable() {
    image.style.display = 'none';
    if (loading) { loading.style.display = ''; loading.textContent = 'Modelbillede ikke tilgængeligt.'; }
    credit.textContent = '';
    core.setStored(key, '');
  }
  try {
    const saved = JSON.parse(core.getStored(key) || 'null');
    if (saved && Date.now() - saved.savedAt < 7 * 86400000 && modelMatches(saved.modelTitle) && !bad.test(saved.title) && exterior.test(saved.title) && show(saved)) return;
  } catch (_) {}
  (async () => {
    const query = brand + ' ' + model + ' ("side view" OR profile OR exterior OR "three quarter")';
    const url = 'https://commons.wikimedia.org/w/api.php?origin=*&action=query&generator=search&gsrnamespace=6&gsrsearch=' + encodeURIComponent(query) + '&gsrlimit=30&prop=imageinfo&iiprop=url%7Cextmetadata%7Csize&iiurlwidth=1400&format=json';
    const data = await core.fetchJSON(url, { cache: 'force-cache' }, 6000);
    const candidates = Object.values(data.query?.pages || {}).map(page => {
      const info = page.imageinfo?.[0], meta = info?.extmetadata;
      if (!info || !meta || !page.pageid) return null;
      const modelTitle = clean(page.title);
      const title = clean((page.title || '') + ' ' + (meta.ImageDescription?.value || '') + ' ' + (meta.ObjectName?.value || ''));
      if (bad.test(title) || !exterior.test(title) || !modelMatches(modelTitle) || !(info.width / info.height > 1.12)) return null;
      const license = clean(meta.LicenseShortName?.value);
      const author = clean(meta.Artist?.value);
      if (!license || !author) return null;
      return { title, modelTitle, url: info.thumburl || info.url, author, license, licenseURL: meta.LicenseUrl?.value || '', page: 'https://commons.wikimedia.org/?curid=' + page.pageid, savedAt: Date.now(), width: info.width };
    }).filter(Boolean).sort((a, b) => b.width - a.width);
    const photo = candidates[0];
    if (!photo || !show(photo)) throw new Error('Intet sikkert modelmatch');
    core.setStored(key, JSON.stringify(photo));
  })().catch(unavailable);
})(window);
