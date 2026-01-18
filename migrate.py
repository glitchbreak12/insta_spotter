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

        # Migrate ip_address column
        try:
            connection.execute(text('ALTER TABLE spotted_messages ADD COLUMN ip_address VARCHAR'))
            connection.commit()
            print("✅ Colonna 'ip_address' aggiunta con successo.")
        except Exception as e:
            if "duplicate column name" in str(e) or "already exists" in str(e):
                print("ℹ️  Colonna 'ip_address' già esistente.")
            else:
                print(f"❌ Errore colonna 'ip_address': {e}")
            connection.rollback()

        # Create technical_users table
        try:
            connection.execute(text('''
                CREATE TABLE technical_users (
                    id VARCHAR PRIMARY KEY,
                    username VARCHAR,
                    password_hash VARCHAR,
                    role VARCHAR DEFAULT 'moderator',
                    first_seen_at TIMESTAMP,
                    last_seen_at TIMESTAMP,
                    trust_score INTEGER DEFAULT 100,
                    status VARCHAR DEFAULT 'active',
                    created_by VARCHAR,
                    is_active INTEGER DEFAULT 1
                )
            '''))
            connection.commit()
            print("✅ Tabella 'technical_users' creata con successo.")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Tabella 'technical_users' già esistente.")
                # Try to add missing columns
                missing_columns = [
                    ('username', 'VARCHAR'),
                    ('password_hash', 'VARCHAR'),
                    ('role', "VARCHAR DEFAULT 'moderator'"),
                    ('created_by', 'VARCHAR'),
                    ('is_active', 'INTEGER DEFAULT 1')
                ]
                for col_name, col_type in missing_columns:
                    try:
                        connection.execute(text(f'ALTER TABLE technical_users ADD COLUMN {col_name} {col_type}'))
                        connection.commit()
                        print(f"✅ Colonna '{col_name}' aggiunta alla tabella 'technical_users'.")
                    except Exception as col_e:
                        if "duplicate column name" in str(col_e) or "already exists" in str(col_e):
                            print(f"ℹ️  Colonna '{col_name}' già esistente.")
                        else:
                            print(f"ℹ️  Colonna '{col_name}' non aggiunta: {col_e}")
                        connection.rollback()
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

        # Add ai_model column separately
        try:
            connection.execute(text('ALTER TABLE daily_post_settings ADD COLUMN ai_model VARCHAR DEFAULT \'gemini\''))
            connection.commit()
            print("✅ Colonna 'ai_model' aggiunta alla tabella 'daily_post_settings'.")
        except Exception as e:
            if "duplicate column name" in str(e) or "already exists" in str(e):
                print("ℹ️  Colonna 'ai_model' già esistente.")
            else:
                print(f"ℹ️  Colonna 'ai_model' non aggiunta: {e}")
            connection.rollback()

        # Create daily_posts table (semplificata, senza gestione stili)
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
                    message_ids VARCHAR,
                    images VARCHAR
                )
            '''))
            connection.commit()
            print("✅ Tabella 'daily_posts' creata con successo (senza gestione stili).")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Tabella 'daily_posts' già esistente.")
                # Rimuovi colonne di stile se esistono
                for column in ['post_style', 'style_config']:
                    try:
                        connection.execute(text(f'ALTER TABLE daily_posts DROP COLUMN {column}'))
                        connection.commit()
                        print(f"✅ Colonna '{column}' rimossa dalla tabella 'daily_posts'.")
                    except Exception as drop_e:
                        if "no such column" in str(drop_e).lower():
                            print(f"ℹ️  Colonna '{column}' non esistente.")
                        else:
                            print(f"ℹ️  Colonna '{column}' non rimossa: {drop_e}")
                        connection.rollback()

                # Assicurati che la colonna images esista
                try:
                    connection.execute(text('ALTER TABLE daily_posts ADD COLUMN images VARCHAR'))
                    connection.commit()
                    print("✅ Colonna 'images' aggiunta alla tabella 'daily_posts'.")
                except Exception as col_e:
                    if "duplicate column name" in str(col_e) or "already exists" in str(col_e):
                        print("ℹ️  Colonna 'images' già esistente.")
                    else:
                        print(f"ℹ️  Colonna 'images' non aggiunta: {col_e}")
                    connection.rollback()
            else:
                print(f"❌ Errore tabella 'daily_posts': {e}")
            connection.rollback()

        # Rimuovi tabella style_configs se esiste (rimozione gestione stili)
        try:
            connection.execute(text('DROP TABLE IF EXISTS style_configs'))
            connection.commit()
            print("✅ Tabella 'style_configs' rimossa con successo (gestione stili eliminata).")
        except Exception as e:
            print(f"ℹ️  Tabella 'style_configs' non rimossa: {e}")
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

        # Create system_settings table for persistent settings
        try:
            connection.execute(text('''
                CREATE TABLE system_settings (
                    id INTEGER PRIMARY KEY,
                    key VARCHAR UNIQUE NOT NULL,
                    value TEXT,
                    value_type VARCHAR DEFAULT 'string',
                    description VARCHAR,
                    category VARCHAR DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            connection.commit()
            print("✅ Tabella 'system_settings' creata con successo.")

            # Insert default settings
            default_settings = [
                ('maintenance_mode', '0', 'boolean', 'Modalità manutenzione abilitata', 'system'),
                ('max_messages_per_hour', '10', 'integer', 'Massimo messaggi per ora', 'limits'),
                ('session_timeout', '24', 'integer', 'Timeout sessione in ore', 'security'),
                ('instagram_username', '', 'string', 'Username Instagram', 'instagram'),
                ('instagram_password', '', 'string', 'Password Instagram', 'instagram'),
                ('gemini_api_key', '', 'string', 'API Key Google Gemini', 'ai'),
                ('ai_enabled', '1', 'boolean', 'AI abilitata', 'ai'),
                ('ai_moderation_enabled', '1', 'boolean', 'Moderazione AI abilitata', 'ai'),
                ('ai_model', 'gemini', 'string', 'Modello AI selezionato', 'ai'),
                ('ai_auto_approve_threshold', '0.8', 'float', 'Soglia approvazione automatica AI', 'ai'),
                ('daily_post_enabled', '1', 'boolean', 'Daily post abilitato', 'daily_post'),
                ('daily_post_time', '20:00', 'string', 'Orario daily post', 'daily_post'),
                ('daily_post_max_messages', '20', 'integer', 'Max messaggi per daily post', 'daily_post'),
                ('daily_post_title_template', '🌟 Spotted del giorno {date} 🌟\n\nEcco tutti gli spotted della giornata! 💫', 'string', 'Template titolo daily post', 'daily_post'),
                ('daily_post_hashtag_template', '#spotted #instaspotter #dailyrecap', 'string', 'Template hashtag daily post', 'daily_post'),
            ]

            for key, value, value_type, description, category in default_settings:
                try:
                    connection.execute(text('''
                        INSERT OR IGNORE INTO system_settings (key, value, value_type, description, category)
                        VALUES (?, ?, ?, ?, ?)
                    '''), (key, value, value_type, description, category))
                    connection.commit()
                except Exception as insert_e:
                    print(f"ℹ️  Impostazione '{key}' già esistente: {insert_e}")
                    connection.rollback()

            print("✅ Impostazioni predefinite inserite.")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Tabella 'system_settings' già esistente.")
            else:
                print(f"❌ Errore tabella 'system_settings': {e}")
            connection.rollback()

    print("\n🎉 Migrazione database completata con successo!")

if __name__ == "__main__":
    run_migration()
