"""
spider.py — Scraper Jiji.ci : Mode & Vêtements en Côte d'Ivoire
ENSEA AS Data Science — Projet Web Scraping
Respect éthique : User-Agent identifié, délai >= 1s, max 500 items
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
import random
from datetime import datetime
from typing import Optional

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────
BASE_URL = "https://jiji.co.ci"

# Toutes les catégories mode visibles sur le site
SEARCH_URLS = [
    "https://jiji.co.ci/womens-fashion",     # Mode Femme
    "https://jiji.co.ci/mens-fashion",        # Mode Homme
    "https://jiji.co.ci/kids-fashion",        # Mode Bébé & Enfant
    "https://jiji.co.ci/fashion-and-beauty",  # Mode général
]

# Pour compatibilité avec le reste du code
SEARCH_URL = SEARCH_URLS[0]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "X-Scraper-Info": "ENSEA Educational Project - Web Scraping AS Data Science",
}

MIN_DELAY = 1.0   # secondes minimum entre requêtes (éthique)
MAX_DELAY = 2.5   # secondes maximum
MAX_ITEMS = 500   # limite éthique du projet
MAX_PAGES = 20    # sécurité : max de pages à parcourir


def get_page(url: str, retries: int = 3) -> Optional[BeautifulSoup]:
    """Récupère une page HTML avec gestion des erreurs et retry."""
    for attempt in range(retries):
        try:
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            time.sleep(delay)

            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            logger.info(f"Page récupérée : {url} (délai: {delay:.1f}s)")
            return BeautifulSoup(response.text, "html.parser")

        except requests.exceptions.HTTPError as e:
            logger.warning(f"Erreur HTTP {e.response.status_code} — tentative {attempt+1}/{retries}")
            if e.response.status_code == 429:
                time.sleep(10)  # Rate limit : attendre 10s
        except requests.exceptions.ConnectionError:
            logger.warning(f"Erreur connexion — tentative {attempt+1}/{retries}")
            time.sleep(5)
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout — tentative {attempt+1}/{retries}")

    logger.error(f"Impossible de récupérer la page après {retries} tentatives : {url}")
    return None


def parse_listing_page(soup: BeautifulSoup) -> list:
    """
    Extrait les annonces d'une page de listing Jiji.ci.
    Retourne une liste de dictionnaires (données brutes).
    """
    items = []

    # Sélecteur principal des cartes d'annonce sur Jiji.ci
    cards = soup.select("article.b-list-advert__item-wrapper, div.b-list-advert__item")

    if not cards:
        cards = soup.select("[class*='b-list-advert']")

    logger.info(f"{len(cards)} annonces trouvées sur cette page")

    for card in cards:
        try:
            item = extract_item_data(card)
            if item:
                items.append(item)
        except Exception as e:
            logger.debug(f"Erreur parsing d'une carte : {e}")
            continue

    return items


def extract_item_data(card) -> Optional[dict]:
    """Extrait les données d'une carte d'annonce individuelle."""

    # Titre de l'annonce
    title_el = (
        card.select_one("div.b-list-advert-base__item-title") or
        card.select_one("[class*='title']") or
        card.select_one("h3") or
        card.select_one("h2")
    )
    title = title_el.get_text(strip=True) if title_el else None

    # Prix
    price_el = (
        card.select_one("div.b-list-advert__price-box") or
        card.select_one("[class*='price']") or
        card.select_one("span.price")
    )
    price_raw = price_el.get_text(strip=True) if price_el else None

    # Localisation
    location_el = (
        card.select_one("span.b-list-advert__region__text") or
        card.select_one("[class*='region']") or
        card.select_one("[class*='location']")
    )
    location = location_el.get_text(strip=True) if location_el else None

    # Lien vers l'annonce
    link_el = card.select_one("a[href]")
    link = BASE_URL + link_el["href"] if link_el and link_el.get("href", "").startswith("/") else None

    # Image (URL)
    img_el = card.select_one("img[src]")
    image_url = img_el.get("src") or img_el.get("data-src") if img_el else None

    # ID unique extrait du lien
    item_id = None
    if link:
        parts = link.rstrip("/").split("--")
        if len(parts) > 1:
            item_id = parts[-1].split("?")[0]

    # Date de publication
    date_el = card.select_one("[class*='date'], time")
    published_at = date_el.get_text(strip=True) if date_el else None

    # Ignorer les cartes sans titre ni prix
    if not title and not price_raw:
        return None

    return {
        "item_id":      item_id,
        "title":        title,
        "price_raw":    price_raw,
        "location":     location,
        "link":         link,
        "image_url":    image_url,
        "published_at": published_at,
        "scraped_at":   datetime.utcnow().isoformat(),
        "category":     "mode",
        "source":       "jiji.co.ci",
    }


def get_next_page_url(soup: BeautifulSoup, current_page: int, base_url: str) -> Optional[str]:
    """Retourne l'URL de la page suivante, ou None si dernière page."""
    next_btn = soup.select_one("a[rel='next'], a.pagination-next, [class*='next-page']")
    if next_btn and next_btn.get("href"):
        href = next_btn["href"]
        return BASE_URL + href if href.startswith("/") else href

    # Fallback : construction manuelle de l'URL
    return f"{base_url}?page={current_page + 1}"


def scrape_jiji_mode(max_items: int = 500) -> list:
    """
    Scrape toutes les catégories mode de Jiji.ci.
    Parcourt plusieurs catégories ET plusieurs pages par catégorie.

    Args:
        max_items: Nombre maximum d'annonces (max éthique : 500)

    Returns:
        Liste de dictionnaires contenant les données brutes
    """
    max_items  = min(max_items, MAX_ITEMS)
    all_items  = []
    seen_links = set()  # Éviter les doublons inter-catégories

    logger.info(f"=== Démarrage scraping Jiji.ci/mode — Objectif: {max_items} items ===")
    logger.info(f"Catégories ciblées : {len(SEARCH_URLS)}")

    for base_url in SEARCH_URLS:
        if len(all_items) >= max_items:
            break

        logger.info(f"\n--- Catégorie : {base_url} ---")
        current_page = 1

        while len(all_items) < max_items and current_page <= MAX_PAGES:
            # Construction URL avec pagination
            url = base_url if current_page == 1 else f"{base_url}?page={current_page}"
            logger.info(f"Page {current_page} : {url}")

            soup = get_page(url)
            if not soup:
                logger.warning("Page irrécupérable, passage à la catégorie suivante")
                break

            page_items = parse_listing_page(soup)
            if not page_items:
                logger.info("Aucun item — fin de cette catégorie")
                break

            # Dédoublonner par lien entre catégories
            new_items = []
            for item in page_items:
                link = item.get("link")
                if link and link in seen_links:
                    continue
                if link:
                    seen_links.add(link)
                new_items.append(item)

            remaining = max_items - len(all_items)
            all_items.extend(new_items[:remaining])
            logger.info(f"Total collecté : {len(all_items)}/{max_items}")

            current_page += 1

    logger.info(f"=== Scraping terminé : {len(all_items)} annonces collectées ===")
    return all_items


def save_raw_data(items: list, filepath: str = "raw_data.json") -> None:
    """Sauvegarde les données brutes en JSON."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    logger.info(f"Données brutes sauvegardées : {filepath} ({len(items)} items)")


if __name__ == "__main__":
    items = scrape_jiji_mode(max_items=500)
    save_raw_data(items, "raw_data.json")
    print(f"\n✅ {len(items)} annonces collectées")
    if items:
        print(f"\nExemple d'item :\n{json.dumps(items[0], ensure_ascii=False, indent=2)}")