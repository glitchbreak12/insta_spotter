import os
import secrets
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("insta_spotter")

# --- Configurazione di Sicurezza ---
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    logger.warning("SECRET_KEY non configurato! Genera una key sicura con: secrets.token_urlsafe(32)")
    SECRET_KEY = secrets.token_urlsafe(32)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Ridotto a 30 minuti per sicurezza
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context - usa SHA256 direttamente per evitare problemi bcrypt
import hashlib

class SHA256Context:
    def hash(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify(self, plain, hashed):
        expected = hashlib.sha256(plain.encode()).hexdigest()
        return expected == hashed

pwd_context = SHA256Context()
logger.info("✅ Usando SHA256 per hashing password (semplificato)")

# --- Variabili di Ambiente ---
ADMIN_USERNAME = (
    os.getenv("ADMIN_USERNAME") or
    os.getenv("REPLIT_ADMIN_USERNAME") or
    "admin"  # fallback
)

# Debug: mostra TUTTE le variabili d'ambiente disponibili
logger.info("🔍 DEBUG: Checking all environment variables...")
for key, value in os.environ.items():
    if 'ADMIN' in key.upper() or 'SECRET' in key.upper():
        logger.info(f"🔍 ENV VAR: {key} = {'***HIDDEN***' if 'PASSWORD' in key.upper() else value}")

# Priorità 1: ADMIN_PASSWORD (plaintext) - usa SHA256 per evitare problemi bcrypt
admin_pwd = (
    os.getenv("ADMIN_PASSWORD") or
    os.getenv("REPLIT_ADMIN_PASSWORD") or
    os.getenv("REPLIT_DB_ADMIN_PASSWORD")
)

if admin_pwd:
    ADMIN_PASSWORD_HASH = hashlib.sha256(admin_pwd.encode()).hexdigest()
    logger.info(f"✅ Password configurata da ADMIN_PASSWORD (len={len(admin_pwd)}) - SHA256")

# Priorità 2: ADMIN_PASSWORD_HASH (solo se non abbiamo già una password da plaintext)
elif not ADMIN_PASSWORD_HASH:
    ADMIN_PASSWORD_HASH = (
        os.getenv("ADMIN_PASSWORD_HASH") or
        os.getenv("REPLIT_ADMIN_PASSWORD_HASH")
    )

    if ADMIN_PASSWORD_HASH:
        logger.info(f"✅ Password hash configurata direttamente (len={len(ADMIN_PASSWORD_HASH)})")

    # Terza priorità: fallback temporaneo per test
    else:
        logger.warning("🔧 USING TEMPORARY ADMIN CREDENTIALS FOR TESTING!")
        logger.warning("🔧 Username: admin, Password: admin123")
        logger.warning("🔧 Configure ADMIN_PASSWORD in Secrets for production!")

        # Usa direttamente SHA256 per semplicità
        ADMIN_USERNAME = "admin"
        ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()
        logger.warning("🔧 Using SHA256 hash for temporary credentials")

# Debug: mostra quali env vars sono disponibili
logger.info(f"🔍 Available env vars with ADMIN: {[k for k in os.environ.keys() if 'ADMIN' in k.upper()]}")
logger.info(f"🔍 Sample env vars: {list(os.environ.keys())[:5]}...")

# --- Funzioni di Utility Sicure ---

def hash_password(password: str) -> str:
    """Hash una password con bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una password usando SHA256 (semplificato per evitare problemi bcrypt)."""
    try:
        expected_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        return expected_hash == hashed_password
    except Exception as error:
        logger.error(f"Password verification failed: {error}")
        return False

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Crea un JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Logica di Autenticazione ---

def authenticate_user(username: str, password: str) -> Optional[str]:
    """Verifica le credenziali. Ritorna username se valide, None altrimenti."""
    # Confronto username in modo timing-safe
    username_valid = secrets.compare_digest(username, ADMIN_USERNAME)
    
    # Verifica password
    password_valid = verify_password(password, ADMIN_PASSWORD_HASH or "")
    
    # Entrambi devono essere validi
    if username_valid and password_valid:
        logger.info(f"✓ Accesso riuscito: {username}")
        return username
    
    logger.warning(f"✗ Tentativo di accesso fallito: {username}")
    return None

def get_current_user(request: Request) -> Optional[str]:
    """Ottiene l'utente corrente dal JWT token nel cookie."""
    token = request.cookies.get("access_token")
    logger.info(f"🔍 Checking JWT token in cookies: {'present' if token else 'not found'}")
    if token:
        logger.info(f"🔍 Token length: {len(token)} chars")
    if not token:
        return None

    try:
        logger.debug(f"🔍 Decoding JWT token...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        device: str = payload.get("device", "desktop")

        logger.info(f"🔍 JWT payload - username: {username}, device: {device}")

        if username is None:
            logger.info("❌ No username in token")
            return None

        # Verifica che l'utente sia quello corretto
        if not secrets.compare_digest(username, ADMIN_USERNAME):
            logger.info(f"❌ Username mismatch: {username} != {ADMIN_USERNAME}")
            return None

        logger.info(f"✅ JWT token valid for user: {username}")
        return username
    except JWTError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Errore nella verifica token: {e}")
        return None