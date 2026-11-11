/* Shared arithmetic and field definitions for the homepage and five guide pages. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.EVCalculators = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';
  const definitions = {
  "1": {
    "name": "Opladning",
    "title": "FULD <span>OPLADNING</span>",
    "description": "Beregn prisen for en hel eller delvis opladning med dit skøn over ekstra strømforbrug.",
    "fields": [
      [
        "battery",
        "Batteri i beregningen (kWh)",
        "60",
        "battery"
      ],
      [
        "electricPrice",
        "Samlet elpris (kr./kWh)",
        "2",
        "liveElectric"
      ],
      [
        "from",
        "Start på batteriet (%)",
        "0",
        "manual"
      ],
      [
        "to",
        "Slut på batteriet (%)",
        "100",
        "manual"
      ],
      [
        "overhead",
        "Ekstra strømforbrug (%)",
        "0",
        "manual"
      ]
    ]
  },
  "3": {
    "name": "El vs. benzin",
    "title": "EL VS. <span>BENZIN</span>",
    "description": "Sammenlign energiudgiften med en benzinbil.",
    "fields": [
      [
        "consumption",
        "Elbil kWh/100 km",
        "15.5",
        "consumption"
      ],
      [
        "electricPrice",
        "Elpris pr. kWh",
        "2",
        "liveElectric"
      ],
      [
        "fuelEconomy",
        "Benzin km/l",
        "16",
        "manual"
      ],
      [
        "fuelPrice",
        "Benzinpris pr. liter",
        "16",
        "livePetrol"
      ],
      [
        "annualKm",
        "Årlige km",
        "20000",
        "manual"
      ]
    ]
  },
  "8": {
    "name": "Opladningstid",
    "title": "OPLADNINGS<span>TID</span>",
    "description": "Beregn den teoretiske opladningstid.",
    "fields": [
      [
        "battery",
        "Batteri kWh",
        "60",
        "battery"
      ],
      [
        "from",
        "Start %",
        "20",
        "manual"
      ],
      [
        "to",
        "Slut %",
        "80",
        "manual"
      ],
      [
        "power",
        "Gennemsnitlig ladeeffekt (kW)",
        "11",
        "manual"
      ]
    ]
  },
  "12": {
    "name": "Leasing vs. køb",
    "title": "LEASING VS. <span>KØB</span>",
    "description": "Sammenlign leasingbetaling med værditab og øvrige købsudgifter over samme periode.",
    "fields": [
      [
        "months",
        "Periode (måneder)",
        "36",
        "manual"
      ],
      [
        "monthlyLease",
        "Leasingydelse (kr./md.)",
        "3999",
        "manual"
      ],
      [
        "leaseUpfront",
        "Førstegangsydelse (kr.)",
        "15000",
        "manual"
      ],
      [
        "leaseOther",
        "Øvrige leasingudgifter i perioden (kr.)",
        "0",
        "manual"
      ],
      [
        "price",
        "Købspris (kr.)",
        "250000",
        "price"
      ],
      [
        "resaleValue",
        "Dit skøn over salgspris efter perioden (kr.)",
        "150000",
        "manual"
      ],
      [
        "purchaseOther",
        "Øvrige købsudgifter i perioden (kr.)",
        "0",
        "manual"
      ]
    ]
  },
  "14": {
    "name": "5 års økonomi",
    "title": "BILENS <span>5 ÅRS ØKONOMI</span>",
    "description": "Beregn en simpel samlet 5-års økonomi med estimeret restværdi.",
    "fields": [
      [
        "price",
        "Købspris",
        "250000",
        "price"
      ],
      [
        "annualRunning",
        "Drift pr. år",
        "15000",
        "manual"
      ],
      [
        "futureValue",
        "Dit skøn over værdi efter 5 år (kr.)",
        "100000",
        "manual"
      ]
    ]
  },
  "2": {
    "name": "Pris pr. km",
    "title": "PRIS PR. <span>KM</span>",
    "description": "Beregn strømudgiften pr. kilometer.",
    "fields": [
      [
        "consumption",
        "Forbrug (kWh/100 km)",
        "16",
        "consumption"
      ],
      [
        "electricPrice",
        "Samlet elpris (kr./kWh)",
        "2",
        "liveElectric"
      ]
    ]
  },
  "4": {
    "name": "El vs. diesel",
    "title": "EL VS. <span>DIESEL</span>",
    "description": "Sammenlign årlige energiudgifter.",
    "fields": [
      [
        "consumption",
        "Elbil (kWh/100 km)",
        "16",
        "consumption"
      ],
      [
        "electricPrice",
        "Elpris (kr./kWh)",
        "2",
        "liveElectric"
      ],
      [
        "fuelEconomy",
        "Dieselbil (km/l)",
        "20",
        "manual"
      ],
      [
        "fuelPrice",
        "Dieselpris (kr./liter)",
        "17",
        "liveDiesel"
      ],
      [
        "annualKm",
        "Årlige kilometer",
        "20000",
        "manual"
      ]
    ]
  },
  "6": {
    "name": "Køretur",
    "title": "PRIS FOR <span>KØRETUREN</span>",
    "description": "Beregn turens energibehov og strømudgift.",
    "fields": [
      [
        "km",
        "Turens samlede kilometer",
        "250",
        "manual"
      ],
      [
        "consumption",
        "Forbrug (kWh/100 km)",
        "18",
        "consumption"
      ],
      [
        "electricPrice",
        "Samlet elpris (kr./kWh)",
        "2.5",
        "liveElectric"
      ]
    ]
  },
  "7": {
    "name": "Rækkevidde",
    "title": "BEREGN <span>RÆKKEVIDDE</span>",
    "description": "Matematisk overslag med dine egne tal.",
    "fields": [
      [
        "battery",
        "Energi til rådighed (kWh)",
        "60",
        "battery"
      ],
      [
        "consumption",
        "Forventet forbrug (kWh/100 km)",
        "18",
        "consumption"
      ]
    ]
  },
  "9": {
    "name": "Strømforbrug",
    "title": "ÅRLIGT <span>STRØMFORBRUG</span>",
    "description": "Beregn kWh pr. år, måned og dag.",
    "fields": [
      [
        "annualKm",
        "Årlige kilometer",
        "20000",
        "manual"
      ],
      [
        "consumption",
        "Forbrug (kWh/100 km)",
        "16",
        "consumption"
      ]
    ]
  }
};
  const numeric = value => value == null || String(value).trim() === '' ? NaN : Number(value);
  const number = value => Number(value).toLocaleString('da-DK', { maximumFractionDigits: 2 });
  const money = value => number(value) + ' kr.';
  function defaults(id) {
    return Object.fromEntries(definitions[id].fields.map(field => [field[0], numeric(field[2])]));
  }
  function validate(id, values) {
    id = Number(id);
    const errors = {}, definition = definitions[id];
    if (!definition) return { calculator: 'Beregneren findes ikke.' };
    for (const [key] of definition.fields) {
      const value = numeric(values[key]);
      if (!Number.isFinite(value)) errors[key] = 'Indtast et gyldigt tal.';
      else if (key !== 'electricPrice' && value < 0) errors[key] = 'Værdien skal være 0 eller større.';
    }
    const v = key => numeric(values[key]);
    if ([3, 4].includes(id) && Number.isFinite(v('fuelEconomy')) && v('fuelEconomy') <= 0) errors.fuelEconomy = 'Værdien skal være større end 0.';
    if ([1, 8].includes(id)) {
      for (const key of ['from', 'to']) if (Number.isFinite(v(key)) && v(key) > 100) errors[key] = 'Ladeprocenten må højst være 100.';
      if (!errors.to && v('to') < v('from')) errors.to = 'Slutprocenten skal være mindst startprocenten.';
    }
    if (id === 7 && Number.isFinite(v('consumption')) && v('consumption') <= 0) errors.consumption = 'Værdien skal være større end 0.';
    if (id === 8 && Number.isFinite(v('power')) && v('power') <= 0) errors.power = 'Værdien skal være større end 0.';
    if (id === 1 && v('overhead') > 100) errors.overhead = 'Indtast ekstra strømforbrug fra 0 til 100 %.';
    if (id === 12 && Number.isFinite(v('months')) && (v('months') <= 0 || !Number.isInteger(v('months')))) errors.months = 'Indtast et positivt helt antal måneder.';
    return errors;
  }
  function compute(id, values) {
    id = Number(id);
    const errors = validate(id, values);
    if (Object.keys(errors).length) throw new RangeError(Object.values(errors)[0]);
    const v = key => numeric(values[key]);
    let result;
    switch (id) {
      case 1: {
        const batteryEnergy = v('battery') * (v('to') - v('from')) / 100;
        const paidEnergy = batteryEnergy * (1 + v('overhead') / 100);
        result = { batteryEnergy, paidEnergy, total: paidEnergy * v('electricPrice') }; break;
      }
      case 2: { result = { perKm: v('consumption') * v('electricPrice') / 100, per100: v('consumption') * v('electricPrice') }; break; }
      case 3:
      case 4: {
        const kwh = v('consumption') * v('annualKm') / 100;
        const electricTotal = kwh * v('electricPrice');
        const litres = v('annualKm') / v('fuelEconomy');
        const fuelTotal = litres * v('fuelPrice');
        result = { kwh, litres, electricTotal, fuelTotal, saving: fuelTotal - electricTotal }; break;
      }
      case 6: { const energy = v('km') * v('consumption') / 100; result = { energy, total: energy * v('electricPrice') }; break; }
      case 7: { result = { range: v('battery') / v('consumption') * 100 }; break; }
      case 9: { const yearly = v('annualKm') * v('consumption') / 100; result = { yearly, monthly: yearly / 12, daily: yearly / 365 }; break; }
      case 8: {
        const energy = v('battery') * (v('to') - v('from')) / 100;
        result = { energy, hours: energy / v('power') }; break;
      }
      case 12: {
        const leaseTotal = v('leaseUpfront') + v('monthlyLease') * v('months') + v('leaseOther');
        const buyTotal = v('price') - v('resaleValue') + v('purchaseOther');
        result = { leaseTotal, buyTotal, difference: leaseTotal - buyTotal, leaseMonthly: leaseTotal / v('months'), buyMonthly: buyTotal / v('months') }; break;
      }
      case 14: {
        const purchase = v('price'), running = v('annualRunning') * 5, residual = v('futureValue');
        result = { purchase, running, residual, total: purchase + running - residual, monthly: (purchase + running - residual) / 60 }; break;
      }
    }
    if (!result || Object.values(result).some(value => !Number.isFinite(value))) throw new RangeError('Tallene er for store til en gyldig beregning.');
    return result;
  }
  function render(id, r) {
    const table = rows => '<table class="answer-table"><tbody>' + rows.map(([label, value]) => '<tr><th scope="row">' + label + '</th><td>' + value + '</td></tr>').join('') + '</tbody></table>';
    switch (Number(id)) {
      case 2: return table([['Strøm pr. kilometer', money(r.perKm)], ['Strøm pr. 100 km', money(r.per100)]]) + '<p class="result-note">Kun strømudgiften. Bilens øvrige omkostninger er ikke med.</p>';
      case 6: return table([['Turens energibehov', number(r.energy) + ' kWh'], ['Turens strømudgift', money(r.total)]]) + '<p class="result-note">Regnet for den samlede distance, du har indtastet.</p>';
      case 7: return 'Beregnet rækkevidde:<strong>' + number(r.range) + ' km</strong><p class="result-note">Matematisk overslag. Ikke en WLTP-test eller garanti for faktisk rækkevidde.</p>';
      case 9: return table([['Strøm pr. år', number(r.yearly) + ' kWh'], ['Gennemsnit pr. måned', number(r.monthly) + ' kWh'], ['Gennemsnit pr. dag (365 dage)', number(r.daily) + ' kWh']]);
      case 1: return 'Pris for opladningen:<strong>' + money(r.total) + '</strong>' + table([['Energi til batteriet', number(r.batteryEnergy) + ' kWh'], ['Energi, du betaler for', number(r.paidEnergy) + ' kWh']]);
      case 3: return table([['Elbil, energi pr. år', money(r.electricTotal)], ['Benzinbil, energi pr. år', money(r.fuelTotal)], ['Benzin minus el', money(r.saving)]]) + '<p class="result-note">' + (r.saving > 0 ? 'El er billigere i dette energiscenarie.' : r.saving < 0 ? 'Benzin er billigere i dette energiscenarie.' : 'Samme beregnede energiudgift.') + ' Bilernes samlede ejeromkostninger indgår ikke.</p>';
      case 4: return table([['Elbil, energi pr. år', money(r.electricTotal)], ['Dieselbil, energi pr. år', money(r.fuelTotal)], ['Diesel minus el', money(r.saving)]]) + '<p class="result-note">' + (r.saving > 0 ? 'El er billigere i dette energiscenarie.' : r.saving < 0 ? 'Diesel er billigere i dette energiscenarie.' : 'Samme beregnede energiudgift.') + ' Bilernes samlede ejeromkostninger indgår ikke.</p>';
      case 8: return 'Energi:<strong>' + number(r.energy) + ' kWh</strong>Teoretisk tid:<strong>' + number(r.hours) + ' timer</strong><p class="result-note">Regnet med konstant gennemsnitlig effekt. Faktisk ladetid kan afvige.</p>';
      case 12: return table([['Leasing i perioden', money(r.leaseTotal)], ['Køb minus salgspris og inkl. øvrige udgifter', money(r.buyTotal)], ['Leasing minus køb', money(r.difference)], ['Leasing, gennemsnit pr. måned', money(r.leaseMonthly)], ['Køb, gennemsnit pr. måned', money(r.buyMonthly)]]) + '<p class="result-note">' + (r.difference > 0 ? 'Køb giver den laveste beregnede omkostning i dette scenarie.' : r.difference < 0 ? 'Leasing giver den laveste beregnede omkostning i dette scenarie.' : 'Samme beregnede omkostning i perioden.') + ' Resultatet afhænger blandt andet af dit skøn over salgsprisen.</p>';
      case 14: return table([['Købspris', money(r.purchase)], ['Drift i 5 år', money(r.running)], ['Skønnet salgspris efter 5 år', money(r.residual)], ['Nettoomkostning i 5 år', money(r.total)], ['Gennemsnit pr. måned', money(r.monthly)]]) + '<p class="result-note">Medtag selv finansiering og øvrige udgifter i driftsbudgettet. Salgsprisen er dit skøn.</p>';
      default: throw new RangeError('Beregneren findes ikke.');
    }
  }
  function run(id, values) {
    try { return render(id, compute(id, values)); }
    catch (_) { return '<p role="alert">Indtast gyldige værdier i alle felter. Kontrollér procent, periode og eventuelle meget store tal.</p>'; }
  }
  return { definitions, defaults, validate, compute, render, run };
});

