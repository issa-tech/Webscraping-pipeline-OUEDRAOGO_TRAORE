"""
api/app.py — Factory Flask
ENSEA AS Data Science — Projet Web Scraping
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from prometheus_client import make_wsgi_app, Counter
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

db      = SQLAlchemy()
migrate = Migrate()

# ── Métriques Prometheus ───────────────────────────────────────────────────────
SCRAPE_COUNT = Counter(
    "jiji_scrape_total",
    "Nombre total de scrapings effectués",
    ["status"]
)
ITEMS_SCRAPED = Counter(
    "jiji_items_scraped_total",
    "Nombre total d annonces scrapees"
)


def create_app():
    app = Flask(__name__)

    # ── Config JSON ────────────────────────────────────────────────────────────
    app.config["JSON_ENSURE_ASCII"] = False
    app.json.ensure_ascii = False

    # ── Configuration base de données ──────────────────────────────────────────
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/jiji_mode"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    # ── Extensions ─────────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)

    # ── Middleware Prometheus — expose /metrics ────────────────────────────────
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        "/metrics": make_wsgi_app()
    })

    # ── Blueprints ─────────────────────────────────────────────────────────────
    from api.routes import api_bp
    app.register_blueprint(api_bp)

    # ── Health check ───────────────────────────────────────────────────────────
    @app.route("/health")
    def health():
        return {"status": "ok", "service": "jiji-mode-api"}, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)