#!/usr/bin/env python3
"""End-to-end test of the OpenDict site in real Chromium."""
import sys
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

    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector(".stat b", timeout=20000)
    stats = page.inner_text(".stats")
    oknum = any(x in stats for x in ["16.728", "16,728", "16728"])
    check("home renders + stats", oknum, stats.replace("\n", " ")[:80])

    # search "beau" -> suggestions -> beautiful
    page.fill("#searchInput", "beau")
    page.wait_for_selector(".suggest-item", timeout=8000)
    sug = page.inner_text("#suggestBox")
    check("suggestions for 'beau'", "beautiful" in sug, sug[:60].replace("\n", " "))
    page.click(".suggest-item >> nth=0")
    page.wait_for_selector(".entry-word", timeout=8000)
    word = page.inner_text(".entry-word")
    body = page.inner_text("#view")
    check("EN entry beautiful", word == "beautiful" and "đẹp" in body and "/ˈbjuːtɪ.fəl/" in body,
          f"word={word} ipa={'/ˈbjuːtɪ.fəl/' in body} vi={'đẹp' in body}")

    # search "dep" -> diacritic-insensitive -> đẹp
    page.fill("#searchInput", "dep")
    page.wait_for_selector(".suggest-item", timeout=8000)
    sug = page.inner_text("#suggestBox")
    check("diacritic-insensitive 'dep'->'đẹp'", "đẹp" in sug, sug[:60].replace("\n", " "))
    # click the đẹp suggestion
    items = page.query_selector_all(".suggest-item")
    clicked = False
    for it in items:
        txt = it.inner_text().replace("\n", " ")
        if " đẹp" in txt or txt.startswith("đẹp"):
            it.click(); clicked = True; break
    if not clicked and items: items[0].click()
    page.wait_for_selector(".entry-word", timeout=8000)
    word = page.inner_text(".entry-word")
    body = page.inner_text("#view")
    check("VI entry đẹp", word == "đẹp" and "beautiful" in body, f"word={word}")

    # inflected form: more beautiful -> beautiful (mini-data safe)
    page.goto(BASE + "#/en/more%20beautiful", wait_until="networkidle")
    page.wait_for_selector(".entry-word", timeout=8000)
    word = page.inner_text(".entry-word")
    redir = "chuyển hướng" in page.inner_text("#view") or "redirected" in page.inner_text("#view")
    check("inflected form redirect", word == "beautiful" and redir, f"word={word} note={redir}")

    # about page
    page.goto(BASE + "#/about", wait_until="networkidle")
    body = page.inner_text("#view")
    nsrc = body.count("kaikki.org") + body.count("ECDICT") + body.count("CEFR-J") + body.count("Octanove")
    check("about sources table", nsrc >= 5, f"mentions={nsrc}")

    # theme + language toggle
    page.click("#themeToggle")
    th = page.eval_on_selector("html", "e => e.dataset.theme")
    check("theme toggle", th == "dark", f"theme={th}")
    page.click("#langToggle")
    ph = page.get_attribute("#searchInput", "placeholder")
    check("language toggle", ph.startswith("Look up"), f"ph={ph[:30]}")

    # not found
    page.goto(BASE + "#/notfound/xyzqwerty", wait_until="networkidle")
    body = page.inner_text("#view")
    check("not-found page", "xyzqwerty" in body and ("Không tìm thấy" in body or "Not found" in body), body[:60].replace("\n", " "))

    # favorites
    page.goto(BASE + "#/en/beautiful", wait_until="networkidle")
    page.wait_for_selector("#favBtn", timeout=8000)
    page.click("#favBtn")
    page.goto(BASE + "#/favorites", wait_until="networkidle")
    body = page.inner_text("#view")
    check("favorites", "beautiful" in body, body[:60].replace("\n", " "))

    # history
    page.goto(BASE + "#/history", wait_until="networkidle")
    body = page.inner_text("#view")
    check("history", "beautiful" in body, body[:60].replace("\n", " "))

    real_errors = [e for e in errors if "favicon" not in e.lower()]
    check("no console errors", not real_errors, "; ".join(real_errors[:3]))
    browser.close()

fails = [r for r in results if not r[1]]
print(f"\n{len(results)-len(fails)}/{len(results)} passed")
sys.exit(1 if fails else 0)
