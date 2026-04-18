"""
tasks/celery_app.py — Configuration Celery + Beat
ENSEA AS Data Science — Projet Web Scraping
"""

import sys
import os

# S'assurer que /app est dans le path
sys.path.insert(0, "/app")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

BROKER_URL  = os.getenv("CELERY_BROKER_URL",     "redis://redis:6379/0")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

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
    worker_hijack_root_logger = False,

    beat_schedule = {
        "scrape-jiji-toutes-les-6h": {
            "task":     "tasks.scrape_task.scrape_task",
            "schedule": crontab(minute=0, hour="*/6"),
            "args":     (100,),
        },
    },
)