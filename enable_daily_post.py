#!/usr/bin/env python3
"""
Script per abilitare il daily post.
Esegui: python enable_daily_post.py
"""

import os
import sys
from pathlib import Path

# Aggiungi il percorso del progetto al PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database import SessionLocal, get_daily_post_settings, DailyPostSettings
from sqlalchemy import text

def main():
    """Abilita il daily post."""

    print("🔄 Abilitazione Daily Post...")

    # Ottieni una sessione del database
    db = SessionLocal()
    try:
        # Verifica se esiste già un record
        existing_settings = get_daily_post_settings(db)

        if existing_settings:
            # Aggiorna il record esistente
            existing_settings.enabled = 1
            db.commit()
            print("✅ Daily post abilitato con successo (aggiornato record esistente)!")
            print(f"   ⏰ Orario: {existing_settings.post_time}")
            print(f"   🎨 Stile: {existing_settings.style}")
            print(f"   📊 Max messaggi: {existing_settings.max_messages}")
        else:
            # Crea un nuovo record usando SQL diretta per gestire l'autoincrement
            sql = text("""
                INSERT INTO daily_post_settings
                (enabled, post_time, style, max_messages, title_template, hashtag_template, ai_model, created_at, updated_at)
                VALUES
                (1, '20:00', 'CAROUSEL', 20, '🌟 Spotted del giorno {date} 🌟\n\nEcco tutti gli spotted della giornata! 💫',
                 '#spotted #instaspotter #dailyrecap', 'GEMINI', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)
            db.execute(sql)
            db.commit()
            print("✅ Daily post abilitato con successo (creato nuovo record)!")

    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
