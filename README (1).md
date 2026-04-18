# 🛍️ Pipeline Web Scraping — Mode en Côte d'Ivoire

![Niveau](https://img.shields.io/badge/Niveau-🥇%20OR-gold?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-REST%20API-black?style=for-the-badge&logo=flask)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql)
![Celery](https://img.shields.io/badge/Celery-Beat-37814A?style=for-the-badge)
![Prometheus](https://img.shields.io/badge/Prometheus-Grafana-E6522C?style=for-the-badge&logo=prometheus)

> **Pipeline complet de production** pour la collecte, le nettoyage, le stockage et l'analyse des annonces de mode sur [Jiji.co.ci](https://jiji.co.ci) — avec API REST, tâches asynchrones et monitoring en temps réel.

---

## 👥 Membres du Groupe

| Nom | Rôle |
|-----|------|
| **OUEDRAOGO [Prénom]** | Data Engineer — Scraping & Nettoyage |
| **TRAORE [Prénom]** | Backend / DevOps — API, Docker, Celery, Monitoring |

**Institution :** ENSEA — AS Data Science  
**Enseignant :** Dr N'golo Konate  
**Année :** 2025–2026

---

## 📌 Description du Projet

Ce projet analyse le **marché de la mode en Côte d'Ivoire** en collectant automatiquement les annonces vestimentaires publiées sur Jiji.ci (la principale plateforme d'annonces en ligne en CI).

### Ce que fait le pipeline :

```
Jiji.co.ci
    │
    ▼ scraping (BeautifulSoup)
raw_data.json (500 annonces brutes)
    │
    ▼ nettoyage (pandas)
clean_data.json (prix, localisation, catégorie standardisés)
    │
    ▼ stockage
PostgreSQL (base de données persistante)
    │
    ▼ exposition
API Flask REST + Swagger UI
    │
    ▼ monitoring
Prometheus + Grafana Dashboard
```

### Données collectées :
- **500 annonces** de mode (femme, homme, enfant)
- Prix en FCFA, localisation Abidjan & villes CI
- Sous-catégories : robe, chaussure, sac, accessoire, veste, boubou, pagne...
- Prix moyen : ~13 147 FCFA

---

## 🛠️ Technologies Utilisées

| Composant | Technologie |
|-----------|-------------|
| Scraping | Python 3.11 + BeautifulSoup4 |
| Nettoyage | pandas |
| API REST | Flask + flask-restx (Swagger) |
| Base de données | PostgreSQL 15 |
| Tâches async | Celery + Redis |
| Planification | Celery Beat (toutes les 6h) |
| Conteneurisation | Docker + Docker Compose |
| Monitoring | Prometheus + Grafana |
| Tests | pytest (27 tests) |

---

## 📁 Structure du Projet

```
webscraping-pipeline/
├── scraper/
│   ├── spider.py          # Spider BeautifulSoup — collecte Jiji.ci
│   ├── cleaner.py         # Nettoyage et standardisation pandas
│   ├── raw_data.json      # Données brutes (500 items)
│   └── clean_data.json    # Données nettoyées
├── api/
│   ├── __init__.py
│   ├── app.py             # Factory Flask + métriques Prometheus
│   ├── models.py          # Modèles SQLAlchemy (PostgreSQL)
│   └── routes.py          # 7 endpoints REST + Swagger
├── tasks/
│   ├── celery_app.py      # Configuration Celery + Beat
│   └── scrape_task.py     # Tâche async de scraping
├── monitoring/
│   ├── prometheus.yml     # Configuration Prometheus
│   └── grafana/           # Dashboard Grafana
├── tests/
│   └── test_scraper.py    # 27 tests pytest
├── docker-compose.yml     # Orchestration 7 services
├── Dockerfile             # Image Python 3.11-slim
├── run.py                 # Point d'entrée Flask
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚡ Installation et Lancement

### Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et lancé
- Git

### Lancement en 2 commandes

```bash
# 1. Cloner le projet
git clone https://github.com/issa-tech/Webscraping-pipeline-OUEDRAOGO_TRAORE.git
cd Webscraping-pipeline-OUEDRAOGO_TRAORE

# 2. Lancer tous les services
docker-compose up --build
```

Attendre que les 7 services démarrent (~2-3 min). Vous verrez :

```
jiji_api | ✅ Tables créées avec succès
jiji_api | * Running on http://0.0.0.0:5000
```

### Accès aux interfaces

| Interface | URL | Identifiants |
|-----------|-----|--------------|
| API Health | http://localhost:5000/health | — |
| Swagger UI | http://localhost:5000/api/docs | — |
| Métriques | http://localhost:5000/metrics | — |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | — |

### Arrêter les services

```bash
docker-compose down
```

---

## 🔌 Endpoints API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/health` | Statut de l'API |
| `GET` | `/api/data/` | Toutes les annonces (paginées) |
| `GET` | `/api/data/{id}` | Une annonce par ID |
| `GET` | `/api/data/search?query=robe` | Recherche par mot-clé |
| `GET` | `/api/data/stats` | Statistiques globales |
| `POST` | `/api/scrape/` | Scraping synchrone |
| `POST` | `/api/scrape/async` | Scraping asynchrone (Celery) |
| `GET` | `/api/scrape/tasks/{id}` | Statut d'une tâche Celery |
| `GET` | `/metrics` | Métriques Prometheus |

### Exemples de réponses

**GET /api/data/stats**
```json
{
  "total_annonces": 500,
  "prix_moyen": 13147.46,
  "top_ville": "Abidjan",
  "sous_categories": {
    "autre": 353,
    "accessoire": 56,
    "sac": 42,
    "chaussure": 35,
    "veste": 14
  }
}
```

**POST /api/scrape/**
```json
{
  "status": "success",
  "items_found": 100,
  "items_saved": 100,
  "message": "100 annonces ajoutées en base"
}
```

---

## 🧪 Tests

```bash
# Activer l'environnement virtuel
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# Lancer les 27 tests
python -m pytest tests/test_scraper.py -v
```

**Résultat attendu :**
```
27 passed in 5.13s ✅
```

Les tests couvrent :
- `TestCleanPrice` — nettoyage des prix (FCFA, EUR, null, gratuit...)
- `TestCleanLocation` — normalisation des localisations
- `TestCleanTitle` — standardisation des titres
- `TestExtractCategory` — détection des sous-catégories
- `TestCleanData` — pipeline complet
- `TestSpider` — fonctions du scraper

---

## 📊 Monitoring Grafana

Le dashboard **"Jiji Mode CI — Monitoring"** affiche :

- **Total annonces scrapées** — compteur en temps réel
- **Scrapings réussis** — nombre d'exécutions
- **CPU & Mémoire** — ressources consommées
- **Évolution des annonces** — courbe temporelle
- **Jauge de complétion** — progression vers 500 items
- **Historique des scrapings** — barres par 5 minutes

Pour importer le dashboard :
1. Aller sur http://localhost:3000
2. Dashboards → New → Import
3. Uploader le fichier `monitoring/grafana/dashboard.json`
4. Sélectionner **Prometheus** comme datasource

---

## ⚙️ Architecture Docker

```
docker-compose up
      │
      ├── jiji_api          (Flask — port 5000)
      ├── jiji_db           (PostgreSQL — port 5432)
      ├── jiji_redis        (Redis — port 6379)
      ├── jiji_celery_worker (Celery — tâches async)
      ├── jiji_celery_beat  (Celery Beat — scraping auto toutes les 6h)
      ├── jiji_prometheus   (Prometheus — port 9090)
      └── jiji_grafana      (Grafana — port 3000)
```

---

## ⚖️ Respect de la Charte Éthique

| Règle | Application |
|-------|-------------|
| ✅ robots.txt vérifié | `/ci/fashion` interdit → `/womens-fashion` autorisé |
| ✅ Délai entre requêtes | 1 à 2.5 secondes aléatoires |
| ✅ User-Agent identifiable | `ENSEA Educational Project - Web Scraping AS Data Science` |
| ✅ Pas de données personnelles | Annonces publiques uniquement |
| ✅ Volume limité | Maximum 500 items |

---

## 📈 Résultats

| Métrique | Valeur |
|----------|--------|
| Annonces collectées | 500 |
| Prix moyen | 13 147 FCFA |
| Catégories couvertes | Mode Femme, Mode Homme, Mode Enfant |
| Tests passés | 27 / 27 ✅ |
| Services Docker | 7 |
| Endpoints API | 9 |

---

## 📄 Licence

Projet académique — ENSEA AS Data Science 2025–2026.  
Usage éducatif uniquement.
