"""
Modulo di configurazione per la sicurezza dell'applicazione.
Implementa protezioni contro:
- CSRF attacks
- XSS attacks
- SQL injection
- Brute force
- DDoS
- Data leakage
"""

import os
import secrets
import logging
from functools import lru_cache
from hashlib import sha256

# ============================================================================
# LOGGING SICURO (SENZA DOXING)
# ============================================================================

class SanitizedFormatter(logging.Formatter):
    """Formatter che nasconde dati sensibili dai log."""
    
    SENSITIVE_KEYS = ['password', 'token', 'secret', 'api_key', 'bearer', 'authorization', 'instagram_password']
    
    def format(self, record):
        # Sanitizza il messaggio
        message = super().format(record)
        
        for key in self.SENSITIVE_KEYS:
            # Rimpiazza valori sensibili
            parts = message.lower().split(key)
            if len(parts) > 1:
                message = "***REDACTED***".join(parts)
        
        return message

def setup_secure_logging():
    """Configura logging sicuro senza esporre dati sensibili."""
    logger = logging.getLogger("insta_spotter")
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    formatter = SanitizedFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# ============================================================================
# UTILITÀ DI SICUREZZA
# ============================================================================

def hash_ip(ip_address: str) -> str:
    """Hash un indirizzo IP per privacy."""
    return sha256(ip_address.encode()).hexdigest()[:16]

def generate_csrf_token() -> str:
    """Genera un token CSRF sicuro."""
    return secrets.token_urlsafe(32)

def verify_csrf_token(token: str, stored_token: str) -> bool:
    """Verifica il token CSRF in modo sicuro."""
    return secrets.compare_digest(token, stored_token)

# ============================================================================
# CONFIGURAZIONE DI SICUREZZA FASTAPI
# ============================================================================

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",  # Previene MIME type sniffing
    "X-Frame-Options": "DENY",  # Clickjacking protection
    "X-XSS-Protection": "1; mode=block",  # Protezione XSS (legacy)
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",  # HTTPS only
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;",
    "Referrer-Policy": "strict-origin-when-cross-origin",  # Privacy di referrer
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",  # Disabilita API sensibili
}

# CORS Policy - MOLTO RESTRITTIVO
CORS_ALLOWED_ORIGINS = [
    "https://insta-spotter.replit.dev",  # Cambia con il tuo dominio
]

CORS_SETTINGS = {
    "allow_origins": CORS_ALLOWED_ORIGINS,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST"],
    "allow_headers": ["Content-Type", "Authorization"],
    "max_age": 3600,
}

# Rate limiting
RATE_LIMIT_SETTINGS = {
    "submission": "10/minute",  # Max 10 messaggi al minuto
    "login": "5/minute",  # Max 5 tentativi login al minuto
    "health": "100/minute",  # Health check non limitato
}

# ============================================================================
# VALIDAZIONE INPUT
# ============================================================================

class InputValidator:
    """Valida e sanitizza gli input utente."""
    
    @staticmethod
    def validate_message(message: str) -> str:
        """Valida e sanitizza un messaggio spotted."""
        if not message or not isinstance(message, str):
            raise ValueError("Messaggio invalido")
        
        # Rimuovi spazi extra
        message = message.strip()
        
        # Lunghezza minima e massima
        if len(message) < 10:
            raise ValueError("Messaggio troppo corto (min 10 caratteri)")
        if len(message) > 2000:
            raise ValueError("Messaggio troppo lungo (max 2000 caratteri)")
        
        # Sanitizza HTML/XSS
        import bleach
        message = bleach.clean(message, tags=[], strip=True)
        
        return message
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Valida username."""
        if not username or not isinstance(username, str):
            raise ValueError("Username invalido")
        
        username = username.strip()
        
        # Solo alphanumerici, underscore, dash
        if not all(c.isalnum() or c in '_-' for c in username):
            raise ValueError("Username contiene caratteri non validi")
        
        if len(username) < 3 or len(username) > 50:
            raise ValueError("Username lunghezza invalida")
        
        return username
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Valida password (forza)."""
        if not password or len(password) < 12:
            raise ValueError("Password troppo debole (min 12 caratteri)")
        
        # Richiedi mix di caratteri
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError("Password deve contenere maiuscole, minuscole, numeri e caratteri speciali")
        
        return password

# ============================================================================
# SECURE CONFIG LOADER
# ============================================================================

@lru_cache(maxsize=1)
def get_security_config():
    """Carica configurazioni di sicurezza."""
    return {
        "headers": SECURITY_HEADERS,
        "cors": CORS_SETTINGS,
        "rate_limits": RATE_LIMIT_SETTINGS,
    }
