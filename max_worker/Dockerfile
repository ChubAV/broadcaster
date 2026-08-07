FROM python:3.12-slim

ARG MAX_WORKER_BUILD_REVISION=unknown
LABEL org.opencontainers.image.revision=${MAX_WORKER_BUILD_REVISION}
ENV MAX_WORKER_BUILD_REVISION=${MAX_WORKER_BUILD_REVISION}

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./max_worker

EXPOSE 3000

CMD ["python", "-m", "max_worker.main"]
