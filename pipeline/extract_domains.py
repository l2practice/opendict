#!/usr/bin/env python3
"""Build specialist-domain word lists for OpenDict (Kinh tế & Kế toán).

Strategy (documented, re-runnable):
  1. Curated seed lists of genuine economics/business & accounting terms
     (one term per line), intersected with words actually present in the
     built dictionary. No translations are invented: a term is included
     only if the open data already provides a Vietnamese translation.
  2. Topic mining over English Wiktionary (Wiktextract/kaikki, CC BY-SA 4.0)
     with TIGHT topics only (economics/finance/accounting/… — the generic
     'business' topic is far too loose in Wiktionary: it tags weapons,
     clothing, farm machines…). A lowercase word is tagged when >=2 of its
     senses (all POS records) carry a domain topic, >=1 for multiword terms.
  3. A small manual denylist removes leftovers.

Input : build/en_entries.jsonl, build/vi_entries.jsonl,
        raw/kaikki-en.jsonl.gz, raw/kaikki-vi.jsonl.gz
Output: build/domains.json
        {"kte":   {"en": [words], "vi": [words]},
         "ktoan": {"en": [words], "vi": [words]}}
"""
import gzip, json, sys
from collections import Counter

# tight topics only — 'business'/'commerce'/'marketing' are too loose in Wiktionary
KTE_TOPICS = {
    "economics", "microeconomics", "finance", "financial", "banking",
    "insurance", "taxation", "stock-market", "money", "investment",
}
KTOAN_TOPICS = {"accounting", "finance", "financial", "banking", "taxation", "insurance"}

KTE_SEEDS = """inflation
deflation
stagflation
recession
depression
gross domestic product
fiscal policy
monetary policy
exchange rate
interest rate
unemployment
trade deficit
balance of payments
purchasing power parity
supply and demand
monopoly
oligopoly
perfect competition
market economy
emerging market
privatization
deregulation
subsidy
tariff
free trade
protectionism
globalization
outsourcing
supply chain
logistics
procurement
inventory
wholesale
retail
e-commerce
startup
entrepreneur
venture capital
angel investor
initial public offering
joint venture
franchise
conglomerate
cartel
embargo
quota
consumer price index
business cycle
economic growth
aggregate demand
fiscal deficit
public debt
sovereign debt
currency devaluation
forex
foreign exchange
foreign direct investment
stock market
bond market
capital market
money market
securities
portfolio
dividend yield
market capitalization
bull market
bear market
branding
advertising
market share
market research
human resources
labor market
minimum wage
microeconomics
macroeconomics
econometrics
game theory
comparative advantage
economies of scale
diminishing returns
opportunity cost
sunk cost
marginal cost
fixed cost
variable cost
break-even
elasticity
dumping
price discrimination
central bank
money supply
hyperinflation
liquidity trap
quantitative easing
austerity
stimulus package
bailout
trade war
sanctions
trade barrier
value chain
vertical integration
diversification
merger
acquisition
takeover
leveraged buyout
corporate governance
shareholder
stakeholder
board of directors
chief executive officer
chief financial officer
annual report
blue chip
preferred stock
common stock
treasury stock
stock split
dividend
stock buyback
fintech
sharing economy
gig economy
circular economy
green economy
digital economy
knowledge economy
trade agreement
world trade organization
international monetary fund
world bank
purchasing power
national income
disposable income
per capita
business model
network effect
competitive advantage
swot analysis
market segmentation
target market
supply shock
demand shock
inflation targeting
core inflation
wage-price spiral
cost-push inflation
demand-pull inflation
structural unemployment
frictional unemployment
cyclical unemployment
underemployment
gini coefficient
income inequality
human development index
consumer confidence
yield curve
risk premium
default risk
systemic risk
moral hazard
adverse selection
information asymmetry
hostile takeover
poison pill
golden parachute
spin-off
divestiture
asset sale
joint-stock company
limited liability company
partnership
sole proprietorship
cooperative
multinational corporation
small and medium enterprise
incubator
mezzanine financing
bridge loan
convertible note
underwriter
market maker
broker
dealer
investment bank
commercial bank
retail bank
credit union
microfinance
credit score
credit rating
rating agency
collateralized debt obligation
mortgage-backed security
credit default swap
interest rate swap
hedge fund
mutual fund
index fund
exchange-traded fund
pension fund
sovereign wealth fund
private equity
real estate investment trust
derivatives
call option
put option
strike price
option premium
short selling
margin trading
leverage
margin call
arbitrage
high-frequency trading
market order
limit order
stop-loss
bid-ask spread
technical analysis
fundamental analysis
efficient market hypothesis
behavioral finance
loss aversion
discounted cash flow
net present value
internal rate of return
payback period
cost of capital
weighted average cost of capital
capital asset pricing model
beta
alpha
sharpe ratio
modern portfolio theory
efficient frontier
diversification
value investing
growth investing
momentum investing
dollar-cost averaging
buy and hold
emerging markets
housing bubble
subprime mortgage
foreclosure
commercial real estate
commodity
contango
backwardation
spot price
currency pair
carry trade
currency hedging
trade finance
letter of credit
bill of lading
factoring
export
import
incoterms
customs duty
excise tax
value-added tax
goods and services tax
sales tax
tax haven
tax avoidance
tax evasion
transfer pricing
double taxation
tax treaty
withholding tax
payroll tax
property tax
capital gains tax
inheritance tax
carbon tax
antitrust
competition law
intellectual property
patent
trademark
copyright
trade secret
licensing
royalty
research and development
innovation
productivity
offshoring
reshoring
lean manufacturing
six sigma
total quality management
third-party logistics
last-mile delivery
vendor management
safety stock
warehousing
fulfillment
dropshipping
omnichannel
point of sale
consumer behavior
brand equity
brand loyalty
customer lifetime value
churn rate
customer acquisition cost
conversion rate
search engine optimization
content marketing
social media marketing
influencer marketing
email marketing
affiliate marketing
market penetration
porter five forces
core competency
blue ocean strategy
disruptive innovation
economies of scope
labor union
collective bargaining
strike
freelancer
remote work
corporate social responsibility
sustainability
stakeholder capitalism
impact investing
green bond
carbon credit
cap and trade
net zero""".split("\n")

KTOAN_SEEDS = """accounting
audit
auditing
bookkeeping
ledger
general ledger
journal
balance sheet
income statement
cash flow statement
trial balance
chart of accounts
asset
liability
equity
revenue
expense
profit
loss
depreciation
amortization
accrual
goodwill
intangible asset
tangible asset
fixed asset
current asset
current liability
long-term liability
contingent liability
accounts payable
accounts receivable
notes payable
payroll
invoice
receipt
voucher
debit
credit
double-entry bookkeeping
fiscal year
accounting period
accrual basis
cash basis
income tax
corporate tax
vat
deduction
tax credit
deferred tax
write-off
write down
bad debt
allowance for doubtful accounts
provision
retained earnings
shareholders' equity
paid-in capital
dividends
working capital
current ratio
quick ratio
return on equity
return on assets
cost of goods sold
gross profit
net profit
operating profit
ebit
ebitda
operating income
net income
cash flow
operating cash flow
free cash flow
liquidity
solvency
bankruptcy
insolvency
going concern
audit report
auditor
internal audit
external audit
forensic audit
financial statement
disclosure
consolidation
subsidiary
parent company
adjusting entry
closing entry
prepaid expense
accrued expense
unearned revenue
deferred revenue
accumulated depreciation
depreciation expense
straight-line
declining balance
impairment
fifo
lifo
weighted average
conservatism
matching principle
revenue recognition
historical cost
fair value
mark to market
materiality
gaap
ifrs
internal control
segregation of duties
fraud
embezzlement
tax audit
tax return
tax planning
capital expenditure
operating expenditure
capex
opex
budget
budgeting
variance
zero-based budgeting
forecast
financial modeling
sensitivity analysis
cost accounting
managerial accounting
financial accounting
activity-based costing
standard costing
break-even analysis
contribution margin
margin of safety
operating leverage
relevant cost
capital budgeting
cost center
profit center
responsibility accounting
balanced scorecard
benchmarking
inventory turnover
days sales outstanding
cash conversion cycle
ratio analysis
liquidity ratio
profitability ratio
leverage ratio
earnings per share
price-earnings ratio
book value
statement of changes in equity
statement of retained earnings
other comprehensive income
business combination
bargain purchase
operating lease
finance lease
right-of-use asset
performance obligation
provisions
pension
defined benefit
stock compensation
share-based payment
earnings management
creative accounting
related party transaction
unqualified opinion
qualified opinion
adverse opinion
certified public accountant
big four
accounting software
erp
purchase order
sales order
credit memo
debit memo
petty cash
cash equivalent
bank reconciliation
outstanding check
wire transfer
treasury management
credit policy
aging schedule
present value
future value
annuity
time value of money
net working capital
financial leverage
combined leverage
cost-volume-profit
flexible budget
static budget
master budget
cash budget
capital budget
economic value added
residual income
return on investment
just-in-time
target costing
life-cycle costing
quality cost
sustainability reporting
integrated reporting
forensic accounting
fraud triangle
audit risk
inherent risk
control risk
detection risk
substantive procedure
test of controls
audit evidence
professional skepticism
independence
engagement letter
management representation letter
key audit matters
continuous auditing
conceptual framework
faithful representation
comparability
verifiability
elements of financial statements
amortized cost
expected credit loss
lease liability
sale and leaseback
construction contract
percentage of completion
government grant
valuation allowance
uncertain tax position
pushdown accounting
segment reporting
interim reporting
discontinued operations
held for sale
basic eps
diluted eps
deferred compensation
treasury stock method
stock dividend
reverse stock split
noncontrolling interest
variable interest entity
hedge accounting
cash flow hedge
fair value hedge
embedded derivative
financial instruments""".split("\n")

# generic words Wiktionary loosely tags with finance topics; never list them
DENY = {
    "a", "and", "of", "the", "to", "in", "able", "add", "age", "aim", "american",
    "app", "ar", "at", "barn", "base", "beanie", "beat", "beg", "bet", "big",
    "bizarre", "black", "boast", "bone", "boss", "box", "brake", "buffer",
    "bullet", "button", "calico", "cannon", "catastrophe", "cd", "chat", "chew",
    "clause", "coffin", "collar", "compound", "cope", "creel", "cushion",
    "digital", "disk", "down", "drip", "dust", "ether", "far", "fire", "fit",
    "flap", "fork", "fresh", "give", "green", "hat", "holiday", "juice", "kite",
    "lift", "long", "mast", "meltdown", "microcontroller", "name", "nearby",
    "ninja", "old", "parachute", "parking", "pinch", "pipe", "pip", "play",
    "plug", "plum", "potentiometer", "put", "quantum", "quarry", "rack", "ram",
    "random", "reheat", "rest", "rig", "rigid", "rod", "rom", "round", "row",
    "run", "shark", "sickle", "sister", "slug", "smurf", "snake", "sock",
    "socket", "spaceship", "speed", "spur", "stab", "stir", "stool", "strip",
    "stubble", "sunrise", "sunset", "swift", "thimble", "top", "torch", "tower",
    "tractor", "tram", "transformer", "trouble", "turboprop", "up", "upside",
    "velocity", "vest", "visa", "visit", "volga", "volunteer", "walk", "wash",
    "weak", "wise", "woof", "wring", "yard", "yem", "actual", "balloon",
    "battle", "bed", "bomber", "brain", "breast", "brick", "broadcast",
    "broadcaster", "bulletproof vest", "butt", "cage", "canard", "cathode",
    "cathode ray", "cathode ray tube", "cave", "chew the cud", "chip",
    "circuit board", "coffee", "comb", "combine harvester", "copper", "cotton",
    "couch", "crab", "cradle", "dance", "dead end", "dish", "dive bomber",
    "dock", "documentary", "doff", "drain", "drawer", "dress", "drive", "dry",
    "dump", "electric field", "electric potential", "engine", "error", "escape",
    "everlasting", "face", "family tree", "fang", "feather", "first", "five",
    "flat", "float", "floor", "flush", "fly", "frame", "fret", "fuse", "game",
    "gas", "gate", "gather", "gift", "gig", "give up", "grid", "guerrilla",
    "haircut", "hammer", "hard", "head", "headline", "heart", "heavy", "herd",
    "horizontal", "human", "series",
}

# final precision prune: generic headwords that merely *have* a finance sense
PRUNE_KTE_EN = {
    "break", "call", "carry", "cent", "chain", "corner", "green card",
    "in the red", "issue", "journal", "ledger", "liquid", "miner", "output",
    "panic buying", "position", "print", "rally", "real", "realize", "risk",
    "roll", "round trip", "security", "short", "speed bump", "split",
    "strike", "upside down", "water",
}
PRUNE_KTOAN_EN = {
    "backwardation", "basis", "bear", "break", "bull", "call", "carry", "cent",
    "corner", "foreign direct investment", "foreign trade", "green card",
    "in the red", "independence", "issue", "liquid", "miner", "panic buying",
    "position", "print", "rally", "realize", "risk", "round trip", "security",
    "short", "speed bump", "split", "strike", "unicorn", "upside down", "water",
}
PRUNE_VI = {"bạt", "bắt kịp", "tiền bo", "tiền nước", "ví tiền", "trường quốc tế",
            "ngách", "gửi", "tiền", "dịch vụ", "ngành", "供"}

def load_index_words(path):
    words = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            words.add(json.loads(line)["w"].lower())
    return words

def mine_topics(kaikki_path, lang_code, in_dict, topics,
               min_senses_single=2, min_senses_multi=1):
    """words with >=N senses carrying one of `topics` (lowercase records only)."""
    counts = Counter()
    with gzip.open(kaikki_path, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("lang_code") != lang_code:
                continue
            w = r["word"]
            if w != w.lower():
                continue  # drop Proper nouns / ALLCAPS initialisms
            wl = w.lower()
            if wl not in in_dict:
                continue
            n = sum(1 for s in r.get("senses", [])
                    if set(s.get("topics") or []) & topics)
            if n:
                counts[wl] += n
    return {w for w, n in counts.items()
            if n >= (min_senses_multi if " " in w else min_senses_single)}

def main():
    en_words = load_index_words("build/en_entries.jsonl")
    vi_words = load_index_words("build/vi_entries.jsonl")

    kte = (({s.strip().lower() for s in KTE_SEEDS if s.strip()}
            | mine_topics("raw/kaikki-en.jsonl.gz", "en", en_words, KTE_TOPICS))
           & en_words) - DENY
    ktoan = (({s.strip().lower() for s in KTOAN_SEEDS if s.strip()}
              | mine_topics("raw/kaikki-en.jsonl.gz", "en", en_words, KTOAN_TOPICS))
             & en_words) - DENY

    kte_vi = mine_topics("raw/kaikki-vi.jsonl.gz", "vi", vi_words, KTE_TOPICS,
                         min_senses_single=1) - PRUNE_VI
    ktoan_vi = mine_topics("raw/kaikki-vi.jsonl.gz", "vi", vi_words, KTOAN_TOPICS,
                           min_senses_single=1) - PRUNE_VI
    kte -= PRUNE_KTE_EN
    ktoan -= PRUNE_KTOAN_EN

    domains = {
        "kte": {"en": sorted(kte), "vi": sorted(kte_vi)},
        "ktoan": {"en": sorted(ktoan), "vi": sorted(ktoan_vi)},
    }
    with open("build/domains.json", "w", encoding="utf-8") as f:
        json.dump(domains, f, ensure_ascii=False, separators=(",", ":"))
    print(f"kte: en={len(kte)} vi={len(kte_vi)} | ktoan: en={len(ktoan)} vi={len(ktoan_vi)}",
          file=sys.stderr)
    with open("build/domains_review.txt", "w", encoding="utf-8") as f:
        for d in ("kte", "ktoan"):
            f.write(f"=== {d} EN ({len(domains[d]['en'])}) ===\n")
            f.write(", ".join(domains[d]["en"]) + "\n\n")
            f.write(f"=== {d} VI ({len(domains[d]['vi'])}) ===\n")
            f.write(", ".join(domains[d]["vi"]) + "\n\n")
    print("review: build/domains_review.txt", file=sys.stderr)

if __name__ == "__main__":
    main()
