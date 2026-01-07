# Importare il Progetto su Replit

## Passo 1: Accedi a Replit
1. Vai su [https://replit.com](https://replit.com)
2. Accedi con il tuo account GoogleMapes

## Passo 2: Importa dal Repository GitHub
1. Clicca su **"Create Repl"**
2. Nella sezione **"Import from GitHub"**, inserisci:
   - **Repository URL**: `https://github.com/glitchbreak12/insta_spotter.git`
3. Seleziona **"Import from GitHub"**

## Passo 3: Configura il Repl
1. Il progetto dovrebbe caricarsi automaticamente
2. Verifica che tutti i file siano presenti nella cartella `workspace`

## Passo 4: Configura le Secrets (Environment Variables)
1. Nel pannello laterale sinistro, clicca su **"Secrets"** (icona lucchetto)
2. Aggiungi queste variabili obbligatorie:

### Credenziali Admin
```
ADMIN_USERNAME = admin
ADMIN_PASSWORD_HASH = $2b$12$U8nX942nhunNPi3rcz3KaeC1Vhr0W8tNkTYs9N7nDCnNRUp.OX.l2
SECRET_KEY = una_chiave_sicura_lunga_almeno_32_caratteri
```

### API Keys
```
GEMINI_API_KEY = la_tua_chiave_gemini_api
```

### Instagram (Opzionali)
```
INSTAGRAM_USERNAME = spottedatbz
INSTAGRAM_PASSWORD = la_password_del_tuo_account_instagram
INSTAGRAM_VERIFICATION_CODE = codice_6_cifre_se_richiesto
```

## Passo 5: Installa le Dipendenze
1. Nel terminal di Replit, esegui:
```bash
pip install -r requirements.txt
```

## Passo 6: Avvia l'Applicazione
1. Nel file `.replit`, assicurati che ci sia:
   - **run**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **language**: `python3`

2. Clicca su **"Run"** per avviare l'applicazione

## Passo 7: Verifica il Funzionamento
1. Una volta avviato, Replit ti darà un URL pubblico
2. Vai su `TUO_URL_REPLIT/spotted/new` per testare l'interfaccia utente
3. Vai su `TUO_URL_REPLIT/admin/login` per accedere alla dashboard admin
   - Username: `admin`
   - Password: `Admin123!Password`

## Passo 8: Mantieni l'App Attiva (Opzionale)
Per mantenere l'app sempre attiva gratuitamente:
1. Clicca su **"Publish"** in alto a destra
2. Seleziona **"Webview"** per rendere l'app pubblica
3. Oppure configura il keep-alive nel codice (già presente)

## Risoluzione Problemi Comuni

### Errore "Invalid Host Header"
- Questo è normale su Replit e viene gestito automaticamente dal codice

### Errore Database
- Il database SQLite viene creato automaticamente nella cartella `data/`

### Errore wkhtmltoimage
- Il codice ha un fallback a PIL che genera le immagini automaticamente

### Errore Instagram
- Assicurati che le credenziali Instagram siano corrette nelle Secrets
- Il codice gestisce automaticamente i challenge di verifica

## URL Pubblico
Dopo l'avvio, Replit fornirà un URL simile a:
`https://insta-spotter.googlemapes.replit.app`

Usa questo URL per accedere all'app da qualsiasi dispositivo.
