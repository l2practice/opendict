#!/usr/bin/env python3
"""Scan kaikki-en postprocessed data: collect all topics, and check which
business/accounting seed terms have Vietnamese translations.
Writes build/topic_stats.json and prints coverage report."""
import gzip, json
from collections import Counter

SEEDS = """audit accounting depreciation asset liability equity revenue expense
profit loss balance sheet income statement cash flow invoice merger acquisition
dividend shareholder stakeholder bankruptcy insolvency liquidity solvency
capital interest loan mortgage credit debit amortization fiscal budget deficit
surplus inflation deflation gdp tariff quota subsidy franchise payroll ledger
journal voucher accrual depreciation amortization goodwill trademark patent
economy market trade commerce finance banking insurance tax tariff
entrepreneur startup venture capital stock bond securities portfolio
overhead margin markup discount wholesale retail supply demand monopoly
oligopoly inflation recession depression gdp fiscal monetary exchange rate
forex payroll recruitment outsourcing logistics procurement inventory""".split()

topics = Counter()
word_topics = {}
seed_hits = {}
n = 0
with gzip.open("raw/kaikki-en.jsonl.gz", "rt", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r.get("lang_code") != "en":
            continue
        n += 1
        ts = set()
        for s in r.get("senses", []):
            for t in s.get("topics", []) or []:
                topics[t] += 1
                ts.add(t)
        w = r["word"].lower()
        if ts:
            word_topics.setdefault(w, set()).update(ts)
        if w in SEEDS:
            trs = r.get("translations") or []
            if any(t.get("lang_code") == "vi" for t in trs):
                seed_hits[w] = True
        if n % 400000 == 0:
            print(f"  {n}...", flush=True)

print("records:", n)
biz = {t: c for t, c in topics.items()
       if any(k in t for k in ("business", "econom", "financ", "account", "bank", "tax", "insur", "trade", "commerc", "money", "invest", "market"))}
print("business-ish topics:", sorted(biz.items(), key=lambda x: -x[1])[:40])
print(f"seed coverage: {len(seed_hits)}/{len(SEEDS)}")
missing = [s for s in SEEDS if s not in seed_hits]
print("missing seeds:", missing[:40])
json.dump({"topics": dict(topics), "word_topics": {w: sorted(ts) for w, ts in word_topics.items() if any(
    any(k in t for k in ("business", "econom", "financ", "account", "bank", "tax", "insur", "trade", "commerc", "invest")) for t in ts)}},
    open("build/topic_stats.json", "w", encoding="utf-8"), ensure_ascii=False)
print("wrote build/topic_stats.json")
