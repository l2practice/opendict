#!/usr/bin/env python3
"""Build Vietnamese->English entries from kaikki Vietnamese Wiktionary data.

Input : pipeline/raw/kaikki-vi.jsonl.gz
Output: pipeline/build/vi_entries.jsonl  (one compact JSON per line)

Compact entry schema:
{
  "w": headword,
  "pos": [{"p": "noun", "senses": [
      {"g": ["english gloss", ...], "x": [["vi example", "en translation"]],
       "syn": [...], "ant": [...]} ]}],
  "ipa": {"hn": "...", "hue": "...", "sg": "..."},
  "rel": [related words], "der": [derived words]
}
Limits keep the web payload small: senses<=8/POS, examples<=3/sense,
syn/ant<=10, rel/der<=12.
"""
import gzip, json, sys, unicodedata
from collections import defaultdict

RAW = "raw/kaikki-vi.jsonl.gz"
OUT = "build/vi_entries.jsonl"

POS_MAP = {
    "noun": "danh từ", "verb": "động từ", "adj": "tính từ", "adjective": "tính từ",
    "adv": "trạng từ", "adverb": "trạng từ", "pron": "đại từ", "pronoun": "đại từ",
    "prep": "giới từ", "preposition": "giới từ", "conj": "liên từ",
    "conjunction": "liên từ", "interj": "thán từ", "interjection": "thán từ",
    "num": "số từ", "numeral": "số từ", "particle": "trợ từ", "det": "hạn định từ",
    "determiner": "hạn định từ", "phrase": "cụm từ", "proverb": "tục ngữ",
    "name": "danh từ riêng",
}

def norm_vi(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d")

def clean_ipa(s):
    return s.strip().strip("/[]")

def main():
    # merge records by word (kaikki has one record per word+pos+etymology)
    entries = {}
    n_rec = 0
    with gzip.open(RAW, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("lang_code") != "vi":
                continue
            n_rec += 1
            w = r["word"]
            e = entries.setdefault(w, {"w": w, "pos": [], "_pos_idx": {}})
            pos = r.get("pos") or ""
            if pos not in e["_pos_idx"]:
                e["_pos_idx"][pos] = len(e["pos"])
                e["pos"].append({"p": pos, "senses": []})
            sec = e["pos"][e["_pos_idx"][pos]]
            # sounds -> ipa once per entry
            if "ipa" not in e:
                ipa = {}
                for s in r.get("sounds") or []:
                    ip = s.get("ipa")
                    if not ip:
                        continue
                    tags = " ".join(s.get("tags") or [])
                    note = s.get("note") or ""
                    key = None
                    if "Hà-Nội" in tags or "Hanoi" in tags or "Hà Nội" in note:
                        key = "hn"
                    elif "Huế" in tags or "Hue" in tags:
                        key = "hue"
                    elif "Saigon" in note or "Sài Gòn" in note or "Hồ Chí Minh" in tags:
                        key = "sg"
                    if key and key not in ipa:
                        ipa[key] = clean_ipa(ip)
                if ipa:
                    e["ipa"] = ipa
            for s in r.get("senses") or []:
                if len(sec["senses"]) >= 8:
                    break
                glosses = [g for g in (s.get("glosses") or []) if g]
                if not glosses:
                    continue
                ex = []
                for x in s.get("examples") or []:
                    t = x.get("text")
                    if t and len(ex) < 3:
                        ex.append([t, x.get("translation") or ""])
                entry_sense = {"g": glosses[:3]}
                if ex:
                    entry_sense["x"] = ex
                syn = [x.get("word") for x in (s.get("synonyms") or []) if x.get("word")]
                ant = [x.get("word") for x in (s.get("antonyms") or []) if x.get("word")]
                if syn:
                    entry_sense["syn"] = syn[:10]
                if ant:
                    entry_sense["ant"] = ant[:10]
                sec["senses"].append(entry_sense)
            for x in (r.get("related") or [])[:12]:
                if x.get("word"):
                    e.setdefault("rel", [])
                    if x["word"] not in e["rel"]:
                        e["rel"].append(x["word"])
            for x in (r.get("derived") or [])[:12]:
                if x.get("word"):
                    e.setdefault("der", [])
                    if x["word"] not in e["der"]:
                        e["der"].append(x["word"])
    # drop empties, write
    kept = 0
    with open(OUT, "w", encoding="utf-8") as out:
        for w in sorted(entries):
            e = entries[w]
            e["pos"] = [p for p in e["pos"] if p["senses"]]
            if not e["pos"]:
                continue
            del e["_pos_idx"]
            e["n"] = norm_vi(w)
            out.write(json.dumps(e, ensure_ascii=False, separators=(",", ":")) + "\n")
            kept += 1
    print(f"records={n_rec} distinct={len(entries)} kept={kept} -> {OUT}", file=sys.stderr)

if __name__ == "__main__":
    main()
