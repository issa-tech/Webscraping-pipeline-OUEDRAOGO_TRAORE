"""
tasks/celery_app.py — Configuration Celery + Beat
ENSEA AS Data Science — Projet Web Scraping
"""

from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

load_dotenv()

BROKER_URL  = os.getenv("CELERY_BROKER_URL",  "redis://localhost:6379/0")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "jiji_scraper",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=["tasks.scrape_task"],
)

celery_app.conf.update(
    task_serializer    = "json",
    result_serializer  = "json",
    accept_content     = ["json"],
    timezone           = "Africa/Abidjan",
    enable_utc         = True,
    task_track_started = True,

    # ── Celery Beat : planification automatique ────────────────────────────────
    beat_schedule = {
        "scrape-jiji-toutes-les-6h": {
            "task":     "tasks.scrape_task.scrape_task",
            "schedule": crontab(minute=0, hour="*/6"),  # toutes les 6 heures
            "args":     (100,),
        },
    },
)
