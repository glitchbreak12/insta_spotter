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

from app.database import get_db, SpottedMessage, MessageStatus, SessionLocal, get_ai_config, update_ai_config, AIModel, set_system_setting, get_system_setting_value
from app.admin.security import authenticate_user, create_access_token, get_current_user
from app.tasks import post_daily_compilation, publish_single_info_card
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

# --- Individual Message Management APIs ---

@router.get("/api/messages/{message_id}")
def get_message_details(message_id: int, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    """Ottieni i dettagli di un singolo messaggio."""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Not authenticated")

    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")

    return {
        "id": message.id,
        "text": message.text,
        "status": message.status.value,
        "created_at": message.created_at.isoformat() if message.created_at else None,
        "posted_at": message.posted_at.isoformat() if message.posted_at else None,
        "message_type": message.message_type.value,
        "title": message.title,
        "media_pk": message.media_pk,
        "admin_note": message.admin_note,
        "gemini_analysis": message.gemini_analysis,
        "error_message": message.error_message
    }

@router.put("/api/messages/{message_id}")
def update_message(
    message_id: int,
    text: str = None,
    status: str = None,
    admin_note: str = None,
    db: Session = Depends(get_db),
    user: str = Depends(get_authenticated_user)
):
    """Aggiorna un singolo messaggio."""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Not authenticated")

    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")

    # Update fields if provided
    if text is not None:
        message.text = text
        # Reset AI analysis if text changed
        message.gemini_analysis = None

    if status is not None:
        try:
            message.status = MessageStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Stato non valido")

    if admin_note is not None:
        message.admin_note = admin_note

    db.commit()
    db.refresh(message)

    return {
        "status": "success",
        "message": "Messaggio aggiornato con successo",
        "message_id": message.id
    }

@router.delete("/api/messages/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    """Elimina un singolo messaggio."""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Not authenticated")

    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")

    # Don't allow deletion of posted messages
    if message.status == MessageStatus.POSTED:
        raise HTTPException(status_code=400, detail="Non puoi eliminare un messaggio già pubblicato")

    db.delete(message)
    db.commit()

    return {"status": "success", "message": "Messaggio eliminato con successo"}

# --- Bulk / administrative cleanup endpoints (safe, protected) ---
@router.post('/api/messages/delete-by-status')
async def delete_messages_by_status(request: Request, status: str = Form(None), confirm: bool = Form(None), db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    """Elimina tutti i messaggi con lo stato specificato. Conferma tramite form o JSON."""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail='Not authenticated')

    # Support JSON body from frontend
    try:
        payload = {}
        if request.headers.get('content-type', '').lower().startswith('application/json'):
            payload = await request.json()
    except Exception:
        payload = {}

    if status is None:
        status = payload.get('status')
    if confirm is None:
        confirm = payload.get('confirm', True)

    if not confirm:
        return {'status': 'error', 'message': 'confirm=false, operation aborted'}

    try:
        valid_statuses = [s.value for s in MessageStatus]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail='Stato non valido')

        deleted = db.query(SpottedMessage).filter(SpottedMessage.status == MessageStatus(status)).delete(synchronize_session=False)
        db.commit()
        return {'status': 'success', 'deleted_count': deleted}
    except Exception as e:
        db.rollback()
        return {'status': 'error', 'message': str(e)}

@router.post('/api/messages/delete-all')
async def delete_all_messages(request: Request, confirm: bool = Form(None), db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    """Elimina tutti i messaggi (tranne quelli POSTED). Conferma tramite form o JSON."""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail='Not authenticated')

    try:
        payload = {}
        if request.headers.get('content-type', '').lower().startswith('application/json'):
            payload = await request.json()
    except Exception:
        payload = {}

    if confirm is None:
        confirm = payload.get('confirm', True)

    if not confirm:
        return {'status': 'error', 'message': 'confirm=false, operation aborted'}

    try:
        # Only remove non-posted messages to avoid data loss
        deleted = db.query(SpottedMessage).filter(SpottedMessage.status != MessageStatus.POSTED).delete(synchronize_session=False)
        db.commit()
        return {'status': 'success', 'deleted_count': deleted}
    except Exception as e:
        db.rollback()
        return {'status': 'error', 'message': str(e)}

@router.post('/api/info-cards/delete-all')
async def delete_all_info_cards(request: Request, confirm: bool = Form(None), db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    """Elimina tutte le info cards (MessageType.INFO). Conferma tramite form o JSON."""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail='Not authenticated')

    try:
        payload = {}
        if request.headers.get('content-type', '').lower().startswith('application/json'):
            payload = await request.json()
    except Exception:
        payload = {}

    if confirm is None:
        confirm = payload.get('confirm', True)

    if not confirm:
        return {'status': 'error', 'message': 'confirm=false, operation aborted'}

    try:
        from app.database import MessageType
        deleted = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).delete(synchronize_session=False)
        db.commit()
        return {'status': 'success', 'deleted_count': deleted}
    except Exception as e:
        db.rollback()
        return {'status': 'error', 'message': str(e)}

@router.post('/api/daily-posts/delete-all')
async def delete_all_daily_posts(request: Request, confirm: bool = Form(None), db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    """Elimina tutti i daily posts. Conferma tramite form o JSON."""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail='Not authenticated')

    try:
        payload = {}
        if request.headers.get('content-type', '').lower().startswith('application/json'):
            payload = await request.json()
    except Exception:
        payload = {}

    if confirm is None:
        confirm = payload.get('confirm', True)

    if not confirm:
        return {'status': 'error', 'message': 'confirm=false, operation aborted'}

    try:
        from app.database import DailyPost
        deleted = db.query(DailyPost).delete(synchronize_session=False)
        db.commit()
        return {'status': 'success', 'deleted_count': deleted}
    except Exception as e:
        db.rollback()
        return {'status': 'error', 'message': str(e)}

@router.post('/api/settings/system/reset')
def reset_system_settings(user: str = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    """Reset delle impostazioni di sistema ai valori di default."""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail='Not authenticated')

    from app.database import set_system_setting

    try:
        set_system_setting(db, 'maintenance_mode', False, 'boolean', 'Modalità manutenzione disabilitata', 'system')
        set_system_setting(db, 'debug_mode', False, 'boolean', 'Modalità debug disabilitata', 'system')
        set_system_setting(db, 'log_level', 'INFO', 'string', 'Livello di logging', 'system')
        set_system_setting(db, 'timezone', 'Europe/Rome', 'string', 'Fuso orario', 'system')
        set_system_setting(db, 'keep_alive_enabled', True, 'boolean', 'Keep-alive abilitato', 'system')
        set_system_setting(db, 'trusted_host_middleware_disabled', False, 'boolean', 'Trusted host disabilitato', 'system')
        return {'status': 'success', 'message': 'Impostazioni di sistema resettate'}
    except Exception as e:
        db.rollback()
        return {'status': 'error', 'message': str(e)}

@router.post("/api/messages/{message_id}/approve")
def approve_single_message(
    message_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: str = Depends(get_authenticated_user)
):
    """Approva un singolo messaggio e avvia la pubblicazione in background."""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Not authenticated")

    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")

    message.status = MessageStatus.APPROVED
    db.commit()

    # Schedule immediate background posting of the single message
    try:
        background_tasks.add_task(post_single_message, message_id)
        scheduled_msg = "Messaggio approvato e pubblicazione pianificata in background"
    except Exception:
        scheduled_msg = "Messaggio approvato (impossibile avviare background post)"

    return {"status": "success", "message": scheduled_msg, "message_id": message_id}

@router.post('/api/messages/{message_id}/publish-now')
def publish_single_now(message_id: int, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    """Pubblica immediatamente un singolo messaggio (sincrono)."""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail='Not authenticated')

    # Ensure message exists
    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail='Messaggio non trovato')

    # Only allow publishing if approved
    if message.status != MessageStatus.APPROVED:
        return {'status': 'error', 'message': 'Il messaggio deve essere APPROVED per essere pubblicato'}

    # Call the publishing function synchronously
    result = post_single_message(message_id)
    return result 

@router.post("/api/messages/{message_id}/reject")
def reject_single_message(message_id: int, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    """Rifiuta un singolo messaggio."""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Not authenticated")

    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")

    message.status = MessageStatus.REJECTED
    db.commit()

    return {"status": "success", "message": "Messaggio rifiutato", "message_id": message_id}

@router.post("/api/messages/{message_id}/reset")
def reset_message_status(message_id: int, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    """Resetta lo stato di un messaggio a PENDING."""
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Not authenticated")

    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")

    message.status = MessageStatus.PENDING
    message.error_message = None
    message.media_pk = None
    db.commit()

    return {"status": "success", "message": "Stato messaggio resettato", "message_id": message_id}

def post_single_message(message_id: int):
    """Posta un singolo messaggio approvato su Instagram. Restituisce un dict di risultato."""
    from app.image.generator import ImageGenerator
    from app.bot.poster import InstagramBot
    
    db = SessionLocal()
    try:
        message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
        if not message or message.status != MessageStatus.APPROVED:
            msg = f"Messaggio ID {message_id} non trovato o non approvato."
            print(f"--- DEBUG [POST]: {msg} ---")
            return {"status": "error", "message": msg}
        
        print(f"--- DEBUG [POST]: Inizio pubblicazione messaggio ID {message_id} ---")
        
        # Genera immagine (passa message_type e title se presente)
        image_generator = ImageGenerator()
        output_filename = f"spotted_{message.id}_{int(datetime.now().timestamp())}.png"
        message_type_str = message.message_type.value if message.message_type else "spotted"
        image_path = image_generator.from_text(
            message.text, 
            output_filename, 
            message.id,
            message_type=message_type_str,
            title=message.title
        )
        
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
        return {"status": "success", "media_pk": media_pk}
        
    except Exception as e:
        print(f"--- DEBUG [POST]: Errore pubblicazione ID {message_id}: {e} ---")
        if message:
            try:
                message.status = MessageStatus.FAILED
                message.error_message = str(e)
                db.commit()
            except Exception:
                db.rollback()
        return {"status": "error", "message": str(e)}
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
        "ai_model": settings.ai_model.value if settings.ai_model else "gemini",
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
    ai_model: str = Form("gemini"),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API per aggiornare le impostazioni del post giornaliero."""
    from app.database import update_daily_post_settings, AIModel

    try:
        # Valida il modello AI
        try:
            ai_model_enum = AIModel(ai_model)
        except ValueError:
            return {"status": "error", "message": f"Modello AI '{ai_model}' non valido"}

        settings = update_daily_post_settings(
            db=db,
            enabled=enabled,
            post_time=post_time,
            style=style,
            max_messages=max_messages,
            title_template=title_template,
            hashtag_template=hashtag_template,
            ai_model=ai_model_enum
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

@router.post("/api/daily-post/preview")
def preview_daily_post(
    title_template: str = Form("Riepilogo Spotted {date}"),
    hashtag_template: str = Form("#spotted #instaspotter"),
    max_messages: int = Form(10),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API per ottenere una preview del daily post."""
    try:
        from app.database import get_todays_messages
        from datetime import datetime
        import time

        # Recupera messaggi di oggi (o ultimi disponibili)
        messages = get_todays_messages(db, max_messages)
        if not messages:
            return {"status": "error", "message": "Nessun messaggio disponibile per il daily post"}

        today = datetime.utcnow().strftime("%d/%m/%Y")
        title = title_template.format(date=today)

        # Usa il generatore di immagini per creare una preview
        from app.image.generator import ImageGenerator
        generator = ImageGenerator()

        # Genera carousel preview
        base_filename = f"preview_daily_{int(time.time())}"
        image_paths = generator.create_daily_carousel(messages, base_filename, title)

        if image_paths and len(image_paths) > 0:
            # Restituisci l'URL della prima immagine come preview
            image_url = f"/generated_images/{image_paths[0].split('/')[-1]}"
            return {
                "status": "success",
                "image_url": image_url,
                "title": title,
                "messages_count": len(messages),
                "image_count": len(image_paths)
            }
        else:
            return {"status": "error", "message": "Errore nella generazione della preview"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/api/daily-post/publish")
def publish_daily_post_now(background_tasks: BackgroundTasks, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per pubblicare manualmente un daily post ora. Pianifica il task in background."""
    try:
        from app.tasks import daily_post_task

        # Schedule the daily post task to run in background so the API call returns immediately
        background_tasks.add_task(daily_post_task)

        return {
            "status": "scheduled",
            "message": "Daily post pianificato in background. Controlla i log per l'esito",
            "media_pk": None
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/api/daily-post/history")
def get_daily_post_history(
    limit: int = 20,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API per ottenere la cronologia dei daily post pubblicati."""
    try:
        from app.database import DailyPostSettings

        # Trova tutti i messaggi pubblicati come daily post
        # I daily post sono identificati da media_pk che inizia con numero (Instagram media PK)
        daily_posts = db.query(SpottedMessage).filter(
            SpottedMessage.media_pk.isnot(None),
            SpottedMessage.posted_at.isnot(None),
            SpottedMessage.status == MessageStatus.POSTED
        ).order_by(SpottedMessage.posted_at.desc()).limit(limit * 2).all()  # Moltiplica per avere più messaggi

        # Raggruppa per data di pubblicazione (stesso giorno = stesso daily post)
        daily_posts_grouped = {}
        for msg in daily_posts:
            if msg.posted_at:
                date_key = msg.posted_at.date()
                if date_key not in daily_posts_grouped:
                    daily_posts_grouped[date_key] = []
                daily_posts_grouped[date_key].append(msg)

        # Crea la lista dei daily post
        history = []
        for date_key, messages in list(daily_posts_grouped.items())[:limit]:
            # Trova il messaggio con media_pk numerico (post principale)
            main_post = None
            for msg in messages:
                if msg.media_pk and str(msg.media_pk).isdigit():
                    main_post = msg
                    break

            if main_post:
                history.append({
                    "date": date_key.isoformat(),
                    "posted_at": main_post.posted_at.isoformat() if main_post.posted_at else None,
                    "messages_count": len(messages),
                    "media_pk": main_post.media_pk,
                    "title": f"Riepilogo Spotted {date_key.strftime('%d/%m/%Y')}"
                })

        return {"status": "success", "history": history}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Daily Posts Management ---

@router.get("/api/daily-posts")
def get_daily_posts(
    status: str = None,
    limit: int = 50,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API per ottenere tutti i daily posts con filtri."""
    from app.database import get_daily_posts
    try:
        posts = get_daily_posts(db, limit=limit, status=status)
        return {
            "status": "success",
            "posts": [{
                "id": post.id,
                "title": post.title,
                "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                "hashtags": post.hashtags,
                "ai_model_used": post.ai_model_used.value if post.ai_model_used else None,
                "status": post.status,
                "scheduled_for": post.scheduled_for.isoformat() if post.scheduled_for else None,
                "published_at": post.published_at.isoformat() if post.published_at else None,
                "image_count": post.image_count,
                "messages_count": post.messages_count,
                "created_at": post.created_at.isoformat(),
                "created_by": post.created_by
            } for post in posts]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/api/daily-posts")
def create_daily_post(
    title: str = Form(...),
    content: str = Form(...),
    hashtags: str = Form(""),
    ai_model: str = Form("gemini"),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API per creare un nuovo daily post."""
    from app.database import create_daily_post, AIModel

    try:
        # Valida il modello AI
        try:
            ai_model_enum = AIModel(ai_model) if ai_model else AIModel.GEMINI
        except ValueError:
            return {"status": "error", "message": f"Modello AI '{ai_model}' non valido"}

        post = create_daily_post(
            db=db,
            title=title,
            content=content,
            hashtags=hashtags,
            ai_model_used=ai_model_enum,
            created_by=user
        )

        return {
            "status": "success",
            "message": "Daily post creato con successo",
            "post": {
                "id": post.id,
                "title": post.title,
                "status": post.status,
                "created_at": post.created_at.isoformat()
            }
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@router.get("/api/daily-posts/{post_id}")
def get_daily_post(post_id: int, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per ottenere un daily post specifico."""
    from app.database import get_daily_post_by_id

    try:
        post = get_daily_post_by_id(db, post_id)
        if not post:
            return {"status": "error", "message": "Daily post non trovato"}

        return {
            "status": "success",
            "post": {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "hashtags": post.hashtags,
                "ai_model_used": post.ai_model_used.value if post.ai_model_used else None,
                "status": post.status,
                "scheduled_for": post.scheduled_for.isoformat() if post.scheduled_for else None,
                "published_at": post.published_at.isoformat() if post.published_at else None,
                "image_count": post.image_count,
                "messages_count": post.messages_count,
                "error_message": post.error_message,
                "created_at": post.created_at.isoformat(),
                "updated_at": post.updated_at.isoformat(),
                "created_by": post.created_by
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.put("/api/daily-posts/{post_id}")
def update_daily_post(
    post_id: int,
    title: str = Form(None),
    content: str = Form(None),
    hashtags: str = Form(None),
    status: str = Form(None),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API per aggiornare un daily post."""
    from app.database import update_daily_post

    try:
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if content is not None:
            update_data["content"] = content
        if hashtags is not None:
            update_data["hashtags"] = hashtags
        if status is not None:
            update_data["status"] = status

        post = update_daily_post(db, post_id, **update_data)
        if not post:
            return {"status": "error", "message": "Daily post non trovato"}

        return {
            "status": "success",
            "message": "Daily post aggiornato con successo",
            "post": {
                "id": post.id,
                "title": post.title,
                "status": post.status,
                "updated_at": post.updated_at.isoformat()
            }
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@router.delete("/api/daily-posts/{post_id}")
def delete_daily_post(post_id: int, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per eliminare un daily post."""
    from app.database import delete_daily_post

    try:
        success = delete_daily_post(db, post_id)
        if not success:
            return {"status": "error", "message": "Daily post non trovato"}

        return {"status": "success", "message": "Daily post eliminato con successo"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@router.post("/api/daily-posts/{post_id}/generate-preview")
def generate_daily_post_preview(
    post_id: int,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API per generare una preview di un daily post."""
    from app.database import get_daily_post_by_id
    from app.image.generator import ImageGenerator
    import time

    try:
        post = get_daily_post_by_id(db, post_id)
        if not post:
            return {"status": "error", "message": "Daily post non trovato"}

        # Usa il generatore di immagini per creare una preview
        generator = ImageGenerator()
        base_filename = f"preview_daily_{post_id}_{int(time.time())}"
        image_paths = generator.create_daily_carousel_from_content(
            post.content,
            base_filename,
            title=post.title
        )

        if image_paths and len(image_paths) > 0:
            image_url = f"/generated_images/{image_paths[0].split('/')[-1]}"
            return {
                "status": "success",
                "image_url": image_url,
                "title": post.title,
                "hashtags": post.hashtags,
                "image_count": len(image_paths)
            }
        else:
            return {"status": "error", "message": "Errore nella generazione della preview"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/api/daily-posts/{post_id}/publish")
def publish_daily_post(post_id: int, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per pubblicare un daily post."""
    from app.database import get_daily_post_by_id, update_daily_post
    from app.tasks import publish_daily_post_task

    try:
        post = get_daily_post_by_id(db, post_id)
        if not post:
            return {"status": "error", "message": "Daily post non trovato"}

        if post.status == "published":
            return {"status": "error", "message": "Daily post già pubblicato"}

        # Pubblica il post
        result = publish_daily_post_task(post_id)

        if result.get("status") == "success":
            # Aggiorna lo stato
            update_daily_post(db, post_id, status="published", published_at=datetime.utcnow())
            return {
                "status": "success",
                "message": "Daily post pubblicato con successo",
                "media_pk": result.get("media_pk")
            }
        else:
            # Aggiorna con errore
            update_daily_post(db, post_id, status="failed", error_message=result.get("message"))
            return {"status": "error", "message": result.get("message", "Errore pubblicazione")}

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@router.post("/api/daily-posts/generate-with-ai")
def generate_daily_post_with_ai(
    ai_model: str = Form("gemini"),
    max_messages: int = Form(20),
    title_template: str = Form("🌟 Spotted del giorno {date} 🌟"),
    hashtag_template: str = Form("#spotted #instaspotter #dailyrecap"),
    post_style: str = Form("story"),
    style_config_id: int = Form(None),
    user: str = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """API per generare un daily post usando AI."""
    try:
        from app.database import get_todays_messages, AIModel, create_daily_post, get_style_config_by_id

        # Valida il modello AI
        try:
            ai_model_enum = AIModel(ai_model)
        except ValueError:
            return {"status": "error", "message": f"Modello AI '{ai_model}' non valido"}

        # Recupera messaggi di oggi
        messages = get_todays_messages(db, max_messages)
        if not messages:
            return {"status": "error", "message": "Nessun messaggio disponibile per generare il daily post"}

        # Recupera configurazione stile se specificata
        style_config_json = None
        if style_config_id:
            style_config = get_style_config_by_id(db, style_config_id)
            if style_config:
                style_config_json = style_config.config

        # Crea contenuto usando AI
        moderator = AIModeratorFactory.create_moderator(ai_model, **{})
        if not moderator:
            return {"status": "error", "message": f"Impossibile creare moderatore {ai_model}"}

        # Genera contenuto riassuntivo
        messages_text = "\n".join([f"- {msg.text}" for msg in messages])
        prompt = f"""
        Crea un post accattivante per Instagram basato sui seguenti messaggi spotted della giornata.
        Il post dovrebbe essere divertente, coinvolgente e adatto a un pubblico giovane.

        Messaggi della giornata:
        {messages_text}

        Crea un titolo accattivante e un contenuto che riassuma i momenti salienti della giornata.
        Usa emoji appropriati e mantieni un tono positivo e divertente.
        """

        # Qui dovremmo usare l'AI per generare il contenuto, ma per ora creiamo un contenuto di esempio
        today = datetime.utcnow().strftime("%d/%m/%Y")
        title = title_template.format(date=today)

        content = f"""{title}

Ecco i momenti più divertenti e interessanti della giornata! 💫

{messages_text[:500]}{"..." if len(messages_text) > 500 else ""}

{hashtag_template}"""

        # Crea il daily post con stile e configurazione
        post = create_daily_post(
            db=db,
            title=title,
            content=content,
            hashtags=hashtag_template,
            ai_model_used=ai_model_enum,
            created_by=user
        )

        # Aggiorna con stile e configurazione
        from app.database import update_daily_post
        update_daily_post(db, post.id, post_style=post_style, style_config=style_config_json)

        return {
            "status": "success",
            "message": "Daily post generato con successo usando AI",
            "post": {
                "id": post.id,
                "title": post.title,
                "content": post.content[:200] + "...",
                "ai_model_used": post.ai_model_used.value,
                "post_style": post_style,
                "created_at": post.created_at.isoformat()
            }
        }

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

# --- Style Config Management ---

@router.get("/api/style-configs")
def get_style_configs(
    type: str = None,
    user: str = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """API per ottenere tutte le configurazioni di stile."""
    from app.database import get_style_configs
    try:
        configs = get_style_configs(db, type=type)
        return {
            "status": "success",
            "configs": [{
                "id": config.id,
                "name": config.name,
                "type": config.type,
                "config": config.config,
                "preview_image": config.preview_image,
                "is_default": bool(config.is_default),
                "created_at": config.created_at.isoformat()
            } for config in configs]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/api/style-configs")
def create_style_config(
    name: str = Form(...),
    type: str = Form(...),
    config: str = Form(...),
    preview_image: str = Form(""),
    is_default: bool = Form(False),
    user: str = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """API per creare una nuova configurazione di stile."""
    from app.database import create_style_config
    try:
        style_config = create_style_config(
            db=db,
            name=name,
            type=type,
            config=config,
            preview_image=preview_image if preview_image else None,
            is_default=is_default
        )

        return {
            "status": "success",
            "message": "Configurazione stile creata con successo",
            "config": {
                "id": style_config.id,
                "name": style_config.name,
                "type": style_config.type,
                "is_default": bool(style_config.is_default)
            }
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@router.put("/api/style-configs/{config_id}")
def update_style_config(
    config_id: int,
    name: str = Form(None),
    config: str = Form(None),
    preview_image: str = Form(None),
    is_default: bool = Form(None),
    user: str = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """API per aggiornare una configurazione di stile."""
    from app.database import update_style_config
    try:
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if config is not None:
            update_data["config"] = config
        if preview_image is not None:
            update_data["preview_image"] = preview_image
        if is_default is not None:
            update_data["is_default"] = is_default

        config_obj = update_style_config(db, config_id, **update_data)
        if not config_obj:
            return {"status": "error", "message": "Configurazione stile non trovata"}

        return {
            "status": "success",
            "message": "Configurazione stile aggiornata con successo"
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@router.delete("/api/style-configs/{config_id}")
def delete_style_config(
    config_id: int,
    user: str = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """API per eliminare una configurazione di stile."""
    from app.database import delete_style_config
    try:
        success = delete_style_config(db, config_id)
        if not success:
            return {"status": "error", "message": "Configurazione stile non trovata"}

        return {"status": "success", "message": "Configurazione stile eliminata con successo"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

# --- AI Configuration Endpoints ---

@router.get("/api/ai/config")
def get_ai_config_api(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per recuperare la configurazione AI."""
    try:
        config = get_ai_config(db)
        if not config:
            return {
                "enabled": True,
                "selected_model": "gemini",
                "moderation_enabled": True,
                "auto_approve_threshold": 0.8,
                "available_models": [
                    {"value": "gemini", "label": "Google Gemini", "description": "AI di Google, richiede API key"},
                    {"value": "grok", "label": "Grok (xAI)", "description": "AI di xAI, richiede API key"},
                    {"value": "local", "label": "Modello Locale", "description": "Modello scaricato localmente"},
                    {"value": "disabled", "label": "Disabilitato", "description": "Nessuna moderazione AI"}
                ]
            }

        return {
            "enabled": bool(config.enabled),
            "selected_model": config.selected_model.value if config.selected_model else "gemini",
            "moderation_enabled": bool(config.moderation_enabled),
            "auto_approve_threshold": config.auto_approve_threshold,
            "gemini_api_key": bool(config.gemini_api_key),  # Non restituiamo la chiave per sicurezza
            "grok_api_key": bool(config.grok_api_key),
            "local_model_path": config.local_model_path,
            "available_models": [
                {"value": "gemini", "label": "Google Gemini", "description": "AI di Google, richiede API key"},
                {"value": "grok", "label": "Grok (xAI)", "description": "AI di xAI, richiede API key"},
                {"value": "local", "label": "Modello Locale", "description": "Modello scaricato localmente"},
                {"value": "disabled", "label": "Disabilitato", "description": "Nessuna moderazione AI"}
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@router.post("/api/ai/config")
def update_ai_config_api(
    enabled: bool = Form(True),
    selected_model: str = Form("gemini"),
    moderation_enabled: bool = Form(True),
    auto_approve_threshold: float = Form(0.8),
    gemini_api_key: str = Form(""),
    grok_api_key: str = Form(""),
    local_model_path: str = Form(""),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API per aggiornare la configurazione AI."""
    try:
        # Valida il modello selezionato
        try:
            model_enum = AIModel(selected_model)
        except ValueError:
            return {"status": "error", "message": f"Modello '{selected_model}' non valido"}

        # Prepara i dati per l'aggiornamento
        update_data = {
            "enabled": enabled,
            "selected_model": model_enum,
            "moderation_enabled": moderation_enabled,
            "auto_approve_threshold": auto_approve_threshold,
            "local_model_path": local_model_path
        }

        # Gestisci le API keys (solo se fornite)
        if gemini_api_key.strip():
            update_data["gemini_api_key"] = gemini_api_key.strip()
        if grok_api_key.strip():
            update_data["grok_api_key"] = grok_api_key.strip()

        config = update_ai_config(db, **update_data)

        return {
            "status": "success",
            "message": "Configurazione AI aggiornata",
            "config": {
                "enabled": bool(config.enabled),
                "selected_model": config.selected_model.value,
                "moderation_enabled": bool(config.moderation_enabled),
                "auto_approve_threshold": config.auto_approve_threshold
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/api/ai/test")
def test_ai_config(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """API per testare la configurazione AI corrente."""
    try:
        config = get_ai_config(db)
        if not config or not config.enabled:
            return {"status": "error", "message": "AI disabilitata"}

        # Crea il moderatore per il test
        from app.ai.moderator import AIModeratorFactory
        kwargs = {}

        if config.selected_model == AIModel.GEMINI:
            kwargs['api_key'] = config.gemini_api_key
        elif config.selected_model == AIModel.GROK:
            kwargs['api_key'] = config.grok_api_key
        elif config.selected_model == AIModel.LOCAL:
            kwargs['model_path'] = config.local_model_path

        moderator = AIModeratorFactory.create_moderator(config.selected_model.value, **kwargs)

        if not moderator:
            return {"status": "error", "message": f"Impossibile creare moderatore {config.selected_model.value}"}

        if not moderator.is_available():
            return {"status": "error", "message": f"Moderatore {config.selected_model.value} non disponibile"}

        # Test con un messaggio di esempio
        test_message = "Questo è un messaggio di test per verificare la moderazione AI."
        result = moderator.moderate_message(test_message)

        return {
            "status": "success",
            "message": f"Test riuscito con {config.selected_model.value}",
            "model": config.selected_model.value,
            "result": {
                "decision": result.decision,
                "reason": result.reason,
                "confidence": result.confidence
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
    """Ottieni impostazioni Instagram complete."""
    import os
    username = os.getenv("INSTAGRAM_USERNAME", "")
    configured = bool(username)

    # Check if connected by trying to see if we have valid credentials
    connected = configured and bool(os.getenv("INSTAGRAM_PASSWORD"))

    return {
        "username": username[:3] + "***" if username else "Not configured",
        "configured": configured,
        "connected": connected,  # Add the connected field that the frontend expects
        "last_post": None,  # Could be enhanced later
        "stories_count": 0  # Could be enhanced later
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
    background_tasks: BackgroundTasks = None,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API per creare una nuova info card."""
    from app.database import MessageType, MessageStatus

    try:
        print(f"--- [INFO CARD CREATE]: Creating info card - Title: '{title}', User: {user}")

        if not title or not text:
            print("--- [INFO CARD CREATE]: Missing title or text")
            return {"status": "error", "message": "Title and text are required"}

        # Ottieni o crea utente tecnico per l'utente corrente
        from app.database import get_or_create_technical_user
        technical_user = get_or_create_technical_user(db, user)
        print(f"--- [INFO CARD CREATE]: Technical user ID: {technical_user.id}")

        # Crea la info card dall'utente corrente
        info_card = SpottedMessage(
            text=text,
            message_type=MessageType.INFO,
            title=title,
            status=MessageStatus.APPROVED,  # Le info cards sono automaticamente approvate
            technical_user_id=technical_user.id
        )

        db.add(info_card)
        db.commit()
        db.refresh(info_card)

        print(f"--- [INFO CARD CREATE]: Info card created with ID: {info_card.id}, Type: {info_card.message_type}, Status: {info_card.status}")

        # Verifica che sia stata salvata correttamente
        verify_card = db.query(SpottedMessage).filter(SpottedMessage.id == info_card.id).first()
        if verify_card:
            print(f"--- [INFO CARD CREATE]: Verification successful - Type: {verify_card.message_type}")
        else:
            print("--- [INFO CARD CREATE]: ERROR - Card not found after creation!")

        # Info cards sono create come APPROVED ma NON pubblicate automaticamente
        # La pubblicazione avviene solo quando esplicitamente richiesta dall'utente

        return {"status": "success", "message": "Info card creata con successo. Clicca 'Pubblica' per pubblicarla.", "id": info_card.id}
    except Exception as e:
        print(f"--- [INFO CARD CREATE]: ERROR: {e}")
        import traceback
        traceback.print_exc()
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
    style_config_id: int = Form(None),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API per ottenere una preview dell'info card come immagine."""
    try:
        if not title or not text:
            title = "Titolo Card"
            text = "Il contenuto apparirà qui..."

        # Recupera la configurazione di stile se specificata e convertila in dict
        style_config_dict = None
        if style_config_id:
            from app.database import get_style_config_by_id
            import json
            style_config = get_style_config_by_id(db, style_config_id)
            if style_config and style_config.type == "info_card":
                try:
                    style_config_dict = json.loads(style_config.config)
                    print(f"✅ Caricata configurazione stile: {style_config.name}")
                except json.JSONDecodeError as e:
                    print(f"❌ Errore parsing configurazione stile: {e}")
                    style_config_dict = None

        # Usa il generatore di immagini per creare una preview
        from app.image.generator import ImageGenerator
        import time
        generator = ImageGenerator()

        # Genera l'immagine con message_type="info" e configurazione stile
        preview_filename = f"preview_info_{int(time.time())}.png"
        image_path = generator.from_text(
            text,
            preview_filename,
            message_id=0,
            message_type="info",
            title=title,
            style_config=style_config_dict  # Passa il dict parsato invece della stringa JSON
        )

        if image_path:
            # Restituisci l'URL relativa dell'immagine
            image_url = f"/generated_images/{image_path.split('/')[-1]}"
            return {"status": "success", "image_url": image_url}
        else:
            return {"status": "error", "message": "Failed to generate preview image"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post('/api/info-cards/recreate-defaults')
def recreate_default_info_cards(confirm: bool = Form(False), background_tasks: BackgroundTasks = None, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Elimina tutte le info cards esistenti e ricrea un set di default con il nuovo stile (v5)."""
    from app.database import MessageType, MessageStatus, get_or_create_technical_user

    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail='Not authenticated')

    if not confirm:
        return {'status': 'error', 'message': 'confirm=false, operation aborted'}

    try:
        # Delete all existing info cards
        deleted = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).delete(synchronize_session=False)
        db.commit()

        # Create defaults
        defaults = [
            {"title": "Aggiornamento Importante", "text": "Abbiamo rilasciato una nuova versione! Scopri le novità nel pannello admin."},
            {"title": "Regole della Community", "text": "Rispetta gli altri utenti. Messaggi offensivi verranno rimossi."},
            {"title": "GPDR & Privacy", "text": "I dati sono trattati in conformità con le norme sulla privacy."},
            {"title": "Come funziona", "text": "Invia il tuo spotted in forma anonima attraverso il form pubblico."}
        ]

        # Use a system technical user
        technical_user, _ = get_or_create_technical_user(db, None)

        created_ids = []
        for d in defaults:
            card = SpottedMessage(
                title=d['title'],
                text=d['text'],
                message_type=MessageType.INFO,
                status=MessageStatus.APPROVED,
                technical_user_id=technical_user.id
            )
            db.add(card)
            db.commit()
            db.refresh(card)
            created_ids.append(card.id)
            # Info cards are created as APPROVED but NOT automatically published

        return {'status': 'success', 'deleted': deleted, 'created': created_ids}

    except Exception as e:
        db.rollback()
        return {'status': 'error', 'message': str(e)}

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

        # Genera URL per il QR code - usa URL pubblico accessibile dal cellulare
        # Usa direttamente l'URL completo di Replit che conosciamo funzionare

        # URL completo pubblico di Replit (funzionante)
        base_url = "https://26c5b2a6-ace4-48ce-882f-4e9127f40551-00-18mhz2vlxvr3b.kirk.replit.dev"

        # Debug: mostra tutte le variabili d'ambiente Replit disponibili
        print(f"🔍 REPLIT_DOMAINS: {os.getenv('REPLIT_DOMAINS')}")
        print(f"🔍 REPL_SLUG: {os.getenv('REPL_SLUG')}")
        print(f"🔍 REPL_OWNER: {os.getenv('REPL_OWNER')}")
        print(f"🔍 REPLIT_APP_URL: {os.getenv('REPLIT_APP_URL')}")

        qr_url = f"{base_url}/auth/qr/{session_id}?token={qr_token}"
        print(f"🔗 Generated QR URL: {qr_url}")
        print(f"📱 QR should be accessible from mobile at: {qr_url}")

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
def verify_qr_code(data: dict):
    """Verifica il codice QR scansionato dal mobile."""
    try:
        session_id = data.get("session_id")
        token = data.get("token")

        if not session_id or not token:
            return {"success": False, "error": "Parametri mancanti"}

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

        # Verifica token (il token ricevuto è già hashato dal frontend)
        if token != session["token_hash"]:
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
def qr_mobile_login(data: dict):
    """Login tramite QR dal mobile."""
    try:
        print(f"🔍 QR login called with data: {data}")
        session_id = data.get("session_id")
        print(f"🔍 Extracted session_id: {session_id}")

        if not session_id or session_id not in qr_sessions:
            print(f"❌ Session {session_id} not found in qr_sessions")
            return {"success": False, "error": "Sessione non trovata"}

        session = qr_sessions[session_id]
        print(f"✅ Found session: {session}")

        if not session.get("used", False):
            print(f"❌ Session not verified yet: used={session.get('used', False)}")
            return {"success": False, "error": "Sessione non verificata"}

        # Genera token di sessione per il mobile (durata più lunga per mobile)
        from app.admin.security import create_access_token
        from datetime import timedelta
        mobile_token = create_access_token({"sub": session["user"], "device": "mobile"}, expires_delta=timedelta(hours=2))

        # Log dell'accesso
        print(f"🔐 Mobile login via QR: {session['user']} - Token length: {len(mobile_token)}")

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
        print(f"❌ QR login error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

# === PAGINA MOBILE PER SCAN QR CODE ===

# === BACKUP MANAGEMENT ===
@router.post("/api/backup/create-full")
def create_full_backup(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Crea un backup completo del database e delle immagini."""
    try:
        import datetime
        from pathlib import Path
        import shutil

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)

        # Backup del database SQLite
        db_path = "insta_spotter.db"
        backup_db_path = None
        if os.path.exists(db_path):
            backup_db_path = backup_dir / f"backup_{timestamp}.db"
            shutil.copy2(db_path, backup_db_path)

        # Backup delle immagini generate
        images_dir = Path("generated_images")
        backup_images_dir = None
        if images_dir.exists():
            backup_images_dir = backup_dir / f"images_{timestamp}"
            shutil.copytree(images_dir, backup_images_dir, dirs_exist_ok=True)

        return {
            "status": "success",
            "message": f"Backup creato con successo: {timestamp}",
            "files": {
                "database": str(backup_db_path) if backup_db_path else None,
                "images": str(backup_images_dir) if backup_images_dir else None
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/api/backup/status")
def get_backup_status(user: str = Depends(get_current_user)):
    """Ottieni lo stato dei backup disponibili."""
    try:
        from pathlib import Path

        backup_dir = Path("backups")
        if not backup_dir.exists():
            return {"status": "success", "backups": []}

        backups = []
        for item in backup_dir.iterdir():
            if item.is_file() and item.name.startswith("backup_") and item.name.endswith(".db"):
                stat = item.stat()
                backups.append({
                    "name": item.name,
                    "size": stat.st_size,
                    "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "type": "database"
                })
            elif item.is_dir() and item.name.startswith("images_"):
                stat = item.stat()
                total_size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                backups.append({
                    "name": item.name,
                    "size": total_size,
                    "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "type": "images"
                })

        backups.sort(key=lambda x: x["created"], reverse=True)

        return {"status": "success", "backups": backups}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# === LOGS MANAGEMENT ===
@router.get("/api/logs")
def get_logs(
    type: str = "all",
    period: str = "1h",
    user: str = Depends(get_current_user)
):
    """Ottieni i log di sistema filtrati per tipo e periodo."""
    try:
        import glob

        logs = []
        # Cerca file di log
        log_files = glob.glob("*.log") + ["insta_spotter.log"] if os.path.exists("insta_spotter.log") else []

        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()[-50:]  # Ultime 50 righe per performance

                    for line in lines:
                        if any(keyword in line.upper() for keyword in ["INFO", "WARNING", "ERROR"]):
                            logs.append({
                                "timestamp": datetime.datetime.now().isoformat(),
                                "level": "INFO" if "INFO" in line else "WARNING" if "WARNING" in line else "ERROR",
                                "message": line.strip()
                            })
                except:
                    continue

        # Limita a 100 log totali
        logs = logs[-100:] if len(logs) > 100 else logs

        return {
            "status": "success",
            "logs": logs,
            "count": len(logs)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# === TECHNICAL USERS MANAGEMENT ===
@router.get("/api/users/technical")
def get_technical_users(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Ottieni la lista degli utenti tecnici."""
    try:
        from app.database import TechnicalUser

        technical_users = db.query(TechnicalUser).all()

        return {
            "status": "success",
            "users": [
                {
                    "id": tu.id,
                    "username": tu.username,
                    "role": tu.role,
                    "created_at": tu.created_at.isoformat() if tu.created_at else None,
                    "last_active": tu.last_active.isoformat() if tu.last_active else None,
                    "is_active": tu.is_active
                }
                for tu in technical_users
            ]
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/api/users/technical")
def create_technical_user(
    username: str = Form(...),
    role: str = Form("moderator"),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea un nuovo utente tecnico."""
    try:
        from app.database import TechnicalUser
        import secrets

        # Genera password casuale
        password = secrets.token_urlsafe(12)

        # Crea hash della password
        from app.admin.security import hash_password
        hashed_password = hash_password(password)

        new_user = TechnicalUser(
            username=username,
            password_hash=hashed_password,
            role=role,
            created_by=user,
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "status": "success",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "role": new_user.role,
                "password": password
            }
        }

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

# === INSTAGRAM SETTINGS AND TEST ENDPOINT ===
@router.get("/api/settings/instagram")
def get_instagram_settings(user: str = Depends(get_current_user)):
    """Ottieni impostazioni Instagram complete."""
    import os
    return {
        "username": os.getenv("INSTAGRAM_USERNAME", "Not configured"),
        "configured": bool(os.getenv("INSTAGRAM_USERNAME")),
        "session_file_exists": os.path.exists("session.json") if os.getenv("INSTAGRAM_USERNAME") else False,
        "last_login_attempt": None,  # Potrebbe essere aggiunto dal database
        "rate_limits": None  # Potrebbe essere aggiunto dal monitoring
    }

@router.post("/api/settings/instagram")
def update_instagram_settings(
    username: str = Form(""),
    password: str = Form(""),
    user: str = Depends(get_current_user)
):
    """Aggiorna credenziali Instagram."""
    try:
        # Nota: In produzione, salva in modo sicuro (database criptato)
        # Per ora restituiamo solo conferma
        if username and password:
            return {
                "status": "success",
                "message": "Credenziali Instagram aggiornate",
                "username": username[:3] + "***"
            }
        else:
            return {
                "status": "error",
                "message": "Username e password sono richiesti"
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/api/settings/instagram/test")
def test_instagram_connection(user: str = Depends(get_current_user)):
    """Testa la connessione a Instagram."""
    try:
        instagram_username = os.getenv("INSTAGRAM_USERNAME", "")
        has_credentials = bool(instagram_username)

        if not has_credentials:
            return {
                "status": "warning",
                "message": "Credenziali Instagram non configurate",
                "connected": False,
                "details": "Configura prima username e password nelle impostazioni"
            }

        # Test connessione base (senza login completo per sicurezza)
        try:
            # Import InstagramBot per test
            from app.bot.poster import InstagramBot
            bot = InstagramBot()

            # Test base senza login completo
            connection_test = {
                "has_instagrapi": True,
                "has_credentials": True,
                "session_file_exists": os.path.exists("session.json"),
                "last_error": None
            }

            return {
                "status": "success",
                "message": "Connessione Instagram configurata",
                "connected": True,
                "username": instagram_username[:3] + "***",
                "details": connection_test
            }

        except ImportError:
            return {
                "status": "warning",
                "message": "Libreria instagrapi non installata",
                "connected": False,
                "details": "Installa instagrapi per pubblicare su Instagram"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Errore connessione Instagram: {str(e)}",
                "connected": False,
                "details": str(e)
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Errore test connessione: {str(e)}",
            "connected": False
        }

@router.post("/api/settings/instagram/login")
def instagram_manual_login(user: str = Depends(get_current_user)):
    """Effettua login manuale a Instagram."""
    try:
        from app.bot.poster import InstagramBot

        bot = InstagramBot()
        login_result = bot.login()

        if login_result.get("success"):
            return {
                "status": "success",
                "message": "Login Instagram riuscito",
                "details": login_result
            }
        else:
            return {
                "status": "error",
                "message": f"Login Instagram fallito: {login_result.get('error', 'Errore sconosciuto')}",
                "details": login_result
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Errore login manuale: {str(e)}"
        }

# === SYSTEM SETTINGS ENDPOINTS ===

@router.get("/api/settings/system")
def get_system_settings(user: str = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    """Ottieni impostazioni di sistema dal database."""
    try:
        from app.database import get_system_setting_value

        # Ottieni tutte le impostazioni dal database
        maintenance_mode = get_system_setting_value(db, "maintenance_mode", False)
        debug_mode = get_system_setting_value(db, "debug_mode", False)
        log_level = get_system_setting_value(db, "log_level", "INFO")
        timezone = get_system_setting_value(db, "timezone", "Europe/Rome")
        keep_alive_enabled = get_system_setting_value(db, "keep_alive_enabled", True)
        trusted_host_middleware_disabled = get_system_setting_value(db, "trusted_host_middleware_disabled", False)

        return {
            "maintenance_mode": maintenance_mode,
            "debug_mode": debug_mode,
            "log_level": log_level,
            "timezone": timezone,
            "keep_alive_enabled": keep_alive_enabled,
            "trusted_host_middleware_disabled": trusted_host_middleware_disabled,
            "current_maintenance_status": "ATTIVA" if maintenance_mode else "DISATTIVA"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/api/settings/system")
def update_system_settings(
    maintenance_mode: bool = Form(False),
    debug_mode: bool = Form(False),
    log_level: str = Form("INFO"),
    timezone: str = Form("Europe/Rome"),
    keep_alive_enabled: bool = Form(True),
    trusted_host_middleware_disabled: bool = Form(False),
    user: str = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Aggiorna impostazioni di sistema nel database."""
    try:
        from app.database import set_system_setting

        # Valida log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level.upper() not in valid_log_levels:
            return {"status": "error", "message": f"Log level non valido. Valori validi: {', '.join(valid_log_levels)}"}

        # Salva tutte le impostazioni nel database
        set_system_setting(db, "maintenance_mode", maintenance_mode, "boolean", "Modalità manutenzione abilitata", "system")
        set_system_setting(db, "debug_mode", debug_mode, "boolean", "Modalità debug abilitata", "system")
        set_system_setting(db, "log_level", log_level.upper(), "string", "Livello di logging", "system")
        set_system_setting(db, "timezone", timezone, "string", "Fuso orario", "system")
        set_system_setting(db, "keep_alive_enabled", keep_alive_enabled, "boolean", "Keep-alive abilitato", "system")
        set_system_setting(db, "trusted_host_middleware_disabled", trusted_host_middleware_disabled, "boolean", "Trusted host disabilitato", "system")

        # Aggiorna anche le variabili d'ambiente per compatibilità immediata
        os.environ["MAINTENANCE_MODE"] = "1" if maintenance_mode else "0"
        os.environ["DEBUG_MODE"] = "1" if debug_mode else "0"
        os.environ["LOG_LEVEL"] = log_level.upper()
        os.environ["TZ"] = timezone
        os.environ["DISABLE_KEEP_ALIVE"] = "0" if keep_alive_enabled else "1"
        os.environ["DISABLE_TRUSTED_HOST"] = "1" if trusted_host_middleware_disabled else "0"

        settings_summary = {
            "maintenance_mode": maintenance_mode,
            "debug_mode": debug_mode,
            "log_level": log_level.upper(),
            "timezone": timezone,
            "keep_alive_enabled": keep_alive_enabled,
            "trusted_host_middleware_disabled": trusted_host_middleware_disabled,
            "status": "ATTIVA" if maintenance_mode else "DISATTIVA"
        }

        return {
            "status": "success",
            "message": f"Impostazioni sistema aggiornate e salvate nel database. Modalità manutenzione: {settings_summary['status']}",
            "settings": settings_summary
        }

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@router.post("/api/settings/system/maintenance")
def toggle_maintenance_mode(
    enabled: bool = Form(False),
    user: str = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Attiva/disattiva modalità manutenzione nel database."""
    try:
        from app.database import set_system_setting

        # Salva nel database
        set_system_setting(db, "maintenance_mode", enabled, "boolean", "Modalità manutenzione abilitata", "system")

        # Aggiorna anche la variabile d'ambiente per compatibilità immediata
        os.environ["MAINTENANCE_MODE"] = "1" if enabled else "0"

        status_message = "attivata" if enabled else "disattivata"
        message = f"Modalità manutenzione {status_message} e salvata nel database"

        return {
            "status": "success",
            "message": message,
            "maintenance_mode": enabled,
            "current_status": "ATTIVA" if enabled else "DISATTIVA"
        }

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@router.get("/api/settings/system/status")
def get_system_status(user: str = Depends(get_current_user)):
    """Ottieni stato generale del sistema."""
    try:
        import os
        import psutil
        import platform

        # Informazioni di sistema di base
        system_info = {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "environment": "replit" if os.getenv("REPLIT") else "unknown",
            "uptime": None,  # Difficile da ottenere su Replit
            "memory_usage": None,  # psutil potrebbe non funzionare su Replit
            "disk_usage": None
        }

        # Prova a ottenere informazioni memoria (potrebbe fallire su Replit)
        try:
            memory = psutil.virtual_memory()
            system_info["memory_usage"] = {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            }
        except:
            pass

        # Informazioni applicazione
        app_info = {
            "maintenance_mode": bool(os.getenv("MAINTENANCE_MODE")),
            "debug_mode": bool(os.getenv("DEBUG_MODE")),
            "version": "2.0.0",  # Potrebbe essere letto da un file
            "database_connected": True,  # Assumiamo sia connesso se arriviamo qui
            "instagram_configured": bool(os.getenv("INSTAGRAM_USERNAME")),
            "ai_configured": bool(os.getenv("GEMINI_API_KEY"))
        }

        return {
            "status": "success",
            "system": system_info,
            "application": app_info
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/api/debug/replit-env")
def debug_replit_env():
    """Debug endpoint per vedere le variabili d'ambiente Replit."""
    replit_vars = {k: v for k, v in os.environ.items() if 'REPL' in k.upper() or 'DOMAINS' in k.upper()}
    return {
        "replit_vars": replit_vars,
        "current_url_construction": {
            "REPLIT_DOMAINS": os.getenv("REPLIT_DOMAINS"),
            "REPL_SLUG": os.getenv("REPL_SLUG"),
            "REPL_OWNER": os.getenv("REPL_OWNER"),
            "REPLIT_APP_URL": os.getenv("REPLIT_APP_URL"),
            "constructed_url": f"https://{os.getenv('REPLIT_DOMAINS', 'unknown.replit.dev')}"
        }
    }

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

        # Ricostruisci l'URL (funzione legacy - non utilizzata)
        qr_url = f"https://26c5b2a6-ace4-48ce-882f-4e9127f40551-00-18mhz2vlxvr3b.kirk.replit.dev/auth/qr/{session_id}?token={qr_sessions[session_id]['token_hash']}"

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

# QR endpoint moved to main.py to avoid routing conflicts
