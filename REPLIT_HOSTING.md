# 🚀 Guida Hosting 24/7 Gratuito su Replit

Questa guida ti aiuterà a configurare InstaSpotter per rimanere online 24/7 su Replit gratuitamente.

## ✅ Configurazione Automatica

L'applicazione è già configurata con:
- ✅ **Keep-alive automatico**: L'app fa ping a se stessa ogni 5 minuti per rimanere attiva
- ✅ **Health check endpoint**: `/health` per monitoraggio esterno
- ✅ **Configurazione Replit**: File `.replit` già pronto

## 📋 Passi per l'Hosting su Replit

### 1. Importa il Progetto su Replit

1. Vai su [Replit](https://replit.com)
2. Clicca su "Create Repl"
3. Scegli "Import from GitHub" o carica i file del progetto
4. Seleziona il linguaggio Python

### 2. Configura le Variabili d'Ambiente

Nella sezione "Secrets" (🔒) di Replit, aggiungi:

```
INSTAGRAM_USERNAME=tuo_username
INSTAGRAM_PASSWORD=tua_password
GEMINI_API_KEY=tua_gemini_api_key (opzionale)
REPLIT_URL=https://tuo-repl.replit.app
```

**⚠️ IMPORTANTE**: 
- Sostituisci `tuo-repl` con il nome del tuo Repl
- Il formato è: `https://NOME-REPL.utente.replit.app`
- Puoi trovare l'URL esatto nella sezione "Webview" di Replit

### 3. Avvia l'Applicazione

1. Clicca sul pulsante "Run" in Replit
2. L'app si avvierà automaticamente
3. Controlla i log per verificare che il keep-alive sia attivo:
   ```
   ✓ Keep-alive task avviato per hosting 24/7
   ✓ Keep-alive ping riuscito
   ```

### 4. Abilita "Always On" (Opzionale ma Consigliato)

**Nota**: Replit gratuito mette in pausa i Repl dopo inattività. Il keep-alive aiuta, ma per garantire 24/7:

1. Vai su [Replit Deploy](https://replit.com/deploy) (richiede account)
2. Oppure considera alternative gratuite elencate sotto

## 🔄 Come Funziona il Keep-Alive

L'applicazione include un task in background che:
- Attende 1 minuto dopo l'avvio
- Fa un ping all'endpoint `/health` ogni 5 minuti
- Mantiene il Repl attivo prevenendo il "sonno" per inattività

## 🌐 Alternative Gratuite 24/7

Se Replit non è sufficiente, ecco alternative gratuite:

### 1. **Render.com** (Consigliato)
- ✅ Hosting gratuito 24/7 per web services
- ✅ Auto-deploy da GitHub
- ✅ Database PostgreSQL gratuito incluso
- 📝 Setup: Crea un nuovo "Web Service" e collega il tuo repo GitHub

### 2. **Railway.app**
- ✅ $5 di credito gratuito al mese
- ✅ Hosting 24/7
- ✅ Auto-deploy da GitHub
- 📝 Setup: Crea un nuovo progetto e collega GitHub

### 3. **Fly.io**
- ✅ Hosting gratuito con limiti generosi
- ✅ 24/7 disponibile
- 📝 Setup: Usa il file `fly.toml` già presente nel progetto

### 4. **UptimeRobot + Replit**
- ✅ Monitoraggio gratuito esterno
- ✅ Ping automatico ogni 5 minuti
- 📝 Setup: Crea account su UptimeRobot e aggiungi il tuo URL Replit

## 🛠️ Troubleshooting

### L'app si spegne dopo un po'
- Verifica che `REPLIT_URL` sia configurato correttamente
- Controlla i log per errori del keep-alive
- Considera di usare UptimeRobot come backup

### Errore "Port already in use"
- Replit usa automaticamente la variabile `$PORT`
- Il file `.replit` è già configurato correttamente

### Il worker non funziona
- Su Replit, il worker può essere eseguito in un processo separato
- Considera di integrare il worker nell'app principale se necessario

## 📊 Monitoraggio

Puoi monitorare lo stato dell'app:
- **Health check**: `https://tuo-repl.replit.app/health`
- **Logs**: Controlla la console di Replit
- **UptimeRobot**: Configura monitoraggio esterno per notifiche

## 🔐 Sicurezza

- ✅ Le credenziali sono in "Secrets" (non nel codice)
- ✅ CORS e security headers configurati
- ✅ Rate limiting attivo

## 📝 Note Importanti

1. **Replit Gratuito**: Ha limiti di risorse (CPU/RAM)
2. **Cold Start**: Il primo avvio può richiedere alcuni secondi
3. **Database**: SQLite locale su Replit (considera PostgreSQL su Render per produzione)

## 🆘 Supporto

Se hai problemi:
1. Controlla i log in Replit
2. Verifica le variabili d'ambiente
3. Testa l'endpoint `/health` manualmente

---

**Buon hosting! 🎉**

