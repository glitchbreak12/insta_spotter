from fastapi import APIRouter, Request, Depends, HTTPException, Form, Response, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import secrets
import hashlib
import json
import io
import os

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

        # Usa il generatore di immagini per creare una preview
        from app.image.generator import ImageGenerator
        generator = ImageGenerator()

        # Genera l'immagine con message_type="INFO"
        image_path = generator.from_text(text, f"preview_{hash(title+text)}", message_type="INFO", title=title)

        if image_path:
            # Restituisci l'URL relativa dell'immagine
            image_url = f"/generated_images/{image_path.split('/')[-1]}"
            return {"status": "success", "image_url": image_url}
        else:
            return {"status": "error", "message": "Failed to generate preview image"}

    except Exception as e:
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

# === SISTEMA QR LOGIN MOBILE ===

# Store temporaneo per sessioni QR (in memoria)
qr_sessions = {}

@router.post("/api/auth/generate-qr")
def generate_qr_code(user: str = Depends(get_current_user)):
    """Genera un codice QR per autenticazione mobile."""
    try:
        # Genera token sicuro unico
        qr_token = secrets.token_urlsafe(32)
        session_id = secrets.token_hex(16)

        # Hash del token per storage sicuro
        token_hash = hashlib.sha256(qr_token.encode()).hexdigest()

        # Scadenza: 5 minuti
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        # Store della sessione QR
        qr_sessions[session_id] = {
            "token_hash": token_hash,
            "user": user,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "used": False
        }

        # Genera URL per il QR code - usa URL dinamico per Replit
        base_url = os.getenv("REPLIT_APP_URL", "http://localhost:8000").replace("https://", "http://")
        qr_url = f"{base_url}/admin/auth/qr/{session_id}?token={qr_token}"

        # Try server-side QR generation (optional, client-side will always work)
        qr_image_b64 = None
        qr_image_url = None

        try:
            print(f"🔧 Attempting server-side QR generation for user {user}")
            import qrcode
            from PIL import Image
            import base64
            import io

            print("✅ QRCode and PIL libraries imported successfully")

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_url)
            qr.make(fit=True)

            print("✅ QR code data added and made")

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")

            print("✅ QR image generated and saved to buffer")

            # Create direct image URL only if generation succeeded
            qr_image_url = f"{base_url}/admin/api/auth/qr-image/{session_id}"

            # Also create base64 as backup
            image_data = buffer.getvalue()
            qr_image_b64 = f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"

            print(f"✅ QR image available at: {qr_image_url}")

        except ImportError as e:
            print(f"⚠️ QR libraries not available on server: {e}")
            print("📱 Client-side QR generation will be used instead")
        except Exception as qr_error:
            print(f"❌ Server-side QR generation failed: {qr_error}")
            import traceback
            traceback.print_exc()

        return {
            "success": True,
            "qr_data": {
                "session_id": session_id,
                "url": qr_url,
                "expires_in": 300,  # 5 minuti
                "qr_image_url": qr_image_url,  # Direct image URL (if available)
                "qr_image_b64": qr_image_b64   # Base64 backup (if available)
            },
            "message": "QR Code generato. Scansiona con il cellulare per accedere automaticamente."
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/api/auth/verify-qr")
def verify_qr_code(session_id: str, token: str):
    """Verifica il codice QR scansionato dal mobile."""
    try:
        # Controlla se la sessione QR esiste
        if session_id not in qr_sessions:
            return {"success": False, "error": "Sessione QR non valida"}

        session = qr_sessions[session_id]

        # Controlla scadenza
        if datetime.utcnow() > session["expires_at"]:
            del qr_sessions[session_id]
            return {"success": False, "error": "Sessione QR scaduta"}

        # Controlla se già usata
        if session["used"]:
            return {"success": False, "error": "Sessione QR già utilizzata"}

        # Verifica token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash != session["token_hash"]:
            return {"success": False, "error": "Token QR non valido"}

        # Marca come usata
        session["used"] = True

        return {
            "success": True,
            "user": session["user"],
            "message": f"Dispositivo mobile collegato con successo a {session['user']}"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/api/auth/qr-login")
def qr_mobile_login(session_id: str):
    """Login tramite QR dal mobile."""
    try:
        if session_id not in qr_sessions:
            return {"success": False, "error": "Sessione non trovata"}

        session = qr_sessions[session_id]
        if not session.get("used", False):
            return {"success": False, "error": "Sessione non verificata"}

        # Genera token di sessione per il mobile
        from app.admin.security import create_access_token
        mobile_token = create_access_token({"sub": session["user"], "device": "mobile"})

        # Log dell'accesso
        print(f"🔐 Mobile login via QR: {session['user']}")

        # Pulisci la sessione QR dopo uso
        del qr_sessions[session_id]

        return {
            "success": True,
            "access_token": mobile_token,
            "user": session["user"],
            "device": "mobile",
            "message": "Login mobile completato con successo"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

# === PAGINA MOBILE PER SCAN QR CODE ===

@router.get("/api/auth/qr-image/{session_id}")
def get_qr_image(session_id: str, user: str = Depends(get_current_user)):
    """Genera e restituisce un'immagine QR code come PNG."""
    try:
        print(f"🖼️ Generating QR image for session {session_id}, user {user}")

        if session_id not in qr_sessions:
            raise HTTPException(status_code=404, detail="Sessione QR non trovata")

        session = qr_sessions[session_id]
        if session["user"] != user:
            raise HTTPException(status_code=403, detail="Non autorizzato")

        # Ricostruisci l'URL
        qr_url = f"https://instaspotter.app/auth/qr/{session_id}?token=qr_sessions[session_id]['token_hash']"

        # Genera QR code
        try:
            import qrcode
            from PIL import Image

            print("✅ Generating QR code with qrcode library")

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Restituisci come immagine PNG
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            print(f"✅ QR image generated successfully, size: {len(buffer.getvalue())} bytes")

            return StreamingResponse(
                buffer,
                media_type="image/png",
                headers={"Content-Disposition": "inline; filename=qr_code.png"}
            )

        except ImportError as e:
            print(f"❌ QR libraries not available: {e}")
            # Return a simple placeholder image or redirect to client-side generation
            # For now, return a 404 to trigger client-side fallback
            raise HTTPException(status_code=404, detail="QR generation not available on server")
        except Exception as e:
            print(f"❌ QR generation error: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Errore generazione QR: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in QR image generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/auth/qr/{session_id}")
def qr_auth_page(session_id: str):
    """Pagina mobile per autenticazione QR."""
    # Verifica che la sessione esista
    if session_id not in qr_sessions:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>Errore</title></head>
        <body style="text-align: center; padding: 50px;">
        <h1>Sessione QR non valida</h1>
        <p>Il codice QR potrebbe essere scaduto. Torna al dashboard e genera un nuovo QR code.</p>
        </body>
        </html>
        """)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>InstaSpotter - Accesso Mobile</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                text-align: center;
                max-width: 400px;
                width: 100%;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            }}
            .logo {{
                font-size: 2.5rem;
                margin-bottom: 20px;
                color: #fff;
            }}
            h1 {{
                font-size: 1.5rem;
                margin-bottom: 10px;
            }}
            .status {{
                font-size: 1rem;
                margin: 20px 0;
                padding: 15px;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.1);
            }}
            .btn {{
                background: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.3);
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                font-size: 1rem;
                cursor: pointer;
                transition: all 0.3s;
                margin: 10px;
                min-width: 200px;
            }}
            .btn:hover {{
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
            }}
            .btn:disabled {{
                opacity: 0.6;
                cursor: not-allowed;
            }}
            .success {{
                background: rgba(16, 185, 129, 0.2);
                border-color: #10b981;
            }}
            .error {{
                background: rgba(239, 68, 68, 0.2);
                border-color: #ef4444;
            }}
            .spinner {{
                border: 3px solid rgba(255, 255, 255, 0.3);
                border-top: 3px solid white;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .hidden {{ display: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <i class="fas fa-mobile-alt"></i>
            </div>
            <h1>InstaSpotter Mobile</h1>
            <div id="status" class="status">
                <div id="statusText">Verificando sessione...</div>
            </div>
            <button id="authBtn" class="btn" onclick="authenticate()" disabled>
                <i class="fas fa-mobile-alt"></i>
                Accedi da Mobile
            </button>
            <button id="retryBtn" class="btn hidden" onclick="retry()">
                <i class="fas fa-redo"></i>
                Riprova
            </button>
        </div>

        <script>
            let sessionId = '{session_id}';
            let qrToken = null;

            console.log('📱 Mobile QR page loaded for session:', sessionId);

            // Estrai token dall'URL
            const urlParams = new URLSearchParams(window.location.search);
            qrToken = urlParams.get('token');

            console.log('🔑 QR token extracted:', qrToken ? 'present' : 'missing');

            async function checkSession() {{
                console.log('🔍 Checking QR session...');
                if (!qrToken) {{
                    document.getElementById('statusText').innerHTML = '<i class="fas fa-exclamation-triangle"></i> Token QR mancante';
                    document.getElementById('status').className = 'status error';
                    return;
                }}

                try {{
                    const response = await fetch('/admin/api/auth/verify-qr', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            session_id: sessionId,
                            token: qrToken
                        }})
                    }});

                    console.log('📡 Verification response status:', response.status);

                    const data = await response.json();
                    console.log('📋 Verification response data:', data);

                    if (data.success) {{
                        document.getElementById('statusText').innerHTML = '<i class="fas fa-check-circle"></i> Sessione verificata! Pronto per accesso.';
                        document.getElementById('status').className = 'status success';
                        document.getElementById('authBtn').disabled = false;
                    }} else {{
                        document.getElementById('statusText').innerHTML = '<i class="fas fa-exclamation-triangle"></i> ' + (data.error || 'Errore verifica sessione');
                        document.getElementById('status').className = 'status error';
                        document.getElementById('retryBtn').classList.remove('hidden');
                    }}
                }} catch (error) {{
                    console.error('❌ Connection error:', error);
                    document.getElementById('statusText').innerHTML = '<i class="fas fa-times-circle"></i> Errore di connessione';
                    document.getElementById('status').className = 'status error';
                    document.getElementById('retryBtn').classList.remove('hidden');
                }}
            }}

            async function authenticate() {{
                console.log('🚀 Starting mobile authentication...');
                try {{
                    document.getElementById('authBtn').innerHTML = '<div class="spinner"></div>';
                    document.getElementById('authBtn').disabled = true;

                    const response = await fetch('/admin/api/auth/qr-login', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ session_id: sessionId }})
                    }});

                    console.log('📡 Login response status:', response.status);

                    const data = await response.json();
                    console.log('📋 Login response data:', data);

                    if (data.success) {{
                        document.getElementById('statusText').innerHTML = '<i class="fas fa-check-circle"></i> Accesso completato! Puoi chiudere questa pagina.';
                        document.getElementById('status').className = 'status success';
                        document.getElementById('authBtn').style.display = 'none';

                        // Auto-close after 3 seconds
                        setTimeout(() => {{
                            window.close();
                        }}, 3000);
                    }} else {{
                        throw new Error(data.error || 'Errore autenticazione');
                    }}
                }} catch (error) {{
                    console.error('❌ Authentication error:', error);
                    document.getElementById('statusText').innerHTML = '<i class="fas fa-times-circle"></i> ' + error.message;
                    document.getElementById('status').className = 'status error';
                    document.getElementById('authBtn').innerHTML = '<i class="fas fa-mobile-alt"></i> Riprova';
                    document.getElementById('authBtn').disabled = false;
                }}
            }}

            function retry() {{
                document.getElementById('statusText').innerHTML = '<div class="spinner"></div> Verificando...';
                document.getElementById('status').className = 'status';
                document.getElementById('retryBtn').classList.add('hidden');
                checkSession();
            }}

            // Check session on load
            checkSession();

            // Auto-refresh every 10 seconds
            setInterval(checkSession, 10000);
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)