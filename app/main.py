from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
from urllib.parse import urlparse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import asyncio
import httpx

from app.database import create_db_and_tables
from app.web import routes as web_routes
from app.admin import routes as admin_routes
from app.security import SECURITY_HEADERS, CORS_SETTINGS, setup_secure_logging

# Setup logging sicuro
logger = setup_secure_logging()

# --- Creazione dell'Applicazione ---

app = FastAPI(
    title="InstaSpotter",
    description="Bot per la pubblicazione di messaggi spotted anonimi su Instagram Stories.",
    version="1.0.0",
    docs_url=None,  # Disabilita Swagger UI in produzione
    redoc_url=None,  # Disabilita ReDoc in produzione
    openapi_url=None,  # Disabilita OpenAPI schema
)

# --- MIDDLEWARE DI SICUREZZA ---

# 1. CORS - Molto restrittivo
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_SETTINGS["allow_origins"],
    allow_credentials=CORS_SETTINGS["allow_credentials"],
    allow_methods=CORS_SETTINGS["allow_methods"],
    allow_headers=CORS_SETTINGS["allow_headers"],
    max_age=CORS_SETTINGS["max_age"],
)

# 2. Trusted Host - Solo domini conosciuti
# Possibilità di disabilitare temporaneamente il controllo impostando DISABLE_TRUSTED_HOST=1
replit_url = os.getenv("REPLIT_URL")
disable_trusted = os.getenv("DISABLE_TRUSTED_HOST", "0") == "1"
# Rileva se siamo su Replit (Replit imposta queste variabili d'ambiente)
is_replit = os.getenv("REPL_ID") is not None or os.getenv("REPL_SLUG") is not None or "replit" in os.getenv("HOME", "").lower()

# Su Replit, disabilita TrustedHost per evitare problemi con richieste interne
if is_replit:
    disable_trusted = True
    logger.info("🔵 Rilevato ambiente Replit - TrustedHostMiddleware disabilitato per compatibilità")

if not disable_trusted:
    # Costruisci la lista di host permessi dinamicamente usando REPLIT_URL se impostato
    allowed_hosts = ["localhost", "127.0.0.1", "*"]  # * permette qualsiasi host su Replit
    
    if replit_url:
        try:
            parsed = urlparse(replit_url)
            if parsed.hostname:
                allowed_hosts.append(parsed.hostname)
                # Aggiungi anche varianti comuni di Replit
                if ".replit.app" in parsed.hostname:
                    # Estrai il nome base
                    base_name = parsed.hostname.split(".")[0]
                    allowed_hosts.extend([
                        f"{base_name}.replit.app",
                        f"{base_name}.replit.dev",
                        "*.replit.app",
                        "*.replit.dev"
                    ])
        except Exception:
            logger.warning("Impossibile parsare REPLIT_URL per TrustedHostMiddleware")

    # Se siamo su Replit, aggiungi pattern comuni
    if is_replit:
        allowed_hosts.extend([
            "*.replit.app",
            "*.replit.dev",
            "*.repl.co",
            "*"  # Permetti qualsiasi host su Replit (per richieste interne)
        ])
        logger.info("Rilevato ambiente Replit - TrustedHost configurato per Replit")

    # Rimuovi duplicati mantenendo l'ordine
    allowed_hosts = list(dict.fromkeys(allowed_hosts))
    
    # Su Replit, usa una configurazione più permissiva
    if is_replit and "*" in allowed_hosts:
        # Su Replit, disabilita TrustedHost per evitare problemi con richieste interne
        logger.info("TrustedHostMiddleware disabilitato su Replit per compatibilità")
    else:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts,
        )
else:
    logger.info("TrustedHostMiddleware disabilitato tramite DISABLE_TRUSTED_HOST=1")

# 3. Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: {"detail": "Troppi richieste"})
app.add_middleware(SlowAPIMiddleware)

# --- SECURITY HEADERS MIDDLEWARE ---

@app.middleware("http")
async def add_security_headers(request, call_next):
    """Aggiunge headers di sicurezza a tutte le response."""
    response = await call_next(request)
    
    # Aggiungi headers di sicurezza
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    
    # Forza HTTPS (in produzione)
    if request.url.scheme != "http":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    return response

# --- Keep Alive Background Task per Replit ---

async def keep_alive_task():
    """Task in background che fa ping a se stesso ogni 5 minuti per mantenere Replit attivo."""
    await asyncio.sleep(60)  # Attendi 1 minuto dopo l'avvio
    
    # Costruisci l'URL corretto per Replit
    replit_url = os.getenv("REPLIT_URL")
    if replit_url:
        # Se REPLIT_URL è impostato, usalo
        base_url = replit_url.rstrip('/')
        # Assicurati che sia un URL valido (non l'URL di Replit stesso)
        if "replit.com" in base_url and not base_url.endswith(".replit.app"):
            # Se è l'URL di Replit, prova a costruire l'URL dell'app
            # Formato: https://NOME-REPL.utente.replit.app
            base_url = "http://localhost:8000"  # Fallback a localhost
            logger.warning("⚠ REPLIT_URL sembra essere l'URL di Replit invece dell'app. Uso localhost.")
    else:
        # Se non è impostato, usa localhost (per Replit interno)
        base_url = "http://localhost:8000"
    
    logger.info(f"🔄 Keep-alive task avviato. URL: {base_url}")
    
    while True:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{base_url}/health")
                if response.status_code == 200:
                    logger.info("✓ Keep-alive ping riuscito")
                else:
                    logger.warning(f"⚠ Keep-alive ping restituito status {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠ Keep-alive ping fallito: {e}")
        
        # Attendi 5 minuti (300 secondi) prima del prossimo ping
        await asyncio.sleep(300)

async def daily_post_scheduler():
    """Task in background che controlla ogni minuto se è ora di pubblicare il post giornaliero."""
    await asyncio.sleep(120)  # Attendi 2 minuti dopo l'avvio per dare tempo al sistema

    logger.info("📅 Daily post scheduler avviato - controlla ogni minuto")

    while True:
        try:
            from app.tasks import daily_post_task
            from app.database import get_daily_post_settings, SessionLocal
            from datetime import datetime

            # Controlla impostazioni daily post
            db = SessionLocal()
            try:
                settings = get_daily_post_settings(db)
                if settings and settings.enabled:
                    # Verifica se è ora di pubblicare
                    now = datetime.utcnow()
                    current_time = now.strftime("%H:%M")

                    if current_time == settings.post_time:
                        logger.info(f"🕐 Ora del daily post! Eseguo pubblicazione...")
                        result = await asyncio.get_event_loop().run_in_executor(None, daily_post_task)

                        if result["status"] == "success":
                            logger.info("✅ Daily post pubblicato con successo!")
                        elif result["status"] == "simulated":
                            logger.info("🎭 Daily post simulato (bot non disponibile)")
                        elif result["status"] == "already_run":
                            logger.info("📋 Daily post già pubblicato oggi")
                        else:
                            logger.warning(f"❌ Daily post fallito: {result.get('message', 'Errore sconosciuto')}")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"❌ Errore nel daily post scheduler: {e}")

        # Controlla ogni minuto
        await asyncio.sleep(60)

# --- Eventi di Avvio e Spegnimento ---

def check_and_install_wkhtmltopdf():
    """Verifica se wkhtmltopdf è installato."""
    import shutil
    
    # Verifica se wkhtmltoimage è disponibile
    wkhtmltoimage_path = shutil.which('wkhtmltoimage')
    
    if wkhtmltoimage_path:
        logger.info(f"✓ wkhtmltoimage trovato: {wkhtmltoimage_path}")
        return True
    
    # Se non trovato, mostra istruzioni
    if is_replit:
        logger.warning("""
    ⚠ ATTENZIONE: wkhtmltoimage non è disponibile!
    
    Per installarlo su Replit:
    1. Apri il pannello "System Dependencies" (Dipendenze di Sistema)
       - Cerca nel menu ☰ o vai su Tools → System Dependencies
    2. Cerca "wkhtmltopdf" e clicca "Add" o "Install"
    3. Attendi che l'installazione completi
    4. Riavvia l'app
    
    NOTA: Su Replit NON puoi usare apt-get direttamente nella shell.
    Devi usare il pannello System Dependencies.
    
    Guida completa: vedi INSTALLA_WKHTMLTOPDF_REPLIT.md
    
    Senza wkhtmltoimage, la generazione delle immagini non funzionerà.
    """)
    else:
        logger.warning("""
    ⚠ ATTENZIONE: wkhtmltoimage non è disponibile!
    
    Per installarlo:
    - Linux: sudo apt-get install -y wkhtmltopdf
    - macOS: brew install wkhtmltopdf
    - Windows: Scarica da https://wkhtmltopdf.org/downloads.html
    
    Riavvia l'app dopo l'installazione.
    """)
    return False

@app.on_event("startup")
async def on_startup():
    """Funzioni da eseguire all'avvio dell'applicazione."""
    logger.info("🚀 Avvio dell'applicazione InstaSpotter...")
    
    try:
        create_db_and_tables()
        logger.info("✓ Database e tabelle pronti.")
    except Exception as e:
        logger.error(f"✗ Errore nell'inizializzazione del database: {e}")
        raise
    
    # Verifica e installa wkhtmltopdf se necessario
    check_and_install_wkhtmltopdf()
    
    # Avvia i task in background
    asyncio.create_task(keep_alive_task())
    logger.info("✓ Keep-alive task avviato per hosting 24/7")

    asyncio.create_task(daily_post_scheduler())
    logger.info("📅 Daily post scheduler avviato - controlla ogni minuto")

# --- Inclusione delle Rotte ---

app.include_router(web_routes.router)
app.include_router(admin_routes.router)

# --- Endpoint QR Mobile (fuori dal router admin per evitare conflitti) ---

@app.get("/auth/qr/{session_id}")
def qr_auth_page(session_id: str, token: str = None):
    """Pagina mobile per autenticazione QR."""
    from app.admin.routes import qr_sessions
    import hashlib

    print(f"🔍 QR page accessed - session: {session_id}, token: {token}")

    # Verifica che la sessione esista
    if session_id not in qr_sessions:
        print(f"❌ Session {session_id} not found in qr_sessions")
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>Errore</title></head>
        <body style="text-align: center; padding: 50px;">
        <h1>Sessione QR non valida</h1>
        <p>Session ID: {session_id}</p>
        <p>Il codice QR potrebbe essere scaduto. Torna al dashboard e genera un nuovo QR code.</p>
        </body>
        </html>
        """)

    session = qr_sessions[session_id]
    print(f"✅ Session found - user: {session['user']}, expires: {session['expires_at']}")

    # Verifica token se fornito
    if token:
        # Determina se il token è già hashato (64 caratteri hex)
        is_already_hashed = len(token) == 64 and all(c in '0123456789abcdef' for c in token)

        if is_already_hashed:
            # Token già hashato, confronta direttamente
            token_to_compare = token
            print(f"🔍 Comparing pre-hashed token directly")
        else:
            # Token originale, hasha prima di confrontare
            token_to_compare = hashlib.sha256(token.encode()).hexdigest()
            print(f"🔐 Hashing original token before comparison")

        if token_to_compare != session["token_hash"]:
            print(f"❌ Token mismatch - received: {token}, expected hash: {session['token_hash']}, computed/used: {token_to_compare}")
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head><title>Token Non Valido</title></head>
            <body style="text-align: center; padding: 50px;">
            <h1>Token QR non valido</h1>
            <p>Il codice QR potrebbe essere vecchio. Torna al dashboard e genera un nuovo QR code.</p>
            </body>
            </html>
            """)
        print(f"✅ Token valid - received: {token}, matches session hash")

    # Pagina mobile per il login
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
            .success {{
                background: rgba(46, 204, 113, 0.2);
                border: 1px solid #2ecc71;
            }}
            .error {{
                background: rgba(231, 76, 60, 0.2);
                border: 1px solid #e74c3c;
            }}
            .btn {{
                background: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.3);
                color: white;
                padding: 12px 24px;
                border-radius: 25px;
                text-decoration: none;
                display: inline-block;
                margin-top: 20px;
                transition: all 0.3s ease;
                cursor: pointer;
            }}
            .btn:hover {{
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
            }}
            .spinner {{
                border: 3px solid rgba(255, 255, 255, 0.3);
                border-top: 3px solid white;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                animation: spin 1s linear infinite;
                display: inline-block;
                margin-right: 10px;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <i class="fab fa-instagram"></i>
            </div>
            <h1>InstaSpotter</h1>
            <p>Accesso Mobile QR</p>

            <div id="statusText" class="status">
                <div class="spinner"></div>
                Verifica in corso...
            </div>

            <button class="btn" onclick="retryAuth()">
                <i class="fas fa-redo"></i>
                Riprova
            </button>
        </div>

        <script>
            let sessionId = '{session_id}';
            let qrToken = '{token}' || null;

            // Estrai token dall'URL se presente (ha priorità)
            const urlParams = new URLSearchParams(window.location.search);
            const urlToken = urlParams.get('token');
            if (urlToken) {{
                qrToken = urlToken;
            }}

            console.log('📱 Mobile QR page loaded for session:', sessionId);
            console.log('🔑 QR token extracted:', qrToken);
            console.log('🔗 URL token:', urlToken);

            async function checkSession() {{
                console.log('🔍 Checking QR session...');

                if (!qrToken) {{
                    document.getElementById('statusText').innerHTML = '<i class="fas fa-exclamation-triangle"></i> Token QR mancante';
                    document.getElementById('statusText').className = 'status error';
                    return;
                }}

                try {{
                    // Determina se il token è già hashato (64 caratteri hex) o originale
                    const isAlreadyHashed = qrToken && qrToken.length === 64 && /^[a-f0-9]+$/.test(qrToken);
                    console.log('🔍 Token already hashed?', isAlreadyHashed);

                    let tokenToSend;
                    if (isAlreadyHashed) {{
                        // Token già hashato, usalo direttamente
                        tokenToSend = qrToken;
                        console.log('✅ Using pre-hashed token');
                    }} else {{
                        // Token originale, hasha prima di inviare
                        const tokenHash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(qrToken));
                        tokenToSend = Array.from(new Uint8Array(tokenHash)).map(b => b.toString(16).padStart(2, '0')).join('');
                        console.log('🔐 Hashed token for sending');
                    }}

                    const response = await fetch('/admin/api/auth/verify-qr', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            session_id: sessionId,
                            token: tokenToSend
                        }})
                    }});

                    if (response.ok) {{
                        const data = await response.json();
                        if (data.success) {{
                            // Ora completa il login chiamando qr-login per ottenere il token mobile
                            console.log('✅ QR token verified, completing login...');
                            setTimeout(() => {{
                                completeMobileLogin();
                            }}, 500); // Piccola pausa per assicurarsi che tutto sia pronto
                        }} else {{
                            document.getElementById('statusText').innerHTML = '<i class="fas fa-times-circle"></i> ' + (data.error || 'Autenticazione fallita');
                            document.getElementById('statusText').className = 'status error';
                            console.log('❌ QR authentication failed:', data.error);
                        }}
                    }} else {{
                        document.getElementById('statusText').innerHTML = '<i class="fas fa-times-circle"></i> Errore di connessione';
                        document.getElementById('statusText').className = 'status error';
                        console.log('❌ QR verification request failed:', response.status);
                    }}
                }} catch (error) {{
                    document.getElementById('statusText').innerHTML = '<i class="fas fa-times-circle"></i> Errore: ' + error.message;
                    document.getElementById('statusText').className = 'status error';
                    console.error('❌ QR authentication error:', error);
                }}
            }}

            async function completeMobileLogin() {{
                try {{
                    console.log('🚀 Completing mobile login...');
                    const response = await fetch('/admin/api/auth/qr-login', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ session_id: sessionId }})
                    }});

                    let loginData;
                    try {{
                        loginData = await response.json();
                        console.log('📋 Login response data:', loginData);
                    }} catch (e) {{
                        console.error('❌ Failed to parse login response:', e);
                        loginData = {{ error: 'Risposta non valida dal server' }};
                    }}

                    if (response.ok && loginData && loginData.success && loginData.access_token) {{
                        // Salva il token di accesso per il mobile
                        localStorage.setItem('access_token', loginData.access_token);
                        document.cookie = `access_token=${loginData.access_token}; path=/; max-age=86400`;

                        document.getElementById('statusText').innerHTML = '<i class="fas fa-check-circle"></i> Accesso mobile completato! Reindirizzamento...';
                        console.log('✅ Mobile login completed successfully');

                        // Redirect alla dashboard dopo 2 secondi
                        setTimeout(() => {{
                            window.location.href = '/admin/dashboard';
                        }}, 2000);
                    }} else {{
                        const errorMsg = loginData && loginData.error ? loginData.error : 'Errore completamento login';
                        document.getElementById('statusText').innerHTML = '<i class="fas fa-times-circle"></i> ' + errorMsg;
                        document.getElementById('status').className = 'status error';
                        console.error('❌ Mobile login failed:', errorMsg);
                    }}
                }} catch (error) {{
                    document.getElementById('statusText').innerHTML = '<i class="fas fa-times-circle"></i> Errore: ' + error.message;
                    document.getElementById('status').className = 'status error';
                    console.error('❌ Mobile login completion error:', error);
                }}
            }}

            function retryAuth() {{
                document.getElementById('statusText').innerHTML = '<div class="spinner"></div> Verifica in corso...';
                document.getElementById('statusText').className = 'status';
                checkSession();
            }}

            // Start authentication check
            checkSession();
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)

# --- Rotta di Benvenuto ---

@app.get("/", tags=["Root"])
def read_root():
    """Ritorna un messaggio di benvenuto."""
    return {"message": "Benvenuto in InstaSpotter. Vai su /spotted/new per inviare un messaggio."}

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint per mantenere l'app attiva su Replit."""
    return {"status": "alive", "service": "InstaSpotter"}

@app.get("/debug/admin", tags=["Debug"])
def debug_admin_config():
    """Endpoint pubblico di debug per vedere la configurazione admin."""
    import os

    # Non mostrare password reali per sicurezza
    debug_info = {
        "admin_username_configured": bool(
            os.getenv("ADMIN_USERNAME") or
            os.getenv("REPLIT_ADMIN_USERNAME")
        ),
        "admin_password_configured": bool(
            os.getenv("ADMIN_PASSWORD") or
            os.getenv("REPLIT_ADMIN_PASSWORD") or
            os.getenv("ADMIN_PASSWORD_HASH") or
            os.getenv("REPLIT_ADMIN_PASSWORD_HASH")
        ),
        "available_admin_env_vars": [k for k in os.environ.keys() if 'ADMIN' in k.upper()],
        "using_temporary_credentials": not any([
            os.getenv("ADMIN_PASSWORD"),
            os.getenv("REPLIT_ADMIN_PASSWORD"),
            os.getenv("ADMIN_PASSWORD_HASH"),
            os.getenv("REPLIT_ADMIN_PASSWORD_HASH")
        ])
    }

    return debug_info
