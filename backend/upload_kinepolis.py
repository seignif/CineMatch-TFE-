"""
Script standalone : scrape Kinepolis localement puis uploade les données vers Railway.
Usage : python upload_kinepolis.py <JWT_TOKEN>
"""
import json
import sys
import subprocess
import os

RAILWAY_URL = "https://cinematch-tfe-production.up.railway.app/api/admin/sync-kinepolis-data/"
SCRAPER = os.path.join(os.path.dirname(__file__), "apps", "films", "services", "_kinepolis_scraper.py")

def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_kinepolis.py <JWT_TOKEN>")
        sys.exit(1)

    token = sys.argv[1]

    print("1. Scraping Kinepolis.be (headless=False)...")
    result = subprocess.run(
        [sys.executable, SCRAPER],
        capture_output=True,
        timeout=300,
    )
    if result.returncode != 0:
        print(f"ERREUR scraper:\n{result.stderr.decode('utf-8', errors='replace')}")
        sys.exit(1)

    data = json.loads(result.stdout.decode('utf-8'))
    films_count = len(data.get('current_movies', {}).get('films', []))
    sessions_count = len(data.get('current_movies', {}).get('sessions', []))
    print(f"   -> {films_count} films, {sessions_count} séances scrapés")

    print("2. Upload vers Railway...")
    import urllib.request
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        RAILWAY_URL,
        data=body,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"   -> {resp.read().decode()}")
            print("3. Sync lancé sur Railway (tourne en arrière-plan ~2 min).")
    except Exception as e:
        print(f"ERREUR upload: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
