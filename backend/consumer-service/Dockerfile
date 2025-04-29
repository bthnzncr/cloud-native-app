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

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Create models directory
RUN mkdir -p ./models

# Copy only necessary production files
COPY app/ ./app/
COPY Filtered_News_Dataset.json .
COPY train_model.py .

# Install scikit-learn and related packages
RUN pip install scikit-learn pandas numpy

# Run the model training script with train-only flag since we already have the filtered dataset
RUN python train_model.py --train-only

# Remove dataset after model is built to reduce image size
RUN rm Filtered_News_Dataset.json train_model.py

# Command to run the consumer service
CMD ["python", "-m", "app.consumer_runner"] 