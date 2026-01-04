from sqlalchemy import create_engine, text
from config import settings

def run_migration():
    engine = create_engine(settings.database.db_url)
    print("--- Avvio Migrazione Database ---")
    with engine.connect() as connection:
        # Migrate media_pk column
        try:
            print("Aggiungo la colonna 'media_pk' alla tabella 'spotted_messages'...")
            connection.execute(text('ALTER TABLE spotted_messages ADD COLUMN media_pk VARCHAR'))
            connection.commit()
            print("Colonna 'media_pk' aggiunta con successo.")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("La colonna 'media_pk' esiste già. Nessuna azione necessaria.")
            else:
                print(f"Errore durante l'aggiunta della colonna 'media_pk': {e}")
            connection.rollback() # Rollback in case of other errors

        # Migrate gemini_analysis column
        try:
            print("Aggiungo la colonna 'gemini_analysis' alla tabella 'spotted_messages'...")
            connection.execute(text('ALTER TABLE spotted_messages ADD COLUMN gemini_analysis VARCHAR'))
            connection.commit()
            print("Colonna 'gemini_analysis' aggiunta con successo.")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("La colonna 'gemini_analysis' esiste già. Nessuna azione necessaria.")
            else:
                print(f"Errore durante l'aggiunta della colonna 'gemini_analysis': {e}")
            connection.rollback() # Rollback in case of other errors

    print("Migrazione database completata.")

if __name__ == "__main__":
    run_migration()
