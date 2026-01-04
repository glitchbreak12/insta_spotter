# Usa Python 3.11
FROM python:3.11-slim-bullseye

# Imposta la cartella di lavoro
WORKDIR /app

# Installa wkhtmltopdf
RUN apt-get update && apt-get install -y --no-install-recommends wkhtmltopdf && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copia e installa le dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice
COPY . .

# Comando per avviare il worker
CMD ["python", "worker.py"]