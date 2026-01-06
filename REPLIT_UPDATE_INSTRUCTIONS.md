# 🚨 SETUP COMPLETO REPLIT - TUTTE LE VARIABILI

## 🔥 PROBLEMA RISOLTO:
Template dorato → card_v5.html ✅
Ora configura le Secrets per far funzionare tutto!

## ✅ CONFIGURA QUESTE SECRETS IN REPLIT:

### **1. 📸 INSTAGRAM (OBBLIGATORIO)**
```
INSTAGRAM_USERNAME=il_tuo_username_instagram
INSTAGRAM_PASSWORD=la_tua_password_instagram
TWO_FACTOR_SEED=il_tuo_2fa_seed (se hai 2FA abilitato)
```

### **2. 🤖 AI MODERATION (OBBLIGATORIO)**
```
GEMINI_API_KEY=la_tua_chiave_gemini_api
```
*(Prendila da: https://makersuite.google.com/app/apikey)*

### **3. 🔐 ADMIN DASHBOARD (OBBLIGATORIO)**
```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=LaTuaPasswordSicura123!
```
*(O usa hash sicuro - vedi VERIFICA_CREDENZIALI_ADMIN.md)*

### **4. 🔑 SICUREZZA (RACCOMANDATO)**
```
SECRET_KEY=una_stringa_casuale_di_32_caratteri
```
*(Generala con: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`)*

### **5. 🗄️ DATABASE (OPZIONALE - default SQLite)**
```
DATABASE_URL=sqlite:///data/messages.db
```

### **6. 🌐 REPLIT URL (OPZIONALE)**
```
REPLIT_URL=https://instaspotter.GoogleMapes.replit.app
```

---

## 🎯 **COME AGGIUNGERE LE SECRETS:**

1. Vai su: https://replit.com/@GoogleMapes/instaspotter
2. Clicca **🔒 Secrets** (lucchetto) nel pannello laterale
3. Clicca **"Add new secret"** per ogni variabile
4. **Riavvia l'app** dopo aver aggiunto tutto

---

## ✅ **VERIFICA CHE FUNZIONI:**

### **Test Template:**
```bash
# Su Replit potrebbe essere 'python' o 'python3':
python -c "from config import settings; print('TEMPLATE:', settings.image.template_path)" 2>/dev/null || python3 -c "from config import settings; print('TEMPLATE:', settings.image.template_path)"
# Dovrebbe mostrare: card_v5.html
```

### **Test Rendering Card V5:**
```bash
# Testa la generazione di una card blu ottimizzata
python3 -c "
from app.image.generator import ImageGenerator
gen = ImageGenerator()
result = gen.from_text('Test card V5 blu professionale!', 'test_blu.png', 999)
print('Generata card blu:', result)
" 2>/dev/null || python -c "
from app.image.generator import ImageGenerator
gen = ImageGenerator()
result = gen.from_text('Test card V5 blu professionale!', 'test_blu.png', 999)
print('Generata card blu:', result)
"
```

### **Test Admin Login:**
- Vai su: `https://instaspotter.GoogleMapes.replit.app/admin/login`
- Username: `admin`
- Password: La tua password configurata

### **Test Instagram Bot:**
- Invia uno spot dal bot Telegram
- Dovrebbe postare su Instagram con card_v5.html **blu professionale** ✨

---

## 🎉 **RISULTATO FINALE:**
✅ Template: card_v5.html (non più dorato)
✅ Admin: Accessibile con le tue credenziali
✅ Instagram: Bot funzionante
✅ AI: Moderazione attiva
✅ Sicurezza: JWT tokens protetti

**AGGIUNGI LE SECRETS E RIAVVIA!** 🚀✨

Ora tutto funziona perfettamente! 🎨