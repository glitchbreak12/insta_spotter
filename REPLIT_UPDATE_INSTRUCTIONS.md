# 🚨 FIX IMMEDIATO - PASSA A card_v5_fixed.html

## 🔥 PROBLEMA:
Replit usa ancora il template **DORATO** invece di card_v5_fixed.html

## ✅ SOLUZIONE (20 secondi):

### **COPIA E INCOLLA QUESTO in Shell Replit:**
```bash
cd /home/runner/workspace && git pull origin main && python3 -c "
from config import settings
print('TEMPLATE ATTUALE:', settings.image.template_path)
if 'card_v5_fixed.html' in settings.image.template_path:
    print('✅ SUCCESSO: Ora usa card_v5_fixed.html!')
else:
    print('❌ FALLITO: Riprova')
"
```

### **DOPO:**
1. **RIAVVIA** l'app (tasto Restart in Replit)
2. **TESTA** uno spot
3. **VEDRAI** card_v5_fixed.html pulite!

---

## 🎯 COSA CAMBIA:

**VECCHIO:** Template dorato con stelle spaziali
**NUOVO:** card_v5_fixed.html pulito professionale

---

## 🔥 SE NON FUNZIONA:

```bash
# Forza aggiornamento completo:
cd /home/runner/workspace
git fetch origin && git reset --hard origin/main
echo "Forza aggiornamento fatto!"
```

**NON INSTALLARE NULLA** - solo `git pull origin main`!

Ora vai su Replit e fai il pull! 🚀</contents>
</xai:function_call">Write file REPLIT_UPDATE_INSTRUCTIONS.md