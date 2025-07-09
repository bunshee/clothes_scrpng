FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y postgresql-client \ 
    && pip install --no-cache-dir -r requirements.txt \ 
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . .

RUN chmod +x ./docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["api"]
