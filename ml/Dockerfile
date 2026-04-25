FROM python:3.12-slim

ARG USER_ID=1000
ARG GROUP_ID=1000

WORKDIR /workspace/ml

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace/ml/src
ENV HOME=/home/appuser

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git \
    && groupadd --gid "${GROUP_ID}" appuser \
    && useradd --uid "${USER_ID}" --gid "${GROUP_ID}" --create-home --shell /bin/bash appuser \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY params.yaml ./params.yaml
COPY src ./src

CMD ["bash"]
