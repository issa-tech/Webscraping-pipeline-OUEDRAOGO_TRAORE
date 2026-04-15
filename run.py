# run.py — Point d'entrée Flask avec création automatique des tables
from api.app import create_app, db
from api.models import Annonce, ScrapeLog

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Crée les tables directement sans migrations
        print("✅ Tables créées avec succès")
    app.run(debug=True, host="0.0.0.0", port=5000)
