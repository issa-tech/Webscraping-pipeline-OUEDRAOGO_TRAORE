"""
tests/test_scraper.py — Tests unitaires (Jalon 1 → Niveau Or)
ENSEA AS Data Science
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scraper.spider import extract_item_data, parse_listing_page, get_page
from scraper.cleaner import clean_price, clean_location, clean_title, clean_data, extract_category_detail


# ─────────────────────────────────────────────────────────────────────────────
# TESTS CLEANER
# ─────────────────────────────────────────────────────────────────────────────

class TestCleanPrice:
    """Tests de la fonction clean_price."""

    def test_prix_normal_fcfa(self):
        value, devise = clean_price("5 000 FCFA")
        assert value == 5000.0
        assert devise == "FCFA"

    def test_prix_grand_nombre(self):
        value, devise = clean_price("150 000 FCFA")
        assert value == 150000.0

    def test_prix_a_debattre(self):
        value, devise = clean_price("À débattre")
        assert value is None
        assert devise == "À débattre"

    def test_prix_gratuit(self):
        value, devise = clean_price("Gratuit")
        assert value == 0.0
        assert devise == "FCFA"

    def test_prix_none(self):
        value, devise = clean_price(None)
        assert value is None
        assert devise is None

    def test_prix_vide(self):
        value, devise = clean_price("")
        assert value is None

    def test_prix_euros(self):
        value, devise = clean_price("50 €")
        assert value == 50.0
        assert devise == "EUR"


class TestCleanLocation:
    """Tests de la fonction clean_location."""

    def test_ville_et_quartier(self):
        ville, quartier = clean_location("Abidjan, Cocody")
        assert ville == "Abidjan"
        assert quartier == "Cocody"

    def test_ville_seule(self):
        ville, quartier = clean_location("Bouaké")
        assert ville == "Bouaké"
        assert quartier is None

    def test_commune_abidjan_corrigee(self):
        ville, quartier = clean_location("Yopougon")
        assert ville == "Abidjan"
        assert quartier == "Yopougon"

    def test_location_none(self):
        ville, quartier = clean_location(None)
        assert ville is None
        assert quartier is None


class TestCleanTitle:
    """Tests de la fonction clean_title."""

    def test_title_normal(self):
        result = clean_title("  robe de soirée  ")
        assert result == "Robe de soirée"

    def test_title_espaces_multiples(self):
        result = clean_title("veste   cuir   homme")
        assert result == "Veste cuir homme"

    def test_title_none(self):
        result = clean_title(None)
        assert result is None


class TestExtractCategory:
    """Tests de la classification par sous-catégorie."""

    def test_detection_chaussure(self):
        assert extract_category_detail("Chaussures Nike air max") == "chaussure"

    def test_detection_robe(self):
        assert extract_category_detail("Robe de soirée noire") == "robe"

    def test_detection_boubou(self):
        assert extract_category_detail("Grand boubou bazin brodé") == "boubou"

    def test_detection_pagne(self):
        assert extract_category_detail("Pagne wax africain 6 yards") == "pagne"

    def test_autre(self):
        assert extract_category_detail("Truc indéfinissable") == "autre"


class TestCleanData:
    """Tests du pipeline complet de nettoyage."""

    def get_sample_items(self):
        return [
            {
                "item_id": "001",
                "title": "  Robe de soirée   ",
                "price_raw": "25 000 FCFA",
                "location": "Abidjan, Cocody",
                "link": "https://jiji.co.ci/item/001",
                "image_url": None,
                "scraped_at": "2024-01-15T10:00:00",
                "category": "mode",
                "source": "jiji.co.ci",
            },
            {
                "item_id": "002",
                "title": "Chaussures Nike",
                "price_raw": "15 000 FCFA",
                "location": "Bouaké",
                "link": "https://jiji.co.ci/item/002",
                "image_url": "https://img.jiji.co.ci/002.jpg",
                "scraped_at": "2024-01-15T10:05:00",
                "category": "mode",
                "source": "jiji.co.ci",
            },
            # Doublon
            {
                "item_id": "001",
                "title": "  Robe de soirée   ",
                "price_raw": "25 000 FCFA",
                "location": "Abidjan, Cocody",
                "link": "https://jiji.co.ci/item/001",
                "image_url": None,
                "scraped_at": "2024-01-15T11:00:00",
                "category": "mode",
                "source": "jiji.co.ci",
            },
        ]

    def test_suppression_doublons(self):
        items = self.get_sample_items()
        df = clean_data(items)
        assert len(df) == 2  # 3 items - 1 doublon

    def test_colonnes_presentes(self):
        df = clean_data(self.get_sample_items())
        assert "title" in df.columns
        assert "price_value" in df.columns
        assert "city" in df.columns
        assert "subcategory" in df.columns

    def test_prix_converti_numerique(self):
        df = clean_data(self.get_sample_items())
        assert df["price_value"].dtype in ["float64", "float32"]
        assert df[df["item_id"] == "001"]["price_value"].values[0] == 25000.0

    def test_sous_categorie_inferee(self):
        df = clean_data(self.get_sample_items())
        robe_row = df[df["item_id"] == "001"]
        assert robe_row["subcategory"].values[0] == "robe"


# ─────────────────────────────────────────────────────────────────────────────
# TESTS SPIDER (avec mock HTTP)
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_HTML = """
<html><body>
  <article class="b-list-advert__item-wrapper">
    <a href="/ci/fashion/item--test123">
      <div class="b-list-advert-base__item-title">Robe pagne wax</div>
      <div class="b-list-advert__price-box">12 000 FCFA</div>
      <span class="b-list-advert__region__text">Abidjan, Marcory</span>
      <img src="https://img.jiji.co.ci/test.jpg"/>
    </a>
  </article>
</body></html>
"""


class TestSpider:
    """Tests du spider avec HTML mocké."""

    def test_extract_item_data(self):
        soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
        card = soup.select_one("article")
        item = extract_item_data(card)

        assert item is not None
        assert item["title"] == "Robe pagne wax"
        assert item["price_raw"] == "12 000 FCFA"
        assert item["location"] == "Abidjan, Marcory"
        assert item["source"] == "jiji.co.ci"

    def test_parse_listing_page(self):
        soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
        items = parse_listing_page(soup)

        assert len(items) == 1
        assert items[0]["title"] == "Robe pagne wax"

    @patch("scraper.spider.requests.get")
    def test_get_page_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch("scraper.spider.time.sleep"):  # Désactiver le délai en test
            result = get_page("https://jiji.co.ci/ci/fashion")

        assert result is not None

    @patch("scraper.spider.requests.get")
    def test_get_page_erreur_http(self, mock_get):
        import requests
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.side_effect = requests.exceptions.HTTPError(response=mock_response)

        with patch("scraper.spider.time.sleep"):
            result = get_page("https://jiji.co.ci/inexistant", retries=1)

        assert result is None
