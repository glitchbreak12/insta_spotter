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

def moderate_message_task(message_id: int):
    """
    Task in background per analizzare un messaggio con l'AI selezionata,
    salvare il risultato e aggiornare lo stato del messaggio.
    """
    import time
    print(f"--- [TASK] [{time.time()}] Avvio moderazione AI per messaggio ID: {message_id} ---")

    db = SessionLocal()
    try:
        print(f"--- [TASK] [{time.time()}] Query messaggio ID: {message_id} ---")
        message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()

        if not message:
            print(f"--- [TASK] [{time.time()}] ERRORE: Messaggio ID {message_id} non trovato nel database ---")
            return

        print(f"--- [TASK] [{time.time()}] Messaggio ID {message_id} trovato. Stato attuale: {message.status.name} ---")
        print(f"--- [TASK] [{time.time()}] Testo messaggio: '{message.text[:50]}...' ---")

        # Recupera configurazione AI
        from app.database import get_ai_config
        ai_config = get_ai_config(db)

        if not ai_config or not ai_config.moderation_enabled or ai_config.selected_model == "disabled":
            print(f"--- [TASK] [{time.time()}] Moderazione AI disabilitata per ID {message_id} ---")
            message.gemini_analysis = "Moderazione AI disabilitata - approvato automaticamente"
            message.status = MessageStatus.APPROVED
            db.commit()
            return

        # Crea il moderatore appropriato
        from app.ai.moderator import AIModeratorFactory
        kwargs = {}

        if ai_config.selected_model == "gemini":
            kwargs['api_key'] = ai_config.gemini_api_key
        elif ai_config.selected_model == "grok":
            kwargs['api_key'] = ai_config.grok_api_key
        elif ai_config.selected_model == "local":
            kwargs['model_path'] = ai_config.local_model_path

        moderator = AIModeratorFactory.create_moderator(ai_config.selected_model.value, **kwargs)

        if not moderator or not moderator.is_available():
            print(f"--- [TASK] [{time.time()}] Moderatore {ai_config.selected_model.value} non disponibile per ID {message_id} ---")
            message.gemini_analysis = f"Moderatore {ai_config.selected_model.value} non disponibile - approvato automaticamente"
            message.status = MessageStatus.APPROVED
            db.commit()
            return

        print(f"--- [TASK] [{time.time()}] Usando moderatore: {ai_config.selected_model.value} ---")

        # Esegui la moderazione
        try:
            result = moderator.moderate_message(message.text)

            print(f"--- [TASK] Risultato moderazione AI per ID {message_id}: {result} ---")

            # Salva la motivazione dell'AI nel campo di analisi
            message.gemini_analysis = result.reason

            # Aggiorna lo stato del messaggio in base alla decisione
            if result.decision == "APPROVE":
                message.status = MessageStatus.APPROVED
            elif result.decision == "REJECT":
                message.status = MessageStatus.REJECTED
            else: # "PENDING" o in caso di errore
                message.status = MessageStatus.PENDING

            db.commit()
            print(f"--- [TASK] Moderazione AI per ID {message_id} completata. Decisione: {result.decision}, Stato: {message.status.name} ---")

        except Exception as e:
            import time
            error_msg = str(e)
            print(f"--- [TASK] [{time.time()}] ECCEZIONE in moderazione ID {message_id}: {error_msg[:300]} ---")

            # In caso di errore, approva comunque per sicurezza
            message.gemini_analysis = f"Errore AI ({error_msg[:100]}) - approvato automaticamente per sicurezza"
            message.status = MessageStatus.APPROVED
            try:
                db.commit()
                print(f"--- [TASK] [{time.time()}] Database commit riuscito per ID {message_id} ---")
            except Exception as db_error:
                print(f"--- [TASK] [{time.time()}] ERRORE database commit: {db_error} ---")
                db.rollback()

    except Exception as e:
        import time
        print(f"--- [TASK] [{time.time()}] ERRORE CRITICO durante la moderazione per ID {message_id}: {e} ---")
        try:
            db.rollback()
            # In caso di errore critico, approva comunque il messaggio per sicurezza
            message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
            if message and message.status == MessageStatus.PENDING:
                message.status = MessageStatus.APPROVED
                message.gemini_analysis = "Errore critico - approvato automaticamente per sicurezza"
                db.commit()
                print(f"--- [TASK] [{time.time()}] Messaggio ID {message_id} approvato automaticamente dopo errore critico ---")
        except Exception as rollback_error:
            print(f"--- [TASK] [{time.time()}] Anche il rollback è fallito: {rollback_error} ---")
    finally:
        db.close()

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

        # Controlla se Instagram bot è disponibile
        if not INSTAGRAM_BOT_AVAILABLE:
            print("--- DEBUG [TASK]: ⚠️ Instagram bot non disponibile (instagrapi non installato). Pubblicazione saltata. ---")
            # Aggiorna comunque lo stato dei messaggi come pubblicati (per non bloccarli)
            for msg in messages_to_post:
                msg.status = MessageStatus.POSTED
                msg.media_pk = "instagram_bot_unavailable"
            db.commit()
            print(f"--- DEBUG [TASK]: Messaggi marcati come pubblicati (bot non disponibile). ---")
            return {"status": "success", "message": f"Album simulato pubblicato (bot non disponibile). {len(messages_to_post)} messaggi."}

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

# --- Daily Post Task ---

def daily_post_task():
    """
    Task giornaliero che pubblica TUTTI gli spotted della giornata come carousel Instagram.
    Crea una card introduttiva, tutte le card spotted, e una card finale.
    """
    try:
        print("--- DEBUG [DAILY POST]: Avvio task giornaliero completo ---")

        db = SessionLocal()
        try:
            # Recupera impostazioni del daily post
            from app.database import get_daily_post_settings, mark_daily_post_run, get_todays_messages, update_daily_post_settings, MessageType
            settings = get_daily_post_settings(db)

            # Se non esistono impostazioni, creane di default abilitate
            if not settings:
                print("--- DEBUG [DAILY POST]: Creazione impostazioni daily post di default ---")
                settings = update_daily_post_settings(
                    db=db,
                    enabled=True,
                    post_time="20:00",
                    style="carousel",
                    max_messages=50,  # Aumentato per gestire più messaggi
                    title_template="🌟 Spotted del giorno {date} 🌟\n\nEcco tutti gli spotted della giornata! 💫",
                    hashtag_template="#spotted #instaspotter #dailyrecap",
                    ai_model="gemini"
                )

            # If the daily post settings exist but are disabled, bail out early
            if settings and getattr(settings, 'enabled', 1) == 0:
                print("--- DEBUG [DAILY POST]: Daily post disabilitato ---")
                return {"status": "disabled", "message": "Daily post disabilitato"} 

            # Verifica se abbiamo già pubblicato oggi
            from datetime import datetime, time
            today_start = datetime.combine(datetime.utcnow().date(), time.min)
            if settings and settings.last_run and settings.last_run >= today_start:
                print("--- DEBUG [DAILY POST]: Post giornaliero già pubblicato oggi ---")
                return {"status": "already_run", "message": "Già pubblicato oggi"}

            # Recupera TUTTI i messaggi APPROVED di oggi (solo SPOTTED, non INFO)
            messages = db.query(SpottedMessage).filter(
                SpottedMessage.status == MessageStatus.APPROVED,
                SpottedMessage.message_type == MessageType.SPOTTED,  # Solo spotted, non info cards
                SpottedMessage.created_at >= today_start
            ).order_by(SpottedMessage.created_at).limit(settings.max_messages).all()

            if not messages:
                print("--- DEBUG [DAILY POST]: Nessun messaggio spotted approvato di oggi ---")
                return {"status": "no_messages", "message": "Nessun messaggio spotted approvato oggi"}

            print(f"--- DEBUG [DAILY POST]: Trovati {len(messages)} messaggi spotted approvati di oggi ---")

            # Genera carousel: usa il metodo create_daily_carousel che esiste
            generator = ImageGenerator()
            today = datetime.utcnow().strftime("%d/%m/%Y")
            base_filename = f"daily_carousel_{datetime.utcnow().strftime('%Y%m%d')}"

            # Crea carousel con tutti gli spotted
            image_paths = generator.create_daily_carousel(messages, base_filename, today)            
            if not image_paths:
                print("--- DEBUG [DAILY POST]: ERRORE nella generazione del carousel ---")
                return {"status": "error", "message": "Errore generazione carousel"}

            # Pubblica su Instagram come CAROUSEL
            if not INSTAGRAM_BOT_AVAILABLE:
                print("--- DEBUG [DAILY POST]: ⚠️ Instagram bot non disponibile (simulazione) ---")
                # Simula pubblicazione per test
                mark_daily_post_run(db)
                return {"status": "simulated", "message": f"Simulato carousel giornaliero completo con {len(messages)} spotted"}

            try:
                bot = InstagramBot()

                # Crea caption completa con titolo e hashtag
                title = settings.title_template.format(date=today)
                full_caption = f"{title}\n\n{settings.hashtag_template}"

                print(f"--- DEBUG [DAILY POST]: Pubblicazione carousel con {len(image_paths)} immagini ---")
                media_pk = bot.post_carousel(image_paths, full_caption)

                if media_pk:
                    print(f"--- DEBUG [DAILY POST]: Carousel giornaliero pubblicato con successo! Media PK: {media_pk} ---")
                    mark_daily_post_run(db)

                    # Salva info del post pubblicato nel database per cronologia
                    from app.database import create_daily_post
                    post_record = create_daily_post(
                        db=db,
                        title=title,
                        content=f"Carousel giornaliero con {len(messages)} spotted del {today}",
                        hashtags=settings.hashtag_template,
                        ai_model_used=None,  # Non usiamo AI qui
                        created_by="system"
                    )

                    return {
                        "status": "success",
                        "message": f"Pubblicato carousel giornaliero completo con {len(messages)} spotted",
                        "media_pk": media_pk,
                        "image_count": len(image_paths),
                        "spotted_count": len(messages)
                    }
                else:
                    print("--- DEBUG [DAILY POST]: ERRORE nella pubblicazione del carousel ---")
                    return {"status": "error", "message": "Errore pubblicazione carousel Instagram"}

            except Exception as e:
                print(f"--- DEBUG [DAILY POST]: ERRORE pubblicazione Instagram: {e} ---")
                return {"status": "error", "message": f"Errore Instagram: {str(e)}"}

        finally:
            db.close()

    except Exception as e:
        print(f"--- DEBUG [DAILY POST]: ERRORE CRITICO nel daily post task: {e} ---")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

def test_daily_post():
    """
    Funzione di test per il daily post - può essere chiamata dall'admin.
    """
    print("--- DEBUG [DAILY POST TEST]: Avvio test daily post ---")
    result = daily_post_task()
    print(f"--- DEBUG [DAILY POST TEST]: Risultato: {result} ---")
    return result

# --- Info Card Publishing Task ---

def publish_single_info_card(card_id: int):
    """
    Pubblica una singola info card come storia su Instagram.
    Questa è la funzione chiamata dal background task.
    """
    try:
        print(f"--- DEBUG [INFO CARD BG TASK]: Pubblicazione info card ID {card_id} ---")

        # Chiama la funzione esistente
        result = publish_info_card_task(card_id)

        if result.get("status") == "success":
            print(f"--- DEBUG [INFO CARD BG TASK]: Info card {card_id} pubblicata con successo ---")
        else:
            print(f"--- DEBUG [INFO CARD BG TASK]: ERRORE pubblicazione info card {card_id}: {result.get('message')} ---")

        return result

    except Exception as e:
        print(f"--- DEBUG [INFO CARD BG TASK]: ERRORE CRITICO in background task: {e} ---")
        return {"status": "error", "message": str(e)}

# --- Daily Post Publishing Task ---

def publish_daily_post_task(post_id: int):
    """
    Pubblica un daily post su Instagram.
    """
    try:
        print(f"--- DEBUG [DAILY POST PUBLISH]: Pubblicazione daily post ID {post_id} ---")

        db = SessionLocal()
        try:
            # Recupera il daily post
            from app.database import get_daily_post_by_id
            post = get_daily_post_by_id(db, post_id)

            if not post:
                print(f"--- DEBUG [DAILY POST PUBLISH]: Daily post {post_id} non trovato ---")
                return {"status": "error", "message": "Daily post non trovato"}

            if post.status == "published":
                print(f"--- DEBUG [DAILY POST PUBLISH]: Daily post {post_id} già pubblicato ---")
                return {"status": "error", "message": "Daily post già pubblicato"}

            # Genera immagini dal contenuto del post
            generator = ImageGenerator()
            base_filename = f"daily_post_{post_id}_{int(datetime.now().timestamp())}"

            # Crea carousel dal contenuto del post
            image_paths = generator.create_daily_carousel_from_content(
                post.content,
                base_filename,
                title=post.title
            )

            if not image_paths:
                print("--- DEBUG [DAILY POST PUBLISH]: ERRORE generazione immagini ---")
                return {"status": "error", "message": "Errore generazione immagini"}

            print(f"--- DEBUG [DAILY POST PUBLISH]: Generate {len(image_paths)} immagini ---")

            # Pubblica su Instagram
            if not INSTAGRAM_BOT_AVAILABLE:
                print("--- DEBUG [DAILY POST PUBLISH]: ⚠️ Instagram bot non disponibile (simulazione) ---")
                # Aggiorna stato come pubblicato per simulazione
                from app.database import update_daily_post
                update_daily_post(db, post_id, status="published", published_at=datetime.utcnow())
                return {"status": "simulated", "message": f"Daily post '{post.title}' simulato come pubblicato"}

            try:
                bot = InstagramBot()
                full_caption = f"{post.title}\n\n{post.content}\n\n{post.hashtags}"

                if len(image_paths) == 1:
                    # Singola immagine
                    media_pk = bot.post_story(image_paths[0], full_caption)
                else:
                    # Carousel
                    media_pk = bot.post_carousel(image_paths, full_caption)

                if media_pk:
                    print(f"--- DEBUG [DAILY POST PUBLISH]: Daily post pubblicato con successo! Media PK: {media_pk} ---")
                    # Aggiorna stato del post
                    from app.database import update_daily_post
                    update_daily_post(db, post_id, status="published", published_at=datetime.utcnow())
                    return {"status": "success", "message": f"Daily post '{post.title}' pubblicato", "media_pk": media_pk}
                else:
                    print("--- DEBUG [DAILY POST PUBLISH]: ERRORE pubblicazione ---")
                    from app.database import update_daily_post
                    update_daily_post(db, post_id, status="failed", error_message="Errore pubblicazione Instagram")
                    return {"status": "error", "message": "Errore pubblicazione Instagram"}

            except Exception as e:
                print(f"--- DEBUG [DAILY POST PUBLISH]: ERRORE Instagram: {e} ---")
                from app.database import update_daily_post
                update_daily_post(db, post_id, status="failed", error_message=f"Errore Instagram: {str(e)}")
                return {"status": "error", "message": f"Errore Instagram: {str(e)}"}

        finally:
            db.close()

    except Exception as e:
        print(f"--- DEBUG [DAILY POST PUBLISH]: ERRORE CRITICO: {e} ---")
        return {"status": "error", "message": str(e)}
