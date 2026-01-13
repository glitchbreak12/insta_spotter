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
                    ai_model VARCHAR DEFAULT 'gemini',
                    last_run TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            connection.commit()
            print("✅ Tabella 'daily_post_settings' creata con successo.")

            # Insert default settings
            connection.execute(text('''
                INSERT INTO daily_post_settings (enabled, post_time, style, max_messages, title_template, hashtag_template, ai_model)
                VALUES (1, '20:00', 'carousel', 20, '🌟 Spotted del giorno {date} 🌟\n\nEcco tutti gli spotted della giornata! 💫', '#spotted #instaspotter #dailyrecap', 'gemini')
            '''))
            connection.commit()
            print("✅ Impostazioni predefinite per il post giornaliero inserite.")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Tabella 'daily_post_settings' già esistente.")
                # Try to add ai_model column if it doesn't exist
                try:
                    connection.execute(text('ALTER TABLE daily_post_settings ADD COLUMN ai_model VARCHAR DEFAULT \'gemini\''))
                    connection.commit()
                    print("✅ Colonna 'ai_model' aggiunta alla tabella 'daily_post_settings'.")
                except Exception as col_e:
                    if "duplicate column name" in str(col_e) or "already exists" in str(col_e):
                        print("ℹ️  Colonna 'ai_model' già esistente.")
                    else:
                        print(f"ℹ️  Colonna 'ai_model' non aggiunta: {col_e}")
                    connection.rollback()
            else:
                print(f"❌ Errore tabella 'daily_post_settings': {e}")
            connection.rollback()

        # Create daily_posts table
        try:
            connection.execute(text('''
                CREATE TABLE daily_posts (
                    id INTEGER PRIMARY KEY,
                    title VARCHAR NOT NULL,
                    content VARCHAR NOT NULL,
                    hashtags VARCHAR DEFAULT '',
                    ai_model_used VARCHAR,
                    status VARCHAR DEFAULT 'draft',
                    scheduled_for TIMESTAMP,
                    published_at TIMESTAMP,
                    image_count INTEGER DEFAULT 0,
                    messages_count INTEGER DEFAULT 0,
                    error_message VARCHAR,
                    created_by VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_ids VARCHAR
                )
            '''))
            connection.commit()
            print("✅ Tabella 'daily_posts' creata con successo.")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Tabella 'daily_posts' già esistente.")
            else:
                print(f"❌ Errore tabella 'daily_posts': {e}")
            connection.rollback()

        # Correggi valori message_type errati (enum aspetta 'SPOTTED' maiuscolo, non 'spotted' minuscolo)
        try:
            # Aggiorna tutti i valori al formato corretto maiuscolo
            # Nota: su PostgreSQL non possiamo usare LOWER su enum, quindi usiamo valori diretti
            connection.execute(text("UPDATE spotted_messages SET message_type = 'SPOTTED' WHERE message_type::text = 'spotted'"))
            connection.execute(text("UPDATE spotted_messages SET message_type = 'INFO' WHERE message_type::text = 'info'"))
            # Imposta default per valori nulli o non validi
            connection.execute(text("UPDATE spotted_messages SET message_type = 'SPOTTED' WHERE message_type IS NULL OR message_type::text = ''"))
            connection.commit()
            print("✅ Corretti valori message_type al formato enum corretto (maiuscolo)")
        except Exception as e:
            print(f"ℹ️ Colonna message_type già corretta: {e}")
            try:
                connection.rollback()
            except:
                pass

        # Create AI Config table
        try:
            connection.execute(text('''
                CREATE TABLE ai_config (
                    id INTEGER PRIMARY KEY,
                    enabled INTEGER DEFAULT 1,
                    selected_model VARCHAR DEFAULT 'gemini',
                    gemini_api_key VARCHAR,
                    grok_api_key VARCHAR,
                    local_model_path VARCHAR,
                    moderation_enabled INTEGER DEFAULT 1,
                    auto_approve_threshold REAL DEFAULT 0.8,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            connection.commit()
            print("✅ Tabella 'ai_config' creata con successo.")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Tabella 'ai_config' già esistente.")
            else:
                print(f"❌ Errore tabella 'ai_config': {e}")
            connection.rollback()

    print("\n🎉 Migrazione database completata con successo!")

if __name__ == "__main__":
    run_migration()
