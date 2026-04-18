"""
tasks/scrape_task.py — Tâche Celery de scraping asynchrone
ENSEA AS Data Science — Projet Web Scraping
"""

import sys
import os

# S'assurer que /app est dans le path Python du worker
sys.path.insert(0, "/app")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks.celery_app import celery_app
import math
import logging

logger = logging.getLogger(__name__)


def clean_val(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


@celery_app.task(bind=True, name="tasks.scrape_task.scrape_task")
def scrape_task(self, max_items=100):
    """Tâche Celery : scrape Jiji.ci, nettoie, insère en base."""

    # Imports tardifs pour éviter les imports circulaires
    import sys, os
    sys.path.insert(0, "/app")

    from api.app import create_app, db, SCRAPE_COUNT, ITEMS_SCRAPED
    from api.models import Annonce, ScrapeLog
    from scraper.spider import scrape_jiji_mode
    from scraper.cleaner import clean_data
    from datetime import datetime

    app = create_app()

    with app.app_context():
        log = ScrapeLog(status="running")
        db.session.add(log)
        db.session.commit()

        try:
            # 1. Scraping
            logger.info(f"Démarrage du scraping Jiji.ci (max {max_items} items)...")
            raw_items = scrape_jiji_mode(max_items=max_items)
            logger.info(f"{len(raw_items)} items bruts collectés")

            # 2. Nettoyage
            df = clean_data(raw_items)
            clean_items = df.where(df.notna(), None).to_dict(orient="records")

            # 3. Insertion en base (sans doublons)
            saved = 0
            for item in clean_items:
                link = clean_val(item.get("link"))
                if link and Annonce.query.filter_by(link=link).first():
                    continue
                annonce = Annonce(
                    item_id     = clean_val(item.get("item_id")),
                    title       = clean_val(item.get("title")) or "Sans titre",
                    price_value = clean_val(item.get("price_value")),
                    currency    = clean_val(item.get("currency")) or "FCFA",
                    city        = clean_val(item.get("city")) or "Non précisé",
                    district    = clean_val(item.get("district")),
                    category    = clean_val(item.get("category")) or "mode",
                    subcategory = clean_val(item.get("subcategory")) or "autre",
                    link        = link,
                    image_url   = clean_val(item.get("image_url")),
                    source      = clean_val(item.get("source")) or "jiji.co.ci",
                )
                db.session.add(annonce)
                saved += 1

            db.session.commit()

            # 4. Métriques Prometheus
            try:
                SCRAPE_COUNT.labels(status="success").inc()
                ITEMS_SCRAPED.inc(saved)
            except Exception:
                pass

            # 5. Log final
            log.finished_at = datetime.utcnow()
            log.items_found = len(raw_items)
            log.items_saved = saved
            log.status      = "success"
            db.session.commit()

            logger.info(f"Tâche terminée : {saved} items sauvegardés")
            return {
                "status":      "success",
                "items_found": len(raw_items),
                "items_saved": saved,
            }

        except Exception as e:
            logger.error(f"Erreur tâche Celery : {e}")
            try:
                log.status    = "error"
                log.error_msg = str(e)
                db.session.commit()
                SCRAPE_COUNT.labels(status="error").inc()
            except Exception:
                pass
            raise