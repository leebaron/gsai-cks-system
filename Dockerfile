FROM python:3.11-slim

WORKDIR /app

COPY runtime /app/runtime
COPY cocs /app/cocs
COPY csco /app/csco
COPY ral /app/ral
COPY replay /app/replay
COPY ledger /app/ledger
COPY sealing /app/sealing
COPY governance /app/governance
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
ENV MODE=production

EXPOSE 8080

CMD ["python", "-m", "runtime.kernel"]
