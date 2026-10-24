(function (global) {
  'use strict';
  const core = global.EVCore, config = document.currentScript.dataset;
  const brand = config.brand, model = config.model;
  const image = document.getElementById('carPhoto');
  const loading = document.getElementById('photoLoading');
  const credit = document.getElementById('photoCredit');
  if (!core || !image || !brand || !model) return;

  const normalise = value => String(value || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  const clean = value => String(value || '').replace(/<[^>]*>/g, '').replace(/&[^;]+;/g, ' ').trim();
  const safeURL = value => { try { return new URL(value).protocol === 'https:'; } catch (_) { return false; } };
  const brandWords = normalise(brand).split(' '), modelWords = normalise(model).split(' ');
  let identity = brandWords.concat(modelWords);
  if (normalise(model).replace(/ /g, '').startsWith(normalise(brand).replace(/ /g, ''))) identity = modelWords;
  else for (let count = Math.min(brandWords.length, modelWords.length); count > 0; count--) {
    if (brandWords.slice(-count).join(' ') === modelWords.slice(0, count).join(' ')) {
      identity = brandWords.concat(modelWords.slice(count)); break;
    }
  }
  const modelPattern = new RegExp('(?:^| )' + identity.join(' *') + '(?= |$)');
  const modelMatches = value => {
    const text = normalise(value), match = modelPattern.exec(text);
    if (!match) return false;
    // IONIQ 5/6 N have separate model pages; do not use their photos for the standard car.
    if (normalise(brand) === 'hyundai' && /^ioniq (5|6)$/.test(normalise(model)) && /^n(?: |$)/.test(text.slice(match.index + match[0].length).trim())) return false;
    return true;
  };
  // Check the filename, not every word in a long description or photographer biography.
  const badFilename = /interior|inside|cockpit|dashboard|steering|driver.?seat|front.?seat|rear.?seat|seats|cabin|console|infotainment|engine|badge|logo|wheels?|rims?|headlights?|taillights?|cutaway|diagram|crash|accident|brochure|manual|toy|scale.model|\.svg$/i;
  const preferredView = /side.view|sideview|side.profile|profile|lateral|three.?quarter|3.?4|exterior|front.?side|rear.?side/i;
  const cacheKey = 'evModelPhoto:v3:' + normalise(brand + ' ' + model);

  function renderCredit(photo) {
    credit.textContent = photo.author ? 'Foto: ' + photo.author + ' · ' : 'Kilde: Wikimedia Commons · ';
    const license = document.createElement('a');
    license.textContent = photo.license || 'Fotograf og billedlicens';
    license.href = safeURL(photo.licenseURL) ? photo.licenseURL : photo.page;
    license.target = '_blank'; license.rel = 'noopener noreferrer'; credit.appendChild(license);
    credit.appendChild(document.createTextNode(' · '));
    const source = document.createElement('a');
    source.href = photo.page; source.textContent = photo.source || 'Wikimedia Commons';
    source.target = '_blank'; source.rel = 'noopener noreferrer'; credit.appendChild(source);
  }
  function display(photo) {
    return new Promise((resolve, reject) => {
      if (!safeURL(photo.url) || !safeURL(photo.page)) { reject(new Error('Ugyldig billedadresse')); return; }
      let timer;
      function finish(error) {
        global.clearTimeout(timer); image.onload = null; image.onerror = null;
        if (error) { reject(error); return; }
        image.style.display = 'block';
        image.alt = brand + ' ' + model + ' – udvendigt modelbillede';
        if (loading) loading.style.display = 'none';
        renderCredit(photo); resolve(photo);
      }
      image.onload = () => finish(image.naturalWidth > 0 ? null : new Error('Tomt billede'));
      image.onerror = () => finish(new Error('Billedet kunne ikke indlæses'));
      timer = global.setTimeout(() => finish(new Error('Billedet tog for lang tid')), 20000);
      image.src = photo.url;
      if (image.complete && image.naturalWidth > 0) image.onload();
    });
  }
  function remember(photo) {
    photo.savedAt = Date.now(); core.setStored(cacheKey, JSON.stringify(photo));
  }
  function unavailable() {
    image.style.display = 'none'; credit.textContent = ''; core.setStored(cacheKey, '');
    if (loading) { loading.style.display = ''; loading.textContent = 'Modelbillede ikke tilgængeligt.'; }
  }

  async function commonsPhoto() {
    const query = brand + ' ' + model;
    const url = 'https://commons.wikimedia.org/w/api.php?origin=*&action=query&generator=search&gsrnamespace=6&gsrsearch=' + encodeURIComponent(query) + '&gsrlimit=30&prop=imageinfo&iiprop=url%7Cextmetadata%7Csize%7Cmime&iiurlwidth=1400&format=json';
    const data = await core.fetchJSON(url, { cache: 'force-cache' }, 15000);
    const candidates = Object.values(data.query?.pages || {}).map(page => {
      const info = page.imageinfo?.[0], title = clean(page.title), meta = info?.extmetadata || {};
      if (!info || !page.pageid || !modelMatches(title) || badFilename.test(title) || !(info.width / info.height > 1.05)) return null;
      if (info.mime && !/^image\/(jpeg|png|webp|avif)$/.test(info.mime)) return null;
      const description = clean(meta.ImageDescription?.value || '');
      return { modelTitle: title, url: info.thumburl || info.url, author: clean(meta.Artist?.value), license: clean(meta.LicenseShortName?.value), licenseURL: meta.LicenseUrl?.value || '', page: 'https://commons.wikimedia.org/?curid=' + page.pageid, source: 'Wikimedia Commons', score: (preferredView.test(title + ' ' + description) ? 100 : 0) + Math.min(info.width, 2000) / 2000 };
    }).filter(Boolean).sort((a, b) => b.score - a.score);
    if (!candidates[0]) throw new Error('Intet Commons-modelmatch');
    return candidates[0];
  }
  async function wikipediaPhoto() {
    const query = brand + ' ' + model;
    const url = 'https://en.wikipedia.org/w/api.php?origin=*&action=query&generator=search&gsrnamespace=0&gsrsearch=' + encodeURIComponent(query) + '&gsrlimit=5&prop=pageimages%7Cinfo&piprop=thumbnail%7Cname&pithumbsize=1400&inprop=url&format=json';
    const data = await core.fetchJSON(url, { cache: 'force-cache' }, 15000);
    const pages = Object.values(data.query?.pages || {}).sort((a, b) => (a.index || 0) - (b.index || 0));
    for (const page of pages) {
      if (!modelMatches(page.title) || !page.thumbnail?.source || !page.pageimage || badFilename.test(page.pageimage)) continue;
      const thumbnail = new URL(page.thumbnail.source);
      if (thumbnail.protocol !== 'https:' || !['upload.wikimedia.org', 'thumb.wikimedia.org'].includes(thumbnail.hostname) || !thumbnail.pathname.startsWith('/wikipedia/commons/')) continue;
      return { modelTitle: page.title, fileTitle: page.pageimage, url: page.thumbnail.source, author: '', license: '', licenseURL: 'https://commons.wikimedia.org/wiki/File:' + encodeURIComponent(page.pageimage), page: page.fullurl || 'https://en.wikipedia.org/wiki/' + encodeURIComponent(page.title.replace(/ /g, '_')), source: 'Wikipedia' };
    }
    throw new Error('Intet Wikipedia-modelmatch');
  }
  async function enrichCredit(photo) {
    if (!photo.fileTitle || (photo.author && photo.license)) return;
    try {
      // Wikipedia exposes Commons image metadata through its shared file repository too.
      const url = 'https://en.wikipedia.org/w/api.php?origin=*&action=query&titles=' + encodeURIComponent('File:' + photo.fileTitle) + '&prop=imageinfo&iiprop=extmetadata%7Curl&format=json';
      const data = await core.fetchJSON(url, { cache: 'force-cache' }, 10000);
      const info = Object.values(data.query?.pages || {}).find(p => p.imageinfo?.[0])?.imageinfo[0];
      const meta = info?.extmetadata;
      if (!meta) return;
      photo.author = clean(meta.Artist?.value); photo.license = clean(meta.LicenseShortName?.value);
      photo.licenseURL = meta.LicenseUrl?.value || photo.licenseURL;
      if (image.src === photo.url) { renderCredit(photo); remember(photo); }
    } catch (_) {}
  }
  (async () => {
    try {
      const cached = JSON.parse(core.getStored(cacheKey) || 'null');
      if (cached && Date.now() - cached.savedAt < 7 * 86400000 && modelMatches(cached.modelTitle)) {
        try { await display(cached); enrichCredit(cached); return; } catch (_) { core.setStored(cacheKey, ''); }
      }
    } catch (_) {}
    // Preserve the independent Wikipedia fallback. A missing view keyword is not a failed model match.
    const sources = [commonsPhoto(), wikipediaPhoto()];
    let first;
    try { first = await Promise.any(sources); await display(first); remember(first); enrichCredit(first); return; }
    catch (_) {}
    for (const source of sources) {
      try {
        const photo = await source;
        if (photo === first) continue;
        await display(photo); remember(photo); enrichCredit(photo); return;
      } catch (_) {}
    }
    unavailable();
  })();
})(window);
