"""
debug_spider.py — Diagnostic de la structure HTML de Jiji.ci
Lance ce script et colle le résultat dans le chat.
"""
import requests
from bs4 import BeautifulSoup
import time, random

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

URL = "https://jiji.co.ci/fashion-and-beauty"

print(f"Fetching: {URL}")
time.sleep(random.uniform(1, 2))
resp = requests.get(URL, headers=HEADERS, timeout=20)
print(f"Status: {resp.status_code}")

soup = BeautifulSoup(resp.text, "lxml")

# Test tous les sélecteurs possibles
selectors = [
    "article.b-list-advert__item-wrapper",
    "article[class*='advert']",
    "div.b-list-advert__item",
    "li[class*='advert']",
    "[class*='advert-list'] article",
    "article",
    "div[class*='masonry'] div",
    "div[class*='list'] article",
    "[data-qa='advert']",
    "[class*='QaAdvert']",
    "div[class*='b-advert']",
    "a[class*='advert']",
]

print("\n=== TEST SELECTEURS ===")
for sel in selectors:
    found = soup.select(sel)
    print(f"  {sel!r:50s} → {len(found)} éléments")

# Afficher les 10 premiers tags du body
print("\n=== PREMIERS TAGS DU BODY ===")
body = soup.body
if body:
    tags = [c for c in body.children if hasattr(c, 'name') and c.name]
    for tag in tags[:10]:
        cls = tag.get('class', [])
        print(f"  <{tag.name} class='{' '.join(cls) if cls else ''}'>")

# Chercher les balises article
print("\n=== BALISES ARTICLE ===")
articles = soup.find_all("article")
print(f"  Total articles: {len(articles)}")
if articles:
    a = articles[0]
    print(f"  Premier article classes: {a.get('class')}")
    for child in list(a.children)[:5]:
        if hasattr(child, 'name') and child.name:
            print(f"    <{child.name} class='{child.get('class')}'>")

# Chercher les liens d'annonces (souvent les meilleurs indicateurs)
print("\n=== LIENS QUI RESSEMBLENT A DES ANNONCES ===")
links = soup.find_all("a", href=True)
annonce_links = [l for l in links if l.get("href","").count("/") >= 2 and "jiji" not in l.get("href","")]
print(f"  Liens internes trouvés: {len(annonce_links)}")
if annonce_links:
    for l in annonce_links[:3]:
        print(f"  href={l['href']!r} class={l.get('class')}")

# Afficher un extrait du HTML brut
print("\n=== EXTRAIT HTML (premiers 1500 chars du body) ===")
if body:
    print(str(body)[:1500])
