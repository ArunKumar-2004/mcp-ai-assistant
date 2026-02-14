FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if any (e.g. for psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port (Internal use or SSE)
EXPOSE 8000

# The command to run the MCP server over stdio
CMD ["python", "server.py"]
