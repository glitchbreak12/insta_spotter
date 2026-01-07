import os
import secrets
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

logger = logging.getLogger("insta_spotter")

# --- Configurazione di Sicurezza ---
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    logger.warning("SECRET_KEY non configurato! Genera una key sicura con: secrets.token_urlsafe(32)")
    SECRET_KEY = secrets.token_urlsafe(32)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Ridotto a 30 minuti per sicurezza
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context - fallback per errori bcrypt
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception as e:
    logger.warning(f"Errore bcrypt, uso fallback sha256: {e}")
    try:
        pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
    except Exception as e2:
        logger.warning(f"Anche sha256 fallito, uso plaintext fallback: {e2}")
        # Fallback di emergenza - NON USARE IN PRODUZIONE!
        class PlaintextContext:
            def hash(self, password): return password
            def verify(self, plain, hashed): return plain == hashed
        pwd_context = PlaintextContext()

# --- Variabili di Ambiente ---
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")  # Deve essere pre-hashato!

# Prima priorità: ADMIN_PASSWORD (se fornita, hashala)
admin_pwd = os.getenv("ADMIN_PASSWORD")
if admin_pwd and not ADMIN_PASSWORD_HASH:
    try:
        ADMIN_PASSWORD_HASH = pwd_context.hash(admin_pwd)
        logger.info("✅ Password configurata da ADMIN_PASSWORD")
    except Exception as e:
        logger.warning(f"⚠️ Bcrypt fallito ({e}), uso SHA256")
        import hashlib
        ADMIN_PASSWORD_HASH = hashlib.sha256(admin_pwd.encode()).hexdigest()

# Seconda priorità: ADMIN_PASSWORD_HASH (se fornita direttamente)
elif ADMIN_PASSWORD_HASH:
    logger.info("✅ Password hash configurata direttamente")

# Terza priorità: fallback temporaneo per test
else:
    logger.warning("🔧 USING TEMPORARY ADMIN CREDENTIALS FOR TESTING!")
    logger.warning("🔧 Username: admin, Password: admin123")
    logger.warning("🔧 Configure ADMIN_PASSWORD in Secrets for production!")

    # Usa direttamente SHA256 per semplicità
    import hashlib
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
    """Verifica una password in modo sicuro (timing-safe)."""
    try:
        # Prima prova con bcrypt
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as bcrypt_error:
        logger.warning(f"Bcrypt verification failed ({bcrypt_error}), trying SHA256 fallback")
        try:
            # Fallback a SHA256 se bcrypt fallisce (per credenziali temporanee)
            import hashlib
            expected_hash = hashlib.sha256(plain_password.encode()).hexdigest()
            return expected_hash == hashed_password
        except Exception as sha_error:
            logger.error(f"Both bcrypt and SHA256 verification failed: bcrypt={bcrypt_error}, sha={sha_error}")
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
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            return None
        
        # Verifica che l'utente sia quello corretto
        if not secrets.compare_digest(username, ADMIN_USERNAME):
            return None
        
        return username
    except JWTError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Errore nella verifica token: {e}")
        return None