#!/bin/bash
set -euo pipefail

echo "🔑 Creating secrets from cluster-secrets.yaml..."
kubectl apply -f cluster-secrets.yaml

echo "📦 Creating the image pull secret for Google Artifact Registry..."
# Replace with your actual key file if different
kubectl create secret docker-registry gcr-json-key \
  --docker-server=europe-west2-docker.pkg.dev \
  --docker-username=_json_key \
  --docker-password="$(cat ./key.json)" \
  --docker-email=your-email@example.com \
  || echo "Secret gcr-json-key may already exist"

echo "🚀 Deploying application components..."
kubectl apply -f deploy.yaml

echo "⚖️ Applying Horizontal Pod Autoscaler configurations..."
kubectl apply -f hpa.yaml

echo "🔍 Checking deployment status..."
echo "RabbitMQ:"
kubectl get pods -l app=rabbitmq
echo ""

echo "API Service:"
kubectl get pods -l app=api-service
echo ""

echo "Deduplicator Classifier Service:"
kubectl get pods -l app=deduplicator-classifier-service
echo ""

echo "Frontend:"
kubectl get pods -l app=frontend
echo ""

echo "📊 Service endpoints:"
kubectl get services

echo "✅ Deployment completed! Your application should be available at the LoadBalancer external IPs." 