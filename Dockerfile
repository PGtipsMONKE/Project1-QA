FROM python:3.11

WORKDIR /app

COPY . .

CMD ["python", "src/main.py"]