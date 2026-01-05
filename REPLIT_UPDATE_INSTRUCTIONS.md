# 🚨 REPLIT - FIX FINALE

## 🔥 PROBLEMA:
File Replit bloccano il download del codice.

## ✅ SOLUZIONE SEMPLICISSIMA:

### **OPZIONE 1 - COMANDO UNICO:**
```bash
cd /home/runner/workspace && echo "=== SALVA FILE ===" && mkdir -p /tmp/replit_backup && cp .env.example /tmp/replit_backup/ 2>/dev/null || true && cp .gitignore /tmp/replit_backup/ 2>/dev/null || true && cp .replit /tmp/replit_backup/ 2>/dev/null || true && cp replit.nix /tmp/replit_backup/ 2>/dev/null || true && echo "=== RIMUOVI BLOCCANTI ===" && rm -f .env.example .gitignore .replit replit.nix && echo "=== PULL CODICE ===" && git pull origin main && echo "=== RIPRISTINA FILE ===" && cp /tmp/replit_backup/* . 2>/dev/null || true && echo "✅ FATTO!"
```

### **OPZIONE 2 - PASSO PER PASSO (se il comando unico non funziona):**
```bash
# PASSO 1: Salva file importanti
mkdir -p /tmp/replit_backup
cp .env.example /tmp/replit_backup/ 2>/dev/null || true
cp .gitignore /tmp/replit_backup/ 2>/dev/null || true
cp .replit /tmp/replit_backup/ 2>/dev/null || true

# PASSO 2: Rimuovi file che bloccano
rm -f .env.example .gitignore .replit

# PASSO 3: Scarica codice
git pull origin main

# PASSO 4: Ripristina file
cp /tmp/replit_backup/* . 2>/dev/null || true
echo "✅ CODICE AGGIORNATO!"
```

### **VERIFICA:**
```bash
# Su Replit potrebbe essere 'python' o 'python3':
python -c "from config import settings; print('TEMPLATE:', settings.image.template_path)" 2>/dev/null || python3 -c "from config import settings; print('TEMPLATE:', settings.image.template_path)"
# Dovrebbe mostrare: card_v5.html
```

### **SE PYTHON NON FUNZIONA:**
```bash
# Verifica quale versione Python è disponibile:
which python || which python3 || echo "Python non trovato - riavvia Replit"
```

### **RIAVVIA:**
- Premi **Restart** in Replit
- **TESTA** uno spot
- **VEDRAI** card_v5.html glow blu!

---

## 🎯 **RISULTATO:**
✅ Template dorato eliminato  
✅ card_v5.html attivo  
✅ Tutto funziona  

**COPIA IL COMANDO UNICO E FATTO!** 🚀✨