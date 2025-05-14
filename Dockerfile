FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar librerías requeridas para SentenceTransformer
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add non-root user for security
RUN adduser --disabled-password --gecos "" myuser && \
    chown -R myuser:myuser /app

# Copy application code
COPY . .

# Switch to non-root user
USER myuser

ENV PATH="/home/myuser/.local/bin:${PATH}"
ENV PORT=8080

# Command to run the application
CMD ["python", "main.py"] 