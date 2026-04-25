FROM python:3.12-alpine

WORKDIR /app
RUN apk add --no-cache build-base postgresql-dev
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["sh", "-c", "python -c \"import sys; sys.path.insert(0, '/app'); from app.db.bootstrap import main; main()\" && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
