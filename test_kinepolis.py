from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        channel="chrome",
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = browser.new_page()
    page.goto("https://kinepolis.be/fr/", wait_until="networkidle")
    page.wait_for_timeout(8000)
    
    data = page.evaluate("() => Drupal.settings.variables")
    browser.close()

# Sauvegarder en JSON pour inspecter
with open("kinepolis_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ Sauvegardé dans kinepolis_data.json")
print("Films:", len(data["current_movies"]["films"]))
print("Sessions:", len(data["current_movies"]["sessions"]))
print("Cinémas:", len(data["complexes"]))

# Afficher un exemple de cinéma
print("\n🎬 Exemple cinéma:")
print(json.dumps(data["complexes"][0], indent=2, ensure_ascii=False))