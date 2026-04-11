FROM python:3.12-slim

WORKDIR /app

RUN python -m http.server --help >/dev/null

COPY static /app

EXPOSE 8080
CMD ["python", "-m", "http.server", "8080", "--directory", "/app"]

