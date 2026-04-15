"""
tasks/scrape_task.py — Tâche Celery de scraping
ENSEA AS Data Science — Projet Web Scraping
"""

import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.scrape_task.scrape_task")
def scrape_task(self, max_items: int = 100):
    """
    Tâche Celery : scraping + nettoyage + insertion en base.
    Appelée via POST /api/scrape/async ou automatiquement par Celery Beat.
    """
    from api.app import create_app, db
    from api.models import Annonce, ScrapeLog
    from scraper.spider  import scrape_jiji_mode
    from scraper.cleaner import clean_data

    app = create_app()

    with app.app_context():
        log = ScrapeLog(status="running", task_id=self.request.id)
        db.session.add(log)
        db.session.commit()

        try:
            # Mise à jour du statut Celery
            self.update_state(state="PROGRESS", meta={"step": "scraping"})
            logger.info(f"[Task {self.request.id}] Démarrage scraping ({max_items} items)")

            raw_items = scrape_jiji_mode(max_items=max_items)
            logger.info(f"[Task {self.request.id}] {len(raw_items)} items bruts collectés")

            self.update_state(state="PROGRESS", meta={"step": "cleaning"})
            df          = clean_data(raw_items)
            clean_items = df.where(df.notna(), None).to_dict(orient="records")

            self.update_state(state="PROGRESS", meta={"step": "saving"})
            saved = 0
            for item in clean_items:
                if item.get("link") and Annonce.query.filter_by(link=item["link"]).first():
                    continue
                annonce = Annonce(
                    title       = item.get("title") or "Sans titre",
                    price_value = item.get("price_value"),
                    currency    = item.get("currency", "FCFA"),
                    city        = item.get("city", "Non précisé"),
                    district    = item.get("district"),
                    subcategory = item.get("subcategory", "autre"),
                    link        = item.get("link"),
                    image_url   = item.get("image_url"),
                    source      = item.get("source", "jiji.co.ci"),
                )
                db.session.add(annonce)
                saved += 1
            db.session.commit()

            log.finished_at = datetime.utcnow()
            log.items_found = len(raw_items)
            log.items_saved = saved
            log.status      = "success"
            db.session.commit()

            logger.info(f"[Task {self.request.id}] Terminé : {saved} items sauvegardés")
            return {"status": "success", "items_found": len(raw_items), "items_saved": saved}

        except Exception as e:
            log.status    = "error"
            log.error_msg = str(e)
            db.session.commit()
            logger.error(f"[Task {self.request.id}] Erreur : {e}")
            raise
