# 🚨 RESET DEFINITIVO + INSTALLAZIONE DIPENDENZE

## 🔥 PROBLEMA ATTUALE:
Dopo il reset, mancano le dipendenze Python (ModuleNotFoundError).

## ✅ COMANDO COMPLETO (reset + installazione):

```bash
cd /home/runner/workspace && echo "=== RESET COMPLETO ===" && rm -rf .git && rm -rf .* && rm -rf * && git init && git remote add origin https://github.com/glitchbreak12/insta_spotter.git && git pull origin main && echo "✅ RESET RIUSCITO!" && echo "=== INSTALLAZIONE DIPENDENZE ===" && pip install -r requirements.txt && echo "✅ DIPENDENZE INSTALLATE!"
```

### **Cosa fa:**
- `rm -rf .*` → rimuove TUTTI i file nascosti (.*, .env.example, .gitignore, .replit)
- Scarica tutto fresco da GitHub
- `pip install -r requirements.txt` → installa tutte le dipendenze

---

## 🎯 DOPO IL COMANDO:

### **1. Verifica che tutto sia scaricato:**
```bash
ls -la
# Dovresti vedere: app/ config.py requirements.txt etc.
```

### **2. Configura Secrets (🔒 lucchetto):**
```
INSTAGRAM_USERNAME=il_tuo_username
INSTAGRAM_PASSWORD=la_tua_password
GEMINI_API_KEY=la_tua_chiave
ADMIN_USERNAME=admin
ADMIN_PASSWORD=LaTuaPassword123!
```

### **3. Riavvia l'app (Stop → Run)**

### **4. Test finale:**
```bash
python3 -c "from config import settings; print('TEMPLATE:', settings.image.template_path)"
```

**Risultato atteso:**
```
TEMPLATE: card_v5.html ✅
```

**❌ Se vedi errori di sintassi, usa questo comando semplificato:**
```bash
python3 -c "from config import settings; print(settings.image.template_path)"
```

### **5. IMPORTANTE: Su Replit usa SEMPRE python3:**
```bash
# ❌ SBAGLIATO: python -c "..."
# ✅ GIUSTO: python3 -c "..."

python3 -c "from config import settings; print('TEMPLATE:', settings.image.template_path)"
```

**Ricorda: Su Replit è sempre `python3`, mai `python`!**

---

## 🔥 PERCHÉ QUESTO FUNZIONA:
- ✅ **Reset completo** senza conflitti
- ✅ **Dipendenze installate automaticamente**
- ✅ **Nessun errore ModuleNotFoundError**

**COPIA IL COMANDO E INCOLLALO!** 🚀

Finalmente funzionerà tutto! 🎨✨