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


def _get_drupal_data(page):
    """Attend que Drupal.settings.variables soit défini (max 90s) puis le retourne."""
    page.wait_for_function(
        "() => typeof Drupal !== 'undefined' && Drupal.settings && Drupal.settings.variables",
        timeout=90000,
    )
    return page.evaluate("() => Drupal.settings.variables")


def main():
    from playwright.sync_api import sync_playwright

    is_linux = platform.system() == "Linux"
    today = date.today()
    dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

    with sync_playwright() as p:
        if is_linux:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled",
                    "--window-size=1920,1080",
                    "--lang=fr-BE",
                ],
            )
        else:
            browser = p.chromium.launch(
                headless=False,
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"],
            )

        try:
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="fr-BE",
                timezone_id="Europe/Brussels",
                extra_http_headers={
                    "Accept-Language": "fr-BE,fr;q=0.9,en;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                },
            )

            page = context.new_page()

            # playwright-stealth : masque toutes les traces d'automatisation
            try:
                from playwright_stealth import stealth_sync
                stealth_sync(page)
            except ImportError:
                # Fallback manuel si playwright-stealth indisponible
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
                    Object.defineProperty(navigator, 'languages', { get: () => ['fr-BE', 'fr', 'en'] });
                    window.chrome = { runtime: {} };
                """)

            # Jour 0 : chargement initial — wait_until="load" pour laisser le challenge CF se résoudre
            page.goto("https://kinepolis.be/fr/", wait_until="load", timeout=90000)
            base_data = _get_drupal_data(page)

            all_sessions = {"current_movies": [], "future_movies": []}
            for section in ("current_movies", "future_movies"):
                all_sessions[section].extend(
                    base_data.get(section, {}).get("sessions", [])
                )

            # Jours 1-6 : même contexte (cookies Cloudflare déjà obtenus)
            for date_str in dates[1:]:
                try:
                    page.goto(
                        f"https://kinepolis.be/fr/?date={date_str}",
                        wait_until="load",
                        timeout=30000,
                    )
                    day_data = _get_drupal_data(page)
                    for section in ("current_movies", "future_movies"):
                        all_sessions[section].extend(
                            day_data.get(section, {}).get("sessions", [])
                        )
                except Exception as e:
                    print(f"[scraper] {date_str} skipped: {e}", file=sys.stderr)

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
