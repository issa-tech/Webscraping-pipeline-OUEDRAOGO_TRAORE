"""
api/routes.py — Endpoints REST + Swagger
ENSEA AS Data Science — Projet Web Scraping
"""

from flask import Blueprint, request
from flask_restx import Api, Resource, fields, Namespace
from sqlalchemy import func
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.app import db
from api.models import Annonce, ScrapeLog

# ── Blueprint + Swagger ────────────────────────────────────────────────────────
api_bp  = Blueprint("api", __name__, url_prefix="/api")
api_doc = Api(
    api_bp,
    version="1.0",
    title="Jiji Mode CI — API",
    description="Pipeline Web Scraping — Mode en Côte d'Ivoire | ENSEA AS Data Science",
    doc="/docs",
)

ns        = Namespace("data",   description="Annonces de mode Jiji.ci")
ns_scrape = Namespace("scrape", description="Contrôle du scraping")
api_doc.add_namespace(ns,        path="/data")
api_doc.add_namespace(ns_scrape, path="/scrape")

# ── Modèles Swagger ────────────────────────────────────────────────────────────
annonce_model = ns.model("Annonce", {
    "id":          fields.Integer(description="ID interne"),
    "title":       fields.String(description="Titre de l'annonce"),
    "price_value": fields.Float(description="Prix en FCFA"),
    "currency":    fields.String(description="Devise"),
    "city":        fields.String(description="Ville"),
    "district":    fields.String(description="Quartier"),
    "subcategory": fields.String(description="Sous-catégorie mode"),
    "link":        fields.String(description="URL de l'annonce"),
    "image_url":   fields.String(description="URL de l'image"),
    "scraped_at":  fields.String(description="Date de collecte"),
    "source":      fields.String(description="Source"),
})

pagination_model = ns.model("Pagination", {
    "items":    fields.List(fields.Nested(annonce_model)),
    "total":    fields.Integer(description="Nombre total d'annonces"),
    "page":     fields.Integer(description="Page courante"),
    "pages":    fields.Integer(description="Nombre total de pages"),
    "per_page": fields.Integer(description="Items par page"),
})

stats_model = ns.model("Stats", {
    "total_annonces":    fields.Integer(),
    "items_avec_prix":   fields.Integer(),
    "prix_moyen":        fields.Float(),
    "prix_median":       fields.Float(),
    "prix_min":          fields.Float(),
    "prix_max":          fields.Float(),
    "villes":            fields.Raw(),
    "sous_categories":   fields.Raw(),
    "derniere_collecte": fields.String(),
})

scrape_model = ns_scrape.model("ScrapeResult", {
    "message":     fields.String(),
    "items_found": fields.Integer(),
    "items_saved": fields.Integer(),
    "task_id":     fields.String(),
    "status":      fields.String(),
})


# ── Helper : nettoyage NaN ─────────────────────────────────────────────────────
def clean_val(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


# ── Helper : insertion en base ─────────────────────────────────────────────────
def save_items_to_db(items: list) -> int:
    saved = 0
    for item in items:
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
    return saved


# ── Endpoints : /api/data ──────────────────────────────────────────────────────

@ns.route("/")
class AnnonceList(Resource):

    @ns.doc("list_annonces", params={
        "page":        "Numéro de page (défaut: 1)",
        "limit":       "Items par page (défaut: 20, max: 100)",
        "per_page":    "Items par page (alias de limit)",
        "subcategory": "Filtrer par sous-catégorie",
        "city":        "Filtrer par ville",
    })
    def get(self):
        """Récupérer toutes les annonces avec pagination et filtres."""
        page        = request.args.get("page", 1, type=int)
        per_page    = min(
            request.args.get("per_page",
                request.args.get("limit", 20, type=int),
            type=int), 100
        )
        subcategory = request.args.get("subcategory")
        city        = request.args.get("city")

        query = Annonce.query
        if subcategory:
            query = query.filter(Annonce.subcategory == subcategory)
        if city:
            query = query.filter(Annonce.city.ilike(f"%{city}%"))

        pagination = query.order_by(Annonce.scraped_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            "items":    [a.to_dict() for a in pagination.items],
            "total":    pagination.total,
            "page":     pagination.page,
            "pages":    pagination.pages,
            "per_page": per_page,
        }, 200


@ns.route("/<int:id>")
@ns.param("id", "ID de l'annonce")
class AnnonceDetail(Resource):

    @ns.doc("get_annonce")
    def get(self, id):
        """Récupérer une annonce par son ID."""
        annonce = Annonce.query.get(id)
        if not annonce:
            return {"error": f"Annonce {id} introuvable"}, 404
        return annonce.to_dict(), 200


@ns.route("/search")
class AnnonceSearch(Resource):

    @ns.doc("search_annonces", params={
        "query": "Mot-clé à rechercher dans les titres",
        "page":  "Numéro de page (défaut: 1)",
        "limit": "Items par page (défaut: 20)",
    })
    def get(self):
        """Rechercher des annonces par mot-clé dans le titre."""
        query_str = request.args.get("query", "")
        page      = request.args.get("page",  1,  type=int)
        per_page  = min(request.args.get("limit", 20, type=int), 100)

        if not query_str:
            return {"error": "Paramètre 'query' requis"}, 400

        pagination = Annonce.query.filter(
            Annonce.title.ilike(f"%{query_str}%")
        ).order_by(Annonce.scraped_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            "query":    query_str,
            "items":    [a.to_dict() for a in pagination.items],
            "total":    pagination.total,
            "page":     pagination.page,
            "pages":    pagination.pages,
            "per_page": per_page,
        }, 200


@ns.route("/stats")
class AnnonceStats(Resource):

    @ns.doc("get_stats")
    def get(self):
        """Statistiques globales sur les annonces collectées."""
        total = Annonce.query.count()

        prix_stats = db.session.query(
            func.avg(Annonce.price_value),
            func.min(Annonce.price_value),
            func.max(Annonce.price_value),
            func.count(Annonce.price_value),
        ).filter(Annonce.price_value.isnot(None)).first()

        villes = db.session.query(
            Annonce.city, func.count(Annonce.id)
        ).group_by(Annonce.city).order_by(
            func.count(Annonce.id).desc()
        ).limit(10).all()

        subcats = db.session.query(
            Annonce.subcategory, func.count(Annonce.id)
        ).group_by(Annonce.subcategory).order_by(
            func.count(Annonce.id).desc()
        ).all()

        last = Annonce.query.order_by(Annonce.scraped_at.desc()).first()

        return {
            "total_annonces":    total,
            "items_avec_prix":   int(prix_stats[3]) if prix_stats[3] else 0,
            "prix_moyen":        round(float(prix_stats[0]), 2) if prix_stats[0] else None,
            "prix_median":       None,
            "prix_min":          float(prix_stats[1]) if prix_stats[1] else None,
            "prix_max":          float(prix_stats[2]) if prix_stats[2] else None,
            "villes":            {str(v): int(c) for v, c in villes},
            "sous_categories":   {str(s): int(c) for s, c in subcats},
            "derniere_collecte": last.scraped_at.isoformat() if last else None,
        }, 200


# ── Endpoints : /api/scrape ────────────────────────────────────────────────────

@ns_scrape.route("/")
class ScrapeSync(Resource):

    @ns_scrape.doc("scrape_sync")
    def post(self):
        """Lancer un scraping synchrone (bloquant ~2 min)."""
        from scraper.spider  import scrape_jiji_mode
        from scraper.cleaner import clean_data
        from api.app import SCRAPE_COUNT, ITEMS_SCRAPED
        from datetime import datetime

        log = ScrapeLog(status="running")
        db.session.add(log)
        db.session.commit()

        try:
            raw_items   = scrape_jiji_mode(max_items=100)
            df          = clean_data(raw_items)
            clean_items = df.where(df.notna(), None).to_dict(orient="records")
            saved       = save_items_to_db(clean_items)

            SCRAPE_COUNT.labels(status="success").inc()
            ITEMS_SCRAPED.inc(saved)

            log.finished_at = datetime.utcnow()
            log.items_found = len(raw_items)
            log.items_saved = saved
            log.status      = "success"
            db.session.commit()

            return {
                "message":     f"{saved} annonces ajoutées en base",
                "items_found": len(raw_items),
                "items_saved": saved,
                "status":      "success",
            }, 200

        except Exception as e:
            log.status    = "error"
            log.error_msg = str(e)
            db.session.commit()
            try:
                from api.app import SCRAPE_COUNT
                SCRAPE_COUNT.labels(status="error").inc()
            except Exception:
                pass
            return {"error": str(e)}, 500


@ns_scrape.route("/async")
class ScrapeAsync(Resource):

    @ns_scrape.doc("scrape_async")
    def post(self):
        """Lancer un scraping asynchrone via Celery (non bloquant)."""
        try:
            from tasks.scrape_task import scrape_task
            task = scrape_task.delay()
            return {
                "message": "Tâche de scraping lancée",
                "task_id": str(task.id),
                "status":  "pending",
            }, 202
        except Exception as e:
            return {"error": f"Celery non disponible : {str(e)}"}, 503


@ns_scrape.route("/tasks/<string:task_id>")
@ns_scrape.param("task_id", "ID de la tâche Celery")
class TaskStatus(Resource):

    @ns_scrape.doc("get_task_status")
    def get(self, task_id):
        """Vérifier le statut d'une tâche Celery."""
        try:
            from tasks.celery_app import celery_app
            task = celery_app.AsyncResult(task_id)

            response = {
                "task_id": str(task_id),
                "status":  str(task.state),
            }

            if task.state == "SUCCESS":
                raw = task.result
                # S'assurer que le résultat est sérialisable
                if isinstance(raw, dict):
                    response["result"] = {
                        k: (str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v)
                        for k, v in raw.items()
                    }
                elif raw is not None:
                    response["result"] = str(raw)

            elif task.state == "FAILURE":
                # task.info contient l'exception — on la convertit en string
                response["error"] = str(task.info) if task.info else "Erreur inconnue"

            elif task.state == "PENDING":
                response["message"] = "Tâche en attente ou ID inconnu"

            elif task.state == "STARTED":
                response["message"] = "Tâche en cours d'exécution"

            return response, 200

        except Exception as e:
            return {
                "task_id": str(task_id),
                "status":  "UNKNOWN",
                "error":   str(e),
            }, 200