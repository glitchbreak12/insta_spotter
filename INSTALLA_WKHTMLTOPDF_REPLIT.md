# 🚀 Installazione wkhtmltopdf su Replit - GUIDA RAPIDA

## ⚠️ IMPORTANTE: Su Replit non puoi usare `apt-get` direttamente!

Replit usa un sistema diverso per le dipendenze di sistema. Segui questa guida:

## 📋 Installazione tramite System Dependencies (2 minuti)

### Passo 1: Apri il pannello System Dependencies
1. Nel tuo Replit, cerca il pannello **"System Dependencies"** (Dipendenze di Sistema)
2. Si trova solitamente nella barra laterale sinistra o nel menu a tre righe ☰
3. Se non lo vedi, vai su **Tools** → **System Dependencies**

### Passo 2: Aggiungi wkhtmltopdf
1. Nel campo di ricerca, digita: `wkhtmltopdf`
2. Clicca su **"Add"** o **"Install"**
3. Attendi che l'installazione completi

### Passo 3: Verifica l'installazione
Apri la Shell di Replit e verifica:
```bash
wkhtmltoimage --version
```

Dovresti vedere qualcosa come:
```
wkhtmltoimage 0.12.6
```

### Passo 4: Riavvia l'app
1. Ferma l'app (Stop)
2. Riavvia (Run)

## ✅ Verifica che funzioni

Dopo il riavvio, quando approvi un messaggio, nei log dovresti vedere:
```
✓ wkhtmltoimage trovato: /usr/bin/wkhtmltoimage
Immagine generata con successo: ...
```

## 🔍 Troubleshooting

### ❌ Non trovo il pannello "System Dependencies"
1. Cerca nel menu a tre righe ☰ in alto a sinistra
2. Oppure vai su **Tools** → **System Dependencies**
3. Se ancora non lo trovi, prova a cercare "dependencies" nella barra di ricerca di Replit

### ❌ "wkhtmltopdf" non appare nella ricerca
1. Prova a cercare solo "wkhtml"
2. Oppure cerca "htmltopdf"
3. Se non appare, potrebbe non essere disponibile nel repository di Replit

### ❌ L'installazione funziona ma l'app non lo trova
1. Verifica che sia installato: `wkhtmltoimage --version` nella Shell
2. Riavvia completamente l'app (Stop → Run)
3. Controlla i log all'avvio per vedere se viene rilevato

### ❌ Ancora non funziona - Alternativa
Se `wkhtmltopdf` non è disponibile nel pannello System Dependencies, potresti dover:
1. Contattare il supporto Replit
2. O considerare di usare un'alternativa come `playwright` o `selenium` per generare immagini

## 📝 Note

- L'installazione è permanente su Replit (rimane anche dopo il riavvio)
- Se cambi Repl, devi reinstallarlo
- L'installazione automatica all'avvio funziona solo se l'app ha i permessi necessari

