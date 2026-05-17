"""
Standalone script — DO NOT import directly.
Called as a subprocess by kinepolis_service.py to avoid asyncio conflicts
on Python 3.13 / Windows when Playwright runs inside a Django management command.

Outputs Drupal.settings.variables as JSON to stdout, or exits with code 1 on error.
"""
import json
import sys
import platform


def main():
    from playwright.sync_api import sync_playwright

    is_linux = platform.system() == "Linux"

    with sync_playwright() as p:
        if is_linux:
            # Prod / CI : headless obligatoire, pas de Chrome installé → Chromium system
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
        else:
            # Windows dev : headless=False requis (Cloudflare bloque headless)
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
