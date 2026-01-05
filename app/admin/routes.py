from fastapi import APIRouter, Request, Depends, HTTPException, Form, Response, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db, SpottedMessage, MessageStatus
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
    if not user or isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Fetch all messages, keeping it simple
        messages_query = db.query(SpottedMessage).order_by(SpottedMessage.created_at.desc()).limit(200).all()

        # Manually build the response to ensure it's clean
        messages_data = [
            {
                "id": msg.id,
                "text": msg.text,
                "status": msg.status.value, # Safely get enum value
                "created_at": msg.created_at.isoformat(), # Use ISO format for JS
                "media_pk": msg.media_pk,
                "admin_note": msg.admin_note,
                "gemini_analysis": msg.gemini_analysis
            }
            for msg in messages_query
        ]
        
        # Return the clean data
        return {"messages": messages_data}

    except Exception as e:
        print(f"--- CRITICAL ERROR in get_dashboard_data: {e} ---")
        # If anything goes wrong, send a clear error
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")



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
        "messages": messages,
        "kpis": kpis,
        "chart_data": chart_data,
        "MessageStatus": MessageStatus,
        "current_user": user,
        "settings": settings # Pass settings to the template
    })

@router.post("/messages/{message_id}/approve", response_class=RedirectResponse)
def approve_message(request: Request, message_id: int, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    if isinstance(user, RedirectResponse): return user
    print(f"--- DEBUG: Richiesta di approvazione per messaggio ID: {message_id} ---")
    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        print(f"--- DEBUG: Messaggio ID: {message_id} non trovato. ---")
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
    
    print(f"--- DEBUG: Messaggio trovato. Cambio stato in APPROVED. ---")
    message.status = MessageStatus.APPROVED
    db.commit()
    print(f"--- DEBUG: Commit eseguito. Stato per ID {message_id} è ora APPROVED. ---")
    
    return RedirectResponse(url=str(request.url_for('show_dashboard')), status_code=303)

@router.post("/messages/{message_id}/reject", response_class=RedirectResponse)
def reject_message(request: Request, message_id: int, db: Session = Depends(get_db), user: str = Depends(get_authenticated_user)):
    if isinstance(user, RedirectResponse): return user
    message = db.query(SpottedMessage).filter(SpottedMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
    
    message.status = MessageStatus.REJECTED
    db.commit()
    
    return RedirectResponse(url=str(request.url_for('show_dashboard')), status_code=303)