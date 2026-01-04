from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
from urllib.parse import urlparse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

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

if not disable_trusted:
    # Costruisci la lista di host permessi dinamicamente usando REPLIT_URL se impostato
    allowed_hosts = ["localhost", "127.0.0.1"]
    if replit_url:
        try:
            parsed = urlparse(replit_url)
            if parsed.hostname:
                allowed_hosts.append(parsed.hostname)
        except Exception:
            logger.warning("Impossibile parsare REPLIT_URL per TrustedHostMiddleware")

    # Se non abbiamo un REPLIT_URL, manteniamo il dominio di default usato in sviluppo
    if len(allowed_hosts) == 2:
        allowed_hosts.append("insta-spotter.replit.dev")

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

# --- Eventi di Avvio e Spegnimento ---

@app.on_event("startup")
def on_startup():
    """Funzioni da eseguire all'avvio dell'applicazione."""
    logger.info("🚀 Avvio dell'applicazione InstaSpotter...")
    
    try:
        create_db_and_tables()
        logger.info("✓ Database e tabelle pronti.")
    except Exception as e:
        logger.error(f"✗ Errore nell'inizializzazione del database: {e}")
        raise

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
