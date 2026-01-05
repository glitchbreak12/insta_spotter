# 🔐 Verifica Credenziali Admin

## 📋 Credenziali Attuali

Le credenziali admin dipendono da cosa hai configurato nelle **Secrets** di Replit.

### Username (Default)

**Username di default**: `admin`

Questo è il valore di default se non hai configurato `ADMIN_USERNAME` nelle Secrets.

### Password

La password dipende da cosa hai configurato nelle Secrets:

- Se hai configurato `ADMIN_PASSWORD` → usa quella password
- Se hai configurato `ADMIN_PASSWORD_HASH` → devi ricordare la password originale (l'hash non può essere invertito)
- Se non hai configurato nessuna delle due → **non puoi accedere** (vedrai un errore nei log)

## 🔍 Come Verificare le Tue Credenziali

### Metodo 1: Controlla le Secrets di Replit

1. Vai su https://replit.com/@GoogleMapes/instaspotter
2. Clicca sul lucchetto **"Secrets"** (🔒) nel pannello laterale
3. Cerca queste variabili:
   - `ADMIN_USERNAME` → questo è il tuo username
   - `ADMIN_PASSWORD` → questa è la tua password (se configurata)
   - `ADMIN_PASSWORD_HASH` → se vedi solo questo, devi ricordare la password originale

### Metodo 2: Controlla i Log

Nei log di Replit, cerca questi messaggi:

- Se vedi: `❌ ADMIN_PASSWORD_HASH o ADMIN_PASSWORD non configurati!` → **non hai configurato la password**
- Se vedi: `⚠️ Password configurata da ADMIN_PASSWORD plaintext` → hai configurato `ADMIN_PASSWORD` nelle Secrets

## 🚀 Se Non Hai Configurato le Credenziali

### Setup Rapido:

1. **Scegli una password sicura** (min 12 caratteri, con maiuscole, numeri, caratteri speciali)

2. **Nel terminale di Replit**, genera l'hash:
   ```bash
   python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt']); print(pwd_context.hash('TUA_PASSWORD_SICURA'))"
   ```

3. **Aggiungi in Secrets**:
   ```
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD_HASH=$2b$12$... (incolla l'hash generato)
   ```
   
   **Oppure** (più semplice ma meno sicuro):
   ```
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=tua_password_sicura
   ```

4. **Riavvia l'app** (Stop → Run)

## 🔑 Credenziali di Default (Se Non Configurate)

Se **NON** hai configurato nulla nelle Secrets:

- **Username**: `admin` (valore di default)
- **Password**: **NON FUNZIONA** - devi configurarla

## ✅ Come Accedere

1. Vai su: `https://instaspotter.GoogleMapes.replit.app/admin/login`
2. Inserisci:
   - **Username**: `admin` (o quello che hai configurato in `ADMIN_USERNAME`)
   - **Password**: La password che hai configurato in `ADMIN_PASSWORD` o quella usata per generare `ADMIN_PASSWORD_HASH`

## 🆘 Se Non Riesci ad Accedere

### Problema: "Credenziali non valide"

**Soluzioni:**

1. **Verifica le Secrets:**
   - Controlla che `ADMIN_USERNAME` e `ADMIN_PASSWORD` (o `ADMIN_PASSWORD_HASH`) siano configurate
   - Verifica che i nomi siano esatti (case-sensitive)

2. **Riavvia l'app:**
   - Stop → Run
   - Le nuove credenziali vengono caricate all'avvio

3. **Prova a resettare:**
   - Rimuovi le Secrets esistenti
   - Aggiungi nuove credenziali
   - Riavvia l'app

4. **Controlla i log:**
   - Cerca errori di autenticazione
   - Verifica che le credenziali vengano caricate correttamente

## 📝 Nota Importante

- ✅ Le credenziali sono **case-sensitive** (maiuscole/minuscole contano)
- ✅ Se usi `ADMIN_PASSWORD_HASH`, devi ricordare la password originale (l'hash non può essere invertito)
- ✅ Le credenziali sono salvate in modo sicuro nelle Secrets di Replit (non nel codice)

---

**Per sicurezza, non condividere mai le tue credenziali admin! 🔒**

