"""
Standalone script — DO NOT import directly.
Called as a subprocess by kinepolis_service.py to avoid asyncio conflicts
on Python 3.13 / Windows when Playwright runs inside a Django management command.

Outputs Drupal.settings.variables as JSON to stdout, or exits with code 1 on error.
"""
import json
import sys


def main():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            page = browser.new_page()
            page.goto("https://kinepolis.be/fr/", wait_until="networkidle")
            page.wait_for_timeout(8000)
            data = page.evaluate("() => Drupal.settings.variables")
        finally:
            browser.close()

    sys.stdout.buffer.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"SCRAPER_ERROR: {e}", file=sys.stderr)
        sys.exit(1)
