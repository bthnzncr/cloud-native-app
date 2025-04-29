FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Copy requirements and install dependencies
COPY requirements.txt .
# This line installs all packages from requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Command to run the service
CMD ["python", "-m", "app.main"] 