# 🚨 AGGIORNAMENTO REPLIT OBBLIGATORIO - Template card_v5_fixed.html

## 🔥 PROBLEMA CRITICO:
Replit sta usando il vecchio template DORATO (card_v11_celestial) invece di **card_v5_fixed.html**!

## ✅ SOLUZIONE IMMEDIATA (3 minuti):

### **PASSO 1: PULL CODICE**
```bash
# Apri Shell su Replit:
cd /home/runner/workspace
git pull origin main
echo "✅ Template aggiornato a card_v5_fixed.html!"
```

### **PASSO 2: VERIFICA**
```bash
python3 -c "
from config import settings
print('Template attuale:', settings.image.template_path)
if 'card_v5_fixed.html' in settings.image.template_path:
    print('✅ CORRETTO: Ora usa card_v5_fixed.html!')
else:
    print('❌ ANCORA SBAGLIATO - riprova git pull')
"
```

### **PASSO 3: RIAVVIA**
- Premi **"Restart"** in Replit
- Ora le card saranno **card_v5_fixed.html** pulite!

---

## 🎭 OPZIONALE: Playwright per rendering perfetto

Se vuoi il rendering HTML perfetto (non necessario, ma meglio):

```bash
pip install playwright
playwright install chromium

# Verifica
python3 -c "
from app.image.generator import ImageGenerator
gen = ImageGenerator()
print('Playwright disponibile:', gen.playwright_available)
"
```

---

## 🎯 RISULTATO FINALE:
- ✅ Template: **card_v5_fixed.html** (non più dorato)
- ✅ Sistema retry: **primo post ora funziona**
- ✅ Card pulite con glow 3D professionale

**AGGIORNA SUBITO REPLIT CON `git pull origin main`!** 🚀</contents>
</xai:function_call">Write file REPLIT_UPDATE_INSTRUCTIONS.md