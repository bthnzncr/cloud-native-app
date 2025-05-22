# Cloud-Native RSS Feed Processing Application

This project is a cloud-native application designed to fetch and process RSS feeds from 20 different English news sources. It consists of two main services: a Fetcher Service and a Consumer Service, both of which are designed to be scalable and modular.

## Deployment Steps

### 1. MongoDB Setup
- **Provision a Google Compute Engine VM**: Set up a virtual machine on Google Cloud.
- **Install MongoDB**: Follow the official MongoDB installation guide for your operating system.
- **Configure Authentication**: Enable authentication and create necessary users.
- **Create Firewall Rule**: Allow traffic on port 27017 from the internal Kubernetes network.

### 2. Containerization and Image Preparation
- **Build Docker Images**: Use `build-cluster-images.sh` to build images for backend services, frontend, and RabbitMQ.
- **Create Artifact Registry**: The script will handle the creation if it doesn't exist.
- **Apply Deployment and HPA Configurations**: Use `kubectl apply -f cluster-secrets.yaml`, `kubectl apply -f deploy.yaml` and `kubectl apply -f hpa.yaml` to deploy the application components and configure Horizontal Pod Autoscalers in your Google Cloud 

### 3. Deploy Fetcher Service
- **Deploy as Google Cloud Function**: Use `deploy-function.sh` to package and deploy the fetcher-service.

### 4. Set Up Cloud Scheduler
- **Automate Fetcher Invocation**: Use `deploy-scheduler.sh` to set up a Cloud Scheduler job.

### 5. Configure Networking
- **Apply Firewall Rules**: Manually configure rules to allow secure communication between components.
- **VPC Connector Configuration**: Ensure proper VPC setup for Cloud Function to RabbitMQ and Kubernetes to MongoDB communication.

### 6. Performance Testing
- **Deploy Locust for Testing**: Use the `locust-test` directory to deploy Locust.


