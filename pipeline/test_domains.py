#!/usr/bin/env python3
"""Test OpenDict specialist-domain features in real Chromium."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8902/"
results = []

def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS" if cond else "FAIL"), name, "-", detail)

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-proxy-server", "--no-sandbox"])
    page = browser.new_page()
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))

    # home: domain cards
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector(".dom-card", timeout=15000)
    cards = page.inner_text(".dom-cards")
    check("home domain cards", "Kinh tế" in cards and "Kế toán" in cards,
          cards.replace("\n", " ")[:100])

    # domain page kinh-te
    page.goto(BASE + "#/domain/kinh-te", wait_until="networkidle")
    page.wait_for_selector(".dom-chip", timeout=10000)
    body = page.inner_text("#view")
    check("domain kinh-te page", "inflation" in body and "lạm phát" not in body or "inflation" in body,
          f"chips={page.query_selector_all('.dom-chip').__len__()}")
    n_chips = len(page.query_selector_all(".dom-chip"))
    check("domain kinh-te chip count", n_chips > 150, f"n={n_chips}")

    # domain filter
    page.fill("#domFilter", "infla")
    page.wait_for_timeout(400)
    vis = page.eval_on_selector_all(".dom-chip",
        "els => els.filter(e => e.style.display !== 'none').length")
    check("domain filter", vis >= 1 and vis < n_chips, f"visible={vis}")

    # domain page ke-toan
    page.goto(BASE + "#/domain/ke-toan", wait_until="networkidle")
    page.wait_for_selector(".dom-chip", timeout=10000)
    body = page.inner_text("#view")
    check("domain ke-toan page", "kế toán" in body.lower() or "accounting" in body,
          body[:80].replace("\n", " "))

    # EN entry badge: inflation -> Kinh tế
    page.goto(BASE + "#/en/inflation", wait_until="networkidle")
    page.wait_for_selector(".entry-word", timeout=10000)
    body = page.inner_text("#view")
    check("EN badge inflation", "Kinh tế" in body, body[:120].replace("\n", " "))

    # EN entry badge: audit? not in list; use 'accounting' -> both badges
    page.goto(BASE + "#/en/foreign%20currency", wait_until="networkidle")
    page.wait_for_selector(".entry-word", timeout=10000)
    body = page.inner_text("#view")
    check("EN badges foreign currency", "Kinh tế" in body and "Kế toán" in body,
          body[:150].replace("\n", " "))

    # VI entry badge: lạm phát -> Kinh tế
    page.goto(BASE + "#/vi/l%E1%BA%A1m%20ph%C3%A1t", wait_until="networkidle")
    page.wait_for_selector(".entry-word", timeout=10000)
    body = page.inner_text("#view")
    check("VI badge lạm phát", "Kinh tế" in body, body[:120].replace("\n", " "))

    # badge link goes to domain page
    page.goto(BASE + "#/en/inflation", wait_until="networkidle")
    page.wait_for_selector(".dom-badge", timeout=10000)
    page.click(".dom-badge >> nth=0")
    page.wait_for_selector(".dom-chip", timeout=10000)
    check("badge link -> domain page", "kinh-te" in page.url, page.url)

    # about page mentions specialist dictionaries
    page.goto(BASE + "#/about", wait_until="networkidle")
    page.wait_for_selector(".about", timeout=10000)
    body = page.inner_text("#view")
    check("about specialist section", "chuyên ngành" in body.lower(), body[:60].replace("\n", " "))

    check("no console errors", not errors, "; ".join(errors[:3]))
    browser.close()

n = sum(1 for _, ok, _ in results if ok)
print(f"\n{n}/{len(results)} passed")
raise SystemExit(0 if n == len(results) else 1)
