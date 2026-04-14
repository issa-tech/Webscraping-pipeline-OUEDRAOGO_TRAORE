# 🛍️ Pipeline Web Scraping — Mode en Côte d'Ivoire

![Niveau](https://img.shields.io/badge/Niveau-OR%20🥇-gold)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![Flask](https://img.shields.io/badge/API-Flask%20+%20Swagger-green)
![Celery](https://img.shields.io/badge/Async-Celery%20+%20Redis-red)

> **ENSEA — AS Data Science | Projet Web Scraping**  
> Enseignant : Dr N'golo Konate  
> Pipeline complet de collecte, nettoyage, stockage et exposition des annonces de mode sur Jiji.ci

---

## 👥 Membres et Rôles

| Membre | Rôle |
|--------|------|
| [Prénom NOM] | Data Engineer (Scraping + Nettoyage) |
| [Prénom NOM] | Backend/DevOps (API + Docker + Monitoring) |

---

## 🎯 Description du Projet

Ce pipeline collecte automatiquement les annonces de **vêtements et accessoires de mode** publiées sur [Jiji.co.ci](https://jiji.co.ci), le principal site de petites annonces en Côte d'Ivoire. Les données sont nettoyées, stockées en base PostgreSQL et exposées via une API REST documentée avec Swagger.

**Pertinence :** Le marché de la mode ivoirienne est en forte croissance sur le numérique. Ce dataset permet d'analyser les tendances de prix, les types de vêtements les plus vendus et la répartition géographique des vendeurs.

---

## 🏗️ Architecture

```
Jiji.ci
   ↓ BeautifulSoup Spider
Celery Worker (async) ← Redis (broker) ← Celery Beat (planification)
   ↓
PostgreSQL (stockage)
   ↓
Flask API REST (Swagger docs)
   ↓
Prometheus → Grafana (monitoring)
```

---

## 🛠️ Technologies

| Composant | Technologie |
|-----------|-------------|
| Scraping | BeautifulSoup 4 + Requests |
| Nettoyage | pandas |
| Base de données | PostgreSQL 15 |
| API REST | Flask + flask-restx (Swagger) |
| Async Tasks | Celery 5 + Redis |
| Planification | Celery Beat |
| Conteneurisation | Docker Compose |
| Monitoring | Prometheus + Grafana |
| Tests | pytest + pytest-cov |

---

## 📂 Structure du Projet

```
webscraping-pipeline/
├── scraper/
│   ├── spider.py         # Spider BeautifulSoup (Jiji.ci)
│   └── cleaner.py        # Nettoyage pandas
├── api/
│   ├── app.py            # Factory Flask
│   ├── models.py         # Modèles SQLAlchemy
│   └── routes.py         # Endpoints REST + Swagger
├── tasks/
│   ├── celery_app.py     # Configuration Celery
│   └── scrape_task.py    # Tâche async de scraping
├── monitoring/
│   ├── prometheus.yml    # Config scraping métriques
│   └── grafana/          # Dashboards JSON
├── tests/
│   ├── test_scraper.py   # Tests du spider + cleaner
│   ├── test_api.py       # Tests des endpoints
│   └── test_tasks.py     # Tests Celery
├── docker-compose.yml    # Orchestration 6 services
├── Dockerfile            # Image Flask + Celery
├── requirements.txt
├── .env.example          # Variables d'environnement
└── README.md
```

---

## 🚀 Installation & Lancement

### Prérequis
- Docker Desktop ≥ 4.x
- Python 3.10+ (pour développement local)

### Lancement rapide avec Docker

```bash
# 1. Cloner le repo
git clone https://github.com/[groupe]/webscraping-pipeline.git
cd webscraping-pipeline

# 2. Copier et configurer les variables d'environnement
cp .env.example .env

# 3. Lancer tous les services
docker-compose up --build

# 4. Vérifier que tout fonctionne
curl http://localhost:5000/health
```

### Services disponibles

| Service | URL |
|---------|-----|
| API Flask | http://localhost:5000 |
| Swagger UI | http://localhost:5000/docs |
| Flower (Celery) | http://localhost:5555 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

---

## 📡 Endpoints API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Statut de l'API |
| GET | `/data` | Toutes les annonces (paginé) |
| GET | `/data/{id}` | Une annonce par ID |
| GET | `/data/search?query=robe` | Recherche par mot-clé |
| GET | `/data/stats` | Statistiques globales |
| POST | `/scrape` | Lancer un scraping synchrone |
| POST | `/scrape/async` | Lancer un scraping asynchrone |
| GET | `/tasks/{task_id}` | Statut d'une tâche Celery |
| GET | `/metrics` | Métriques Prometheus |

---

## ✅ Éthique du Scraping

- ✅ `robots.txt` vérifié : seuls `/admin/`, `/test/`, `/crm/` sont interdits
- ✅ User-Agent identifié : `ENSEA Educational Project`
- ✅ Délai entre requêtes : 1–2.5 secondes
- ✅ Volume limité : maximum 500 annonces
- ✅ Aucune donnée personnelle collectée

---

## 🧪 Tests

```bash
# Lancer tous les tests
pytest tests/ -v

# Avec couverture de code
pytest tests/ --cov=. --cov-report=html
```

---

## 📸 Captures d'écran

*(à ajouter après implémentation)*

---

## 📄 Licence

Projet académique — ENSEA 2024/2025
