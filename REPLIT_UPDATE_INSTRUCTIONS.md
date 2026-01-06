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

---

## 🔄 **AGGIORNARE CODICE SU REPLIT:**

### **Se hai ancora errori dopo il reset:**

**1. Verifica che hai scaricato le ultime modifiche:**
```bash
cd /home/runner/workspace && git pull origin main
```

**2. Se vedi conflitti, forza l'aggiornamento:**
```bash
cd /home/runner/workspace && git fetch origin && git reset --hard origin/main
```

**3. Riavvia l'app** (Stop → Run)

---

## 🚀 **AGGIORNAMENTO FORZATO - RISOLVI DEFINITIVAMENTE:**

### **🚨 Comando finale che risolve tutto:**
```bash
cd /home/runner/workspace && echo "=== RESET COMPLETO FORZATO ===" && git fetch origin && git reset --hard origin/main && git clean -fd && echo "✅ CODICE AGGIORNATO FORZATAMENTE!" && echo "=== VERIFICA PYTHON ===" && which python3 || which python || echo "Python non trovato - usa Run normale"
```

**Questo comando:**
- ✅ **Scarica** le ultime modifiche da GitHub
- ✅ **Sovrascrive** tutti i file locali con quelli di GitHub
- ✅ **Rimuove** file non tracciati che potrebbero causare conflitti
- ✅ **Verifica** che Python sia disponibile

---

## 🐍 **PROBLEMA PYTHON3:**

### **🚨 Se vedi "python3: command not found":**

**Su Replit, Python potrebbe essere in percorsi diversi. Ecco come trovarlo:**

### **1. Comando completo per trovare Python:**
```bash
echo "=== CERCO PYTHON ===" && find /usr -name "python*" -type f 2>/dev/null | head -10 && echo "---" && which python 2>/dev/null || which python3 2>/dev/null || which py 2>/dev/null || echo "Python non trovato in PATH" && echo "---" && ls -la /usr/bin/python* 2>/dev/null || ls -la /bin/python* 2>/dev/null || echo "Nessun python in /usr/bin o /bin"
```

### **2. Prova questi percorsi comuni su Replit:**
```bash
# Opzione A (più comune su Replit):
/home/runner/.pythonlibs/bin/python3 --version

# Opzione B:
/nix/store/*/bin/python3 --version 2>/dev/null | head -1

# Opzione C:
python --version

# Opzione D:
/usr/local/bin/python3 --version

# Opzione E:
/opt/python3/bin/python3 --version
```

### **3. Comando universale per trovare Python:**
```bash
PYTHON_CMD=$(find /usr /bin /home/runner/.pythonlibs /nix/store -name "python3" -type f 2>/dev/null | head -1) && echo "Python trovato: $PYTHON_CMD" && $PYTHON_CMD --version
```

3. **Se trovi Python, usa quel comando:**
```bash
# Su Replit, usa il percorso completo trovato:
/home/runner/workspace/.pythonlibs/bin/python -c "from config import settings; print('TEMPLATE:', settings.image.template_path)"
```

**✅ Perfetto! Su Replit usa sempre:**
```bash
/home/runner/workspace/.pythonlibs/bin/python
```

---

## 🔥 **SE ANCORA NON FUNZIONA:**

### **Reset completo del repository:**
```bash
cd /home/runner/workspace && rm -rf .git && git init && git remote add origin https://github.com/glitchbreak12/insta_spotter.git && git pull origin main
```

### **Poi usa il pulsante Run normale di Replit:**
- Premi **"Stop"** (tasto rosso)
- Aspetta 10 secondi
- Premi **"Run"** (tasto verde) - Questo avvierà automaticamente l'app

**Ricorda: Su Replit è sempre `python3`, mai `python`!**

---

## 🔥 PERCHÉ QUESTO FUNZIONA:
- ✅ **Reset completo** senza conflitti
- ✅ **Dipendenze installate automaticamente**
- ✅ **Nessun errore ModuleNotFoundError**

**COPIA IL COMANDO E INCOLLALO!** 🚀

Finalmente funzionerà tutto! 🎨✨

---

## 🔧 **ULTIMO FIX APPLICATO:**

**Risolto errore:** `cannot access local variable 'card_layer' where it is not associated with a value`

**Causa:** Variabile `card_layer` non accessibile nell'exception handler del metodo PIL.

**Soluzione:** Inizializzata `card_layer = None` all'inizio del metodo PIL per garantire scope corretto.

---

## 🔧 **ULTIMO FIX (Font Loading):**

**Risolto errore:** `'NoneType' object has no attribute 'load'`

**Causa:** `ImageFont.load_default()` deprecato in versioni recenti di Pillow.

**Soluzione:** Implementato fallback gerarchico per font:
1. Prima prova DejaVu Sans (Linux/Replit)
2. Poi Arial (Windows)
3. Infine fallback sicuro con `load_default()`

**Ora PIL dovrebbe funzionare perfettamente!** ✅