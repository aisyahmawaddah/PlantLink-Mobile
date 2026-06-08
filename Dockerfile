FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --ignore-requires-python \
    --no-deps psycopg2 || pip install psycopg2-binary
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install django-cors-headers channels python-dotenv

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
