set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
FUNCTION_NAME="fetch_feeds_function"
REGION="europe-west2"
RUNTIME="python311"
ENTRY_POINT="app"
ENV_FILE="$PROJECT_DIR/function-secrets.yaml"
SOURCE_DIR="$PROJECT_DIR/backend/fetcher-service"

echo "Deploying Cloud Function: $FUNCTION_NAME"
echo "Using env file: $ENV_FILE"
echo "Using source directory: $SOURCE_DIR"

gcloud functions deploy "$FUNCTION_NAME" \
  --runtime "$RUNTIME" \
  --trigger-http \
  --entry-point "$ENTRY_POINT" \
  --region "$REGION" \
  --source "$SOURCE_DIR" \
  --env-vars-file "$ENV_FILE" \
  --allow-unauthenticated \
  --gen2
