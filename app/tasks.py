from app.ai.gemini_moderator import GeminiModerator, ModerationResult
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import SessionLocal, SpottedMessage, MessageStatus
from app.image.generator import ImageGenerator
from app.bot.poster import InstagramBot

# --- Tasks di Moderazione ---

def moderate_message_task(message_id: int):
    """
    Task in background per analizzare un messaggio con l'IA, salvare il risultato
    e aggiornare lo stato del messaggio in base alla decisione.
    """
    db = SessionLocal()
    try:
        print(f"--- [TASK] Avvio moderazione AI per messaggio ID: {message_id} ---")
        message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
        
        if not message:
            print(f"--- [TASK] ERRORE: Messaggio ID {message_id} non trovato. ---")
            return

        print(f"--- [TASK] Messaggio ID {message_id} trovato. Stato attuale: {message.status.name} ---")

        # Esegui l'analisi con il nuovo moderatore
        try:
            moderator = GeminiModerator()
            result: ModerationResult = moderator.moderate_message(message.text)
        except (ValueError, ImportError) as e:
            # GEMINI_API_KEY non configurata, pacchetto non installato, o modelli non disponibili
            error_msg = str(e)
            if any(keyword in error_msg for keyword in ["GEMINI_API_KEY", "google-generativeai", "non disponibili", "404", "not found"]):
                print(f"--- [TASK] Moderazione AI non disponibile: {error_msg[:200]}. Messaggio ID {message_id} rimane in PENDING per approvazione manuale. ---")
                message.gemini_analysis = "Moderazione AI non disponibile - richiede approvazione manuale"
                message.status = MessageStatus.PENDING
                db.commit()
                return
            else:
                raise
        except Exception as e:
            # Qualsiasi altro errore - disabilita moderazione AI per questo messaggio
            error_msg = str(e)
            print(f"--- [TASK] Errore moderazione AI: {error_msg[:200]}. Messaggio ID {message_id} rimane in PENDING. ---")
            message.gemini_analysis = f"Errore tecnico moderazione AI - richiede approvazione manuale"
            message.status = MessageStatus.PENDING
            db.commit()
            return
        
        print(f"--- [TASK] Risultato moderazione AI per ID {message_id}: {result} ---")

        # Salva la motivazione dell'IA nel campo di analisi
        message.gemini_analysis = result.reason
        
        # Aggiorna lo stato del messaggio in base alla decisione dell'IA
        if result.decision == "APPROVE":
            message.status = MessageStatus.APPROVED
        elif result.decision == "REJECT":
            message.status = MessageStatus.REJECTED
        else: # "PENDING" o in caso di errore
            message.status = MessageStatus.PENDING

        db.commit()
        print(f"--- [TASK] Moderazione AI per ID {message_id} completata. Decisione: {result.decision}, Stato: {message.status.name} ---")

    except Exception as e:
        print(f"--- [TASK] ERRORE CRITICO durante la moderazione per ID {message_id}: {e} ---")
        db.rollback()
    finally:
        db.close()


def post_daily_compilation(db: Session):
    """Recupera i messaggi approvati, genera le immagini e li pubblica come album."""
    print("--- DEBUG [TASK]: Avvio post_daily_compilation. ---")
    try:
        messages_to_post = db.query(SpottedMessage).filter(
            SpottedMessage.status == MessageStatus.APPROVED
        ).order_by(SpottedMessage.created_at).all()

        if not messages_to_post:
            print("--- DEBUG [TASK]: Nessun messaggio approvato trovato. Uscita. ---")
            return {"status": "noop", "message": "Nessun messaggio da pubblicare."}

        print(f"--- DEBUG [TASK]: Trovati {len(messages_to_post)} messaggi approvati. ---")
        image_paths = []
        image_generator = ImageGenerator()
        
        for msg in messages_to_post:
            print(f"--- DEBUG [TASK]: Processo messaggio ID {msg.id}. ---")
            try:
                output_filename = f"spotted_{msg.id}_{int(datetime.now().timestamp())}.png"
                print(f"--- DEBUG [TASK]: Generazione immagine: {output_filename} ---")
                path = image_generator.from_text(msg.text, output_filename)
                if path:
                    print(f"--- DEBUG [TASK]: Immagine generata con successo: {path} ---")
                    image_paths.append(path)
                else:
                    raise Exception("Image generator returned None.")
            except Exception as e:
                print(f"--- DEBUG [TASK]: ERRORE generazione immagine per ID {msg.id}: {e} ---")
                msg.status = MessageStatus.FAILED
                msg.error_message = f"Errore generazione per album: {e}"
                db.commit()

        if not image_paths:
            print("--- DEBUG [TASK]: Generazione immagini fallita per tutti i messaggi. Uscita. ---")
            return {"status": "fail", "message": "Nessuna immagine generata."}

        print(f"--- DEBUG [TASK]: Inizio pubblicazione album con {len(image_paths)} immagini. ---")
        insta_bot = InstagramBot()
        caption = f"Spotted del giorno {datetime.now().strftime('%d/%m/%Y')}! ✨\n\n#spotted #instaspotter #confessioni"
        media_pk = insta_bot.post_album(image_paths, caption)
        
        if not media_pk:
            raise Exception("InstagramBot.post_album ha restituito False o None.")

        print(f"--- DEBUG [TASK]: Pubblicazione album riuscita. Aggiornamento stato messaggi. ---")
        # Aggiorna lo stato di tutti i messaggi pubblicati con successo
        for msg in messages_to_post:
            # Controlla se l'immagine corrispondente è stata generata
            if any(f"spotted_{msg.id}_" in path for path in image_paths):
                msg.status = MessageStatus.POSTED
                msg.posted_at = datetime.utcnow()
                msg.error_message = None
                msg.media_pk = str(media_pk) # Salva il PK dell'album per ogni messaggio
        db.commit()
        print("--- DEBUG [TASK]: Task completato con successo. ---")
        return {"status": "success", "message": f"Album con {len(image_paths)} immagini pubblicato."}

    except Exception as e:
        print(f"--- DEBUG [TASK]: ERRORE CRITICO nel task: {e} ---")
        return {"status": "error", "message": str(e)}
