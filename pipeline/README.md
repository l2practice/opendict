# pipeline/ — OpenDict data pipeline

Scripts to rebuild `site/data/` from the open sources listed in `sources.toml`.
Each source is downloaded with a recorded checksum (`sources.sha256`) so the
data can be rebuilt exactly.

## Steps

```
# 1. download (or fetch manually from the URLs in sources.toml)
python3 pdownload.py <url> raw/<file> 8

# 2. extract
python3 extract_en.py     # English -> Vietnamese (needs raw-en.jsonl.gz, ~3 GB)
python3 extract_vi.py     # Vietnamese -> English

# 3. enrich English entries (CEFR level, frequency rank, fallback IPA, domain labels)
python3 enrich.py

# 3b. build specialist-domain word lists (needs kaikki-en/vi postprocessed dumps)
python3 extract_domains.py   # -> build/domains.json (Kinh tế / Kế toán)

# 4. pack sharded JSON for the static site
python3 pack.py           # writes site/data/
```

## Scripts

| script | input | output |
|---|---|---|
| `pdownload.py` | URL | parallel ranged download with resume |
| `extract_en.py` | `raw/raw-en.jsonl.gz` | `build/en_entries.jsonl`, `build/en_forms.jsonl` — only English records with ≥1 Vietnamese translation; VI translations are matched to senses via the `sense` label, unmatched go to `vi_other` |
| `extract_vi.py` | `raw/kaikki-vi.jsonl.gz` | `build/vi_entries.jsonl` — Vietnamese headwords with English glosses |
| `enrich.py` | `build/en_entries.jsonl` + CEFR/ECDICT CSVs + `build/domains.json` | adds `cefr`, `freq`, `dom`, fallback `uk` IPA, extra inflection forms |
| `extract_domains.py` | `raw/kaikki-en.jsonl.gz`, `raw/kaikki-vi.jsonl.gz` | `build/domains.json` — specialist domain lists (kte/ktoan × en/vi) from curated seeds + Wiktionary topic mining |
| `pack.py` | `build/*.jsonl` | `site/data/` — `meta.json`, `index-en.json`, `index-vi.json`, `forms.json`, `domains.json`, `shards/en|vi/*.json` |
| `test_site.py` | — | Playwright end-to-end test against a local server |

## Data licences

Dictionary data is **CC BY-SA 4.0** (ECDICT portions: MIT) — see the sources
table in `sources.toml` and the About page in the app for attribution.
