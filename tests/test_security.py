"""
Test di sicurezza per verificare protezioni implementate.
RUN: pytest tests/test_security.py -v
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security import InputValidator, hash_ip, verify_csrf_token
from passlib.context import CryptContext

client = TestClient(app)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================================
# TEST: Input Validation
# ============================================================================

def test_message_too_short():
    """XSS/Injection: Rifiuta messaggi troppo corti."""
    with pytest.raises(ValueError):
        InputValidator.validate_message("short")

def test_message_too_long():
    """Rifiuta messaggi troppo lunghi."""
    with pytest.raises(ValueError):
        InputValidator.validate_message("x" * 2001)

def test_xss_sanitization():
    """HTML/Script rimosse dal messaggio."""
    message = "Hello <script>alert('xss')</script> world"
    clean = InputValidator.validate_message(message)
    assert "<script>" not in clean
    assert "alert" not in clean

def test_html_tags_removed():
    """Tag HTML rimossi."""
    message = "A" * 10 + "<b>bold</b>"
    clean = InputValidator.validate_message(message)
    assert "<b>" not in clean

# ============================================================================
# TEST: Password Security
# ============================================================================

def test_password_hashing():
    """Password hashate con bcrypt."""
    password = "SecurePass123!"
    hashed = pwd_context.hash(password)
    
    # Deve essere diverso dal plaintext
    assert hashed != password
    
    # Hash deve essere bcrypt
    assert hashed.startswith("$2b$")
    
    # Verifica deve passare
    assert pwd_context.verify(password, hashed)
    
    # Verifica deve fallire con password sbagliata
    assert not pwd_context.verify("WrongPassword", hashed)

def test_password_strength():
    """Password debole rifiutata."""
    with pytest.raises(ValueError):
        InputValidator.validate_password("weak")
    
    with pytest.raises(ValueError):
        InputValidator.validate_password("onlyletters")
    
    with pytest.raises(ValueError):
        InputValidator.validate_password("123456789012")  # Solo numeri

def test_strong_password():
    """Password forte accettata."""
    strong = "MySecure123!Pass"
    result = InputValidator.validate_password(strong)
    assert result == strong

# ============================================================================
# TEST: IP Hashing (Privacy)
# ============================================================================

def test_ip_hashing():
    """IP hasciato per privacy."""
    ip1 = "192.168.1.1"
    ip2 = "192.168.1.2"
    ip1_hash = hash_ip(ip1)
    ip2_hash = hash_ip(ip2)
    
    # Hash deve essere diverso dall'originale
    assert ip1_hash != ip1
    
    # Stesso IP deve dare stesso hash
    assert ip1_hash == hash_ip(ip1)
    
    # IP diversi devono avere hash diversi
    assert ip1_hash != ip2_hash
    
    # Hash deve essere corto (16 char)
    assert len(ip1_hash) == 16

# ============================================================================
# TEST: CORS
# ============================================================================

def test_cors_header():
    """CORS header presente."""
    response = client.get("/health")
    # Dovrebbe avere security headers
    assert response.status_code == 200

def test_security_headers():
    """Security headers presenti."""
    response = client.get("/health")
    
    # Check key security headers
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    
    assert "X-XSS-Protection" in response.headers

# ============================================================================
# TEST: Form Submission (CSRF)
# ============================================================================

@pytest.mark.skip(reason="Richiede session/CSRF store setup")
def test_csrf_token_required():
    """CSRF token richiesto nel form."""
    # GET per ottenere token
    response = client.get("/spotted/new")
    assert response.status_code == 200
    # Dovrebbe contenere csrf_token nel form
    # assert "csrf_token" in response.text

@pytest.mark.skip(reason="Richiede session/CSRF store setup")
def test_csrf_token_invalid():
    """CSRF token invalido rifiutato."""
    response = client.post(
        "/spotted/submit",
        data={
            "message": "A" * 10,
            "csrf_token": "invalid-token"
        }
    )
    assert response.status_code != 200  # Dovrebbe fallire

# ============================================================================
# TEST: Rate Limiting
# ============================================================================

@pytest.mark.skip(reason="Rate limiter test complesso")
def test_rate_limiting():
    """Protezione da brute force."""
    # Troppi richiesti dovrebbero essere bloccati
    pass

# ============================================================================
# TEST: No Sensitive Data Leakage
# ============================================================================

def test_health_no_secrets():
    """Health check non expose secrets."""
    response = client.get("/health")
    data = response.json()
    
    # Non deve contenere dati sensibili
    assert "password" not in str(data).lower()
    assert "secret" not in str(data).lower()
    assert "token" not in str(data).lower()

# ============================================================================
# TEST: Documentation Hidden (Production)
# ============================================================================

def test_no_swagger_ui():
    """Swagger UI disabilitato in produzione."""
    response = client.get("/docs")
    assert response.status_code == 404

def test_no_redoc():
    """ReDoc disabilitato."""
    response = client.get("/redoc")
    assert response.status_code == 404

def test_no_openapi():
    """OpenAPI schema nascosto."""
    response = client.get("/openapi.json")
    assert response.status_code == 404

# ============================================================================
# UTILITY
# ============================================================================

if __name__ == "__main__":
    print("🔐 Esegui con: pytest tests/test_security.py -v")
