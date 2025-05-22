#!/bin/bash

set -e
JOB_NAME="fetch-feeds-job"
REGION="europe-west2"
TIME_ZONE="Europe/Istanbul"
SCHEDULE="*/3 * * * *"
FUNCTION_URL="https://europe-west2-tactical-helix-459822-k5.cloudfunctions.net/fetch_feeds_function"
SERVICE_ACCOUNT="78280810437-compute@developer.gserviceaccount.com"

echo "Creating Cloud Scheduler job: $JOB_NAME"

gcloud scheduler jobs create http "$JOB_NAME" \
  --schedule="$SCHEDULE" \
  --uri="$FUNCTION_URL" \
  --http-method=POST \
  --time-zone="$TIME_ZONE" \
  --oidc-service-account-email="$SERVICE_ACCOUNT" \
  --location="$REGION"

echo "✅ Scheduler job created successfully."
