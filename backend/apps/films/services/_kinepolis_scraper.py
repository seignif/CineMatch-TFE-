"""
Standalone script — DO NOT import directly.
Called as a subprocess by kinepolis_service.py to avoid asyncio conflicts
on Python 3.13 / Windows when Playwright runs inside a Django management command.

Scrapes séances for today + the next 6 days (7 days total).
Outputs merged Drupal.settings.variables as JSON to stdout, or exits with code 1 on error.
"""
import json
import sys
import platform
from datetime import date, timedelta


def main():
    from playwright.sync_api import sync_playwright

    is_linux = platform.system() == "Linux"
    today = date.today()
    # Scrape today + next 6 days
    dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

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

            # Jour 0 : chargement initial avec attente Cloudflare longue
            page.goto("https://kinepolis.be/fr/", wait_until="networkidle")
            page.wait_for_timeout(8000)
            base_data = page.evaluate("() => Drupal.settings.variables")

            # Collecter les sessions du jour 0
            all_sessions = {"current_movies": [], "future_movies": []}
            for section in ("current_movies", "future_movies"):
                all_sessions[section].extend(
                    base_data.get(section, {}).get("sessions", [])
                )

            # Jours 1-6 : navigation dans la même session (Cloudflare déjà passé)
            for date_str in dates[1:]:
                try:
                    page.goto(
                        f"https://kinepolis.be/fr/?date={date_str}",
                        wait_until="networkidle",
                    )
                    page.wait_for_timeout(4000)
                    day_data = page.evaluate("() => Drupal.settings.variables")
                    for section in ("current_movies", "future_movies"):
                        all_sessions[section].extend(
                            day_data.get(section, {}).get("sessions", [])
                        )
                except Exception as e:
                    print(f"[scraper] {date_str} skipped: {e}", file=sys.stderr)

            # Fusionner les sessions dans base_data
            for section in ("current_movies", "future_movies"):
                if section in base_data:
                    base_data[section]["sessions"] = all_sessions[section]

        finally:
            browser.close()

    sys.stdout.buffer.write(json.dumps(base_data, ensure_ascii=False).encode('utf-8'))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"SCRAPER_ERROR: {e}", file=sys.stderr)
        sys.exit(1)
