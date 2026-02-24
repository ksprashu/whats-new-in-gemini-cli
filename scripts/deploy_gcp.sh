#!/bin/bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ---------------------------------------------------------------------------
# Deployment script for "What's New in Gemini CLI" on Google Cloud Platform
# This deploys the entire Unified Cloud Architecture in the correct order.
# ---------------------------------------------------------------------------

set -e

if [ -z "$1" ]; then
  echo "Usage: ./deploy_gcp.sh <PROJECT_ID>"
  exit 1
fi

PROJECT_ID=$1
REGION="us-central1"
BUCKET_NAME="${PROJECT_ID}-gemini-reports"

echo "--> Fetching Project Number for IAM bindings..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
# Cloud Run natively uses the Compute Engine Default Service Account
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "========================================="
echo "Deploying to project: $PROJECT_ID"
echo "========================================="

# 1. Enable Required APIs
echo "--> Enabling GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    secretmanager.googleapis.com \
    cloudscheduler.googleapis.com \
    firestore.googleapis.com \
    storage.googleapis.com \
    cloudbuild.googleapis.com \
    --project=$PROJECT_ID || true

# 2. Provision Storage & Database
echo "--> Provisioning Google Cloud Storage Bucket ($BUCKET_NAME)..."
if ! gcloud storage buckets describe gs://$BUCKET_NAME --project=$PROJECT_ID >/dev/null 2>&1; then
    gcloud storage buckets create gs://$BUCKET_NAME --location=$REGION --project=$PROJECT_ID
else
    echo "Bucket already exists."
fi

echo "--> Initializing Firestore..."
# Check if the (default) database already exists
if ! gcloud firestore databases describe "(default)" --project=$PROJECT_ID >/dev/null 2>&1; then
    gcloud firestore databases create --location=$REGION --project=$PROJECT_ID || echo "Firestore already initialized."
else
    echo "Firestore (default) database already initialized."
fi

# 3. Create Secrets
echo "--> Setting up Secret Manager..."
if ! gcloud secrets describe ADMIN_API_KEY --project=$PROJECT_ID >/dev/null 2>&1; then
    echo -n "Please enter a strong, random password for your ADMIN_API_KEY: "
    read -s ADMIN_SECRET
    echo ""
    echo -n $ADMIN_SECRET | gcloud secrets create ADMIN_API_KEY --data-file=- --project=$PROJECT_ID
else
    echo "Secret ADMIN_API_KEY already exists. Skipping creation."
fi

# Grant Cloud Run service account access to the secret
echo "--> Applying IAM secretAccessor role to $SERVICE_ACCOUNT..."
gcloud secrets add-iam-policy-binding ADMIN_API_KEY \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID >/dev/null

# Allow IAM bindings to propagate
sleep 5

# 4. Deploy Backend API
echo "--> Deploying API Service to Cloud Run..."
gcloud run deploy gemini-updates-api \
    --source . \
    --set-secrets=ADMIN_API_KEY=ADMIN_API_KEY:latest \
    --set-env-vars=STORAGE_MODE=cloud,GCS_BUCKET=$BUCKET_NAME \
    --allow-unauthenticated \
    --region=$REGION \
    --project=$PROJECT_ID

# Get API URL to inject into frontends
API_URL=$(gcloud run services describe gemini-updates-api --region=$REGION --project=$PROJECT_ID --format="value(status.url)")
echo "API successfully deployed at: $API_URL"

# 5. Deploy Nightly Worker Job
echo "--> Deploying Orchestrator Worker Job..."
gcloud run jobs deploy gemini-updates-worker \
    --source . \
    --command="/cnb/process/worker" \
    --set-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest,GOOGLE_API_KEY=GEMINI_API_KEY:latest \
    --set-env-vars=STORAGE_MODE=cloud,GCS_BUCKET=$BUCKET_NAME \
    --region=$REGION \
    --project=$PROJECT_ID

# 6. Create Cloud Scheduler
echo "--> Creating Cloud Scheduler trigger for nightly sync at 2:00 AM..."
gcloud scheduler jobs create http gemini-updates-nightly \
    --schedule="0 2 * * *" \
    --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/gemini-updates-worker:run" \
    --http-method=POST \
    --oauth-service-account-email=$SERVICE_ACCOUNT \
    --location=$REGION \
    --project=$PROJECT_ID || echo "Scheduler job already exists or failed."

# 11. Package Frontend
echo "--> Packaging Frontend container..."
mkdir -p .docker_deploy
cp frontend/Dockerfile .docker_deploy/Dockerfile
cp frontend/nginx.conf.template .docker_deploy/
cp -r static .docker_deploy/

# 12. Deploy Public Frontend
echo "--> Deploying Public Frontend to Cloud Run..."
gcloud run deploy gemini-updates-public \
    --source .docker_deploy \
    --set-env-vars=API_URL=$API_URL,ADMIN_API_KEY="",INDEX_PAGE="index.html" \
    --allow-unauthenticated \
    --region=$REGION \
    --project=$PROJECT_ID

# Get Public URL
PUB_URL=$(gcloud run services describe gemini-updates-public --region=$REGION --project=$PROJECT_ID --format="value(status.url)")

# 13. Deploy Admin Frontend
echo "--> Deploying Admin Frontend to Cloud Run..."
gcloud run deploy gemini-updates-admin \
    --source .docker_deploy \
    --set-env-vars=API_URL=$API_URL,INDEX_PAGE="admin.html" \
    --set-secrets=ADMIN_API_KEY=ADMIN_API_KEY:latest \
    --no-allow-unauthenticated \
    --region=$REGION \
    --project=$PROJECT_ID

# Get Admin URL
ADM_URL=$(gcloud run services describe gemini-updates-admin --region=$REGION --project=$PROJECT_ID --format="value(status.url)")

# Cleanup Frontend Build Context
rm -rf .docker_deploy

echo "========================================="
echo "Deployment Complete!"
echo ""
echo "Backend API URL:   $API_URL"
echo "Public App URL:    $PUB_URL"
echo "Secure Admin URL:  $ADM_URL"
echo ""
echo "Note: The Admin App is locked down via Google Cloud IAM. Only authorized users can access it."
echo "========================================="
