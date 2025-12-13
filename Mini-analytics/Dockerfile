# Använd en officiell Python-bild som bas
FROM python:3.10

# Sätt arbetskatalogen i containern
WORKDIR /app

# Kopiera requirements och installera beroenden
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Kopiera hela projektet till containern
COPY app/ .

# Exponera porten som appen körs på
EXPOSE 8000

# Starta appen med uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
