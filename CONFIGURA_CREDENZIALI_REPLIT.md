# 🔐 Configura Credenziali Admin per Replit

## ⚠️ IMPORTANTE: Su Replit NON Usare il File .env

Il file `.env` locale **NON funziona su Replit**. Devi configurare le credenziali nelle **Secrets** di Replit.

## 🚀 Setup Rapido (2 Minuti)

### Passo 1: Scegli Username e Password

Scegli:
- **Username**: `admin` (o quello che preferisci)
- **Password**: una password sicura (es: `Admin123!Password`)

### Passo 2: Genera l'Hash della Password

Nel **terminale di Replit**, esegui:

```bash
python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt']); print(pwd_context.hash('TUA_PASSWORD_SICURA'))"
```

**Sostituisci `TUA_PASSWORD_SICURA`** con la password che hai scelto.

**Esempio:**
```bash
python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt']); print(pwd_context.hash('Admin123!Password'))"
```

**Output:** Copia l'hash che inizia con `$2b$12$...`

### Passo 3: Aggiungi nelle Secrets di Replit

1. Vai su https://replit.com/@GoogleMapes/instaspotter
2. Clicca sul **lucchetto "Secrets"** (🔒) nel pannello laterale
3. Aggiungi queste variabili:

```
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$... (incolla l'hash generato)
```

**⚠️ IMPORTANTE:**
- Il nome della variabile deve essere esattamente `ADMIN_USERNAME` e `ADMIN_PASSWORD_HASH`
- Non usare spazi intorno al `=`
- L'hash deve essere completo (inizia con `$2b$12$`)

### Passo 4: Riavvia l'App

1. **Stop** l'app (se è in esecuzione)
2. **Run** per riavviare
3. Le nuove credenziali verranno caricate

### Passo 5: Accedi alla Dashboard

1. Vai a: `https://26c5b2a6-ace4-48ce-882f-4e9127f40551-00-18mhz2vlxvr3b.kirk.replit.dev/admin/login`
2. Inserisci:
   - **Username**: `admin` (o quello che hai configurato)
   - **Password**: la password originale che hai usato per generare l'hash (NON l'hash stesso!)

## 🔄 Alternativa: Usa Password Plaintext (Meno Sicuro)

Se preferisci non generare l'hash, puoi usare:

```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=tua_password_sicura
```

**⚠️ Meno sicuro**, ma funziona. L'app genererà automaticamente l'hash all'avvio.

## ✅ Verifica che Funzioni

Dopo aver configurato le Secrets e riavviato l'app, controlla i log:

**Se vedi:**
```
⚠️ Password configurata da ADMIN_PASSWORD plaintext
```
→ Funziona! (ma usa ADMIN_PASSWORD_HASH per sicurezza)

**Se vedi:**
```
❌ ADMIN_PASSWORD_HASH o ADMIN_PASSWORD non configurati!
```
→ Le Secrets non sono configurate correttamente

## 🆘 Problemi Comuni

### ❌ "Credenziali non valide"

**Soluzioni:**
1. Verifica che le Secrets siano esatte (case-sensitive)
2. Verifica che non ci siano spazi extra
3. Riavvia l'app dopo aver aggiunto le Secrets
4. Se usi `ADMIN_PASSWORD_HASH`, assicurati di usare la password **originale** (non l'hash) per il login

### ❌ "ADMIN_PASSWORD_HASH non configurato"

**Soluzioni:**
1. Verifica che il nome della variabile sia esattamente `ADMIN_PASSWORD_HASH`
2. Verifica che l'hash sia completo (inizia con `$2b$12$`)
3. Riavvia l'app

### ❌ Il file .env non funziona

**Spiegazione:**
- Su Replit, il file `.env` locale **NON viene letto**
- Devi usare le **Secrets** di Replit
- Le Secrets sono più sicure e funzionano correttamente

## 📝 Esempio Completo

**Secrets da aggiungere:**
```
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ
```

**Credenziali per il login:**
- Username: `admin`
- Password: `Admin123!Password` (la password originale, NON l'hash)

## 🎯 Quick Start

**Se vuoi configurare velocemente:**

1. Aggiungi in Secrets:
   ```
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=Admin123!Password
   ```

2. Riavvia l'app

3. Accedi con:
   - Username: `admin`
   - Password: `Admin123!Password`

**⚠️ Cambia la password dopo il primo accesso per sicurezza!**

---

**Dopo aver configurato le Secrets, potrai accedere alla dashboard! 🔐**

