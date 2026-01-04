import time
import schedule
import random
from datetime import datetime, time as time_obj
from sqlalchemy.orm import Session
from app.database import SessionLocal, SpottedMessage, MessageStatus
from app.image.generator import ImageGenerator
from app.bot.poster import InstagramBot
from config import settings

from app.tasks import post_daily_compilation

def get_db():
    return SessionLocal()

def process_single_story():
    """Task per pubblicare una singola storia approvata."""
    time.sleep(random.randint(5, 15))
    print("--- DEBUG [WORKER]: Avvio controllo per storia singola... ---", flush=True)
    db = get_db()
    try:
        message_to_post = db.query(SpottedMessage).filter(
            SpottedMessage.status == MessageStatus.APPROVED
        ).order_by(SpottedMessage.created_at).first()

        if not message_to_post:
            # Questo è normale, non stampiamo nulla per non intasare i log
            return

        print(f"--- DEBUG [WORKER]: Trovato messaggio ID {message_to_post.id}. Inizio processamento. ---", flush=True)
        try:
            image_generator = ImageGenerator()
            output_filename = f"spotted_{message_to_post.id}_{int(datetime.now().timestamp())}.png"
            print(f"--- DEBUG [WORKER]: Generazione immagine {output_filename}... ---", flush=True)
            image_path = image_generator.from_text(
                message_to_post.text, 
                output_filename,
                message_to_post.id
            )
            if not image_path: raise Exception("Generazione immagine ha restituito None.")
            print(f"--- DEBUG [WORKER]: Immagine generata: {image_path}. Inizio pubblicazione... ---", flush=True)

            insta_bot = InstagramBot()
            result = insta_bot.post_story(image_path)
            
            if not result:
                raise Exception("InstagramBot.post_story ha restituito False o None.")
            
            # Extract media_pk from result
            if isinstance(result, dict) and 'media' in result:
                media_pk = result['media']
            elif isinstance(result, str):
                media_pk = result
            else:
                raise Exception(f"Formato risultato non valido: {result}")
                
            print(f"--- DEBUG [WORKER]: Pubblicazione riuscita. Media PK: {media_pk}. Aggiorno stato a POSTED. ---", flush=True)

            message_to_post.status = MessageStatus.POSTED
            message_to_post.posted_at = datetime.utcnow()
            message_to_post.error_message = None
            message_to_post.media_pk = str(media_pk)
        except Exception as e:
            print(f"--- DEBUG [WORKER]: ERRORE durante processamento ID {message_to_post.id}: {e} ---", flush=True)
            message_to_post.status = MessageStatus.FAILED
            message_to_post.error_message = str(e)
        finally:
            db.commit()
            print(f"--- DEBUG [WORKER]: Commit eseguito per ID {message_to_post.id}. ---", flush=True)
    finally:
        db.close()

def scheduled_daily_compilation():
    """Esegue il task giornaliero e chiude la sessione db."""
    time.sleep(random.randint(5, 15))
    print("--- DEBUG [WORKER]: Avvio posting giornaliero alle 20:00 ---", flush=True)
    db = get_db()
    try:
        # Post all approved messages from today
        today = datetime.utcnow().date()
        end_of_day = datetime.combine(today, time_obj(23, 59, 59))
        messages_to_post = db.query(SpottedMessage).filter(
            SpottedMessage.status == MessageStatus.APPROVED,
            SpottedMessage.created_at >= today,
            SpottedMessage.created_at < end_of_day
        ).order_by(SpottedMessage.created_at).all()
        
        print(f"--- DEBUG [WORKER]: Trovati {len(messages_to_post)} messaggi da pubblicare oggi ---", flush=True)
        
        for message in messages_to_post:
            try:
                time.sleep(random.randint(10, 30))
                print(f"--- DEBUG [WORKER]: Pubblicazione messaggio ID {message.id} ---", flush=True)
                image_generator = ImageGenerator()
                output_filename = f"spotted_{message.id}_{int(datetime.now().timestamp())}.png"
                image_path = image_generator.from_text(
                    message.text, 
                    output_filename,
                    message.id
                )
                
                if not image_path:
                    raise Exception("Generazione immagine fallita")
                
                insta_bot = InstagramBot()
                result = insta_bot.post_story(image_path)
                
                if not result:
                    raise Exception("Posting Instagram fallito")
                
                # Extract media_pk
                if isinstance(result, dict) and 'media' in result:
                    media_pk = result['media']
                elif isinstance(result, str):
                    media_pk = result
                else:
                    raise Exception(f"Formato risultato non valido: {result}")
                
                message.status = MessageStatus.POSTED
                message.posted_at = datetime.utcnow()
                message.error_message = None
                message.media_pk = str(media_pk)
                
                print(f"--- DEBUG [WORKER]: Messaggio ID {message.id} pubblicato con successo ---", flush=True)
                
            except Exception as e:
                print(f"--- DEBUG [WORKER]: Errore pubblicazione ID {message.id}: {e} ---", flush=True)
                message.status = MessageStatus.FAILED
                message.error_message = str(e)
        
        db.commit()
        print(f"--- DEBUG [WORKER]: Posting giornaliero completato ---", flush=True)
        
    except Exception as e:
        print(f"--- DEBUG [WORKER]: Errore nel posting giornaliero: {e} ---", flush=True)
    finally:
        db.close()

def main():
    """Avvia lo scheduler del worker."""
    print("--- Avvio del Worker di InstaSpotter ---", flush=True)
    
    # Job per le storie singole (ogni tot secondi)
    story_interval = settings.automation.check_interval_seconds
    print(f"Controllo per storie singole ogni {story_interval} secondi.", flush=True)
    schedule.every(story_interval).seconds.do(process_single_story)

    # Job per il riepilogo giornaliero (ogni giorno alle 20:00)
    daily_post_time = "20:00"
    print(f"Riepilogo giornaliero programmato per le {daily_post_time}.", flush=True)
    schedule.every().day.at(daily_post_time).do(scheduled_daily_compilation)

    print("--- Worker in esecuzione ---", flush=True)
    # Esegui subito i task all'avvio per non aspettare il primo intervallo
    process_single_story()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()