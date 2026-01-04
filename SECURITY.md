# 🔐 GUIDA DI SICUREZZA - InstaSpotter

## Protezioni Implementate

### ✅ Autenticazione & Password
- **bcrypt hashing**: Password hashate con bcrypt (non plaintext)
- **JWT Tokens**: Token a breve scadenza (30 minuti)
- **Timing-safe comparison**: Protezione contro timing attacks

### ✅ Network & HTTP
- **CORS rigido**: Solo domini conosciuti
- **Trusted Host Middleware**: Valida header Host
- **Security Headers**:
  - `X-Content-Type-Options: nosniff` (MIME sniffing protection)
  - `X-Frame-Options: DENY` (Clickjacking protection)
  - `X-XSS-Protection: 1; mode=block` (XSS protection)
  - `Content-Security-Policy` (XSS/injection protection)
  - `Strict-Transport-Security` (HTTPS enforcement)
  - `Referrer-Policy` (Privacy)
  - `Permissions-Policy` (Disabilita geolocation, camera, etc)

### ✅ Input Validation
- **Bleach sanitization**: Rimuove HTML/script pericolosi
- **Lunghezza controllata**: Min 10, Max 2000 caratteri
- **Tipo validato**: Solo stringhe
- **Regex check**: Username solo alphanumerico

### ✅ CSRF Protection
- **Token CSRF**: Generato per ogni form
- **Token one-time use**: Usato una sola volta
- **Token storage**: In memoria (upgrade a Redis/database per produzione)

### ✅ Rate Limiting
- **slowapi integration**: Limita richieste per IP
- **Brute force protection**: Max 5 login/minuto
- **DDoS mitigation**: Max 10 submission/minuto

### ✅ Logging Sicuro (No Doxing)
- **IP hashing**: IP hasciati con SHA256
- **Sanitizzazione log**: Nessuna password/token in log
- **Log formatter personalizzato**: Redact automatico di dati sensibili

### ✅ Database
- **SQLAlchemy ORM**: Protezione da SQL injection
- **Prepared statements**: Query parametrizzate
- **Connessione secure**: PostgreSQL con credenziali

---

## Setup Sicuro

### 1️⃣ Genera Configurazione Sicura
```bash
chmod +x setup_security.sh
./setup_security.sh
```

Questo genera:
- `SECRET_KEY` casuale e sicuro
- Hash della password admin con bcrypt
- File `.env` pronto

### 2️⃣ Configurazione Variabili d'Ambiente

**Localmente:**
```
cp .env .env.local
# Modifica .env.local con i tuoi valori
```

**Su Replit:**
1. Clicca il lucchetto "Secrets" nel pannello
2. Aggiungi TUTTE le variabili da `.env`
3. Riavvia l'app

**Variables Richieste:**
```
SECRET_KEY=...
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=...
DATABASE_URL=postgresql://...
GEMINI_API_KEY=...
INSTAGRAM_USERNAME=...
INSTAGRAM_PASSWORD=...
REPLIT_URL=https://your-name.replit.dev
```

### 3️⃣ Non Committare Secrets
Il file `.gitignore` esclude automaticamente:
- `.env` (non committare MAI)
- `secrets/`
- `__pycache__/`
- `*.log`

---

## Vulnerabilità Risolte

### ❌ Prima (Vulnerabile)
```python
# Password in plaintext
ADMIN_PASSWORD = "password"

# Nessun CSRF token
@router.post("/submit")
def handle(message: str = Form(...)):
    ...

# Input non validato
if len(message) < 10:
    ...

# Nessun rate limiting
# Chiunque può fare brute force

# Password nei log
logger.info(f"Password: {password}")
```

### ✅ Dopo (Sicuro)
```python
# Password hashata
ADMIN_PASSWORD_HASH = "$2b$12$..."

# CSRF token validato
@router.post("/submit")
def handle(csrf_token: str = Form(...)):
    verify_csrf_token(csrf_token, stored_token)

# Input validato e sanitizzato
InputValidator.validate_message(message)
bleach.clean(message)

# Rate limiting applicato
@limiter.limit("10/minute")
def handle_submission():
    ...

# Nessuna password nei log
logger.info(f"Login: [REDACTED]")
```

---

## Checklist di Sicurezza

- [ ] `.env` configurato con variabili reali
- [ ] `.env` NON committato su Git
- [ ] SECRET_KEY generato (non default)
- [ ] ADMIN_PASSWORD_HASH usato (bcrypt)
- [ ] Database URL configurato
- [ ] API keys di terze parti protette
- [ ] CORS domain configurato (non allow_origins="*")
- [ ] HTTPS abilitato (Replit fa automaticamente)
- [ ] Rate limiting attivo
- [ ] CSRF token nei form
- [ ] Input sanitizzato

---

## Monitoraggio & Logging

### Log Disponibili
```
✓ Accesso riuscito: admin
✗ Tentativo di accesso fallito: attacker
⚠️ CSRF token invalido
✗ Messaggio invalido
✓ Nuovo messaggio (ID: 123) da IP [HASHED]
```

### Non Log (Per Privacy)
- Password o hash
- Token JWT completi
- IP reali (solo hash)
- Dati personali di utenti

---

## Hardening Aggiuntivo (Opzionale)

### 1. Database Encryption
```python
# Encrypt sensibili field in database
from sqlalchemy_utils import EncryptedType
text = Column(EncryptedType(String, SECRET_KEY))
```

### 2. Redis per Session/CSRF
```python
# Store CSRF tokens in Redis (più sicuro di in-memory)
import redis
redis_client = redis.Redis()
redis_client.setex(csrf_token, 3600, ip_hash)
```

### 3. WAF (Web Application Firewall)
- Su Replit: usa Cloudflare protection
- Regex patterns per SQLi/XSS detection

### 4. Monitoring & Alerting
```python
import sentry_sdk
sentry_sdk.init(dsn="...")  # Track errors in production
```

---

## Contatti Sicurezza

Se trovi una vulnerabilità:
1. NON commentare pubblicamente
2. Manda email privata
3. Aspetta fix prima di divulgare

---

## Riferimenti

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
