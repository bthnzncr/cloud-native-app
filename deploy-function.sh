REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
zip -r "$REPO_ROOT/backend/fetcher-service.zip" "$REPO_ROOT/backend/fetcher-service"
gcloud functions deploy fetch_feeds_function \
  --runtime python311 \
  --trigger-http \
  --entry-point app \
  --region europe-west2 \
  --source "$REPO_ROOT/backend/fetcher-service" \
  --env-vars-file "$REPO_ROOT/function-secrets.yaml" \
  --allow-unauthenticated \
  --gen2