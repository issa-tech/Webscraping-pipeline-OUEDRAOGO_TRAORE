# Dockerfile — Image Flask + Celery
# ENSEA AS Data Science — Projet Web Scraping

FROM python:3.11-slim

# Répertoire de travail
WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code
COPY . .

# Port exposé
EXPOSE 5000

# Commande par défaut (Flask)
CMD ["python", "-m", "flask", "--app", "api/app.py", "run", "--host=0.0.0.0", "--port=5000"]
