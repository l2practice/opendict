#!/usr/bin/env python3
"""Enrich EN entries with CEFR levels, frequency ranks and specialist domains (in place).

Input : build/en_entries.jsonl, build/vi_entries.jsonl, build/domains.json
Uses  : raw/cefrj-vocabulary-profile-1.5.csv, raw/octanove-vocabulary-profile-c1c2-1.0.csv,
        raw/ecdict.csv (frq/bnc ranks + fallback IPA + extra inflections)
Output: build/en_entries.jsonl (adds "cefr", "freq", "dom"; fills missing uk IPA)
        build/vi_entries.jsonl (adds "dom")
        build/en_forms.jsonl (appends ECDICT exchange inflections)
"""
import csv, json, sys, re

CEFR_ORDER = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

def load_cefr():
    m = {}
    for path in ["raw/cefrj-vocabulary-profile-1.5.csv",
                 "raw/octanove-vocabulary-profile-c1c2-1.0.csv"]:
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                level = (row.get("CEFR") or "").strip().upper()
                if level not in CEFR_ORDER:
                    continue
                for hw in (row.get("headword") or "").split("/"):
                    hw = hw.strip().lower()
                    if not hw or hw in m:
                        continue
                    m[hw] = level
    return m

def load_ecdict():
    """word.lower() -> (freq_rank, ipa, exchange)"""
    d = {}
    with open("raw/ecdict.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            w = (row.get("word") or "").strip().lower()
            if not w:
                continue
            ranks = []
            for k in ("frq", "bnc"):
                try:
                    v = int(row.get(k) or 0)
                    if v > 0:
                        ranks.append(v)
                except ValueError:
                    pass
            freq = min(ranks) if ranks else None
            ipa = (row.get("phonetic") or "").strip()
            if ipa and not (ipa.startswith("/") or ipa.startswith("[")):
                ipa = "/" + ipa + "/"
            ex = row.get("exchange") or ""
            prev = d.get(w)
            if prev is None or (freq and (prev[0] is None or freq < prev[0])):
                d[w] = (freq, ipa if len(ipa) < 60 else "", ex)
    return d

EX_RE = re.compile(r"([pdisa3]):([^/]+)")

def main():
    cefr = load_cefr()
    print(f"cefr words: {len(cefr)}", file=sys.stderr)
    ecd = load_ecdict()
    print(f"ecdict words: {len(ecd)}", file=sys.stderr)
    domains = json.load(open("build/domains.json", encoding="utf-8"))
    dom_en = {}
    for code in ("kte", "ktoan"):
        for w in domains[code]["en"]:
            dom_en.setdefault(w, []).append(code)
    dom_vi = {}
    for code in ("kte", "ktoan"):
        for w in domains[code]["vi"]:
            dom_vi.setdefault(w, []).append(code)
    print(f"domain words: en={len(dom_en)} vi={len(dom_vi)}", file=sys.stderr)

    n = n_cefr = n_freq = n_ipa = n_dom = 0
    extra_forms = {}
    out_lines = []
    with open("build/en_entries.jsonl", encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            w = e["w"]
            wl = w.lower()
            if wl in cefr:
                e["cefr"] = cefr[wl]
                n_cefr += 1
            if wl in dom_en:
                e["dom"] = dom_en[wl]
                n_dom += 1
            if wl in ecd:
                freq, ipa, ex = ecd[wl]
                if freq:
                    e["freq"] = freq
                    n_freq += 1
                if ipa and not e.get("uk"):
                    e["uk"] = ipa
                    n_ipa += 1
                for tag, form in EX_RE.findall(ex):
                    form = form.strip()
                    if form and form.lower() != wl and len(form) < 40:
                        extra_forms.setdefault(form.lower(), wl)
            out_lines.append(json.dumps(e, ensure_ascii=False, separators=(",", ":")))
            n += 1
    with open("build/en_entries.jsonl", "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")
    # merge extra inflection forms
    existing = set()
    with open("build/en_forms.jsonl", encoding="utf-8") as f:
        for line in f:
            existing.add(json.loads(line)["f"])
    added = 0
    with open("build/en_forms.jsonl", "a", encoding="utf-8") as f:
        for form in sorted(extra_forms):
            if form not in existing:
                f.write(json.dumps({"f": form, "w": extra_forms[form]},
                                   ensure_ascii=False, separators=(",", ":")) + "\n")
                added += 1
    print(f"entries={n} cefr={n_cefr} freq={n_freq} ipa_fallback={n_ipa} dom={n_dom} extra_forms={added}",
          file=sys.stderr)

    # tag VI entries with domains (in place)
    n_vi = n_vi_dom = 0
    vi_lines = []
    with open("build/vi_entries.jsonl", encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            wl = e["w"].lower()
            if wl in dom_vi:
                e["dom"] = dom_vi[wl]
                n_vi_dom += 1
            vi_lines.append(json.dumps(e, ensure_ascii=False, separators=(",", ":")))
            n_vi += 1
    with open("build/vi_entries.jsonl", "w", encoding="utf-8") as f:
        f.write("\n".join(vi_lines) + "\n")
    print(f"vi_entries={n_vi} dom={n_vi_dom}", file=sys.stderr)

if __name__ == "__main__":
    main()
