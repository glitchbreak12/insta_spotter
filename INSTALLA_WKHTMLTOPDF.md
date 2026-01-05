# Installazione wkhtmltopdf su Replit

## Problema
`wkhtmltoimage` è necessario per generare le immagini dei messaggi spotted, ma non è installato di default su Replit.

## Soluzione Automatica

Ho aggiunto l'installazione automatica nel file `.replit`:

```toml
[build]
command = "pip install -r requirements.txt && apt-get update && apt-get install -y wkhtmltopdf"
```

## Installazione Manuale (se necessario)

Se l'installazione automatica non funziona, puoi installare manualmente:

### Opzione 1: Usa lo script
```bash
chmod +x install_wkhtmltopdf.sh
./install_wkhtmltopdf.sh
```

### Opzione 2: Comando diretto
```bash
apt-get update
apt-get install -y wkhtmltopdf xvfb
```

### Opzione 3: Nella Shell di Replit
1. Apri la Shell di Replit
2. Esegui:
   ```bash
   apt-get update
   apt-get install -y wkhtmltopdf
   ```
3. Riavvia l'app

## Verifica Installazione

Per verificare che sia installato correttamente:
```bash
wkhtmltoimage --version
```

Dovresti vedere qualcosa come:
```
wkhtmltoimage 0.12.6
```

## Note

- L'installazione viene eseguita automaticamente quando fai "Run" su Replit
- Se vedi ancora errori, prova a riavviare completamente l'app
- `xvfb` è installato per supportare l'esecuzione headless su Replit

