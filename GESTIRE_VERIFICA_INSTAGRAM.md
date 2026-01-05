# 🔐 Gestire Verifica Instagram (Challenge)

## Problema
Instagram a volte richiede una verifica via email quando rileva un nuovo accesso o attività sospetta. Questo è normale e serve per proteggere il tuo account.

## Soluzione

### Passo 1: Controlla la tua Email
1. Controlla la casella email associata al tuo account Instagram
2. Cerca un'email da Instagram con un codice a 6 cifre
3. Il codice è valido per pochi minuti

### Passo 2: Aggiungi il Codice nei Secrets di Replit
1. Vai su **Secrets** (🔒) nel tuo Replit
2. Aggiungi una nuova variabile:
   - **Key**: `INSTAGRAM_VERIFICATION_CODE`
   - **Value**: Il codice a 6 cifre che hai ricevuto via email
   - Esempio: `123456`

### Passo 3: Riavvia l'App
1. Ferma l'app (Stop)
2. Riavvia (Run)
3. L'app userà automaticamente il codice per completare la verifica

## Esempio

```
Secrets di Replit:
┌─────────────────────────────┬──────────┐
│ Key                         │ Value    │
├─────────────────────────────┼──────────┤
│ INSTAGRAM_USERNAME          │ tuo_user │
│ INSTAGRAM_PASSWORD          │ tua_pass │
│ INSTAGRAM_VERIFICATION_CODE │ 123456   │ ← Aggiungi questo
└─────────────────────────────┴──────────┘
```

## Note Importanti

- ⏰ Il codice è valido solo per pochi minuti
- 🔄 Dopo la prima verifica, Instagram di solito non richiede più il codice
- 🗑️ Puoi rimuovere `INSTAGRAM_VERIFICATION_CODE` dai Secrets dopo il primo login riuscito
- 🔒 La sessione viene salvata, quindi non dovrai rifare la verifica ogni volta

## Se il Codice Non Funziona

1. **Codice scaduto**: Richiedi un nuovo codice (riavvia l'app)
2. **Codice errato**: Verifica di aver copiato correttamente il codice
3. **Email non ricevuta**: Controlla anche la cartella spam

## Troubleshooting

### "Challenge required" continua ad apparire
- Rimuovi il file di sessione: `rm data/instagram_session.json`
- Aggiungi il nuovo codice nei Secrets
- Riavvia l'app

### Instagram blocca l'account
- Vai su instagram.com e sblocca manualmente l'account
- Poi riprova il login dall'app

