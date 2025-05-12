#!/bin/bash
PROJECT_ID=$1
REGION=$2

# build an image 
gcr_image_path=gcr.io/${PROJECT_ID}/ag-web_$(date +%Y-%m-%d_%H-%M)
gcloud builds submit --tag $gcr_image_path

# deploy
gcloud run deploy ag-web --image $gcr_image_path --platform managed --region ${REGION} --allow-unauthenticated --min-instances=1 --max-instances=1

