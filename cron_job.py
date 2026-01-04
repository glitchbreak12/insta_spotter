from worker import process_single_story

if __name__ == "__main__":
    print("--- Avvio Cron Job: Processo una storia singola ---")
    try:
        process_single_story()
        print("--- Fine Cron Job: Esecuzione completata ---")
    except Exception as e:
        print(f"--- ERRORE nel Cron Job: {e} ---")
