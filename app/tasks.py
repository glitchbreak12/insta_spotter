from sqlalchemy.orm import Session
from datetime import datetime
from app.database import SessionLocal, SpottedMessage, MessageStatus
from app.image.generator import ImageGenerator

# Import InstagramBot come condizionale
try:
    from app.bot.poster import InstagramBot
    INSTAGRAM_BOT_AVAILABLE = True
except ImportError:
    INSTAGRAM_BOT_AVAILABLE = False
    InstagramBot = None

# --- Tasks semplificati ---

# --- Info Card Tasks ---

def publish_info_card_task(card_id: int, db_session=None):
    """
    Pubblica una info card come storia su Instagram.
    """
    try:
        print(f"--- DEBUG [INFO CARD]: Pubblicazione info card ID {card_id} ---")

        # Usa la sessione passata o creane una nuova
        db = db_session or SessionLocal()
        should_close = db_session is None

        try:
            # Trova la info card
            from app.database import MessageType
            info_card = db.query(SpottedMessage).filter(
                SpottedMessage.id == card_id,
                SpottedMessage.message_type == MessageType.INFO
            ).first()

            if not info_card:
                print(f"--- DEBUG [INFO CARD]: Info card {card_id} non trovata ---")
                return {"status": "error", "message": "Info card non trovata"}

            print(f"--- DEBUG [INFO CARD]: Pubblicando '{info_card.title}' ---")

            # Genera immagine con template info
            import time
            generator = ImageGenerator()
            image_path = generator.from_text(
                info_card.text,
                f"info_card_{card_id}_{int(time.time())}.png",
                card_id,
                message_type="info",
                title=info_card.title
            )

            if not image_path:
                print("--- DEBUG [INFO CARD]: ERRORE generazione immagine ---")
                info_card.error_message = "Errore generazione immagine"
                if should_close:
                    db.commit()
                return {"status": "error", "message": "Errore generazione immagine"}

            print(f"--- DEBUG [INFO CARD]: Immagine generata: {image_path} ---")

            # Pubblica come storia
            if not INSTAGRAM_BOT_AVAILABLE:
                print("--- DEBUG [INFO CARD]: ⚠️ Instagram bot non disponibile (simulazione) ---")
                # Aggiorna il database anche in simulazione
                from datetime import datetime
                info_card.posted_at = datetime.utcnow()
                info_card.media_pk = f"simulated_{card_id}"
                if should_close:
                    db.commit()
                return {"status": "simulated", "message": f"Info card '{info_card.title}' simulata come pubblicata"}

            try:
                bot = InstagramBot()
                media_pk = bot.post_story(image_path, f"📢 {info_card.title}")

                if media_pk:
                    print(f"--- DEBUG [INFO CARD]: Info card pubblicata con successo! Media PK: {media_pk} ---")
                    # Aggiorna il database con successo
                    from datetime import datetime
                    info_card.posted_at = datetime.utcnow()
                    info_card.media_pk = str(media_pk)
                    if should_close:
                        db.commit()
                    return {"status": "success", "message": f"Info card '{info_card.title}' pubblicata", "media_pk": media_pk}
                else:
                    print("--- DEBUG [INFO CARD]: ERRORE pubblicazione ---")
                    info_card.error_message = "Errore pubblicazione Instagram"
                    if should_close:
                        db.commit()
                    return {"status": "error", "message": "Errore pubblicazione Instagram"}

            except Exception as e:
                print(f"--- DEBUG [INFO CARD]: ERRORE Instagram: {e} ---")
                info_card.error_message = f"Errore Instagram: {str(e)}"
                if should_close:
                    db.commit()
                return {"status": "error", "message": f"Errore Instagram: {str(e)}"}

        finally:
            if should_close:
                db.close()

    except Exception as e:
        print(f"--- DEBUG [INFO CARD]: ERRORE CRITICO: {e} ---")
        return {"status": "error", "message": str(e)}