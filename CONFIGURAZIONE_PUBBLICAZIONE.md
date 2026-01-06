# 🚀 Configurazione Pubblicazione Replit

## 📋 Comandi Build e Run

Quando pubblichi l'app su Replit, ti chiederà di configurare:

### Build Command (Opzionale)

**Lascia vuoto** oppure usa:

```bash
pip install -r requirements.txt
```

**Spiegazione:**
- Il build command viene eseguito prima del deploy
- Serve per installare le dipendenze
- Puoi lasciarlo vuoto se le dipendenze sono già installate

### Run Command (Obbligatorio)

**Usa questo comando:**

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Oppure** (più semplice):

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Spiegazione:**
- Questo comando avvia l'app FastAPI
- `--host 0.0.0.0` rende l'app accessibile pubblicamente
- `--port $PORT` usa la porta configurata da Replit (o 8000)

## ✅ Configurazione Completa

### Opzione 1: Build + Run Separati

**Build Command:**
```bash
pip install -r requirements.txt
```

**Run Command:**
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Opzione 2: Solo Run (Più Semplice)

**Build Command:**
```
(Lascia vuoto)
```

**Run Command:**
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Nota:** Se le dipendenze sono già installate, puoi lasciare il Build Command vuoto.

## 🔧 Verifica Configurazione

Dopo aver configurato i comandi:

1. **Clicca "Publish" o "Deploy"**
2. **Attendi che l'app si avvii**
3. **Controlla i log** - dovresti vedere:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   🚀 Avvio dell'applicazione InstaSpotter...
   ✓ Database e tabelle pronti.
   ```

## 📝 Note Importanti

- ✅ **Build Command è opzionale** - puoi lasciarlo vuoto
- ✅ **Run Command è obbligatorio** - deve avviare l'app
- ✅ **Usa `$PORT`** se disponibile, altrimenti `8000`
- ✅ **Host deve essere `0.0.0.0`** per renderla accessibile pubblicamente

## 🆘 Se l'App Non Si Avvia

1. **Verifica il Run Command** - deve essere esatto
2. **Controlla i log** per errori
3. **Verifica che le dipendenze siano installate**
4. **Prova a riavviare** l'app

---

**Configura questi comandi e l'app sarà pubblicata correttamente! 🎉**

