# 🚨 CARICAMENTO/DEPLOY SU REPLIT - Guida Definitiva

## 🔥 SITUAZIONE:
Hai aggiornato il codice e vuoi vedere le **card_v5.html blu spettacolari** su Replit.

## ✅ METODO 1 - AGGIORNAMENTO SEMPLICE (Raccomandato):

### **PASSO 1: Apri Shell Replit**
- Vai su https://replit.com/@GoogleMapes/instaspotter
- Clicca il pulsante **"Shell"** (o usa Ctrl+Shift+S)

### **PASSO 2: Aggiorna il Codice**
```bash
# Scarica le ultime modifiche
cd /home/runner/workspace
git pull origin main
echo "✅ Codice aggiornato!"
```

### **PASSO 3: Verifica Template**
```bash
# Controlla che sia attivo card_v5.html
python3 -c "from config import settings; print('TEMPLATE ATTUALE:', settings.image.template_path)" 2>/dev/null || python -c "from config import settings; print('TEMPLATE ATTUALE:', settings.image.template_path)"
# Dovrebbe mostrare: card_v5.html
```

### **PASSO 4: Riavvia l'App**
- Premi il pulsante **"Stop"** (se è in esecuzione)
- Premi il pulsante **"Run"** per riavviare
- Aspetta che dica "Application startup complete"

---

## ✅ METODO 2 - FORZA RESET COMPLETO:

Se il metodo 1 non funziona:

```bash
cd /home/runner/workspace && echo "=== BACKUP FILE ===" && mkdir -p /tmp/backup && cp .env.example /tmp/backup/ 2>/dev/null || true && cp .gitignore /tmp/backup/ 2>/dev/null || true && cp .replit /tmp/backup/ 2>/dev/null || true && echo "=== PULIZIA ===" && rm -f .env.example .gitignore .replit && echo "=== RESET REPO ===" && git fetch origin && git reset --hard origin/main && echo "=== RIPRISTINA ===" && cp /tmp/backup/* . 2>/dev/null || true && echo "✅ RESET COMPLETATO!"
```

---

## ✅ METODO 3 - RICREA TUTTO DA ZERO:

Se nulla funziona:

```bash
cd /home/runner/workspace && rm -rf * .git && git init && git remote add origin https://github.com/glitchbreak12/insta_spotter.git && git pull origin main && echo "REPOSITORY RICREATO DA ZERO!"
```

---

## 🎯 TEST FINALE:

### **Test Template:**
```bash
python3 -c "from config import settings; print('TEMPLATE:', settings.image.template_path)"
# Deve dire: card_v5.html
```

### **Test Card Generation:**
```bash
python3 -c "
from app.image.generator import ImageGenerator
gen = ImageGenerator()
result = gen.from_text('Test card V5 blu spettacolare!', 'test_deploy.png', 123)
print('Card generata:', result)
"
```

### **Test Web App:**
- Vai su: https://instaspotter.GoogleMapes.replit.app
- Dovrebbe funzionare con il nuovo codice

---

## 🎉 RISULTATO:
✅ **Template:** card_v5.html attivo
✅ **Rendering:** Blu spettacolare con glow professionale
✅ **Bot:** Pronto per Instagram
✅ **Admin:** Accessibile

**SCEGLI UN METODO E CARICA SUBITO!** 🚀

Dopo il caricamento, le tue card saranno **blu spettacolari** invece che dorate! ✨</contents>
</xai:function_call">Write file REPLIT_UPDATE_INSTRUCTIONS.md