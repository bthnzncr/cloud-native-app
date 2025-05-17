gcloud functions deploy fetch_feeds_function \
  --runtime python311 \
  --trigger-http \
  --entry-point fetch_feeds_function \
  --region europe-west2 \
  --source /home/batu/cloud-native-app/backend/fetcher-service \
  --env-vars-file /home/batu/cloud-native-app/backend/fetcher-service/env.yaml \
  --allow-unauthenticated
