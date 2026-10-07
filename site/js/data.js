/* OpenDict data layer — index search, shard fetching, caches.
   Index formats (written by pipeline/pack.py):
     index-en.json: [[key, shard, freq, display], ...] sorted by key (key = lowercase)
     index-vi.json: [[key, norm, shard, display], ...] sorted by (norm, key)
     forms.json:    {inflectedLower: baseKey}
     shards/<lang>/<shard>.json: {key: entry}   (entry.w = display form)
*/
const Data = (() => {
  const BASE = (() => {
    const p = location.pathname;
    return p.endsWith("/") ? p : p.slice(0, p.lastIndexOf("/") + 1);
  })();
  const D = (f) => fetch(BASE + "data/" + f).then(r => { if (!r.ok) throw new Error(f); return r.json(); });

  let meta = null, idxEn = null, idxVi = null, forms = null;
  const shardCache = new Map();
  const inflight = new Map();

  function normVi(s) {
    return s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d");
  }
  function disp(r) { return r[3] || r[0]; }

  async function load() {
    [meta, idxEn, idxVi, forms] = await Promise.all([
      D("meta.json"), D("index-en.json"), D("index-vi.json"), D("forms.json")
    ]);
    return meta;
  }

  function lowerBound(arr, target, key) {
    let lo = 0, hi = arr.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (key(arr[mid]) < target) lo = mid + 1; else hi = mid;
    }
    return lo;
  }

  // exact VI match: binary search on norm, then disambiguate by key
  function viExact(key) {
    const nq = normVi(key);
    let i = lowerBound(idxVi, nq, r => r[1]);
    while (i < idxVi.length && idxVi[i][1] === nq) {
      if (idxVi[i][0] === key) return idxVi[i];
      i++;
    }
    return null;
  }

  // prefix suggestions; returns [{w, lang, shard, freq, exact}]
  function suggest(q, limit = 12) {
    q = q.trim().toLowerCase();
    if (!q) return [];
    const nq = normVi(q);
    const out = [];
    const exEn = lowerBound(idxEn, q, r => r[0]);
    if (idxEn[exEn] && idxEn[exEn][0] === q)
      out.push({ w: disp(idxEn[exEn]), lang: "en", exact: true, freq: 0 });
    const rv = viExact(q);
    if (rv) out.push({ w: disp(rv), lang: "vi", exact: true, freq: 0 });
    // en prefix
    {
      let i = lowerBound(idxEn, q, r => r[0]), n = 0;
      while (i < idxEn.length && n < 40) {
        const r = idxEn[i];
        if (!r[0].startsWith(q)) break;
        if (r[0] !== q) out.push({ w: disp(r), lang: "en", freq: r[2] });
        i++; n++;
      }
    }
    // vi prefix on normalized form (diacritic-insensitive)
    {
      let i = lowerBound(idxVi, nq, r => r[1]), n = 0;
      while (i < idxVi.length && n < 60) {
        const r = idxVi[i];
        if (!r[1].startsWith(nq)) break;
        if (r[0] !== q) out.push({ w: disp(r), lang: "vi", freq: 1e9, exact: r[1] === nq });
        i++; n++;
      }
    }
    const seen = new Set();
    out.sort((a, b) => ((b.exact ? 1 : 0) - (a.exact ? 1 : 0)) ||
                       ((a.freq || 1e9) - (b.freq || 1e9)) || (a.w < b.w ? -1 : 1));
    return out.filter(o => {
      const k = o.lang + ":" + o.w.toLowerCase();
      if (seen.has(k)) return false; seen.add(k); return true;
    }).slice(0, limit);
  }

  function resolveForm(q) {
    const base = forms[q.toLowerCase()];
    if (!base) return null;
    // return display form of base word
    const i = lowerBound(idxEn, base, r => r[0]);
    return (idxEn[i] && idxEn[i][0] === base) ? disp(idxEn[i]) : base;
  }

  async function getShard(lang, shard) {
    const key = lang + "/" + shard;
    if (shardCache.has(key)) return shardCache.get(key);
    if (inflight.has(key)) return inflight.get(key);
    const p = D(`shards/${lang}/${shard}.json`)
      .then(j => { shardCache.set(key, j); inflight.delete(key); return j; })
      .catch(e => { inflight.delete(key); throw e; });
    inflight.set(key, p);
    return p;
  }

  async function getEntry(lang, word) {
    const key = word.toLowerCase();
    if (lang === "en") {
      const i = lowerBound(idxEn, key, r => r[0]);
      if (!idxEn[i] || idxEn[i][0] !== key) return null;
      const data = await getShard("en", idxEn[i][1]);
      return data[key] || null;
    }
    const r = viExact(key);
    if (!r) return null;
    const data = await getShard("vi", r[2]);
    return data[r[0]] || null;
  }

  function randomWord() {
    if (idxEn.length && Math.random() < 0.5) {
      const r = idxEn[(Math.random() * idxEn.length) | 0];
      return { w: disp(r), lang: "en" };
    }
    const r = idxVi[(Math.random() * idxVi.length) | 0];
    return { w: disp(r), lang: "vi" };
  }

  return { load, suggest, getEntry, resolveForm, randomWord, normVi,
           get meta() { return meta; } };
})();
