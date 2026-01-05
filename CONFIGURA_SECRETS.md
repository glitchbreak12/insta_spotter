# 🔐 Configurazione Secrets su Replit

## ⚠️ Warning Attuali

Vedo questi warning nei log:
- `SECRET_KEY non configurato!`
- `ADMIN_PASSWORD_HASH o ADMIN_PASSWORD non configurati!`

Questi sono importanti per la sicurezza dell'app. Configuriamoli!

## 🚀 Setup Rapido

### 1. Genera SECRET_KEY

Nel terminale di Replit, esegui:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Copia il risultato** (sarà una stringa lunga tipo: `abc123xyz...`)

### 2. Genera ADMIN_PASSWORD_HASH

Scegli una password sicura per l'admin (min 12 caratteri, con maiuscole, numeri, caratteri speciali).

Poi nel terminale di Replit, esegui (sostituisci `TUA_PASSWORD` con la tua password):

```bash
python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt']); print(pwd_context.hash('TUA_PASSWORD'))"
```

**Copia il risultato** (sarà una stringa che inizia con `$2b$12$...`)

### 3. Aggiungi alle Secrets di Replit

1. Clicca sul lucchetto **"Secrets"** nel pannello laterale di Replit
2. Aggiungi queste variabili:

```
SECRET_KEY=<incolla il valore generato al punto 1>
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<incolla il valore generato al punto 2>
```

**Oppure** se preferisci usare una password in plaintext (meno sicuro, ma più semplice):

```
SECRET_KEY=<incolla il valore generato al punto 1>
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<la tua password in plaintext>
```

⚠️ **Nota**: `ADMIN_PASSWORD_HASH` è più sicuro. `ADMIN_PASSWORD` funziona ma genera un warning.

### 4. Riavvia l'App

1. Clicca "Stop"
2. Clicca "Run"
3. I warning dovrebbero sparire!

## ✅ Checklist Completa Secrets

Assicurati di avere tutte queste variabili in Secrets:

- [ ] `SECRET_KEY` (generato)
- [ ] `ADMIN_USERNAME` (di solito `admin`)
- [ ] `ADMIN_PASSWORD_HASH` o `ADMIN_PASSWORD` (generato)
- [ ] `INSTAGRAM_USERNAME` (il tuo username Instagram)
- [ ] `INSTAGRAM_PASSWORD` (la tua password Instagram)
- [ ] `REPLIT_URL` (es: `https://instaspotter.GoogleMapes.replit.app`)
- [ ] `GEMINI_API_KEY` (opzionale, per moderazione AI)

## 🔒 Sicurezza

- ✅ **SECRET_KEY**: Usato per firmare i JWT tokens. Deve essere casuale e segreto.
- ✅ **ADMIN_PASSWORD_HASH**: Hash bcrypt della password admin. Non può essere invertito.
- ✅ **Secrets in Replit**: Non vengono mai committati su Git, sono sicuri.

## 🆘 Problemi?

Se vedi ancora i warning dopo aver aggiunto i secrets:
1. Verifica che i nomi delle variabili siano esatti (case-sensitive)
2. Riavvia completamente l'app (Stop → Run)
3. Controlla i log per errori

---

**Dopo questa configurazione, l'app sarà completamente sicura! 🔐**

