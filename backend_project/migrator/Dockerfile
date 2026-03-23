FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY migrate.py /app/migrate.py

CMD ["python", "/app/migrate.py", "--migrations-dir", "/migrations"]
