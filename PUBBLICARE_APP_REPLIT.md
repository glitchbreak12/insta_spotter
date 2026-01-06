# 🚀 Come Pubblicare l'App su Replit

## ✅ Passi per Rendere l'App Accessibile Pubblicamente

### 1. Assicurati che l'App Sia in Esecuzione

1. Vai su https://replit.com/@GoogleMapes/instaspotter
2. Verifica che il pulsante **"Run"** (▶️) sia verde e l'app sia avviata
3. Controlla i log - dovresti vedere:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

### 2. Pubblica l'App

**Opzione A: Pulsante "Publish" (Se Disponibile)**

1. Nel tuo Replit, cerca il pulsante **"Publish"** o **"Deploy"** in alto a destra
2. Clicca su "Publish"
3. Compila i dettagli:
   - **Title**: InstaSpotter
   - **Description**: Bot per pubblicazione messaggi spotted su Instagram
   - **Visibility**: Public (per renderla accessibile)
4. Clicca "Publish" o "Deploy"

**Opzione B: Webview/Always On**

1. Cerca la sezione **"Webview"** nel pannello laterale
2. Clicca su **"Open in new tab"** o **"Always On"**
3. Questo dovrebbe rendere l'app accessibile pubblicamente

### 3. Verifica l'URL Pubblico

Dopo la pubblicazione, Replit ti fornirà un URL pubblico. Potrebbe essere:

- `https://instaspotter.GoogleMapes.replit.app`
- Oppure un URL diverso che Replit assegna

**Come trovare l'URL esatto:**

1. Dopo aver cliccato "Publish", Replit mostrerà l'URL pubblico
2. Oppure vai su "Webview" → "Open in new tab" e copia l'URL dalla barra degli indirizzi
3. L'URL sarà nel formato: `https://NOME-REPL.UTENTE.replit.app`

### 4. Testa l'Accesso

1. Apri un browser su un altro PC
2. Vai all'URL pubblico che hai ottenuto
3. Dovresti vedere la homepage dell'app

## 🔧 Se l'App Non È Accessibile

### Problema: "This site can't be reached"

**Soluzioni:**

1. **Verifica che l'app sia in esecuzione:**
   - Il pulsante "Run" deve essere verde
   - Nei log deve apparire "Uvicorn running"

2. **Riavvia l'app:**
   - Clicca "Stop"
   - Clicca "Run"
   - Attendi che si avvii completamente

3. **Verifica la configurazione:**
   - Il file `.replit` deve contenere: `run = "python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT"`
   - La porta deve essere configurata (8000)

4. **Pubblica esplicitamente:**
   - Cerca il pulsante "Publish" o "Deploy"
   - Pubblica l'app se non l'hai già fatto

5. **Verifica l'URL:**
   - L'URL potrebbe essere case-sensitive
   - Prova con maiuscole/minuscole diverse
   - Verifica l'URL esatto dalla sezione "Webview"

## 📝 Note Importanti

- ✅ L'app deve essere **in esecuzione** per essere accessibile
- ✅ Su Replit gratuito, l'app potrebbe andare in pausa dopo inattività
- ✅ Il keep-alive automatico aiuta a mantenerla attiva
- ✅ L'URL potrebbe cambiare se ricrei il Repl

## 🆘 Se Continua a Non Funzionare

1. **Controlla i log** su Replit per errori
2. **Verifica che tutte le dipendenze siano installate**: `pip install -r requirements.txt`
3. **Prova a riavviare completamente** l'app
4. **Controlla la sezione "Webview"** per l'URL corretto

---

**Dopo la pubblicazione, l'app sarà accessibile pubblicamente! 🌐**

