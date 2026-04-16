FROM python:3.11

WORKDIR /app

COPY . .

RUN chmod +x scripts/*.sh

ENTRYPOINT ["./scripts/run_fileflow.sh"]