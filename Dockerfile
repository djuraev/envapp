FROM python:3.12-alpine

WORKDIR /app

# no dependencies — pure stdlib
COPY server.py .

EXPOSE 8080

CMD ["python", "server.py"]
