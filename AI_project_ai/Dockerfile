# Gebruik een lichte Python versie
FROM python:3.11-slim

# Zet de werkmap in de container
WORKDIR /app

# Kopieer de requirements eerst (voor betere caching)
COPY requirements.txt .

# Installeer de afhankelijkheden
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de bestanden
COPY . .

# Stel de poort in waar FastAPI op draait
EXPOSE 8000

# Start de applicatie met uvicorn
# We gebruiken 0.0.0.0 om de container bereikbaar te maken van buitenaf
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]