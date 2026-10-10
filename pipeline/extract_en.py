#!/usr/bin/env python3
"""Build English->Vietnamese entries from RAW wiktextract English data.

Input : pipeline/raw/raw-en.jsonl.gz (English Wiktionary, raw wiktextract)
Output: pipeline/build/en_entries.jsonl   (one compact JSON per line)
        pipeline/build/en_forms.jsonl     (inflected form -> base word)

Only English records with >=1 Vietnamese translation are kept.
Vietnamese translations carry a "sense" label; they are attached to the
sense whose gloss best matches that label, otherwise to entry-level vi_other.

Compact entry schema:
{"w": headword, "cefr": "B1", "freq": 1234,
 "uk": "/ipa/", "us": "/ipa/",
 "etym": "From Middle English, ...",   (word origin, cleaned prose)
 "pos": [{"p": "verb", "senses": [
    {"g": ["english gloss"], "vi": ["đi"], "x": [["en example"]],
     "syn": [...], "ant": [...] }]}],
 "vi_other": [...]}
"""
import gzip, json, sys, re, unicodedata

ETY_STARTERS = ("From ", "Borrowed ", "Derived ", "Unknown ", "Perhaps ", "Probably ",
    "Compare ", "Ultimately ", "Cognate ", "Alteration ", "Blend ", "Blending ",
    "Clipping ", "Shortening ", "Back-formation ", "Back formation ", "Variant ",
    "Doublet ", "See ", "Shortened ", "Imitative ", "Onomatopoeic ",
    "Etymology uncertain")

def clean_etymology(t):
    """Extract readable prose from wiktextract etymology_text (CC BY-SA 4.0)."""
    if not t:
        return None
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    start = None
    for i, l in enumerate(lines):
        if l == "Etymology tree":
            continue
        if l.startswith(ETY_STARTERS):
            start = i
            break
    if start is None:
        return None
    text = " ".join(lines[start:])
    text = re.sub(r"\{\{[^{}]*\}\}", lambda m: m.group(0).split("|")[-1].rstrip("}"), text)
    text = re.sub(r"\{\{|\}\}", "", text)
    text = re.sub(r"\[\[([^|\]]*\|)?([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 8:
        return None
    return text[:600]

RAW = "raw/raw-en.jsonl.gz"
OUT = "build/en_entries.jsonl"
FORMS_OUT = "build/en_forms.jsonl"

SKIP_POS = {"punctuation", "symbol", "character"}

def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", s).strip()

def pick_ipa(sounds):
    uk = us = None
    for s in sounds or []:
        ipa = (s.get("ipa") or "").strip()
        if not ipa or len(ipa) > 60:
            continue
        # skip narrow/phonetic bracket variants, keep broad /.../
        tags = " ".join(s.get("tags") or [])
        if ipa.startswith("/") and ipa.endswith("/"):
            if ("UK" in tags or "Received" in tags or "British" in tags) and not uk:
                uk = ipa
            elif "US" in tags and not us:
                us = ipa
            elif not uk and "General" in tags:
                uk = ipa
    if not uk:
        for s in sounds or []:
            ipa = (s.get("ipa") or "").strip()
            if ipa.startswith("/") and ipa.endswith("/") and len(ipa) <= 60:
                uk = ipa
                break
    return uk, us

def main():
    entries = {}
    forms = {}
    n_scan = n_parse = n_keep = 0
    with gzip.open(RAW, "rt", encoding="utf-8") as f:
        for line in f:
            n_scan += 1
            if '"vi"' not in line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            n_parse += 1
            if r.get("lang_code") != "en":
                continue
            trs = [t for t in (r.get("translations") or [])
                   if t.get("lang_code") == "vi" and t.get("word")]
            if not trs:
                continue
            pos = r.get("pos") or ""
            if pos in SKIP_POS:
                continue
            w = r["word"]
            if not re.search(r"[a-z0-9]", w.lower()):
                continue  # skip pure symbols like "&"
            # collect inflected forms -> base
            for fm in r.get("forms") or []:
                fv = fm.get("form")
                tags = fm.get("tags") or []
                if fv and fv != w and len(fv) < 40 and not any(
                        t in ("abbreviation", "alternative", "misspelling", "obsolete")
                        for t in tags):
                    if fv not in forms:
                        forms[fv] = w
            e = entries.setdefault(w, {"w": w, "pos": [], "_p": {}})
            if "_etym" not in e:
                et = clean_etymology(r.get("etymology_text"))
                if et:
                    e["_etym"] = et
            if pos not in e["_p"]:
                e["_p"][pos] = len(e["pos"])
                e["pos"].append({"p": pos, "senses": []})
            sec = e["pos"][e["_p"][pos]]
            if "_uk" not in e:
                uk, us = pick_ipa(r.get("sounds"))
                e["_uk"], e["_us"] = uk, us
            # senses
            sense_vi = {}   # sense idx -> [vi words]
            vi_other = []
            for t in trs:
                tw = t["word"].strip()
                if not tw or len(tw) > 60:
                    continue
                label = norm(t.get("sense") or "")
                placed = False
                if label:
                    for i, s in enumerate(r.get("senses") or []):
                        for g in s.get("glosses") or []:
                            ng = norm(g)
                            if label and (label in ng or ng in label):
                                sense_vi.setdefault(i, [])
                                if tw not in sense_vi[i]:
                                    sense_vi[i].append(tw)
                                placed = True
                                break
                        if placed:
                            break
                if not placed and tw not in vi_other:
                    vi_other.append(tw)
            for i, s in enumerate(r.get("senses") or []):
                if len(sec["senses"]) >= 10:
                    break
                glosses = [g for g in (s.get("glosses") or []) if g][:2]
                if not glosses:
                    continue
                if any(set(glosses) == set(prev["g"]) for prev in sec["senses"]):
                    continue  # dedupe identical senses merged from multiple records
                ex = []
                for x in s.get("examples") or []:
                    t = x.get("text")
                    if t and len(t) < 300 and len(ex) < 3 and x.get("type") != "quotation":
                        ex.append([t])
                    elif t and len(t) < 300 and len(ex) < 3:
                        ex.append([t])
                sn = {"g": glosses}
                if i in sense_vi:
                    sn["vi"] = sense_vi[i][:8]
                if ex:
                    sn["x"] = ex
                syn = [a.get("word") for a in (s.get("synonyms") or []) if a.get("word")]
                ant = [a.get("word") for a in (s.get("antonyms") or []) if a.get("word")]
                if syn:
                    sn["syn"] = syn[:8]
                if ant:
                    sn["ant"] = ant[:8]
                sec["senses"].append(sn)
            if vi_other:
                e.setdefault("_vo", [])
                for tw in vi_other:
                    if tw not in e["_vo"]:
                        e["_vo"].append(tw)
            n_keep += 1
            if n_keep % 20000 == 0:
                print(f"  kept={n_keep} words={len(entries)}", file=sys.stderr)

    kept = 0
    with open(OUT, "w", encoding="utf-8") as out:
        for w in sorted(entries):
            e = entries[w]
            e["pos"] = [p for p in e["pos"] if p["senses"]]
            if not e["pos"]:
                continue
            rec = {"w": w}
            if e.get("_uk"):
                rec["uk"] = e["_uk"]
            if e.get("_us"):
                rec["us"] = e["_us"]
            if e.get("_etym"):
                rec["etym"] = e["_etym"]
            rec["pos"] = e["pos"]
            if e.get("_vo"):
                rec["vi_other"] = e["_vo"][:12]
            out.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
            kept += 1
    with open(FORMS_OUT, "w", encoding="utf-8") as out:
        for fv in sorted(forms):
            out.write(json.dumps({"f": fv, "w": forms[fv]},
                                 ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"scanned={n_scan} parsed={n_parse} kept_records={n_keep} "
          f"words={kept} forms={len(forms)}", file=sys.stderr)

if __name__ == "__main__":
    main()
