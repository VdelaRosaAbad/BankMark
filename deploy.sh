#!/bin/bash

# Script de despliegue automático para Bank Marketing Analytics
# Ejecutar en Cloud Shell

set -e

echo "🚀 Iniciando despliegue de Bank Marketing Analytics..."

# Configuración
PROJECT_ID="BankMarketingVada"
REGION="us-central1"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Verificar configuración
log "Verificando configuración..."

# Verificar que estamos en el proyecto correcto
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    log "Configurando proyecto: $PROJECT_ID"
    gcloud config set project $PROJECT_ID
fi

# Habilitar APIs necesarias
log "Habilitando APIs..."
gcloud services enable bigquery.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable iam.googleapis.com

# Crear service account si no existe
log "Configurando service account..."
SA_EMAIL="bank-marketing-sa@$PROJECT_ID.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe $SA_EMAIL > /dev/null 2>&1; then
    log "Creando service account..."
    gcloud iam service-accounts create bank-marketing-sa \
        --display-name="Bank Marketing Service Account"
fi

# Asignar roles necesarios
log "Asignando roles al service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/bigquery.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/cloudfunctions.developer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/cloudscheduler.admin"

# Crear datasets de BigQuery
log "Creando datasets de BigQuery..."
bq mk --dataset $PROJECT_ID:raw_data
bq mk --dataset $PROJECT_ID:staging
bq mk --dataset $PROJECT_ID:marts

# Instalar dependencias Python
log "Instalando dependencias Python..."
pip install -r requirements.txt

# Configurar DBT
log "Configurando DBT..."
mkdir -p ~/.dbt
cp config/profiles.yml ~/.dbt/
cp config/dbt_project.yml dbt/

cd dbt
dbt deps
cd ..

# Desplegar Cloud Functions
log "Desplegando Cloud Functions..."

# Función principal
gcloud functions deploy bank-marketing-trigger \
    --runtime python39 \
    --trigger-http \
    --allow-unauthenticated \
    --source scripts/cloud_functions \
    --entry-point bank_marketing_trigger \
    --region $REGION \
    --set-env-vars GCP_PROJECT_ID=$PROJECT_ID

# Función de reportes diarios
gcloud functions deploy bank-marketing-daily-report \
    --runtime python39 \
    --trigger-http \
    --allow-unauthenticated \
    --source scripts/cloud_functions \
    --entry-point send_daily_report \
    --region $REGION \
    --set-env-vars GCP_PROJECT_ID=$PROJECT_ID

# Función de calidad de datos
gcloud functions deploy bank-marketing-quality-check \
    --runtime python39 \
    --trigger-http \
    --allow-unauthenticated \
    --source scripts/cloud_functions \
    --entry-point data_quality_check \
    --region $REGION \
    --set-env-vars GCP_PROJECT_ID=$PROJECT_ID

# Función de cálculo de KPIs
gcloud functions deploy bank-marketing-kpi-calculation \
    --runtime python39 \
    --trigger-http \
    --allow-unauthenticated \
    --source scripts/cloud_functions \
    --entry-point kpi_calculation \
    --region $REGION \
    --set-env-vars GCP_PROJECT_ID=$PROJECT_ID

# Configurar Cloud Scheduler
log "Configurando Cloud Scheduler..."

# Job diario a las 9 AM CST (15:00 UTC)
gcloud scheduler jobs create http bank-marketing-daily \
    --schedule="0 15 * * *" \
    --uri="https://$REGION-$PROJECT_ID.cloudfunctions.net/bank-marketing-trigger" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --location=$REGION

# Job de reportes diarios a las 9:30 AM CST
gcloud scheduler jobs create http bank-marketing-daily-report \
    --schedule="30 15 * * *" \
    --uri="https://$REGION-$PROJECT_ID.cloudfunctions.net/bank-marketing-daily-report" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --location=$REGION

# Job de calidad de datos cada 6 horas
gcloud scheduler jobs create http bank-marketing-quality-check \
    --schedule="0 */6 * * *" \
    --uri="https://$REGION-$PROJECT_ID.cloudfunctions.net/bank-marketing-quality-check" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --location=$REGION

# Ejecutar pipeline inicial
log "Ejecutando pipeline inicial..."

# Ingesta de datos
python scripts/data_ingestion.py

# Ejecutar DBT
cd dbt
dbt run --target prod
dbt test --target prod
cd ..

# Verificar despliegue
log "Verificando despliegue..."

# Verificar datasets
if bq ls $PROJECT_ID:raw_data > /dev/null 2>&1; then
    log "✅ Dataset raw_data creado"
else
    error "❌ Error creando dataset raw_data"
fi

# Verificar tablas
if bq ls $PROJECT_ID:raw_data | grep -q bank_marketing; then
    log "✅ Tabla bank_marketing creada"
else
    error "❌ Error creando tabla bank_marketing"
fi

# Verificar Cloud Functions
FUNCTIONS=("bank-marketing-trigger" "bank-marketing-daily-report" "bank-marketing-quality-check" "bank-marketing-kpi-calculation")

for func in "${FUNCTIONS[@]}"; do
    if gcloud functions describe $func --region=$REGION > /dev/null 2>&1; then
        log "✅ Cloud Function $func desplegada"
    else
        error "❌ Error desplegando Cloud Function $func"
    fi
done

# Verificar Cloud Scheduler
SCHEDULERS=("bank-marketing-daily" "bank-marketing-daily-report" "bank-marketing-quality-check")

for job in "${SCHEDULERS[@]}"; do
    if gcloud scheduler jobs describe $job --location=$REGION > /dev/null 2>&1; then
        log "✅ Cloud Scheduler job $job creado"
    else
        error "❌ Error creando Cloud Scheduler job $job"
    fi
done

# Mostrar URLs de las funciones
log "URLs de las Cloud Functions:"
gcloud functions list --region=$REGION --format="table(name,httpsTrigger.url)"

# Mostrar jobs programados
log "Jobs programados:"
gcloud scheduler jobs list --location=$REGION --format="table(name,schedule,state)"

# Información final
log "🎉 Despliegue completado exitosamente!"
echo ""
echo "📋 Resumen del despliegue:"
echo "   • Proyecto GCP: $PROJECT_ID"
echo "   • Región: $REGION"
echo "   • Datasets BigQuery: raw_data, staging, marts"
echo "   • Cloud Functions: 4 funciones desplegadas"
echo "   • Cloud Scheduler: 3 jobs programados"
echo ""
echo "🔗 URLs importantes:"
echo "   • GitHub Repository: https://github.com/VdelaRosaAbad/BankMark"
echo "   • BigQuery Console: https://console.cloud.google.com/bigquery?project=$PROJECT_ID"
echo "   • Cloud Functions: https://console.cloud.google.com/functions?project=$PROJECT_ID"
echo ""
echo "📧 Configurar notificaciones:"
echo "   • Editar variables de entorno en Cloud Functions"
echo "   • Configurar SMTP para emails"
echo "   • Configurar webhook de Slack (opcional)"
echo ""
echo "🚀 Próximos pasos:"
echo "   1. Configurar Looker con BigQuery"
echo "   2. Crear dashboard en Looker"
echo "   3. Configurar alertas de email"
echo "   4. Probar pipeline completo"
echo ""
echo "✅ ¡El proyecto está listo para usar!"
