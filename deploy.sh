# Scripts de Deployment Útiles

## Deploy local con Docker Compose
docker-compose up -d --build

## Deploy a Google Cloud Run (manual)
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ml-service
gcloud run deploy ml-service \
  --image gcr.io/YOUR_PROJECT_ID/ml-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2

## Ver logs en Cloud Run
gcloud run services logs tail ml-service --region us-central1

## Test local
curl http://localhost:8000/health
