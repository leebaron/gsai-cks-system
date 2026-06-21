FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy system modules
COPY kernel/ kernel/
COPY observation/ observation/
COPY cocs/ cocs/
COPY runtime/ runtime/
COPY governance/ governance/
COPY verifier/ verifier/
COPY ledger/ ledger/
COPY cgl/ cgl/

# Default: run the runtime pipeline
CMD ["python", "-m", "kernel.runtime"]
