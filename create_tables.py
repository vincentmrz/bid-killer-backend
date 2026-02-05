import asyncio
import sys
import os

# Ajoute le dossier courant au chemin pour trouver 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db

async def main():
    print("⏳ Démarrage de la création des tables...")
    try:
        await init_db()
        print("✅ SUCCÈS : Toutes les tables ont été créées sur la base de données !")
    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    asyncio.run(main())