# run.py — Point d'entrée Flask avec création automatique des tables
import os
from flask import send_from_directory, Response
from api.app import create_app, db
from api.models import Annonce, ScrapeLog

app = create_app()

# Chemin absolu vers le dossier contenant run.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/dashboard')
def dashboard():
    return send_from_directory(BASE_DIR, 'dashboard_mode_ci.html')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Tables créées avec succès")
    app.run(debug=True, host="0.0.0.0", port=5000)