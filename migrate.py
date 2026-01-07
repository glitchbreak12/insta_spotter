from sqlalchemy import create_engine, text
from config import settings

def run_migration():
    engine = create_engine(settings.database.db_url)
    print("--- Avvio Migrazione Database ---")
    with engine.connect() as connection:
        # Migrate media_pk column
        try:
            connection.execute(text('ALTER TABLE spotted_messages ADD COLUMN media_pk VARCHAR'))
            connection.commit()
            print("✅ Colonna 'media_pk' aggiunta con successo.")
        except Exception as e:
            if "duplicate column name" in str(e) or "already exists" in str(e):
                print("ℹ️  Colonna 'media_pk' già esistente.")
            else:
                print(f"❌ Errore colonna 'media_pk': {e}")
            connection.rollback()

        # Migrate gemini_analysis column
        try:
            connection.execute(text('ALTER TABLE spotted_messages ADD COLUMN gemini_analysis VARCHAR'))
            connection.commit()
            print("✅ Colonna 'gemini_analysis' aggiunta con successo.")
        except Exception as e:
            if "duplicate column name" in str(e) or "already exists" in str(e):
                print("ℹ️  Colonna 'gemini_analysis' già esistente.")
            else:
                print(f"❌ Errore colonna 'gemini_analysis': {e}")
            connection.rollback()

        # Create technical_users table
        try:
            connection.execute(text('''
                CREATE TABLE technical_users (
                    id VARCHAR PRIMARY KEY,
                    first_seen_at TIMESTAMP,
                    last_seen_at TIMESTAMP,
                    trust_score INTEGER,
                    status VARCHAR
                )
            '''))
            connection.commit()
            print("✅ Tabella 'technical_users' creata con successo.")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Tabella 'technical_users' già esistente.")
            else:
                print(f"❌ Errore tabella 'technical_users': {e}")
            connection.rollback()

        # Add foreign key to spotted_messages
        try:
            connection.execute(text('ALTER TABLE spotted_messages ADD COLUMN technical_user_id VARCHAR REFERENCES technical_users(id)'))
            connection.commit()
            print("✅ Colonna 'technical_user_id' aggiunta con successo.")
        except Exception as e:
            if "duplicate column name" in str(e) or "already exists" in str(e):
                print("ℹ️  Colonna 'technical_user_id' già esistente.")
            else:
                print(f"❌ Errore colonna 'technical_user_id': {e}")
            connection.rollback()

        # Add message_type and title columns
        try:
            # Add columns one by one to avoid SQL syntax issues
            connection.execute(text("ALTER TABLE spotted_messages ADD COLUMN message_type VARCHAR"))
            connection.commit()
            connection.execute(text("UPDATE spotted_messages SET message_type = 'spotted' WHERE message_type IS NULL"))
            connection.commit()
            connection.execute(text("ALTER TABLE spotted_messages ADD COLUMN title VARCHAR"))
            connection.commit()
            print("✅ Colonne 'message_type' e 'title' aggiunte con successo.")
        except Exception as e:
            if "duplicate column name" in str(e) or "already exists" in str(e):
                print("ℹ️  Colonne 'message_type' e 'title' già esistenti.")
            else:
                print(f"❌ Errore colonne message_type/title: {e}")
            connection.rollback()

        # Create daily_post_settings table
        try:
            connection.execute(text('''
                CREATE TABLE daily_post_settings (
                    id INTEGER PRIMARY KEY,
                    enabled INTEGER DEFAULT 1,
                    post_time VARCHAR DEFAULT '20:00',
                    style VARCHAR DEFAULT 'carousel',
                    max_messages INTEGER DEFAULT 20,
                    title_template VARCHAR DEFAULT '🌟 Spotted del giorno {date} 🌟\n\nEcco tutti gli spotted della giornata! 💫',
                    hashtag_template VARCHAR DEFAULT '#spotted #instaspotter #dailyrecap',
                    last_run TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            connection.commit()
            print("✅ Tabella 'daily_post_settings' creata con successo.")

            # Insert default settings
            connection.execute(text('''
                INSERT INTO daily_post_settings (enabled, post_time, style, max_messages, title_template, hashtag_template)
                VALUES (1, '20:00', 'carousel', 20, '🌟 Spotted del giorno {date} 🌟\n\nEcco tutti gli spotted della giornata! 💫', '#spotted #instaspotter #dailyrecap')
            '''))
            connection.commit()
            print("✅ Impostazioni predefinite per il post giornaliero inserite.")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Tabella 'daily_post_settings' già esistente.")
            else:
                print(f"❌ Errore tabella 'daily_post_settings': {e}")
            connection.rollback()

        # Correggi valori message_type errati (enum aspetta 'SPOTTED' maiuscolo, non 'spotted' minuscolo)
        try:
            # Aggiorna tutti i valori minuscoli al formato corretto maiuscolo
            connection.execute(text("UPDATE spotted_messages SET message_type = 'SPOTTED' WHERE LOWER(message_type) = 'spotted'"))
            connection.execute(text("UPDATE spotted_messages SET message_type = 'INFO' WHERE LOWER(message_type) = 'info'"))
            # Imposta default per valori nulli
            connection.execute(text("UPDATE spotted_messages SET message_type = 'SPOTTED' WHERE message_type IS NULL OR message_type = ''"))
            connection.commit()
            print("✅ Corretti valori message_type al formato enum corretto (maiuscolo)")
        except Exception as e:
            print(f"ℹ️ Colonna message_type già corretta: {e}")
            try:
                connection.rollback()
            except:
                pass

    print("\n🎉 Migrazione database completata con successo!")

if __name__ == "__main__":
    run_migration()
