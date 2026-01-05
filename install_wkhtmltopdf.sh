#!/bin/bash
# Script per installare wkhtmltopdf su Replit

echo "📦 Installazione di wkhtmltopdf..."

# Aggiorna la lista dei pacchetti
apt-get update

# Installa wkhtmltopdf e le sue dipendenze
apt-get install -y wkhtmltopdf xvfb

# Verifica l'installazione
if command -v wkhtmltoimage &> /dev/null; then
    echo "✅ wkhtmltoimage installato con successo!"
    wkhtmltoimage --version
else
    echo "❌ Errore durante l'installazione di wkhtmltoimage"
    exit 1
fi

echo "✅ Installazione completata!"

