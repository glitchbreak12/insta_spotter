# 🔐 Accedi alla Dashboard Admin - Guida Rapida

## 🔗 URL Dashboard Admin

Basandoti sul tuo URL temporaneo:
**https://26c5b2a6-ace4-48ce-882f-4e9127f40551-00-18mhz2vlxvr3b.kirk.replit.dev**

### URL Dashboard Admin:

**https://26c5b2a6-ace4-48ce-882f-4e9127f40551-00-18mhz2vlxvr3b.kirk.replit.dev/admin/login**

## 🔑 Credenziali Admin

Le credenziali dipendono da cosa hai configurato nelle **Secrets** di Replit.

### Verifica le Tue Credenziali:

1. **Vai su Replit**: https://replit.com/@GoogleMapes/instaspotter
2. **Clicca sul lucchetto "Secrets"** (🔒) nel pannello laterale
3. **Cerca queste variabili:**
   - `ADMIN_USERNAME` → questo è il tuo username
   - `ADMIN_PASSWORD` → questa è la tua password (se configurata)
   - `ADMIN_PASSWORD_HASH` → se vedi solo questo, devi ricordare la password originale

### Credenziali di Default:

Se **NON** hai configurato nulla nelle Secrets:

- **Username**: `admin` (valore di default)
- **Password**: **NON FUNZIONA** - devi configurarla

## 🚀 Se Non Hai Configurato le Credenziali

### Setup Rapido (2 minuti):

1. **Scegli una password sicura** (es: `Admin123!Password`)

2. **Nel terminale di Replit**, genera l'hash:
   ```bash
   python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt']); print(pwd_context.hash('TUA_PASSWORD_SICURA'))"
   ```

3. **Aggiungi in Secrets** (clicca sul lucchetto):
   ```
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD_HASH=$2b$12$... (incolla l'hash generato)
   ```
   
   **Oppure** (più semplice):
   ```
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=tua_password_sicura
   ```

4. **Riavvia l'app** (Stop → Run)

5. **Accedi alla dashboard** con:
   - Username: `admin`
   - Password: quella che hai configurato

## ✅ Come Accedere

1. **Vai all'URL**: https://26c5b2a6-ace4-48ce-882f-4e9127f40551-00-18mhz2vlxvr3b.kirk.replit.dev/admin/login
2. **Inserisci le credenziali** che hai configurato
3. **Clicca "Access Dashboard"**

## 🆘 Se Non Riesci ad Accedere

### Problema: "Credenziali non valide"

**Soluzioni:**

1. **Verifica le Secrets:**
   - Controlla che `ADMIN_USERNAME` e `ADMIN_PASSWORD` (o `ADMIN_PASSWORD_HASH`) siano configurate
   - Verifica che i nomi siano esatti (case-sensitive)

2. **Riavvia l'app:**
   - Stop → Run
   - Le nuove credenziali vengono caricate all'avvio

3. **Controlla i log:**
   - Cerca errori di autenticazione
   - Verifica che le credenziali vengano caricate correttamente

## 📝 Note Importanti

- ✅ Le credenziali sono **case-sensitive** (maiuscole/minuscole contano)
- ✅ Se usi `ADMIN_PASSWORD_HASH`, devi ricordare la password originale
- ✅ Le credenziali sono salvate in modo sicuro nelle Secrets di Replit

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

**Dopo aver configurato le credenziali, potrai accedere alla dashboard! 🔐**

