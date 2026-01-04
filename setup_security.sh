#!/bin/bash
# ============================================================================
# Script per generare configurazioni di sicurezza
# RUN ONCE AL PRIMO SETUP
# ============================================================================

echo "🔐 Setup Sicurezza InstaSpotter"
echo "================================"

# Genera SECRET_KEY sicuro
echo ""
echo "Generando SECRET_KEY..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "SECRET_KEY: $SECRET_KEY"

# Genera ADMIN_PASSWORD e hash
echo ""
read -sp "Inserisci password admin (min 12 caratteri, con maiuscole, numeri, speciali): " ADMIN_PASSWORD
echo ""

ADMIN_PASSWORD_HASH=$(python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt']); print(pwd_context.hash('$ADMIN_PASSWORD'))")
echo "ADMIN_PASSWORD_HASH generato ✓"

# Salva in .env
echo ""
echo "Salvando in .env..."
cat > .env << EOF
# ============================================================================
# SICUREZZA
# ============================================================================
SECRET_KEY=$SECRET_KEY
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$ADMIN_PASSWORD_HASH

# ============================================================================
# DATABASE
# ============================================================================
DATABASE_URL=postgresql://user:password@localhost/insta_spotter

# ============================================================================
# AI & MODERAZIONE
# ============================================================================
GEMINI_API_KEY=your-gemini-key-here

# ============================================================================
# INSTAGRAM
# ============================================================================
INSTAGRAM_USERNAME=your-ig-username
INSTAGRAM_PASSWORD=your-ig-password

# ============================================================================
# REPLIT
# ============================================================================
REPLIT_URL=https://your-replit-name.replit.dev
EOF

echo "✅ .env creato con sicurezza!"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   1. Aggiungi i tuoi valori reali a .env"
echo "   2. NON committare .env su Git"
echo "   3. In Replit, aggiungi queste variabili nel pannello 'Secrets'"
echo ""
