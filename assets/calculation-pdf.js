/* A local, text-based PDF export; no print dialog or third-party service. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.EVCalculationPDF = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';
  const substitutions = { '\u2192': ' -> ', '\u2190': ' <- ', '\u2248': 'ca. ', '\u2212': '-', '\u202f': ' ', '\u00a0': ' ' };
  const extra = { '\u20ac': 128, '\u201a': 130, '\u0192': 131, '\u201e': 132, '\u2026': 133, '\u2020': 134, '\u2021': 135, '\u02c6': 136, '\u2030': 137, '\u0160': 138, '\u2039': 139, '\u0152': 140, '\u017d': 142, '\u2018': 145, '\u2019': 146, '\u201c': 147, '\u201d': 148, '\u2022': 149, '\u2013': 150, '\u2014': 151, '\u02dc': 152, '\u2122': 153, '\u0161': 154, '\u203a': 155, '\u0153': 156, '\u017e': 158, '\u0178': 159 };
  function clean(value) {
    return String(value == null ? '' : value).normalize('NFC').replace(/[\u2192\u2190\u2248\u2212\u202f\u00a0]/g, char => substitutions[char]).replace(/[\x00-\x1f\x7f-\x9f]/g, ' ').replace(/\s+/g, ' ').trim();
  }
  function latin(value) {
    return Array.from(clean(value), char => {
      const code = char.codePointAt(0);
      return String.fromCharCode(extra[char] || (code <= 255 ? code : 63));
    }).join('');
  }
  function literal(value) { return latin(value).replace(/[\\()]/g, '\\$&'); }
  // Helvetica's proportional widths, including the Danish letters.
  function textWidth(value, size, bold) {
    let units = 0;
    for (const c of clean(value)) {
      if ('ilI.,:;!|\'`'.includes(c)) units += 280;
      else if ('mwMW@%ÆŒæœ'.includes(c)) units += 900;
      else if ('frt()[]{} '.includes(c)) units += 360;
      else if (/[A-ZÆØÅÉÖÜ]/.test(c)) units += 730;
      else units += 590;
    }
    return units * size / 1000 * (bold ? 1.04 : 1);
  }
  function wrap(value, size, bold, width) {
    const words = clean(value).split(' ').filter(Boolean), lines = [];
    let line = '';
    for (const word of words) {
      const candidate = line ? line + ' ' + word : word;
      if (textWidth(candidate, size, bold) <= width) { line = candidate; continue; }
      if (line) { lines.push(line); line = ''; }
      let part = '';
      for (const c of word) {
        if (part && textWidth(part + c, size, bold) > width) { lines.push(part); part = ''; }
        part += c;
      }
      line = part;
    }
    if (line) lines.push(line);
    return lines;
  }
  function build(report) {
    if (!report || !Array.isArray(report.fields) || !Array.isArray(report.result) || !report.result.length) throw new TypeError('A calculated result is required');
    const pages = [], margin = 44, width = 507;
    let page, y;
    function newPage() {
      page = { lines: [], links: [] }; pages.push(page); y = 760;
      page.lines.push('0.035 0.09 0.15 rg BT /F2 17 Tf 1 0 0 1 44 800 Tm (EV BEREGNER) Tj ET');
      page.lines.push('0.04 0.65 0.53 RG 1 w 44 789 m 551 789 l S');
    }
    function line(text, size = 11, bold = false, link = '') {
      if (y < 64 + size) newPage();
      const font = bold ? 'F2' : 'F1';
      page.lines.push('0.035 0.09 0.15 rg BT /' + font + ' ' + size + ' Tf 1 0 0 1 ' + margin + ' ' + y + ' Tm (' + literal(text) + ') Tj ET');
      if (link) page.links.push({ x: margin, y: y - 3, width: Math.min(width, textWidth(text, size, bold)), height: size + 6, url: link });
      y -= size * 1.45;
    }
    function paragraph(value, size = 11, bold = false, link = '') {
      for (const item of wrap(value, size, bold, width)) line(item, size, bold, link);
      y -= 5;
    }
    function heading(value) { y -= 9; if (y < 112) newPage(); paragraph(value, 13, true); }
    newPage();
    paragraph(report.title, 19, true);
    paragraph('Gemt: ' + report.savedAt, 9);
    if (report.car) paragraph('Bil: ' + report.car);
    heading('Dine tal');
    for (const item of report.fields) paragraph(item.label + ': ' + item.value);
    heading('Resultat');
    for (const item of report.result) paragraph(item);
    heading('Forudsætninger');
    for (const item of report.notes || []) if (clean(item)) paragraph(item, 10);
    paragraph('Vejledende beregning baseret på dine indtastede tal. Priser og bildata kan ændre sig.', 10);
    heading('Beregn videre');
    paragraph('Kilde: ' + report.source, 9, false, report.source);
    if (report.shareURL) paragraph('Åbn beregningen med de samme indtastede tal', 10, true, report.shareURL);
    const objects = [null];
    function reserve() { objects.push(''); return objects.length - 1; }
    function add(value) { const id = reserve(); objects[id] = value; return id; }
    const catalogId = reserve(), pagesId = reserve();
    const fontId = add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>');
    const boldId = add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>');
    const pageIds = [];
    pages.forEach((item, index) => {
      const pageId = reserve(); pageIds.push(pageId);
      item.lines.push('0.35 0.4 0.45 rg BT /F1 9 Tf 1 0 0 1 44 35 Tm (evberegn.dk) Tj ET');
      item.lines.push('BT /F1 9 Tf 1 0 0 1 475 35 Tm (Side ' + (index + 1) + ' / ' + pages.length + ') Tj ET');
      const stream = item.lines.join('\n') + '\n';
      const contentId = add('<< /Length ' + stream.length + ' >>\nstream\n' + stream + 'endstream');
      const annotations = item.links.filter(link => /^https:\/\/www\.evberegn\.dk\//.test(link.url)).map(link => add('<< /Type /Annot /Subtype /Link /Rect [' + [link.x, link.y, link.x + link.width, link.y + link.height].join(' ') + '] /Border [0 0 0] /A << /S /URI /URI (' + literal(link.url) + ') >> >>'));
      objects[pageId] = '<< /Type /Page /Parent ' + pagesId + ' 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 ' + fontId + ' 0 R /F2 ' + boldId + ' 0 R >> >> /Contents ' + contentId + ' 0 R' + (annotations.length ? ' /Annots [' + annotations.map(id => id + ' 0 R').join(' ') + ']' : '') + ' >>';
    });
    objects[catalogId] = '<< /Type /Catalog /Pages ' + pagesId + ' 0 R >>';
    objects[pagesId] = '<< /Type /Pages /Kids [' + pageIds.map(id => id + ' 0 R').join(' ') + '] /Count ' + pages.length + ' >>';
    let pdf = '%PDF-1.4\n%\xe2\xe3\xcf\xd3\n';
    const offsets = [0];
    for (let i = 1; i < objects.length; i++) { offsets.push(pdf.length); pdf += i + ' 0 obj\n' + objects[i] + '\nendobj\n'; }
    const xref = pdf.length;
    pdf += 'xref\n0 ' + objects.length + '\n0000000000 65535 f \n';
    for (const offset of offsets.slice(1)) pdf += String(offset).padStart(10, '0') + ' 00000 n \n';
    pdf += 'trailer\n<< /Size ' + objects.length + ' /Root ' + catalogId + ' 0 R >>\nstartxref\n' + xref + '\n%%EOF\n';
    return Uint8Array.from(pdf, char => char.charCodeAt(0));
  }
  return { build };
});
