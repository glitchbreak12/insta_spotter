# 🔐 InstaSpotter - Deployment Sicuro

## ⚡ Quick Start Sicuro

```bash
# 1. Installa dipendenze
pip install -r requirements.txt

# 2. Setup sicurezza
chmod +x setup_security.sh
./setup_security.sh

# 3. Configura .env
# Apri .env e modifica i valori

# 4. Avvia app
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🔒 Protezioni Attive

✅ **Autenticazione**: bcrypt + JWT (30 min)  
✅ **CSRF**: Token validato  
✅ **XSS**: Input sanitizzato con Bleach  
✅ **SQL Injection**: ORM parametrizzato  
✅ **Rate Limiting**: 10 req/min per IP  
✅ **Security Headers**: CORS, CSP, HSTS  
✅ **IP Privacy**: Hash SHA256  
✅ **No Doxing**: Log sanitizzati  

---

## ⚠️ Checklist Produzione

- [ ] Leggi `SECURITY.md` completamente
- [ ] Genera `SECRET_KEY` con `setup_security.sh`
- [ ] Hash password con bcrypt (non plaintext)
- [ ] Configura `DATABASE_URL` reale
- [ ] Configura API keys (Gemini, Instagram)
- [ ] Aggiungi variabili in Replit Secrets
- [ ] Testa form CSRF token
- [ ] Monitora log per attacchi

---

## 📝 Variabili Essenziali

```env
SECRET_KEY=<random-32-chars>
ADMIN_PASSWORD_HASH=$2b$12$...  # Generato da setup_security.sh
DATABASE_URL=postgresql://...
GEMINI_API_KEY=...
INSTAGRAM_USERNAME=...
INSTAGRAM_PASSWORD=...
REPLIT_URL=https://your-app.replit.dev
```

**❌ Non usare:**
- Plain password
- Hardcoded keys
- Localhost in produzione

---

## 🚀 Deploy su Replit

1. Import da GitHub
2. Clicca **Secrets** (lucchetto)
3. Aggiungi tutte le variabili da `.env`
4. Clicca **Run**
5. Usa **UptimeRobot** per 24/7

---

## 🧪 Test Sicurezza

```bash
pytest tests/test_security.py -v
```

Verifica:
- ✓ XSS sanitization
- ✓ Password hashing
- ✓ Input validation
- ✓ Headers di sicurezza
- ✓ No sensitive data in logs

---

## 📞 Supporto

Vulnerability found? Email con dettagli (non public).

Leggi [SECURITY.md](SECURITY.md) per hardening avanzato.
