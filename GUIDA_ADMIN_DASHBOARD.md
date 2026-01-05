# 🔐 Guida Admin Dashboard - InstaSpotter

## 📋 Accesso Admin Dashboard

L'admin dashboard ti permette di:
- ✅ Approvare o rifiutare messaggi manualmente
- ✅ Modificare i messaggi prima della pubblicazione
- ✅ Vedere statistiche e analisi
- ✅ Gestire i messaggi in attesa di moderazione

## 🚀 Come Accedere

### 1. Configura le Credenziali Admin

Prima di tutto, devi configurare le credenziali admin nelle **Secrets** di Replit:

#### Opzione A: Usa Password Hash (Consigliato - Più Sicuro)

Nel terminale di Replit, genera l'hash della password:

```bash
python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt']); print(pwd_context.hash('TUA_PASSWORD_SICURA'))"
```

Poi aggiungi in **Secrets**:
```
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$... (incolla l'hash generato)
```

#### Opzione B: Usa Password Plaintext (Più Semplice)

Aggiungi direttamente in **Secrets**:
```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=tua_password_sicura
```

⚠️ **Nota**: L'opzione B è meno sicura ma più semplice. L'opzione A è consigliata per produzione.

### 2. Accedi alla Dashboard

1. Vai su: `https://instaspotter.GoogleMapes.replit.app/admin/login`
2. Inserisci:
   - **Username**: `admin` (o quello che hai configurato)
   - **Password**: La password che hai configurato
3. Clicca "Login"

### 3. Dashboard Principale

Dopo il login, vedrai:
- **Statistiche**: Contatori di messaggi per stato (PENDING, APPROVED, REJECTED, POSTED)
- **Grafico**: Messaggi ricevuti negli ultimi 7 giorni
- **Tabella Messaggi**: Lista di tutti i messaggi con filtri e paginazione

## ✅ Come Approvare/Rifiutare Messaggi

### Metodo 1: Azioni Singole

1. Nella tabella dei messaggi, trova il messaggio che vuoi moderare
2. Clicca sul pulsante:
   - ✅ **Approve** (verde) - per approvare
   - ❌ **Reject** (rosso) - per rifiutare
   - ✏️ **Edit** (blu) - per modificare il testo

### Metodo 2: Azioni Multiple (Bulk)

1. Seleziona più messaggi usando le checkbox
2. Clicca su "Approve Selected" o "Reject Selected" in alto
3. Tutti i messaggi selezionati verranno approvati/rifiutati insieme

### Metodo 3: Dalla Coda di Moderazione

1. Vai alla sezione "Moderation Queue"
2. Vedi solo i messaggi in attesa (PENDING)
3. Clicca "View" per vedere i dettagli
4. Approva o rifiuta direttamente

## 📊 Stati dei Messaggi

- **PENDING**: In attesa di moderazione (i tuoi messaggi attuali)
- **APPROVED**: Approvato e pronto per la pubblicazione
- **REJECTED**: Rifiutato (non verrà pubblicato)
- **POSTED**: Già pubblicato su Instagram
- **FAILED**: Errore durante la pubblicazione

## 🔍 Funzionalità Avanzate

### Modificare un Messaggio

1. Clicca sul pulsante "Edit" (✏️) accanto al messaggio
2. Modifica il testo nella finestra modale
3. Salva le modifiche
4. Il messaggio modificato può essere approvato normalmente

### Aggiungere Note Admin

1. Clicca "View" su un messaggio
2. Nella finestra modale, aggiungi una nota nella sezione "Admin Notes"
3. Le note sono visibili solo a te e aiutano a tracciare decisioni

### Filtrare i Messaggi

- Usa i filtri in alto per vedere solo messaggi con uno stato specifico
- Cerca per testo usando la barra di ricerca
- Ordina per data, ID, o stato

## 🎯 Workflow Consigliato

1. **Ricevi Messaggi**: Gli utenti inviano messaggi → vanno in PENDING
2. **Modera**: Vai su Admin Dashboard → approva/rifiuta i messaggi
3. **Pubblica**: I messaggi APPROVED vengono pubblicati automaticamente dal worker
4. **Monitora**: Controlla i messaggi POSTED per vedere cosa è stato pubblicato

## ⚙️ Configurazione Worker

Il worker pubblica automaticamente i messaggi APPROVED. Per configurare:

1. Vai su "Settings" nella dashboard
2. Configura l'intervallo di pubblicazione
3. Attiva/disattiva la modalità autonoma

## 🆘 Troubleshooting

### Non riesco ad accedere
- Verifica che `ADMIN_USERNAME` e `ADMIN_PASSWORD` (o `ADMIN_PASSWORD_HASH`) siano configurati in Secrets
- Riavvia l'app dopo aver aggiunto le credenziali
- Controlla i log per errori di autenticazione

### I messaggi non si vedono
- Verifica che il database sia configurato correttamente
- Controlla i log per errori di database
- Ricarica la pagina

### Le azioni non funzionano
- Controlla la console del browser (F12) per errori JavaScript
- Verifica che il token di autenticazione sia valido
- Prova a fare logout e login di nuovo

## 📝 Note Importanti

- ✅ I messaggi in PENDING richiedono approvazione manuale
- ✅ Solo i messaggi APPROVED vengono pubblicati
- ✅ Puoi modificare i messaggi prima di approvarli
- ✅ Le modifiche vengono salvate nel database
- ✅ Il worker controlla periodicamente i messaggi APPROVED

---

**Buona moderazione! 🎉**

