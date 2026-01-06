from fastapi import FastAPI
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
    
    # Avvia il task di keep-alive in background per Replit
    asyncio.create_task(keep_alive_task())
    logger.info("✓ Keep-alive task avviato per hosting 24/7")

# --- Inclusione delle Rotte ---

app.include_router(web_routes.router)
app.include_router(admin_routes.router)

# --- Rotta di Benvenuto ---

@app.get("/", tags=["Root"])
def read_root():
    """Ritorna un messaggio di benvenuto."""
    return {"message": "Benvenuto in InstaSpotter. Vai su /spotted/new per inviare un messaggio."}

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint per mantenere l'app attiva su Replit."""
    return {"status": "alive", "service": "InstaSpotter"}

# --- Avvio dell'Applicazione ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
