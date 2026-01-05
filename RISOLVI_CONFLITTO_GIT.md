# 🔧 Risolvi Conflitto Git su Replit

## Problema
Git non può fare pull perché hai modifiche locali al file `.replit`.

## Soluzione Rapida

### Opzione 1: Salva le modifiche locali (Consigliato)
```bash
# Salva le modifiche locali
git stash

# Fai pull
git pull origin main

# Ripristina le modifiche (se necessario)
git stash pop
```

### Opzione 2: Scarta le modifiche locali (se non sono importanti)
```bash
# Scarta le modifiche locali a .replit
git checkout -- .replit

# Fai pull
git pull origin main
```

### Opzione 3: Committa le modifiche locali prima
```bash
# Aggiungi le modifiche
git add .replit

# Committa
git commit -m "Modifiche locali a .replit"

# Fai pull (potrebbe esserci un merge)
git pull origin main
```

## Dopo il Pull

Una volta fatto il pull, installa Pillow:
```bash
pip install Pillow
```

Poi riavvia l'app!

