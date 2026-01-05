from fastapi import APIRouter, Request, Depends, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from slowapi.util import get_remote_address
import logging
import secrets

from app.database import get_db, SpottedMessage, MessageStatus, get_or_create_technical_user, UserStatus
from app.tasks import moderate_message_task
from app.security import InputValidator, hash_ip, generate_csrf_token, verify_csrf_token
from config import settings

logger = logging.getLogger("insta_spotter")

router = APIRouter(
    prefix="/spotted",
    tags=["Web Interface"]
)

templates = Jinja2Templates(directory="app/web/templates")

# In-memory CSRF tokens (in produzione usa Redis o database)
csrf_tokens_store = {}

@router.get("/new", response_class=HTMLResponse)
def show_submission_form(request: Request):
    """Mostra il form di invio con token CSRF."""
    global csrf_tokens_store
    
    # Leggi i parametri dalla query string manualmente (più affidabile)
    success = request.query_params.get("success", "false").lower() == "true"
    error = request.query_params.get("error", None)
    
    # Genera token CSRF per il form
    csrf_token = generate_csrf_token()
    
    # Salva il token (in produzione usa session/database)
    client_ip = get_remote_address(request)
    csrf_tokens_store[csrf_token] = {
        "ip": client_ip,
        "timestamp": __import__("time").time()
    }
    
    # Pulisci token vecchi (> 1 ora)
    current_time = __import__("time").time()
    csrf_tokens_store = {k: v for k, v in csrf_tokens_store.items() if current_time - v["timestamp"] < 3600}
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "success": success,
        "error": error,
        "csrf_token": csrf_token  # Passa il token al template
    })

@router.post("/submit")
def handle_submission(
    request: Request,
    background_tasks: BackgroundTasks,
    message: str = Form(...),
    csrf_token: str = Form(...),
    technical_user_id: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Gestisce l'invio del form con protezione CSRF, rate limiting e identità tecnica.
    """
    client_ip = get_remote_address(request)
    hashed_ip = hash_ip(client_ip)
    
    try:
        # ============================================
        # 1. GESTISCI IDENTITÀ TECNICA
        # ============================================
        user, _ = get_or_create_technical_user(db, technical_user_id)
        
        # Controlla se l'utente è bloccato
        if user.status == UserStatus.BLOCKED:
            logger.warning(f"⚠️ Messaggio bloccato da utente tecnico {user.id} (IP: {hashed_ip})")
            redirect_url = f"{request.url.scheme}://{request.url.netloc}/spotted/new?error=Non+sei+autorizzato+a+inviare+messaggi."
            return RedirectResponse(url=redirect_url, status_code=303)

        # ============================================
        # 2. VERIFICA CSRF TOKEN
        # ============================================
        if csrf_token not in csrf_tokens_store:
            logger.warning(f"⚠️ CSRF token invalido da IP {hashed_ip}")
            redirect_url = f"{request.url.scheme}://{request.url.netloc}/spotted/new?error=Token+di+sicurezza+invalido.+Riprova."
            return RedirectResponse(
                url=redirect_url,
                status_code=303
            )
        
        del csrf_tokens_store[csrf_token]
        
        # ============================================
        # 3. VALIDA INPUT
        # ============================================
        try:
            validated_message = InputValidator.validate_message(message)
        except ValueError as e:
            logger.info(f"⚠️ Messaggio invalido da utente {user.id} (IP: {hashed_ip}): {str(e)}")
            redirect_url = f"{request.url.scheme}://{request.url.netloc}/spotted/new?error={str(e).replace(' ', '+')}"
            return RedirectResponse(
                url=redirect_url, 
                status_code=303
            )
        
        # ============================================
        # 4. SALVA MESSAGGIO
        # ============================================
        new_message = SpottedMessage(
            text=validated_message,
            status=MessageStatus.PENDING,
            author=user  # Associa l'utente al messaggio
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        logger.info(f"✓ Nuovo messaggio (ID: {new_message.id}) da utente {user.id} (IP: {hashed_ip})")
        
        # ============================================
        # 5. AVVIA MODERAZIONE IN BACKGROUND
        # ============================================
        background_tasks.add_task(moderate_message_task, new_message.id)
        
        redirect_url = f"{request.url.scheme}://{request.url.netloc}/spotted/new?success=true"
        
        return RedirectResponse(
            url=redirect_url,
            status_code=303
        )
    
    except Exception as e:
        logger.error(f"✗ Errore nell'invio messaggio da IP {hashed_ip}: {str(e)}")
        import traceback
        traceback.print_exc()
        redirect_url = f"{request.url.scheme}://{request.url.netloc}/spotted/new?error=Errore+del+server.+Riprova."
        return RedirectResponse(
            url=redirect_url,
            status_code=303
        )