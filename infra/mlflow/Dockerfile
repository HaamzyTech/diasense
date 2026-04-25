FROM python:3.12-alpine

WORKDIR /mlflow
RUN apk add --no-cache bash build-base libffi-dev
RUN pip install --no-cache-dir mlflow==3.11.1
EXPOSE 5001
CMD ["mlflow", "--version"]
