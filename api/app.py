"""
api/app.py — Factory Flask + métriques Prometheus
ENSEA AS Data Science — Projet Web Scraping
"""

import os
from flask import Flask, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

db      = SQLAlchemy()
migrate = Migrate()

# ── Métriques Prometheus — protégées contre double enregistrement ─────────────
from prometheus_client import Counter, Gauge, REGISTRY, generate_latest, CONTENT_TYPE_LATEST

def _safe_counter(name, description, labelnames=None):
    try:
        if labelnames:
            return Counter(name, description, labelnames)
        return Counter(name, description)
    except ValueError:
        return REGISTRY._names_to_collectors.get(name)

def _safe_gauge(name, description):
    try:
        return Gauge(name, description)
    except ValueError:
        return REGISTRY._names_to_collectors.get(name)

SCRAPE_COUNT      = _safe_counter("jiji_scrape_total",        "Nombre total de scrapings",     ["status"])
ITEMS_SCRAPED     = _safe_counter("jiji_items_scraped_total",  "Nombre total d annonces scrapees")
DB_ANNONCES_TOTAL = _safe_gauge(  "jiji_db_annonces_total",    "Nombre reel d annonces en base")


def create_app() -> Flask:
    app = Flask(__name__)

    # ── Config ─────────────────────────────────────────────────────────────────
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@db:5432/jiji_mode",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_ENSURE_ASCII"] = False
    try:
        app.json.ensure_ascii = False
    except Exception:
        pass

    # ── Extensions ─────────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)

    # ── Route /metrics manuelle (pas de PrometheusMetrics) ────────────────────
    @app.route("/metrics")
    def metrics():
        """Endpoint Prometheus — met à jour le gauge DB avant de répondre."""
        try:
            from api.models import Annonce
            count = db.session.query(Annonce).count()
            if DB_ANNONCES_TOTAL:
                DB_ANNONCES_TOTAL.set(count)
        except Exception:
            pass
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    # ── Health check ───────────────────────────────────────────────────────────
    @app.route("/health")
    def health():
        return {"status": "ok", "service": "jiji-mode-api"}, 200

    # ── Blueprints ─────────────────────────────────────────────────────────────
    from api.routes import api_bp
    app.register_blueprint(api_bp)

    # ── Création des tables ────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        print("✅ Tables créées avec succès")

    return app