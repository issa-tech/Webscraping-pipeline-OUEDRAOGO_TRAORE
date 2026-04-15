"""
api/models.py — Modèles SQLAlchemy
ENSEA AS Data Science — Projet Web Scraping
"""

from datetime import datetime
from api.app import db


class Annonce(db.Model):
    """Modèle principal — une annonce de mode sur Jiji.ci"""

    __tablename__ = "annonces"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id     = db.Column(db.String(100), nullable=True, index=True)
    title       = db.Column(db.String(500), nullable=False)
    price_value = db.Column(db.Float, nullable=True)
    currency    = db.Column(db.String(20), default="FCFA")
    city        = db.Column(db.String(100), default="Non précisé")
    district    = db.Column(db.String(100), nullable=True)
    category    = db.Column(db.String(50), default="mode")
    subcategory = db.Column(db.String(50), default="autre")
    link        = db.Column(db.Text, nullable=True, unique=True)
    image_url   = db.Column(db.Text, nullable=True)
    scraped_at  = db.Column(db.DateTime, default=datetime.utcnow)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    source      = db.Column(db.String(50), default="jiji.co.ci")

    def to_dict(self):
        return {
            "id":          self.id,
            "item_id":     self.item_id,
            "title":       self.title,
            "price_value": self.price_value,
            "currency":    self.currency,
            "city":        self.city,
            "district":    self.district,
            "category":    self.category,
            "subcategory": self.subcategory,
            "link":        self.link,
            "image_url":   self.image_url,
            "scraped_at":  self.scraped_at.isoformat() if self.scraped_at else None,
            "source":      self.source,
        }

    def __repr__(self):
        return f"<Annonce {self.id} — {self.title[:40]}>"


class ScrapeLog(db.Model):
    """Log de chaque exécution de scraping."""

    __tablename__ = "scrape_logs"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    started_at  = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    items_found = db.Column(db.Integer, default=0)
    items_saved = db.Column(db.Integer, default=0)
    status      = db.Column(db.String(20), default="running")
    error_msg   = db.Column(db.Text, nullable=True)
    task_id     = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            "id":          self.id,
            "started_at":  self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "items_found": self.items_found,
            "items_saved": self.items_saved,
            "status":      self.status,
            "error_msg":   self.error_msg,
            "task_id":     self.task_id,
        }