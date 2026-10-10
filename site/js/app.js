/* OpenDict app — hash router + views */
(() => {
  const view = document.getElementById("view");
  const input = document.getElementById("searchInput");
  const suggestBox = document.getElementById("suggestBox");
  const clearBtn = document.getElementById("searchClear");

  const POS_VI = {
    noun: "danh từ", verb: "động từ", adj: "tính từ", adjective: "tính từ",
    adv: "trạng từ", adverb: "trạng từ", pron: "đại từ", pronoun: "đại từ",
    prep: "giới từ", preposition: "giới từ", conj: "liên từ", conjunction: "liên từ",
    interj: "thán từ", interjection: "thán từ", num: "số từ", numeral: "số từ",
    particle: "trợ từ", det: "hạn định từ", determiner: "hạn định từ",
    phrase: "cụm từ", proverb: "tục ngữ", name: "danh từ riêng", article: "mạo từ",
    prefix: "tiền tố", suffix: "hậu tố", intj: "thán từ", prep_phrase: "cụm giới từ",
    contraction: "dạng rút gọn", abbreviation: "viết tắt",
  };
  const posLabel = (p) => UI_LANG === "vi" ? (POS_VI[p] || p) : p;

  /* ---------- storage ---------- */
  const store = {
    get favs() { try { return JSON.parse(localStorage.getItem("od_favs") || "[]"); } catch { return []; } },
    set favs(v) { localStorage.setItem("od_favs", JSON.stringify(v)); },
    get hist() { try { return JSON.parse(localStorage.getItem("od_hist") || "[]"); } catch { return []; } },
    set hist(v) { localStorage.setItem("od_hist", JSON.stringify(v.slice(0, 100))); },
  };
  const isFav = (lang, w) => store.favs.some(f => f.lang === lang && f.w === w);
  function toggleFav(lang, w) {
    let f = store.favs;
    if (isFav(lang, w)) { f = f.filter(x => !(x.lang === lang && x.w === w)); toast(t("unsaved")); }
    else { f.unshift({ lang, w, at: Date.now() }); toast(t("saved")); }
    store.favs = f;
    renderFavBtn(lang, w);
  }
  function pushHist(lang, w) {
    let h = store.hist.filter(x => !(x.lang === lang && x.w === w));
    h.unshift({ lang, w, at: Date.now() });
    store.hist = h;
  }

  /* ---------- helpers ---------- */
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
  let toastTimer = null;
  function toast(msg) {
    let el = document.querySelector(".toast");
    if (!el) { el = document.createElement("div"); el.className = "toast"; document.body.appendChild(el); }
    el.textContent = msg; el.classList.add("show");
    clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove("show"), 1800);
  }
  function speak(text, lang) {
    try {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = lang === "vi" ? "vi-VN" : "en-US";
      u.rate = 0.9;
      speechSynthesis.cancel(); speechSynthesis.speak(u);
    } catch { /* no tts */ }
  }
  function fmtNum(n) { return Number(n || 0).toLocaleString(UI_LANG === "vi" ? "vi-VN" : "en-US"); }

  /* ---------- search box ---------- */
  let sugList = [], sugActive = -1, sugTimer = null;
  function hideSuggest() { suggestBox.hidden = true; input.setAttribute("aria-expanded", "false"); sugActive = -1; }
  function showSuggest(q) {
    sugList = Data.suggest(q, 12);
    if (!sugList.length) {
      suggestBox.innerHTML = `<div class="suggest-empty">${esc(t("no_suggest"))}</div>`;
    } else {
      suggestBox.innerHTML = sugList.map((s, i) =>
        `<button class="suggest-item" role="option" data-i="${i}">
           <span class="lang-badge ${s.lang}">${s.lang.toUpperCase()}</span>
           <span class="w">${esc(s.w)}</span>
           ${s.exact ? "" : `<span class="hint">${esc(hintFor(s))}</span>`}
         </button>`).join("");
      suggestBox.querySelectorAll(".suggest-item").forEach(b => {
        b.addEventListener("mousedown", (e) => { e.preventDefault(); goWord(sugList[+b.dataset.i]); });
        b.addEventListener("mousemove", () => setActive(+b.dataset.i));
      });
    }
    suggestBox.hidden = false;
    input.setAttribute("aria-expanded", "true");
  }
  function hintFor(s) { return s.lang === "en" ? t("en_entry") : t("vi_entry"); }
  function setActive(i) {
    sugActive = i;
    suggestBox.querySelectorAll(".suggest-item").forEach((b, j) => b.classList.toggle("active", j === i));
  }
  function goWord(s) {
    hideSuggest();
    input.value = "";
    clearBtn.hidden = true;
    location.hash = `#/${s.lang}/${encodeURIComponent(s.w)}`;
  }
  function doSearch(q) {
    q = q.trim();
    if (!q) return;
    const sug = Data.suggest(q, 1);
    if (sug.length && (sug[0].exact || sug[0].w.toLowerCase() === q.toLowerCase())) { goWord(sug[0]); return; }
    // inflected English form?
    const base = Data.resolveForm(q);
    if (base) { location.hash = `#/en/${encodeURIComponent(base)}`; return; }
    if (sug.length) { goWord(sug[0]); return; }
    location.hash = `#/notfound/${encodeURIComponent(q)}`;
  }
  input.addEventListener("input", () => {
    clearBtn.hidden = !input.value;
    clearTimeout(sugTimer);
    const q = input.value;
    if (!q.trim()) { hideSuggest(); return; }
    sugTimer = setTimeout(() => showSuggest(q), 120);
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" && !suggestBox.hidden) { e.preventDefault(); setActive(Math.min(sugActive + 1, sugList.length - 1)); }
    else if (e.key === "ArrowUp" && !suggestBox.hidden) { e.preventDefault(); setActive(Math.max(sugActive - 1, 0)); }
    else if (e.key === "Enter") { e.preventDefault(); if (sugActive >= 0 && sugList[sugActive]) goWord(sugList[sugActive]); else { hideSuggest(); doSearch(input.value); } }
    else if (e.key === "Escape") hideSuggest();
  });
  input.addEventListener("blur", () => setTimeout(hideSuggest, 150));
  clearBtn.addEventListener("click", () => { input.value = ""; clearBtn.hidden = true; input.focus(); hideSuggest(); });
  document.addEventListener("click", (e) => { if (!document.getElementById("searchWrap").contains(e.target)) hideSuggest(); });

  /* ---------- theme & lang ---------- */
  function initTheme() {
    const th = localStorage.getItem("od_theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.dataset.theme = th;
    document.getElementById("themeToggle").textContent = th === "dark" ? "☀️" : "🌙";
  }
  document.getElementById("themeToggle").addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("od_theme", next);
    document.getElementById("themeToggle").textContent = next === "dark" ? "☀️" : "🌙";
  });
  document.getElementById("langToggle").addEventListener("click", () => { setLang(UI_LANG === "vi" ? "en" : "vi"); route(); });

  /* ---------- views ---------- */
  function renderFavBtn(lang, w) {
    const b = document.getElementById("favBtn");
    if (!b) return;
    const saved = isFav(lang, w);
    b.classList.toggle("saved", saved);
    b.textContent = saved ? "★" : "☆";
    b.title = saved ? t("unsave") : t("save");
  }

  const DOM_SLUGS = { "kinh-te": "kte", "ke-toan": "ktoan" };
  const DOM_URL = { kte: "#/domain/kinh-te", ktoan: "#/domain/ke-toan" };
  function domBadges(entry) {
    return (entry.dom || []).map(d =>
      `<a class="dom-badge dom-${d}" href="${DOM_URL[d]}">${esc(t(d === "kte" ? "dom_kte" : "dom_ktoan"))}</a>`
    ).join("");
  }

  function entryHead(lang, entry, redirectedFrom) {
    const fav = `<button id="favBtn" class="icon-btn" aria-label="${esc(t("save"))}">☆</button>`;
    const copy = `<button id="copyBtn" class="icon-btn" title="${esc(t("copy_link"))}">🔗</button>`;
    const cefr = entry.cefr ? `<span class="cefr c-${esc(entry.cefr)}">${esc(entry.cefr)}</span>` : "";
    const freq = entry.freq ? `<span class="freq">#${fmtNum(entry.freq)} ${esc(t("freq_rank"))}</span>` : "";
    const doms = domBadges(entry);
    const redir = redirectedFrom
      ? `<div class="redirect-note">“${esc(redirectedFrom)}” ${esc(t("redirected"))} → <b>${esc(entry.w)}</b></div>` : "";
    return `<div class="entry-head">
        <h1 class="entry-word">${esc(entry.w)}</h1>${cefr}${freq}${doms}
        <div class="entry-actions">${fav}${copy}</div>
      </div>${redir}`;
  }

  function ipaRow(entry, lang) {
    const items = [];
    const btn = (txt, tag, say) =>
      `<span class="ipa"><span class="tag">${esc(tag)}</span><span>${esc(txt)}</span>
       <button class="speak" data-say="${esc(say)}" data-lang="${lang}" aria-label="🔊">🔊</button></span>`;
    if (lang === "en") {
      if (entry.uk) items.push(btn(entry.uk, t("ipa_uk"), entry.w));
      if (entry.us) items.push(btn(entry.us, t("ipa_us"), entry.w));
    } else if (entry.ipa) {
      const L = { hn: t("ipa_hn"), hue: t("ipa_hue"), sg: t("ipa_sg") };
      for (const k of ["hn", "hue", "sg"]) if (entry.ipa[k]) items.push(btn(entry.ipa[k], L[k], entry.w));
    }
    return items.length ? `<div class="ipa-row">${items.join("")}</div>` : "";
  }

  function chips(words, lang) {
    return words.map(w => `<a class="link-chip" href="#/${lang}/${encodeURIComponent(w)}">${esc(w)}</a>`).join("");
  }

  function viewEntryEn(entry, redirectedFrom) {
    let h = entryHead("en", entry, redirectedFrom) + ipaRow(entry, "en");
    for (const sec of entry.pos) {
      h += `<section class="pos-block"><h2 class="pos-title">${esc(posLabel(sec.p))}</h2>`;
      sec.senses.forEach((s, i) => {
        h += `<div class="sense"><span class="sense-num">${i + 1}.</span><span class="gloss">${esc(s.g.join(" "))}</span>`;
        if (s.vi && s.vi.length)
          h += `<div class="vi-meanings"><span class="vi-label">${esc(t("vi_meaning"))}</span>${s.vi.map(v => `<span class="vi-chip">${esc(v)}</span>`).join("")}</div>`;
        for (const x of (s.x || []))
          h += `<div class="example">“${esc(x[0])}”</div>`;
        if (s.syn && s.syn.length)
          h += `<div class="syn-row"><span class="lbl">${esc(t("synonyms"))}</span> ${chips(s.syn, "en")}</div>`;
        if (s.ant && s.ant.length)
          h += `<div class="syn-row"><span class="lbl">${esc(t("antonyms"))}</span> ${chips(s.ant, "en")}</div>`;
        h += `</div>`;
      });
      h += `</section>`;
    }
    if (entry.vi_other && entry.vi_other.length)
      h += `<section class="pos-block"><h2 class="pos-title">${esc(t("other_vi"))}</h2>
            <div class="vi-meanings">${entry.vi_other.map(v => `<span class="vi-chip">${esc(v)}</span>`).join("")}</div></section>`;
    view.innerHTML = h;
    wireEntry("en", entry);
  }

  function viewEntryVi(entry) {
    let h = entryHead("vi", entry, null) + ipaRow(entry, "vi");
    for (const sec of entry.pos) {
      h += `<section class="pos-block"><h2 class="pos-title">${esc(posLabel(sec.p))}</h2>`;
      sec.senses.forEach((s, i) => {
        h += `<div class="sense"><span class="sense-num">${i + 1}.</span><span class="gloss">${esc(s.g.join("; "))}</span>`;
        for (const x of (s.x || []))
          h += `<div class="example">“${esc(x[0])}”${x[1] ? `<span class="ex-vi">${esc(x[1])}</span>` : ""}</div>`;
        if (s.syn && s.syn.length)
          h += `<div class="syn-row"><span class="lbl">${esc(t("synonyms"))}</span> ${chips(s.syn, "vi")}</div>`;
        if (s.ant && s.ant.length)
          h += `<div class="syn-row"><span class="lbl">${esc(t("antonyms"))}</span> ${chips(s.ant, "vi")}</div>`;
        h += `</div>`;
      });
      h += `</section>`;
    }
    const rel = (entry.rel || []).filter(w => w !== entry.w);
    const der = (entry.der || []).filter(w => w !== entry.w);
    if (rel.length || der.length) {
      h += `<section class="pos-block">`;
      if (rel.length) h += `<div class="syn-row"><span class="lbl">${esc(t("related"))}</span> ${chips(rel.slice(0, 14), "vi")}</div>`;
      if (der.length) h += `<div class="syn-row"><span class="lbl">${esc(t("derived"))}</span> ${chips(der.slice(0, 14), "vi")}</div>`;
      h += `</section>`;
    }
    view.innerHTML = h;
    wireEntry("vi", entry);
  }

  function wireEntry(lang, entry) {
    renderFavBtn(lang, entry.w);
    document.getElementById("favBtn").addEventListener("click", () => toggleFav(lang, entry.w));
    document.getElementById("copyBtn").addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(location.href); toast(t("copied")); }
      catch { toast(location.href); }
    });
    view.querySelectorAll(".speak").forEach(b =>
      b.addEventListener("click", () => speak(b.dataset.say, b.dataset.lang)));
    pushHist(lang, entry.w);
    document.title = `${entry.w} — OpenDict`;
  }

  function viewNotFound(q) {
    const sug = Data.suggest(q, 8).filter(s => !s.exact);
    view.innerHTML = `<div class="notfound">
      <h2>${esc(t("not_found_t"))}</h2>
      <p>${esc(t("not_found_s"))} “<b>${esc(q)}</b>”.</p>
      ${sug.length ? `<p>${esc(t("did_you_mean"))}</p><div class="quick-links">` +
        sug.map(s => `<a class="btn" href="#/${s.lang}/${encodeURIComponent(s.w)}">${esc(s.w)}</a>`).join("") + `</div>` : ""}
      <p style="margin-top:22px"><a class="btn" href="#/">${esc(t("back_home"))}</a></p>
    </div>`;
    document.title = `${t("not_found_t")} — OpenDict`;
  }

  function viewHome() {
    const m = Data.meta || {};
    view.innerHTML = `<div class="hero">
      <h1>${esc(t("hero_title_a"))} <span class="accent">${esc(t("hero_title_b"))}</span></h1>
      <p>${esc(t("hero_sub"))}</p>
      <div class="stats">
        <div class="stat"><b>${fmtNum(m.en)}</b><span>${esc(t("stat_en"))}</span></div>
        <div class="stat"><b>${fmtNum(m.vi)}</b><span>${esc(t("stat_vi"))}</span></div>
        <div class="stat"><b>${m.sources || 5}</b><span>${esc(t("stat_src"))}</span></div>
      </div>
      <div class="quick-links">
        <button class="btn primary" id="randomBtn">${esc(t("random_word"))}</button>
        <a class="btn" href="#/about">${esc(t("browse_about"))}</a>
      </div>
      <h2 class="dom-home-title">${esc(t("dom_browse"))}</h2>
      <div class="dom-cards">
        <a class="dom-card dom-kte-card" href="#/domain/kinh-te">
          <span class="dom-card-name">${esc(t("dom_kte"))}</span>
          <span class="dom-card-desc">${esc(t("dom_card_kte_d"))}</span>
          <span class="dom-card-count"><b>${fmtNum((Data.domains && Data.domains.kte && (Data.domains.kte.en.length + Data.domains.kte.vi.length)) || 0)}</b> ${esc(t("dom_terms"))}</span>
        </a>
        <a class="dom-card dom-ktoan-card" href="#/domain/ke-toan">
          <span class="dom-card-name">${esc(t("dom_ktoan"))}</span>
          <span class="dom-card-desc">${esc(t("dom_card_ktoan_d"))}</span>
          <span class="dom-card-count"><b>${fmtNum((Data.domains && Data.domains.ktoan && (Data.domains.ktoan.en.length + Data.domains.ktoan.vi.length)) || 0)}</b> ${esc(t("dom_terms"))}</span>
        </a>
      </div>
    </div>`;
    document.getElementById("randomBtn").addEventListener("click", () => {
      const r = Data.randomWord();
      location.hash = `#/${r.lang}/${encodeURIComponent(r.w)}`;
    });
    document.title = "OpenDict — " + t("hero_title_b");
  }

  /* ---------- specialist domain browse ---------- */
  function viewDomain(slug) {
    const code = DOM_SLUGS[slug];
    const doms = Data.domains;
    if (!code || !doms || !doms[code]) { viewNotFound(slug); return; }
    const d = doms[code];
    const nEn = (d.en || []).length, nVi = (d.vi || []).length;
    const title = t(code === "kte" ? "dom_title_kte" : "dom_title_ktoan");
    const sub = t(code === "kte" ? "dom_sub_kte" : "dom_sub_ktoan");
    const chipList = (words, lang) => words.map(w =>
      `<a class="dom-chip" data-w="${esc(w.toLowerCase())}" href="#/${lang}/${encodeURIComponent(w)}">${esc(w)}</a>`
    ).join("");
    view.innerHTML = `<div class="domain-page">
      <p><a class="btn" href="#/">${esc(t("back_home"))}</a></p>
      <h2>${esc(title)}</h2>
      <p class="dom-sub">${esc(sub)}</p>
      <p class="dom-count"><b>${fmtNum(nEn + nVi)}</b> ${esc(t("dom_terms"))}
        <span class="dot">·</span> ${fmtNum(nEn)} ${esc(t("en_entry"))}
        <span class="dot">·</span> ${fmtNum(nVi)} ${esc(t("vi_entry"))}</p>
      <input id="domFilter" class="dom-filter" type="search" placeholder="${esc(t("dom_search_ph"))}" aria-label="${esc(t("dom_search_ph"))}">
      <p class="dom-note">${esc(t("dom_note"))}</p>
      <h3 class="dom-lang">${esc(t("en_entry"))} (${fmtNum(nEn)})</h3>
      <div class="dom-grid" id="domGridEn">${chipList(d.en || [], "en")}</div>
      <h3 class="dom-lang">${esc(t("vi_entry"))} (${fmtNum(nVi)})</h3>
      <div class="dom-grid" id="domGridVi">${chipList(d.vi || [], "vi")}</div>
      <p class="empty-note" id="domEmpty" hidden>${esc(t("dom_no_match"))}</p>
    </div>`;
    const filt = document.getElementById("domFilter");
    filt.addEventListener("input", () => {
      const q = Data.normVi(filt.value.trim());
      let visible = 0;
      view.querySelectorAll(".dom-chip").forEach(c => {
        const show = !q || Data.normVi(c.dataset.w).includes(q);
        c.style.display = show ? "" : "none";
        if (show) visible++;
      });
      document.getElementById("domEmpty").hidden = visible > 0;
    });
    document.title = `${title} — OpenDict`;
  }

  function viewList(kind) {
    const isFav = kind === "favorites";
    const items = isFav ? store.favs : store.hist;
    let h = `<div class="list-page"><h2>${esc(t(isFav ? "fav_title" : "hist_title"))}</h2>`;
    if (!items.length) {
      h += `<div class="empty-note">${esc(t(isFav ? "fav_empty" : "hist_empty"))}</div>`;
    } else {
      h += items.map((f, i) => `<div class="list-item">
          <span class="lang-badge ${f.lang}">${f.lang.toUpperCase()}</span>
          <a class="w" href="#/${f.lang}/${encodeURIComponent(f.w)}">${esc(f.w)}</a>
          <span class="meta">${new Date(f.at).toLocaleDateString(UI_LANG === "vi" ? "vi-VN" : "en-US")}</span>
          <span class="spacer"></span>
          <button class="mini-btn" data-i="${i}">${esc(t("remove"))}</button>
        </div>`).join("");
      if (!isFav) h += `<p><button class="btn" id="clearHist">${esc(t("clear_hist"))}</button></p>`;
    }
    h += `</div>`;
    view.innerHTML = h;
    view.querySelectorAll(".mini-btn").forEach(b => b.addEventListener("click", () => {
      const i = +b.dataset.i;
      if (isFav) store.favs = store.favs.filter((_, j) => j !== i);
      else store.hist = store.hist.filter((_, j) => j !== i);
      viewList(kind);
    }));
    const c = document.getElementById("clearHist");
    if (c) c.addEventListener("click", () => { store.hist = []; toast(t("hist_cleared")); viewList(kind); });
    document.title = `${t(isFav ? "fav_title" : "hist_title")} — OpenDict`;
  }

  const SOURCES = [
    { name: "English Wiktionary, English entries (Wiktextract, kaikki.org)", url: "kaikki.org/dictionary/English", licence: "CC BY-SA 4.0; GFDL", attr: "Wiktionary contributors; Tatu Ylonen, Wiktextract (LREC 2022)" },
    { name: "Vietnamese Wiktionary (Wiktextract, kaikki.org)", url: "kaikki.org/dictionary/Vietnamese", licence: "CC BY-SA 4.0; GFDL", attr: "Những người đóng góp Wiktionary tiếng Việt; Wiktextract" },
    { name: "ECDICT (BNC/COCA frequency ranks and fallback IPA only)", url: "raw.githubusercontent.com/skywind3000/ECDICT", licence: "MIT", attr: "skywind3000, ECDICT" },
    { name: "CEFR-J Vocabulary Profile 1.5", url: "raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj", licence: "Free for research and commercial use; citation required", attr: "CEFR-J Vocabulary Profile 1.5. Tono Laboratory, Tokyo University of Foreign Studies" },
    { name: "Octanove Vocabulary Profile C1/C2 1.0", url: "raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj", licence: "CC BY-SA 4.0", attr: "Octanove Labs" },
  ];

  function viewAbout() {
    const m = Data.meta || {};
    const rows = SOURCES.map(s => `<tr>
      <td class="src">${esc(s.name)}<span class="url">${esc(s.url)}</span></td>
      <td>${esc(s.licence)}</td><td>${esc(s.attr)}</td><td>${esc(m.retrieved || "")}</td>
    </tr>`).join("");
    view.innerHTML = `<div class="about">
      <h2>${esc(t("about_title"))}</h2>
      <p>${esc(t("about_p1"))}</p>
      <h2>${esc(t("about_h_sources"))}</h2>
      <p>${esc(t("about_sources_note"))}</p>
      <div style="overflow-x:auto"><table>
        <tr><th>${esc(t("th_source"))}</th><th>${esc(t("th_licence"))}</th><th>${esc(t("th_attr"))}</th><th>${esc(t("th_retrieved"))}</th></tr>
        ${rows}
      </table></div>
      <h2>${esc(t("about_h_licence"))}</h2>
      <p>${esc(t("about_lic_app"))}<br>${esc(t("about_lic_data"))}</p>
      <h2>${esc(t("dom_about_h"))}</h2>
      <p>${esc(t("dom_about_p"))}</p>
      <div class="quick-links" style="margin-bottom:18px">
        <a class="btn" href="#/domain/kinh-te">${esc(t("dom_kte"))}</a>
        <a class="btn" href="#/domain/ke-toan">${esc(t("dom_ktoan"))}</a>
      </div>
      <h2>${esc(t("about_h_rebuild"))}</h2>
      <p>${esc(t("about_rebuild_note"))}</p>
      <pre>python3 pipeline/extract_en.py   # English entries (needs raw-en.jsonl.gz)\npython3 pipeline/extract_vi.py   # Vietnamese entries\npython3 pipeline/enrich.py       # CEFR levels + frequency ranks\npython3 pipeline/extract_domains.py  # specialist domain labels (needs kaikki data)\npython3 pipeline/pack.py         # shard + write site/data/</pre>
    </div>`;
    document.title = `${t("about_title")} — OpenDict`;
  }

  /* ---------- router ---------- */
  async function route() {
    const hash = location.hash || "#/";
    const parts = hash.replace(/^#\//, "").split("/");
    const page = parts[0] || "";
    window.scrollTo(0, 0);
    if (page === "en" || page === "vi") {
      const q = decodeURIComponent(parts.slice(1).join("/") || "").trim();
      if (!q) { viewHome(); return; }
      view.innerHTML = `<div class="loading"><div class="spinner"></div><div>${esc(t("loading"))}</div></div>`;
      let entry = await Data.getEntry(page, q);
      let redirectedFrom = null;
      if (!entry && page === "en") {
        const base = Data.resolveForm(q);
        if (base) { entry = await Data.getEntry("en", base); redirectedFrom = q; }
      }
      if (entry) (page === "en" ? viewEntryEn : viewEntryVi)(entry, redirectedFrom);
      else viewNotFound(q);
      return;
    }
    if (page === "about") { viewAbout(); return; }
    if (page === "domain") { viewDomain(parts[1] || ""); return; }
    if (page === "favorites" || page === "history") { viewList(page); return; }
    if (page === "notfound") { viewNotFound(decodeURIComponent(parts.slice(1).join("/") || "")); return; }
    viewHome();
  }

  /* ---------- boot ---------- */
  async function boot() {
    initTheme();
    setLang(UI_LANG);
    view.innerHTML = `<div class="loading"><div class="spinner"></div><div>${esc(t("word_of_load"))}</div></div>`;
    try {
      await Data.load();
    } catch (e) {
      view.innerHTML = `<div class="notfound"><h2>⚠️</h2><p>${esc(t("word_of_error"))}</p></div>`;
      return;
    }
    window.addEventListener("hashchange", route);
    // service worker for offline use
    if ("serviceWorker" in navigator) {
      try { await navigator.serviceWorker.register("sw.js"); } catch { /* ignore */ }
    }
    route();
  }
  document.addEventListener("DOMContentLoaded", boot);
})();
