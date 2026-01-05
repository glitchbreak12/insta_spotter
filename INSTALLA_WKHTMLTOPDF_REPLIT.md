# 🚀 Installazione wkhtmltopdf su Replit - GUIDA RAPIDA

## ⚡ Installazione Automatica

L'app ora tenta di installare automaticamente `wkhtmltopdf` all'avvio. 

**Se vedi ancora l'errore**, installalo manualmente:

## 📋 Installazione Manuale (1 minuto)

### Passo 1: Apri la Shell di Replit
1. Nel tuo Replit, clicca su **"Shell"** (terminale) in basso
2. O usa il tasto `Ctrl + Shift + S`

### Passo 2: Installa wkhtmltopdf
Copia e incolla questi comandi uno alla volta:

```bash
apt-get update
```

Poi:

```bash
apt-get install -y wkhtmltopdf
```

### Passo 3: Verifica l'installazione
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

### ❌ "Permission denied" durante apt-get
Su Replit, a volte serve usare `sudo`:
```bash
sudo apt-get update
sudo apt-get install -y wkhtmltopdf
```

### ❌ L'installazione funziona ma l'app non lo trova
1. Verifica che sia nel PATH: `which wkhtmltoimage`
2. Riavvia completamente l'app (Stop → Run)
3. Controlla i log all'avvio per vedere se viene rilevato

### ❌ Ancora non funziona
Prova a installare anche le dipendenze:
```bash
apt-get install -y wkhtmltopdf xvfb libxrender1 libfontconfig1
```

## 📝 Note

- L'installazione è permanente su Replit (rimane anche dopo il riavvio)
- Se cambi Repl, devi reinstallarlo
- L'installazione automatica all'avvio funziona solo se l'app ha i permessi necessari

