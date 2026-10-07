#!/usr/bin/env python3
"""Pack compact entries into sharded JSON for the static site.

Input : build/en_entries.jsonl, build/vi_entries.jsonl, build/en_forms.jsonl
Output: site/data/
          meta.json, index-en.json, index-vi.json, forms.json
          shards/en/<shard>.json, shards/vi/<shard>.json

Index formats (must match site/js/data.js):
  index-en.json: [[key, shard, freq, display], ...] sorted by key   (key = lower)
  index-vi.json: [[key, norm, shard, display], ...] sorted by key   (key = lower)
  shards: {key: entry}
"""
import json, os, re, sys, unicodedata, shutil
from datetime import date

SITE_DATA = "../site/data"

def norm_vi(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d")

def shard_en(key):
    m = re.sub(r"[^a-z0-9]", "", key)[:2]
    return m if len(m) == 2 else (m + "_" if len(m) == 1 else "other")

def shard_vi(norm):
    c = norm[:1]
    return c if re.match(r"[a-z]", c) else "other"

def main():
    if os.path.exists(SITE_DATA):
        shutil.rmtree(SITE_DATA)
    os.makedirs(SITE_DATA + "/shards/en")
    os.makedirs(SITE_DATA + "/shards/vi")

    # ---- English ----
    en_shards, en_index = {}, []
    n_en = 0
    with open("build/en_entries.jsonl", encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            key = e["w"].lower()
            sh = shard_en(key)
            en_shards.setdefault(sh, {})[key] = e
            en_index.append([key, sh, e.get("freq") or 10**9, e["w"]])
            n_en += 1
    en_index.sort(key=lambda r: r[0])
    # ---- Vietnamese ----
    vi_shards, vi_index = {}, []
    n_vi = 0
    with open("build/vi_entries.jsonl", encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            key = e["w"].lower()
            nv = e.get("n") or norm_vi(key)
            sh = shard_vi(nv)
            vi_shards.setdefault(sh, {})[key] = e
            vi_index.append([key, nv, sh, e["w"]])
            n_vi += 1
    vi_index.sort(key=lambda r: (r[1], r[0]))  # sorted by norm for diacritic-insensitive search
    # ---- forms ----
    forms = {}
    with open("build/en_forms.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            forms.setdefault(r["f"].lower(), r["w"].lower())

    for sh, d in en_shards.items():
        with open(f"{SITE_DATA}/shards/en/{sh}.json", "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    for sh, d in vi_shards.items():
        with open(f"{SITE_DATA}/shards/vi/{sh}.json", "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    with open(f"{SITE_DATA}/index-en.json", "w", encoding="utf-8") as f:
        json.dump(en_index, f, ensure_ascii=False, separators=(",", ":"))
    with open(f"{SITE_DATA}/index-vi.json", "w", encoding="utf-8") as f:
        json.dump(vi_index, f, ensure_ascii=False, separators=(",", ":"))
    with open(f"{SITE_DATA}/forms.json", "w", encoding="utf-8") as f:
        json.dump(forms, f, ensure_ascii=False, separators=(",", ":"))
    meta = {
        "version": "1.0.0",
        "built": date.today().isoformat(),
        "retrieved": "2026-10-06",
        "en": n_en, "vi": n_vi,
        "sources": 5,
        "licence_data": "CC BY-SA 4.0 (ECDICT: MIT)",
    }
    with open(f"{SITE_DATA}/meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    # sizes
    total = 0
    for root, _, files in os.walk(SITE_DATA):
        for fn in files:
            total += os.path.getsize(os.path.join(root, fn))
    print(f"en={n_en} ({len(en_shards)} shards)  vi={n_vi} ({len(vi_shards)} shards)  "
          f"forms={len(forms)}  total={total/1e6:.1f} MB", file=sys.stderr)

if __name__ == "__main__":
    main()
