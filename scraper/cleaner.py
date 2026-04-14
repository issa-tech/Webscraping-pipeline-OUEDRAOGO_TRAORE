"""
cleaner.py — Nettoyage et standardisation des données Jiji.ci
ENSEA AS Data Science — Projet Web Scraping
"""

import pandas as pd
import re
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def clean_price(price_raw: str) -> tuple:
    if pd.isna(price_raw) or not price_raw:
        return None, None

    price_str = str(price_raw).strip()

    if "débattre" in price_str.lower() or "négociable" in price_str.lower():
        return None, "À débattre"
    if "gratuit" in price_str.lower():
        return 0.0, "FCFA"

    # Supprimer tout sauf les chiffres (virgule et espace = séparateurs de milliers)
    digits = re.sub(r"[^\d]", "", price_str)

    try:
        value = float(digits) if digits else None
    except ValueError:
        value = None

    devise = "FCFA"
    if "€" in price_str or "EUR" in price_str.upper():
        devise = "EUR"
    elif "$" in price_str or "USD" in price_str.upper():
        devise = "USD"

    return value, devise


def clean_location(location: str) -> tuple:
    if pd.isna(location) or not location:
        return None, None

    loc = str(location).strip()
    parts = [p.strip() for p in loc.split(",")]

    communes_abidjan = {
        "yopougon", "cocody", "marcory", "plateau", "treichville",
        "adjamé", "abobo", "koumassi", "port-bouët", "attécoubé",
        "bingerville", "anyama"
    }

    ville = parts[0] if parts else None
    quartier = parts[1] if len(parts) > 1 else None

    if ville and ville.lower() in communes_abidjan:
        quartier = ville
        ville = "Abidjan"

    return ville, quartier


def clean_title(title: str):
    if pd.isna(title) or not title:
        return None
    cleaned = re.sub(r"\s+", " ", str(title).strip())
    return cleaned.capitalize() if cleaned else None


def extract_category_detail(title: str) -> str:
    if pd.isna(title) or not title:
        return "autre"

    title_lower = str(title).lower()

    categories = {
        "chaussure":  ["chaussure", "sandale", "basket", "escarpin", "botte", "mocassin", "talon"],
        "robe":       ["robe", "dress"],
        "sac":        ["sac", "bag", "pochette", "cartable"],
        "chemise":    ["chemise", "chemisier", "blouse"],
        "pantalon":   ["pantalon", "jean", "short", "bermuda"],
        "t-shirt":    ["t-shirt", "tshirt", "polo", "top"],
        "veste":      ["veste", "manteau", "blouson", "blazer", "costume"],
        "boubou":     ["boubou", "kaftan", "grand-boubou", "bazin"],
        "pagne":      ["pagne", "tissu", "wax", "ankara"],
        "accessoire": ["bracelet", "collier", "bague", "montre", "ceinture", "lunette"],
        "lingerie":   ["lingerie", "soutien", "sous-vêtement"],
    }

    for cat, keywords in categories.items():
        if any(kw in title_lower for kw in keywords):
            return cat

    return "autre"


def clean_data(raw_items: list) -> pd.DataFrame:
    """
    Pipeline complet de nettoyage.
    """
    logger.info(f"Début nettoyage : {len(raw_items)} items bruts")

    # 1. DataFrame
    df = pd.DataFrame(raw_items)
    logger.info(f"Colonnes disponibles : {list(df.columns)}")

    # 2. Suppression des doublons
    # IMPORTANT : pandas fusionne tous les NULL en 1 ligne si on déduplique
    # directement — on sépare les lignes avec/sans lien avant de dédupliquer
    initial_count = len(df)
    df_with_link  = df[df["link"].notna()].drop_duplicates(subset=["link"], keep="first")
    df_no_link    = df[df["link"].isna()]
    df = pd.concat([df_with_link, df_no_link], ignore_index=True)
    logger.info(f"Doublons supprimés : {initial_count - len(df)}")

    # 3. Supprimer les lignes sans titre ni prix
    df = df.dropna(subset=["title", "price_raw"], how="all")

    # 4. Nettoyage du prix
    price_results     = df["price_raw"].apply(clean_price)
    df["price_value"] = price_results.apply(lambda x: x[0])
    df["currency"]    = price_results.apply(lambda x: x[1])

    # 5. Nettoyage de la localisation
    loc_results    = df["location"].apply(clean_location)
    df["city"]     = loc_results.apply(lambda x: x[0])
    df["district"] = loc_results.apply(lambda x: x[1])

    # 6. Titre nettoyé
    df["title_clean"] = df["title"].apply(clean_title)

    # 7. Sous-catégorie inférée
    df["subcategory"] = df["title_clean"].apply(extract_category_detail)

    # 8. Types et valeurs par défaut
    df["price_value"] = pd.to_numeric(df["price_value"], errors="coerce")
    df["scraped_at"]  = pd.to_datetime(df["scraped_at"], errors="coerce")
    df["city"]        = df["city"].fillna("Non précisé")
    df["currency"]    = df["currency"].fillna("FCFA")

    # 9. Colonnes finales
    final_columns = [
        "item_id", "title_clean", "price_value", "currency",
        "city", "district", "subcategory", "category",
        "link", "image_url", "scraped_at", "source"
    ]
    existing_cols = [c for c in final_columns if c in df.columns]
    df = df[existing_cols]
    df = df.rename(columns={"title_clean": "title"})

    logger.info(f"Nettoyage terminé : {len(df)} items propres")

    return df


def save_clean_data(df: pd.DataFrame, filepath: str = "clean_data.json") -> None:
    records = df.where(pd.notna(df), None).to_dict(orient="records")
    for record in records:
        for key, value in record.items():
            if isinstance(value, pd.Timestamp):
                record[key] = value.isoformat()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info(f"Données propres sauvegardées : {filepath}")


def generate_stats_report(df: pd.DataFrame) -> dict:
    return {
        "total_items":      len(df),
        "items_avec_prix":  int(df["price_value"].notna().sum()),
        "prix_moyen_fcfa":  round(df["price_value"].mean(), 2) if "price_value" in df.columns else None,
        "prix_median_fcfa": round(df["price_value"].median(), 2) if "price_value" in df.columns else None,
        "villes":           df["city"].value_counts().to_dict() if "city" in df.columns else {},
        "sous_categories":  df["subcategory"].value_counts().to_dict() if "subcategory" in df.columns else {},
        "generated_at":     datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import sys

    input_file  = sys.argv[1] if len(sys.argv) > 1 else "raw_data.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "clean_data.json"

    with open(input_file, encoding="utf-8") as f:
        raw_items = json.load(f)

    df = clean_data(raw_items)
    save_clean_data(df, output_file)

    stats = generate_stats_report(df)
    print(f"\n✅ Nettoyage terminé")
    print(f"Total items propres : {stats['total_items']}")
    print(f"Prix moyen : {stats['prix_moyen_fcfa']} FCFA")
    print(f"\nSous-catégories :\n{json.dumps(stats['sous_categories'], ensure_ascii=False, indent=2)}")