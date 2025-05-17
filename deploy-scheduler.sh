gcloud scheduler jobs create http fetch-feeds-job \
  --schedule="*/3 * * * *" \
  --uri="https://europe-west2-tactical-helix-459822-k5.cloudfunctions.net/fetch_feeds_function" \
  --http-method=POST \
  --time-zone="Europe/Istanbul" \
  --oidc-service-account-email="78280810437-compute@developer.gserviceaccount.com" \
  --location=europe-west2
