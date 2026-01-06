# ⚡ Setup Rapido per il Tuo Replit

## 🔗 Il Tuo Replit
**URL**: https://replit.com/@GoogleMapes/instaspotter  
**URL Pubblico**: https://instaspotter.GoogleMapes.replit.app

## 📋 Checklist Configurazione

### 1. ✅ Variabili d'Ambiente (Secrets)

Vai su **Secrets** (🔒) nel tuo Replit e aggiungi:

```env
INSTAGRAM_USERNAME=tuo_username_instagram
INSTAGRAM_PASSWORD=tua_password_instagram
REPLIT_URL=https://instaspotter.GoogleMapes.replit.app
GEMINI_API_KEY=tua_gemini_api_key
```

**⚠️ IMPORTANTE**: 
- L'URL `REPLIT_URL` è già corretto sopra - copialo esattamente così
- Se non hai una Gemini API Key, puoi ometterla (la moderazione AI sarà disabilitata)

### 2. ✅ Verifica il File `.replit`

Assicurati che il file `.replit` contenga:
```toml
run = "python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT"

[env]
PYTHONUNBUFFERED = "1"
PORT = "8000"
```

### 3. ✅ Installa le Dipendenze

Nel terminale di Replit, esegui:
```bash
pip install -r requirements.txt
```

### 4. ✅ Avvia l'Applicazione

1. Clicca sul pulsante **"Run"** (▶️) in Replit
2. Attendi che l'app si avvii
3. Controlla i log - dovresti vedere:
   ```
   🚀 Avvio dell'applicazione InstaSpotter...
   ✓ Database e tabelle pronti.
   ✓ Keep-alive task avviato per hosting 24/7
   ```

### 5. ✅ Testa l'Applicazione

Apri il browser e vai a:
- **Homepage**: https://instaspotter.GoogleMapes.replit.app/
- **Health Check**: https://instaspotter.GoogleMapes.replit.app/health
- **Form Spotted**: https://instaspotter.GoogleMapes.replit.app/spotted/new

## 🔄 Keep-Alive Automatico

L'app è già configurata per:
- ✅ Fare ping automatico ogni 5 minuti
- ✅ Mantenere il Repl attivo 24/7
- ✅ Prevenire il "sonno" per inattività

**Verifica nei log**:
```
✓ Keep-alive ping riuscito
```

## 🛠️ Troubleshooting

### ❌ L'app non si avvia
- Controlla che tutte le dipendenze siano installate: `pip install -r requirements.txt`
- Verifica che le variabili d'ambiente siano configurate in Secrets
- Controlla i log per errori specifici

### ❌ L'app si spegne dopo un po'
- Verifica che `REPLIT_URL` sia impostato correttamente in Secrets
- Controlla i log per vedere se il keep-alive funziona
- Considera di usare **UptimeRobot** come backup (vedi sotto)

### ❌ Errore "Trusted Host"
- Se vedi errori di trusted host, aggiungi in Secrets:
  ```
  DISABLE_TRUSTED_HOST=1
  ```
  (Solo temporaneamente per debug)

### ❌ Porta già in uso
- Il file `.replit` è già configurato correttamente
- Replit usa automaticamente `$PORT` - non modificare

## 🌐 Backup con UptimeRobot (Consigliato)

Per garantire 24/7 anche se Replit ha problemi:

1. Vai su [UptimeRobot.com](https://uptimerobot.com) (gratuito)
2. Crea un account
3. Aggiungi un nuovo monitor:
   - **Type**: HTTP(s)
   - **URL**: https://instaspotter.GoogleMapes.replit.app/health
   - **Interval**: 5 minutes
4. UptimeRobot farà ping automatico ogni 5 minuti

## 📊 Monitoraggio

- **Health Check**: https://instaspotter.GoogleMapes.replit.app/health
- **Logs**: Console di Replit
- **Status**: Controlla il pannello di Replit

## ✅ Verifica Finale

Dopo la configurazione, verifica:

- [ ] L'app si avvia senza errori
- [ ] Vedi "Keep-alive task avviato" nei log
- [ ] L'endpoint `/health` risponde
- [ ] Il form `/spotted/new` è accessibile
- [ ] Le variabili d'ambiente sono in Secrets (non nel codice)

## 🎉 Fatto!

La tua app è ora configurata per rimanere online 24/7 su Replit!

---

**Problemi?** Controlla `REPLIT_HOSTING.md` per più dettagli.

