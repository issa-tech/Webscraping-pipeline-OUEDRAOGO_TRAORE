"""
spider.py — Scraper Jiji.ci — Mode en Côte d'Ivoire
ENSEA AS Data Science — Projet Web Scraping
S�lecteur corrigé : a.qa-advert-list-item
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
import time
import random
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_URL  = "https://jiji.co.ci"
MAX_PAGES = 10
MAX_ITEMS = 500

SEARCH_URLS = [
    ("https://jiji.co.ci/womens-fashion",     "femme"),
    ("https://jiji.co.ci/mens-fashion",       "homme"),
    ("https://jiji.co.ci/fashion-and-beauty", "general"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "X-Scraper-Info": "ENSEA Educational Project - Web Scraping AS Data Science",
}

FEMME_KW  = ['femme','féminin','feminin','lady','robe','jupe','soutien','lingerie',
             'bijou','collier','bague','boucle','vernis','blouse','tunique',
             'maquillage','makeup','parfum','beauté','beaute','tailleur',
             'ensemble femme','escarpin','talon','corset','bustier','legging']
HOMME_KW  = ['homme','masculin','monsieur','costume','veste','chemise','cravate',
             'complet','mocassin','derby','smoking','blazer','boubou homme',
             'ensemble homme','pantalon homme','polo','jeans homme']
ENFANT_KW = ['enfant','bébé','bebe','fille','garçon','garcon','kid','junior',
             'école','ecole','nourrisson','petite fille','petit garçon','layette']


def classify_gender(title: str, link: str, source_gender: str) -> str:
    lk = (link or '').lower()
    if 'womens-fashion' in lk: return 'femme'
    if 'mens-fashion'   in lk: return 'homme'
    if 'kids-fashion'   in lk: return 'enfant'
    text = ((title or '') + ' ' + lk).lower()
    for kw in FEMME_KW:
        if kw in text: return 'femme'
    for kw in HOMME_KW:
        if kw in text: return 'homme'
    for kw in ENFANT_KW:
        if kw in text: return 'enfant'
    return source_gender


def get_page(url: str, retries: int = 3) -> BeautifulSoup | None:
    for attempt in range(1, retries + 1):
        try:
            delay = random.uniform(1.0, 2.5)
            time.sleep(delay)
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                logger.info(f"Page récupérée : {url} (délai: {delay:.1f}s)")
                return BeautifulSoup(response.text, "lxml")
            else:
                logger.warning(f"Erreur HTTP {response.status_code} — tentative {attempt}/{retries}")
        except Exception as e:
            logger.warning(f"Exception tentative {attempt}/{retries} : {e}")
    logger.error(f"Impossible de récupérer la page après {retries} tentatives : {url}")
    return None


def extract_item_data(tag, source_gender: str) -> dict | None:
    try:
        href = tag.get("href", "")
        link = (BASE_URL + href) if href.startswith("/") else href

        title_el = (
            tag.select_one(".b-advert-title-inner")
            or tag.select_one("[class*='title']")
            or tag.select_one("p")
        )
        title = title_el.get_text(strip=True) if title_el else None

        price_el = (
            tag.select_one(".qa-advert-price")
            or tag.select_one("[class*='price']")
        )
        price_raw = price_el.get_text(strip=True) if price_el else None

        loc_el = (
            tag.select_one(".b-list-advert__region__text")
            or tag.select_one("[class*='region']")
            or tag.select_one("[class*='location']")
        )
        location = loc_el.get_text(strip=True) if loc_el else None

        img_el = tag.select_one("img[src], img[data-src]")
        image_url = None
        if img_el:
            src = img_el.get("src") or img_el.get("data-src") or ""
            if src and not src.startswith("data:"):
                image_url = src

        gender = classify_gender(title, link, source_gender)

        return {
            "item_id":         None,
            "title":           title,
            "price_raw":       price_raw,
            "location":        location,
            "link":            link,
            "image_url":       image_url,
            "published_at":    None,
            "scraped_at":      datetime.now().isoformat(),
            "category":        "mode",
            "gender_category": gender,
            "source":          "jiji.co.ci",
        }
    except Exception as e:
        logger.debug(f"Erreur extraction item : {e}")
        return None


def parse_listing_page(soup: BeautifulSoup, source_gender: str) -> list[dict]:
    # Sélecteur principal mis à jour
    tags = soup.select("a.qa-advert-list-item")
    if not tags:
        tags = soup.select("a[class*='b-list-advert-base']")
    if not tags:
        tags = soup.select("a[class*='advert']")
    if not tags:
        tags = [a for a in soup.find_all("a", href=True)
                if a.get("href","").startswith("/") and a.get("href","").count("/") >= 3]

    items = []
    for tag in tags:
        item = extract_item_data(tag, source_gender)
        if item and item.get("title"):
            items.append(item)

    logger.info(f"{len(items)} annonces trouvées sur cette page")
    return items


def scrape_jiji_mode(max_items: int = 500) -> list[dict]:
    max_items = min(max_items, MAX_ITEMS)
    all_items = []
    seen_links = set()

    logger.info(f"=== Démarrage scraping Jiji.ci/mode — Objectif: {max_items} items ===")
    logger.info(f"Catégories ciblées : {len(SEARCH_URLS)}")

    for base_url, source_gender in SEARCH_URLS:
        if len(all_items) >= max_items:
            break

        logger.info(f"\n--- Catégorie : {base_url} (genre: {source_gender}) ---")
        current_page = 1

        while len(all_items) < max_items and current_page <= MAX_PAGES:
            url = base_url if current_page == 1 else f"{base_url}?page={current_page}"
            logger.info(f"Page {current_page} : {url}")

            soup = get_page(url)
            if not soup:
                logger.warning("Page irrécupérable, passage à la catégorie suivante")
                break

            page_items = parse_listing_page(soup, source_gender)
            if not page_items:
                logger.info("Aucun item — fin de cette catégorie")
                break

            new_items = []
            for item in page_items:
                lnk = item.get("link")
                if lnk and lnk in seen_links:
                    continue
                if lnk:
                    seen_links.add(lnk)
                new_items.append(item)

            remaining = max_items - len(all_items)
            all_items.extend(new_items[:remaining])
            logger.info(f"Total collecté : {len(all_items)}/{max_items}")

            current_page += 1

    logger.info(f"=== Scraping terminé : {len(all_items)} annonces collectées ===")
    return all_items


if __name__ == "__main__":
    items = scrape_jiji_mode(max_items=500)

    output_file = "raw_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    logger.info(f"Données brutes sauvegardées : {output_file} ({len(items)} items)")
    print(f"\n✅ {len(items)} annonces collectées")

    from collections import Counter
    genres = Counter(item.get("gender_category", "?") for item in items)
    print("Répartition par genre :")
    for genre, count in sorted(genres.items()):
        print(f"  {genre}: {count}")

    if items:
        print("\nExemple d'item :")
        print(json.dumps(items[0], ensure_ascii=False, indent=2))