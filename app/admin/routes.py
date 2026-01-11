from fastapi import APIRouter, Request, Depends, HTTPException, Form, Response, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db, SpottedMessage, MessageStatus, SessionLocal
from app.admin.security import authenticate_user, create_access_token, get_current_user
from config import settings # Import settings

# --- Configurazione ---

router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"]
)

templates = Jinja2Templates(directory="app/admin/templates")

# --- Rotte di Login / Logout ---

@router.get("/login", response_class=HTMLResponse, name="login_page")
def login_page(request: Request):
    """Mostra la pagina di login personalizzata."""
    return templates.TemplateResponse("login.html", {"request": request, "error": request.query_params.get("error")})

@router.post("/login")
def handle_login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    """Gestisce il login tramite form."""
    user = authenticate_user(username, password)
    if not user:
        # Ricarica la pagina di login con un messaggio di errore
        return RedirectResponse(url="/admin/login?error=Credenziali+non+valide", status_code=303)

    access_token = create_access_token(data={"sub": user})
    # Imposta il token in un cookie HttpOnly per sicurezza
    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="Lax")
    return response

@router.post("/logout")
def logout(response: Response):
    """Esegue il logout cancellando il cookie di sessione."""
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response

# --- Dipendenza per le rotte protette ---

async def get_authenticated_user(request: Request):
    """Controlla se l'utente è loggato. Se no, reindirizza a /login."""
    user = get_current_user(request=request)
    if not user:
        # For API endpoints, return None instead of RedirectResponse
        # The endpoint will check and raise HTTPException
        return None
    return user

import math
from pydantic import BaseModel
from typing import List

# --- New, simplified API endpoint for all dashboard data ---
@router.get("/api/dashboard-data")
def get_dashboard_data(db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    """
    A single, robust endpoint to fetch all data needed for the dashboard.
    This function ONLY reads data and builds a simple JSON response to avoid all previous errors.
    """
    print(f"--- [API] get_dashboard_data called, user: {user} ---")
    
    if not user or isinstance(user, RedirectResponse):
        print("--- [API] User not authenticated ---")
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        print("--- [API] Querying database for messages ---")
        # Fetch all messages, keeping it simple
        messages_query = db.query(SpottedMessage).order_by(SpottedMessage.created_at.desc()).limit(200).all()
        print(f"--- [API] Found {len(messages_query)} messages in database ---")

        # Manually build the response to ensure it's clean
        messages_data = []
        for msg in messages_query:
            try:
                messages_data.append({
                "id": msg.id,
                    "text": msg.text or "",
                    "status": msg.status.value if msg.status else "pending", # Safely get enum value
                    "created_at": msg.created_at.isoformat() if msg.created_at else datetime.utcnow().isoformat(), # Use ISO format for JS
                    "media_pk": msg.media_pk or None,
                    "admin_note": msg.admin_note or None,
                    "gemini_analysis": msg.gemini_analysis or None
                })
            except Exception as e:
                print(f"--- [API] Error processing message {msg.id}: {e} ---")
                continue
        
        print(f"--- [API] Returning {len(messages_data)} messages ---")
        
        # Return the clean data - always return a valid response even if empty
        return {
            "messages": messages_data,
            "total": len(messages_data),
            "status": "success"
        }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"--- CRITICAL ERROR in get_dashboard_data: {e} ---")
        print(f"--- Traceback: {error_trace} ---")
        # Return empty array instead of raising error to prevent frontend crash
        # This allows the dashboard to load even if there's a database error
        return {
            "messages": [],
            "total": 0,
            "status": "error",
            "error": str(e)
        }



# --- Modelli Pydantic per le richieste ---

class BulkUpdateRequest(BaseModel):
    message_ids: List[int]
    action: str

class AutonomousModeRequest(BaseModel):
    enabled: bool

# --- Rotte Protette ---

@router.post("/settings/autonomous-mode")
def update_autonomous_mode(request: AutonomousModeRequest, user: str = Depends(get_authenticated_user)):
    if isinstance(user, RedirectResponse): return user
    
    settings.automation.autonomous_mode_enabled = request.enabled
    print(f"Modalità Autonoma AI impostata su: {settings.automation.autonomous_mode_enabled}")
    return {"status": "success", "enabled": request.enabled}

@router.post("/publish-summary")
def trigger_daily_summary(background_tasks: BackgroundTasks, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    if isinstance(user, RedirectResponse): return user
    
    print("Trigger manuale per la compilazione giornaliera ricevuto.")
    # Esegui il task in background per non bloccare la risposta HTTP
    background_tasks.add_task(post_daily_compilation, db)
    
    # Reindirizza subito l'utente alla dashboard con un messaggio di successo
    # Nota: il messaggio di successo qui è solo per l'avvio del task.
    # L'esito reale sarà visibile nei log del server.
    return RedirectResponse(url="/admin/dashboard?status=summary_started", status_code=303)

@router.post("/schedule-daily-post")
def schedule_daily_post(background_tasks: BackgroundTasks, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    if isinstance(user, RedirectResponse): return user
    
    print("Scheduling daily post for 8 PM...")
    
    # Get all approved messages from today
    from datetime import datetime, date
    today = date.today()
    messages_to_post = db.query(SpottedMessage).filter(
        SpottedMessage.status == MessageStatus.APPROVED,
        SpottedMessage.created_at >= today,
        SpottedMessage.created_at < today + timedelta(days=1)
    ).all()
    
    print(f"Found {len(messages_to_post)} messages to schedule for today")
    
    # Schedule the posting task
    background_tasks.add_task(post_daily_messages, messages_to_post, db)
    
    return {"status": "success", "message": f"Scheduled {len(messages_to_post)} messages for 8 PM posting", "count": len(messages_to_post)}

async def post_daily_messages(messages, db: Session):
    """Post all approved messages from today at 8 PM"""
    from app.image.generator import ImageGenerator
    from app.bot.poster import InstagramBot
    
    print(f"Starting daily posting of {len(messages)} messages...")
    
    for message in messages:
        try:
            print(f"Posting message ID {message.id}...")
            
            # Generate image
            image_generator = ImageGenerator()
            output_filename = f"spotted_{message.id}_{int(datetime.now().timestamp())}.png"
            image_path = image_generator.from_text(message.text, output_filename, message.id)
            
            if not image_path:
                raise Exception("Image generation failed")
            
            # Post to Instagram
            insta_bot = InstagramBot()
            result = insta_bot.post_story(image_path)
            
            if not result:
                raise Exception("Instagram posting failed")
            
            # Extract media_pk
            if isinstance(result, dict) and 'media' in result:
                media_pk = result['media']
            elif isinstance(result, str):
                media_pk = result
            else:
                raise Exception(f"Invalid result format: {result}")
            
            # Update message status
            message.status = MessageStatus.POSTED
            message.posted_at = datetime.utcnow()
            message.error_message = None
            message.media_pk = str(media_pk)
            
            print(f"Message ID {message.id} posted successfully")
            
        except Exception as e:
            print(f"Error posting message ID {message.id}: {e}")
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
    
    # Commit all changes
    try:
        db.commit()
        print("Daily posting completed")
    except Exception as e:
        print(f"Error committing daily posts: {e}")
        db.rollback()

@router.post("/messages/{message_id}/edit")
async def edit_message(message_id: int, request: Request, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    if isinstance(user, RedirectResponse): return user
    
    try:
        form_data = await request.form()
        new_text = form_data.get('text', '').strip()
        
        if not new_text:
            return {"status": "error", "message": "Text cannot be empty"}
        
        # Get the message
        message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
        if not message:
            return {"status": "error", "message": "Message not found"}
        
        # Update the message
        message.text = new_text
        message.gemini_analysis = None  # Reset AI analysis since content changed
        db.commit()
        
        return {"status": "success", "message": "Message updated successfully"}
        
    except Exception as e:
        print(f"Error editing message {message_id}: {e}")
        return {"status": "error", "message": "Failed to update message"}

@router.get("/messages/{message_id}/comments")
def get_message_comments(message_id: int, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    if isinstance(user, RedirectResponse): return user

    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
    
    if not message.media_pk:
        raise HTTPException(status_code=400, detail="Media PK non disponibile per questo messaggio.")

    insta_bot = InstagramBot()
    comments = insta_bot.get_media_comments(message.media_pk)

    if comments is None:
        raise HTTPException(status_code=500, detail="Impossibile recuperare i commenti da Instagram.")

    return {"comments": comments}


@router.post("/messages/{message_id}/note")
def save_admin_note(message_id: int, note: str = Form(...), db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    if isinstance(user, RedirectResponse): return user
    
    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
    
    message.admin_note = note
    db.commit()
    return {"status": "success", "note": note}

@router.post("/messages/{message_id}/edit")
def edit_message_text(message_id: int, text: str = Form(...), db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    if isinstance(user, RedirectResponse): return user

    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
    
    message.text = text
    db.commit()
    return {"status": "success", "new_text": text}


@router.post("/messages/bulk-update")
def bulk_update_messages(request: BulkUpdateRequest, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    if isinstance(user, RedirectResponse): return user

    if request.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Azione non valida.")

    if not request.message_ids:
        raise HTTPException(status_code=400, detail="Nessun messaggio selezionato.")

    new_status = MessageStatus.APPROVED if request.action == "approve" else MessageStatus.REJECTED

    db.query(SpottedMessage).filter(
        SpottedMessage.id.in_(request.message_ids)
    ).update({'status': new_status}, synchronize_session=False)
    
    db.commit()
    
    return {"status": "success", "updated_count": len(request.message_ids)}

@router.get("/dashboard", response_class=HTMLResponse, name="show_dashboard")
def show_dashboard(request: Request, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user), page: int = 1):
    """Mostra la dashboard con statistiche, paginazione e la lista dei messaggi."""
    if isinstance(user, RedirectResponse):
        return user

    # Logica di Paginazione
    PAGE_SIZE = 15
    total_messages = db.query(func.count(SpottedMessage.id)).scalar()
    total_pages = math.ceil(total_messages / PAGE_SIZE)
    offset = (page - 1) * PAGE_SIZE

    messages = db.query(SpottedMessage).order_by(SpottedMessage.id.desc()).offset(offset).limit(PAGE_SIZE).all()
    
    kpi_counts = db.query(SpottedMessage.status, func.count(SpottedMessage.id)).group_by(SpottedMessage.status).all()
    kpis = {status.value: 0 for status in MessageStatus}
    for status, count in kpi_counts:
        kpis[status] = count
    
    today = datetime.utcnow().date()
    seven_days_ago = today - timedelta(days=6)
    
    daily_counts_query = db.query(
        func.date(SpottedMessage.created_at), 
        func.count(SpottedMessage.id)
    ).filter(
        SpottedMessage.created_at >= seven_days_ago
    ).group_by(
        func.date(SpottedMessage.created_at)
    ).all()
    
    daily_counts = {date: count for date, count in daily_counts_query}
    
    chart_labels = [(today - timedelta(days=i)).strftime('%d %b') for i in range(6, -1, -1)]
    chart_data_values = [daily_counts.get((today - timedelta(days=i)).strftime('%Y-%m-%d'), 0) for i in range(6, -1, -1)]
    
    chart_data = {
        "labels": chart_labels,
        "data": chart_data_values
    }

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": user,
        "messages": messages,
        "kpis": kpis,
        "chart_data": chart_data,
        "MessageStatus": MessageStatus,
        "current_user": user,
        "settings": settings # Pass settings to the template
    })

@router.post("/messages/{message_id}/approve")
def approve_message(
    message_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    user: str = Depends(get_authenticated_user)
):
    """Approva un messaggio e lo posta automaticamente su Instagram."""
    if isinstance(user, RedirectResponse): 
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    print(f"--- DEBUG: Richiesta di approvazione per messaggio ID: {message_id} ---")
    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        print(f"--- DEBUG: Messaggio ID: {message_id} non trovato. ---")
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
    
    print(f"--- DEBUG: Messaggio trovato. Cambio stato in APPROVED. ---")
    message.status = MessageStatus.APPROVED
    db.commit()
    print(f"--- DEBUG: Commit eseguito. Stato per ID {message_id} è ora APPROVED. ---")
    
    # Posta automaticamente il messaggio approvato
    print(f"--- DEBUG: Avvio posting automatico per messaggio ID: {message_id} ---")
    background_tasks.add_task(post_single_message, message_id)
    
    return {"status": "success", "message": "Messaggio approvato e in pubblicazione", "message_id": message_id}

@router.post("/messages/{message_id}/reject")
def reject_message(message_id: int, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    """Rifiuta un messaggio."""
    if isinstance(user, RedirectResponse): 
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
    
    message.status = MessageStatus.REJECTED
    db.commit()
    
    return {"status": "success", "message": "Messaggio rifiutato", "message_id": message_id}

def post_single_message(message_id: int):
    """Posta un singolo messaggio approvato su Instagram."""
    from app.image.generator import ImageGenerator
    from app.bot.poster import InstagramBot
    
    db = SessionLocal()
    try:
        message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
        if not message or message.status != MessageStatus.APPROVED:
            print(f"--- DEBUG [POST]: Messaggio ID {message_id} non trovato o non approvato. ---")
            return
        
        print(f"--- DEBUG [POST]: Inizio pubblicazione messaggio ID {message_id} ---")
        
        # Genera immagine
        image_generator = ImageGenerator()
        output_filename = f"spotted_{message.id}_{int(datetime.now().timestamp())}.png"
        image_path = image_generator.from_text(message.text, output_filename, message.id)
        
        if not image_path:
            raise Exception("Image generation failed")
        
        # Posta su Instagram
        insta_bot = InstagramBot()
        result = insta_bot.post_story(image_path)
        
        if not result:
            raise Exception("Instagram posting failed")
        
        # Estrai media_pk
        if isinstance(result, dict) and 'media' in result:
            media_pk = result['media']
        elif isinstance(result, str):
            media_pk = result
        else:
            raise Exception(f"Invalid result format: {result}")
        
        # Aggiorna stato
        message.status = MessageStatus.POSTED
        message.posted_at = datetime.utcnow()
        message.error_message = None
        message.media_pk = str(media_pk)
        
        db.commit()
        print(f"--- DEBUG [POST]: Messaggio ID {message_id} pubblicato con successo. Media PK: {media_pk} ---")
        
    except Exception as e:
        print(f"--- DEBUG [POST]: Errore pubblicazione ID {message_id}: {e} ---")
        if message:
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            db.commit()
    finally:
        db.close()

# --- Daily Post Management ---

@router.get("/daily-post", response_class=HTMLResponse, name="daily_post_page")
def daily_post_page(request: Request, user: str = Depends(get_current_user)):
    """Mostra la pagina di gestione del post giornaliero."""
    return templates.TemplateResponse("daily_post.html", {"request": request})

@router.get("/api/daily-post/settings")
def get_daily_post_settings_api(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per recuperare le impostazioni del post giornaliero."""
    from app.database import get_daily_post_settings
    settings = get_daily_post_settings(db)
    if not settings:
        return {"error": "Impostazioni non trovate"}

    return {
        "enabled": bool(settings.enabled),
        "post_time": settings.post_time,
        "style": settings.style,
        "max_messages": settings.max_messages,
        "title_template": settings.title_template,
        "hashtag_template": settings.hashtag_template,
        "last_run": settings.last_run.isoformat() if settings.last_run else None
    }

@router.post("/api/daily-post/settings")
def update_daily_post_settings(
    enabled: bool = Form(False),
    post_time: str = Form("20:00"),
    style: str = Form("carousel"),
    max_messages: int = Form(20),
    title_template: str = Form("🌟 Spotted del giorno {date} 🌟\n\nEcco tutti gli spotted della giornata! 💫"),
    hashtag_template: str = Form("#spotted #instaspotter #dailyrecap"),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API per aggiornare le impostazioni del post giornaliero."""
    from app.database import update_daily_post_settings

    try:
        settings = update_daily_post_settings(
            db=db,
            enabled=enabled,
            post_time=post_time,
            style=style,
            max_messages=max_messages,
            title_template=title_template,
            hashtag_template=hashtag_template
        )
        return {"status": "success", "message": "Impostazioni aggiornate"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.put("/api/daily-post/settings")
def update_single_daily_post_setting(
    setting: dict,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aggiorna una singola impostazione del post giornaliero."""
    from app.database import update_daily_post_settings

    try:
        key = list(setting.keys())[0]
        value = setting[key]

        # Converti valori se necessario
        if key == "max_messages":
            value = int(value)
        elif key == "enabled":
            value = bool(value)

        # Crea un oggetto settings parziale
        settings_dict = {key: value}
        result = update_daily_post_settings(db=db, **settings_dict)
        return {"status": "success", "message": f"Impostazione {key} aggiornata", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/api/daily-post/test")
def test_daily_post(user: str = Depends(get_current_user)):
    """API per testare il post giornaliero."""
    from app.tasks import test_daily_post
    import asyncio

    try:
        # Esegui il test in un thread separato per non bloccare
        result = test_daily_post()
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/api/daily-post/stats")
def get_daily_post_stats(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per ottenere statistiche del post giornaliero."""
    from app.database import get_todays_messages
    from datetime import datetime

    try:
        # Messaggi di oggi
        todays_messages = get_todays_messages(db)

        # Statistiche
        approved_today = [m for m in todays_messages if m.status == MessageStatus.APPROVED]
        posted_today = [m for m in todays_messages if m.posted_at and m.posted_at.date() == datetime.utcnow().date()]

        return {
            "total_today": len(todays_messages),
            "approved_today": len(approved_today),
            "posted_today": len(posted_today),
            "available_for_daily": len(approved_today)
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/admin/debug")
def debug_admin_credentials():
    """Endpoint di debug per vedere le credenziali configurate (SENZA password)."""
    import os
    from app.admin.security import ADMIN_USERNAME

    debug_info = {
        "configured_username": ADMIN_USERNAME,
        "has_password_hash": bool(os.getenv("ADMIN_PASSWORD_HASH") or os.getenv("REPLIT_ADMIN_PASSWORD_HASH")),
        "has_password": bool(os.getenv("ADMIN_PASSWORD") or os.getenv("REPLIT_ADMIN_PASSWORD")),
        "available_admin_vars": [k for k in os.environ.keys() if 'ADMIN' in k.upper()],
        "sample_env_vars": list(os.environ.keys())[:10]
    }

    return debug_info

@router.get("/api/settings/instagram")
def get_instagram_settings(user: str = Depends(get_current_user)):
    """Ottieni impostazioni Instagram."""
    import os
    return {
        "username": os.getenv("INSTAGRAM_USERNAME", "Not configured"),
        "configured": bool(os.getenv("INSTAGRAM_USERNAME"))
    }

@router.get("/api/settings/gemini")
def get_gemini_settings(user: str = Depends(get_current_user)):
    """Ottieni stato Gemini API."""
    import os
    return {
        "status": "Configured" if os.getenv("GEMINI_API_KEY") else "Not configured",
        "configured": bool(os.getenv("GEMINI_API_KEY"))
    }

# --- Info Cards Management ---

@router.get("/info-cards", response_class=HTMLResponse, name="info_cards_page")
def info_cards_page(request: Request, user: str = Depends(get_current_user)):
    """Mostra la pagina di gestione delle info cards."""
    return templates.TemplateResponse("info_cards.html", {"request": request})

@router.get("/api/info-cards")
def get_info_cards(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per ottenere tutte le info cards."""
    from app.database import MessageType
    info_cards = db.query(SpottedMessage).filter(
        SpottedMessage.message_type == MessageType.INFO
    ).order_by(SpottedMessage.created_at.desc()).all()

    return [{
        "id": card.id,
        "title": card.title,
        "text": card.text,
        "status": card.status,
        "created_at": card.created_at.isoformat() if card.created_at else None,
        "posted_at": card.posted_at.isoformat() if card.posted_at else None,
        "media_pk": card.media_pk
    } for card in info_cards]

@router.post("/api/info-cards")
def create_info_card(
    title: str = Form(...),
    text: str = Form(...),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API per creare una nuova info card."""
    from app.database import MessageType, MessageStatus
    from app.tasks import generate_technical_user

    try:
        if not title or not text:
            return {"status": "error", "message": "Title and text are required"}

        # Crea utente tecnico admin
        admin_user = generate_technical_user(db)

        # Crea la info card
        info_card = SpottedMessage(
            text=text,
            message_type=MessageType.INFO,
            title=title,
            status=MessageStatus.APPROVED,  # Le info cards sono automaticamente approvate
            technical_user_id=admin_user.id
        )

        db.add(info_card)
        db.commit()
        db.refresh(info_card)

        return {"status": "success", "message": "Info card creata con successo", "id": info_card.id}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@router.post("/api/info-cards/{card_id}/publish")
def publish_info_card(card_id: int, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per pubblicare una info card come storia."""
    from app.database import MessageType, MessageStatus
    from app.tasks import publish_info_card_task

    try:
        # Trova la info card
        info_card = db.query(SpottedMessage).filter(
            SpottedMessage.id == card_id,
            SpottedMessage.message_type == MessageType.INFO
        ).first()

        if not info_card:
            return {"status": "error", "message": "Info card non trovata"}

        # Pubblica come storia
        result = publish_info_card_task(info_card.id)

        if result["status"] == "success":
            # Aggiorna stato
            info_card.status = MessageStatus.POSTED
            info_card.posted_at = datetime.utcnow()
            info_card.media_pk = result.get("media_pk")
            db.commit()
            return {"status": "success", "message": "Info card pubblicata con successo"}
        else:
            # Aggiorna con errore
            info_card.status = MessageStatus.FAILED
            info_card.error_message = result.get("message", "Errore sconosciuto")
            db.commit()
            return {"status": "error", "message": result.get("message", "Errore pubblicazione")}

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@router.post("/api/info-cards/preview")
def preview_info_card(
    title: str = Form(""),
    text: str = Form(""),
    user: str = Depends(get_current_user)
):
    """API per ottenere una preview dell'info card come immagine."""
    try:
        if not title or not text:
            title = "Titolo Card"
            text = "Il contenuto apparirà qui..."

        print(f"🎨 Preview request - Title: '{title}', Text: '{text[:50]}...'")

        # Usa il generatore di immagini per creare una preview
        from app.image.generator import ImageGenerator
        generator = ImageGenerator()

        print("📸 Initializing image generator...")

        # Genera l'immagine con message_type="INFO" e message_id fittizio per preview
        # Usa un ID negativo per indicare che è una preview
        image_filename = f"preview_{hash(title+text)}.png"
        print(f"🖼️ Generating image: {image_filename}")

        image_path = generator.from_text(text, image_filename, message_id=-999, message_type="INFO", title=title)

        print(f"📁 Generated image path: {image_path}")

        if image_path and os.path.exists(image_path):
            # Restituisci l'URL relativa dell'immagine
            image_url = f"/generated_images/{os.path.basename(image_path)}"
            print(f"✅ Preview generated successfully: {image_url}")
            return {"status": "success", "image_url": image_url}
        else:
            print("❌ Failed to generate preview image")
            return {"status": "error", "message": "Failed to generate preview image"}

    except Exception as e:
        print(f"❌ Preview generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@router.delete("/api/info-cards/{card_id}")
def delete_info_card(card_id: int, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per eliminare una info card."""
    from app.database import MessageType

    try:
        info_card = db.query(SpottedMessage).filter(
            SpottedMessage.id == card_id,
            SpottedMessage.message_type == MessageType.INFO
        ).first()

        if not info_card:
            return {"status": "error", "message": "Info card non trovata"}

        # Non permettere eliminazione di card già pubblicate
        if info_card.status == MessageStatus.POSTED:
            return {"status": "error", "message": "Non puoi eliminare una card già pubblicata"}

        db.delete(info_card)
        db.commit()

        return {"status": "success", "message": "Info card eliminata con successo"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

# === NUOVI ENDPOINT PER LA DASHBOARD ENTERPRISE ===

@router.get("/api/debug")
def debug_admin_credentials(user: str = Depends(get_current_user)):
    """Endpoint di debug per informazioni di sistema."""
    import platform
    import psutil
    import os

    try:
        return {
            "version": "1.0.0",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": psutil.disk_usage('/')._asdict(),
            "uptime": os.times()._asdict()
        }
    except Exception as e:
        return {
            "version": "1.0.0",
            "python_version": "3.11",
            "error": str(e)
        }

@router.get("/api/analytics/dashboard")
def get_analytics_dashboard(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per analytics della dashboard."""
    from datetime import datetime, timedelta
    from sqlalchemy import func, extract
    from app.database import MessageStatus

    try:
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Messaggi per ora (ultime 24 ore)
        hourly_stats = db.query(
            extract('hour', SpottedMessage.created_at).label('hour'),
            func.count(SpottedMessage.id).label('count')
        ).filter(
            SpottedMessage.created_at >= yesterday
        ).group_by(
            extract('hour', SpottedMessage.created_at)
        ).order_by(
            extract('hour', SpottedMessage.created_at)
        ).all()

        messages_hourly = [{"hour": int(h.hour), "count": h.count} for h in hourly_stats]

        # Messaggi per status
        status_stats = db.query(
            SpottedMessage.status,
            func.count(SpottedMessage.id).label('count')
        ).group_by(SpottedMessage.status).all()

        messages_by_status = {status.value: count for status, count in status_stats}

        # Statistiche utenti (semplificate per ora)
        users_24h = db.query(func.count(func.distinct(SpottedMessage.ip_address))).filter(
            SpottedMessage.created_at >= yesterday
        ).scalar() or 0

        users_7d = db.query(func.count(func.distinct(SpottedMessage.ip_address))).filter(
            SpottedMessage.created_at >= week_ago
        ).scalar() or 0

        users_30d = db.query(func.count(func.distinct(SpottedMessage.ip_address))).filter(
            SpottedMessage.created_at >= month_ago
        ).scalar() or 0

        return {
            "messages_hourly": messages_hourly,
            "messages_by_status": messages_by_status,
            "users_24h": users_24h,
            "users_7d": users_7d,
            "users_30d": users_30d,
            "cpu_usage": 0,  # Placeholder
            "ram_usage": 0,  # Placeholder
            "db_connections": 0,  # Placeholder
            "failed_logins_24h": 0,  # Placeholder
            "security_alerts": 0,  # Placeholder
            "audit_events_24h": 0,  # Placeholder
            "unique_ips_24h": users_24h,
            "top_country": "Italy",  # Placeholder
            "traffic_trend": 0  # Placeholder
        }
    except Exception as e:
        return {
            "messages_hourly": [],
            "messages_by_status": {"PENDING": 0, "APPROVED": 0, "REJECTED": 0},
            "users_24h": 0,
            "users_7d": 0,
            "users_30d": 0,
            "error": str(e)
        }

@router.get("/api/logs")
def get_system_logs(
    type: str = "all",
    period: str = "24h",
    user: str = Depends(get_current_user)
):
    """API per ottenere i log di sistema."""
    from datetime import datetime, timedelta

    try:
        now = datetime.utcnow()

        # Calcola il periodo
        if period == "1h":
            start_time = now - timedelta(hours=1)
        elif period == "24h":
            start_time = now - timedelta(hours=24)
        elif period == "7d":
            start_time = now - timedelta(days=7)
        elif period == "30d":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(hours=24)

        # Mock logs per ora - in produzione leggere da file di log
        mock_logs = [
            {
                "timestamp": (now - timedelta(minutes=i)).isoformat(),
                "level": "INFO",
                "category": "Sistema",
                "message": f"Operazione di sistema completata {i}",
                "user": "system"
            } for i in range(10)
        ]

        # Filtra per tipo
        if type != "all":
            mock_logs = [log for log in mock_logs if log["level"].lower() == type.lower()]

        # Filtra per periodo
        mock_logs = [log for log in mock_logs if datetime.fromisoformat(log["timestamp"]) >= start_time]

        return mock_logs
    except Exception as e:
        return [{"error": str(e)}]

@router.get("/api/backup/status")
def get_backup_status(user: str = Depends(get_current_user)):
    """API per ottenere lo stato dei backup."""
    import os
    from datetime import datetime

    try:
        # Controlla se esiste una cartella backup
        backup_dir = "data/backups"
        if not os.path.exists(backup_dir):
            return {
                "last_backup": None,
                "auto_backup_enabled": False,
                "total_size": "0 MB",
                "backup_count": 0
            }

        backups = []
        total_size = 0

        for file in os.listdir(backup_dir):
            if file.endswith('.zip') or file.endswith('.sql'):
                filepath = os.path.join(backup_dir, file)
                size = os.path.getsize(filepath)
                total_size += size
                backups.append({
                    "filename": file,
                    "size": size,
                    "created_at": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                })

        last_backup = max(backups, key=lambda x: x["created_at"])["created_at"] if backups else None

        return {
            "last_backup": last_backup,
            "auto_backup_enabled": True,  # Placeholder
            "total_size": f"{total_size / (1024*1024):.1f} MB",
            "backup_count": len(backups)
        }
    except Exception as e:
        return {
            "last_backup": None,
            "auto_backup_enabled": False,
            "total_size": "0 MB",
            "backup_count": 0,
            "error": str(e)
        }

@router.post("/api/backup/create-full")
def create_full_backup(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per creare un backup completo."""
    import os
    import zipfile
    from datetime import datetime

    try:
        # Crea directory backup se non esiste
        backup_dir = "data/backups"
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_full_{timestamp}.zip"
        filepath = os.path.join(backup_dir, filename)

        # Crea zip con dati
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Aggiungi immagini se esistono
            if os.path.exists("data/generated_images"):
                for root, dirs, files in os.walk("data/generated_images"):
                    for file in files:
                        zipf.write(os.path.join(root, file),
                                 os.path.relpath(os.path.join(root, file), "."))

            # Aggiungi file di configurazione
            config_files = ["requirements.txt", ".replit", "start.sh", "run.sh"]
            for config_file in config_files:
                if os.path.exists(config_file):
                    zipf.write(config_file)

        return {
            "success": True,
            "filename": filename,
            "size": os.path.getsize(filepath),
            "path": filepath
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/api/backup/create-auto")
def create_automatic_backup(user: str = Depends(get_current_user)):
    """API per creare un backup automatico."""
    # Per ora usa la stessa logica del backup completo
    return create_full_backup(user=user)

@router.get("/api/backup/list")
def list_backups(user: str = Depends(get_current_user)):
    """API per ottenere la lista dei backup."""
    import os
    from datetime import datetime

    try:
        backup_dir = "data/backups"
        if not os.path.exists(backup_dir):
            return []

        backups = []
        for file in os.listdir(backup_dir):
            if file.endswith('.zip') or file.endswith('.sql'):
                filepath = os.path.join(backup_dir, file)
                backups.append({
                    "filename": file,
                    "size": os.path.getsize(filepath),
                    "created_at": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                })

        return sorted(backups, key=lambda x: x["created_at"], reverse=True)
    except Exception as e:
        return []

@router.get("/api/backup/download/{filename}")
def download_backup(filename: str, user: str = Depends(get_current_user)):
    """API per scaricare un backup specifico."""
    import os
    from fastapi.responses import FileResponse

    try:
        filepath = os.path.join("data/backups", filename)
        if os.path.exists(filepath):
            return FileResponse(filepath, filename=filename)
        else:
            return {"error": "Backup not found"}
    except Exception as e:
        return {"error": str(e)}

@router.delete("/api/backup/delete/{filename}")
def delete_backup(filename: str, user: str = Depends(get_current_user)):
    """API per eliminare un backup."""
    import os

    try:
        filepath = os.path.join("data/backups", filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return {"success": True}
        else:
            return {"error": "Backup not found"}
    except Exception as e:
        return {"error": str(e)}

@router.post("/api/backup/restore")
def restore_backup(request: dict, user: str = Depends(get_current_user)):
    """API per ripristinare un backup."""
    # Questa è un'operazione molto pericolosa - per ora solo simulata
    filename = request.get("filename")
    return {
        "success": False,
        "message": "Ripristino backup non ancora implementato per sicurezza",
        "filename": filename
    }

@router.post("/api/messages/delete-by-status")
def delete_messages_by_status(request: dict, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per eliminare messaggi per status."""
    from app.database import MessageStatus

    try:
        status_str = request.get("status")
        status = MessageStatus[status_str]

        # Conta prima
        count = db.query(SpottedMessage).filter(SpottedMessage.status == status).count()

        # Elimina
        deleted = db.query(SpottedMessage).filter(SpottedMessage.status == status).delete()
        db.commit()

        return {"deleted_count": deleted, "status": status_str}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@router.post("/api/messages/delete-all")
def delete_all_messages(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per eliminare tutti i messaggi."""
    try:
        count = db.query(SpottedMessage).count()
        db.query(SpottedMessage).delete()
        db.commit()

        return {"deleted_count": count}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@router.post("/api/info-cards/delete-all")
def delete_all_info_cards(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per eliminare tutte le info cards."""
    from app.database import MessageType

    try:
        count = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).count()
        db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).delete()
        db.commit()

        return {"deleted_count": count}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@router.post("/api/daily-posts/delete-all")
def delete_all_daily_posts(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per eliminare tutti i daily posts."""
    from app.database import DailyPostSettings

    try:
        # Elimina impostazioni
        settings_count = db.query(DailyPostSettings).delete()

        # Elimina messaggi di tipo daily (se esistono)
        from app.database import MessageType
        posts_count = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.DAILY).count()
        db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.DAILY).delete()

        db.commit()

        return {"deleted_settings": settings_count, "deleted_posts": posts_count}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@router.post("/api/settings/reset-all")
def reset_all_settings(user: str = Depends(get_current_user)):
    """API per resettare tutte le impostazioni."""
    # Questa è un'operazione di reset - per ora solo simulata
    return {
        "success": True,
        "message": "Tutte le impostazioni sono state resettate ai valori predefiniti",
        "reset_items": ["instagram", "ai", "system", "daily_post"]
    }

@router.post("/api/system/nuclear-option")
def nuclear_option(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per l'opzione nucleare - cancella tutto."""
    try:
        # Conta tutto prima
        messages_count = db.query(SpottedMessage).count()

        # Cancella tutto
        db.query(SpottedMessage).delete()
        # Altri modelli se necessario...

        db.commit()

        return {
            "success": True,
            "message": "Opzione nucleare completata - tutto il database è stato cancellato",
            "deleted_messages": messages_count
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@router.post("/api/system/restart")
def restart_system(user: str = Depends(get_current_user)):
    """API per riavviare il sistema."""
    # In produzione questo dovrebbe riavviare l'applicazione
    return {
        "success": True,
        "message": "Sistema riavviato (simulato)",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/api/system/clear-cache")
def clear_cache(user: str = Depends(get_current_user)):
    """API per svuotare la cache."""
    import os
    import shutil

    try:
        # Svuota cache directory
        cache_dirs = ["__pycache__", "data/cache", ".pytest_cache"]
        cleared = 0

        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
                cleared += 1

        return {
            "success": True,
            "message": f"Cache svuotata - {cleared} directory eliminate",
            "cleared_dirs": cache_dirs
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/api/users/technical")
def get_technical_users(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per ottenere la lista degli utenti tecnici."""
    # Mock per ora - in produzione leggere da tabella dedicata
    return [
        {
            "id": 1,
            "username": "admin",
            "created_at": "2024-01-01T00:00:00Z",
            "last_login": "2024-01-11T17:00:00Z"
        }
    ]

@router.post("/api/users/technical")
def create_technical_user(request: dict, user: str = Depends(get_current_user)):
    """API per creare un utente tecnico."""
    # Mock per ora
    return {
        "success": True,
        "message": "Utente tecnico creato (simulato)",
        "username": request.get("username")
    }

@router.delete("/api/users/technical/{user_id}")
def delete_technical_user(user_id: int, user: str = Depends(get_current_user)):
    """API per eliminare un utente tecnico."""
    # Mock per ora
    return {"success": True, "message": "Utente tecnico eliminato (simulato)"}

@router.put("/api/users/technical/{user_id}/password")
def reset_technical_user_password(user_id: int, request: dict, user: str = Depends(get_current_user)):
    """API per resettare la password di un utente tecnico."""
    # Mock per ora
    return {"success": True, "message": "Password resettata (simulato)"}

@router.get("/api/messages/search")
def search_messages(
    query: str = "",
    status: str = "",
    date_from: str = "",
    date_to: str = "",
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API per ricerca avanzata nei messaggi."""
    from app.database import MessageStatus

    try:
        q = db.query(SpottedMessage)

        # Filtro per testo
        if query:
            q = q.filter(SpottedMessage.text.ilike(f"%{query}%"))

        # Filtro per status
        if status:
            q = q.filter(SpottedMessage.status == MessageStatus[status])

        # Filtro per date
        if date_from:
            q = q.filter(SpottedMessage.created_at >= date_from)
        if date_to:
            q = q.filter(SpottedMessage.created_at <= date_to)

        results = q.order_by(SpottedMessage.created_at.desc()).limit(100).all()

        return [{
            "id": msg.id,
            "text": msg.text,
            "status": msg.status.value,
            "created_at": msg.created_at.isoformat(),
            "ip_address": msg.ip_address
        } for msg in results]
    except Exception as e:
        return {"error": str(e)}

@router.post("/api/analytics/generate-report")
def generate_analytics_report(user: str = Depends(get_current_user)):
    """API per generare un report analytics completo."""
    # Mock report per ora
    return {
        "total_messages": 150,
        "messages_today": 12,
        "approval_rate": 85.5,
        "top_categories": ["general", "events", "questions"],
        "user_engagement": 92.3,
        "system_performance": {
            "avg_response_time": "245ms",
            "uptime": "99.9%",
            "error_rate": "0.1%"
        },
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/api/analytics/export")
def export_analytics(user: str = Depends(get_current_user)):
    """API per esportare i dati analytics."""
    from fastapi.responses import Response

    # Mock CSV data
    csv_data = """Date,Messages,Approved,Rejected,Users
2024-01-01,10,8,2,5
2024-01-02,15,12,3,8
2024-01-03,8,6,2,4
"""

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analytics_export.csv"}
    )

@router.get("/api/logs/export")
def export_logs(
    type: str = "all",
    period: str = "24h",
    user: str = Depends(get_current_user)
):
    """API per esportare i log."""
    from fastapi.responses import Response

    # Mock CSV data
    csv_data = f"""Timestamp,Level,Category,Message,User
{datetime.utcnow().isoformat()},INFO,System,Log export generated,system
{datetime.utcnow().isoformat()},WARNING,Security,Login attempt,unknown
"""

    filename = f"system_logs_{type}_{period}_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/api/logs/clear-old")
def clear_old_logs(user: str = Depends(get_current_user)):
    """API per eliminare i log più vecchi di 30 giorni."""
    # Mock per ora
    return {
        "success": True,
        "message": "Log vecchi eliminati (simulato)",
        "deleted_count": 150
    }