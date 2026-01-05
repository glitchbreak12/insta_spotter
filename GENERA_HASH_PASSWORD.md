# 🔐 Genera Hash Password - Soluzioni

## ❌ Problema: `!Password': event not found`

Il carattere `!` in bash ha un significato speciale (history expansion). Ecco le soluzioni:

## ✅ Soluzione 1: Usa Virgolette Singole (Più Semplice)

**Usa virgolette singole `'` invece di doppie `"` per la password:**

```bash
python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt']); print(pwd_context.hash('Admin123!Password'))"
```

**Oppure ancora meglio, usa virgolette singole per tutto:**

```bash
python3 -c 'from passlib.context import CryptContext; pwd_context = CryptContext(schemes=["bcrypt"]); print(pwd_context.hash("Admin123!Password"))'
```

## ✅ Soluzione 2: Disabilita History Expansion

```bash
set +H
python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt']); print(pwd_context.hash('Admin123!Password'))"
```

## ✅ Soluzione 3: Crea un File Python Temporaneo (Più Facile)

**Crea un file `hash_password.py`:**

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'])
password = 'Admin123!Password'  # Cambia questa password
hash_value = pwd_context.hash(password)
print(hash_value)
```

**Poi esegui:**
```bash
python3 hash_password.py
```

## ✅ Soluzione 4: Usa Escape per il Carattere !

```bash
python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt']); print(pwd_context.hash('Admin123\!Password'))"
```

## 🎯 Soluzione Consigliata (Più Semplice)

**Usa questo comando (virgolette singole per la password):**

```bash
python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt']); print(pwd_context.hash('Admin123!Password'))"
```

**Oppure crea un file temporaneo:**

1. Crea `hash_password.py`:
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'])
print(pwd_context.hash('Admin123!Password'))
```

2. Esegui:
```bash
python3 hash_password.py
```

3. Copia l'hash generato

4. Elimina il file:
```bash
rm hash_password.py
```

## 📝 Esempio Completo

**Se la tua password è `Admin123!Password`:**

```bash
python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt']); print(pwd_context.hash('Admin123!Password'))"
```

**Output atteso:**
```
$2b$12$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ
```

**Copia questo hash e usalo nelle Secrets di Replit come:**
```
ADMIN_PASSWORD_HASH=$2b$12$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ
```

---

**Prova la Soluzione 1 o 3 - sono le più semplici! 🚀**

