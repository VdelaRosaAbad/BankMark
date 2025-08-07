# Guía de Configuración - Bank Marketing Analytics

## 📋 Prerrequisitos

### 1. Google Cloud Platform
- **Proyecto**: `BankMarketingVada`
- **APIs Requeridas**:
  - BigQuery API
  - Cloud Functions API
  - Cloud Scheduler API
  - Cloud Build API

### 2. GitHub
- **Repositorio**: https://github.com/VdelaRosaAbad/BankMark
- **Acceso**: Permisos de administrador para configurar secrets

### 3. Herramientas Locales
- **Cloud Shell** o **Google Cloud SDK**
- **Python 3.8+**
- **Git**

## 🚀 Configuración Paso a Paso

### Paso 1: Configurar Google Cloud Platform

#### 1.1 Crear Proyecto
```bash
# En Cloud Shell
gcloud projects create BankMarketingVada --name="Bank Marketing Analytics"
gcloud config set project BankMarketingVada
```

#### 1.2 Habilitar APIs
```bash
# Habilitar APIs necesarias
gcloud services enable bigquery.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

#### 1.3 Crear Service Account
```bash
# Crear service account para automatización
gcloud iam service-accounts create bank-marketing-sa \
    --display-name="Bank Marketing Service Account"

# Asignar roles necesarios
gcloud projects add-iam-policy-binding BankMarketingVada \
    --member="serviceAccount:bank-marketing-sa@BankMarketingVada.iam.gserviceaccount.com" \
    --role="roles/bigquery.admin"

gcloud projects add-iam-policy-binding BankMarketingVada \
    --member="serviceAccount:bank-marketing-sa@BankMarketingVada.iam.gserviceaccount.com" \
    --role="roles/cloudfunctions.developer"

# Crear y descargar key
gcloud iam service-accounts keys create ~/bank-marketing-key.json \
    --iam-account=bank-marketing-sa@BankMarketingVada.iam.gserviceaccount.com
```

### Paso 2: Configurar GitHub Repository

#### 2.1 Clonar Repositorio
```bash
git clone https://github.com/VdelaRosaAbad/BankMark.git
cd BankMark
```

#### 2.2 Configurar Secrets en GitHub
En GitHub → Settings → Secrets and variables → Actions:

1. **GCP_SA_KEY**: Contenido del archivo `bank-marketing-key.json`
2. **SMTP_PASSWORD**: Contraseña del email para notificaciones
3. **SLACK_WEBHOOK**: URL del webhook de Slack (opcional)

### Paso 3: Configurar Entorno Local

#### 3.1 Instalar Dependencias
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

#### 3.2 Configurar DBT
```bash
# Crear directorio de configuración
mkdir -p ~/.dbt

# Copiar archivos de configuración
cp config/profiles.yml ~/.dbt/
cp config/dbt_project.yml dbt/

# Instalar dependencias DBT
cd dbt
dbt deps
```

#### 3.3 Configurar Variables de Entorno
```bash
# Crear archivo .env
cat > .env << EOF
GCP_PROJECT_ID=BankMarketingVada
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=bankmarketing@deacero.com
SENDER_PASSWORD=your_password_here
EOF
```

### Paso 4: Ejecutar Pipeline Inicial

#### 4.1 Ingesta de Datos
```bash
# Ejecutar ingesta de datos
python scripts/data_ingestion.py
```

#### 4.2 Ejecutar DBT
```bash
# Ejecutar modelos DBT
cd dbt
dbt run --target prod

# Ejecutar pruebas
dbt test --target prod
```

#### 4.3 Verificar Datos
```bash
# Verificar que los datos se cargaron correctamente
bq query --use_legacy_sql=false "
SELECT COUNT(*) as total_records 
FROM BankMarketingVada.raw_data.bank_marketing
"
```

### Paso 5: Configurar Automatización

#### 5.1 Configurar Cloud Scheduler
```bash
# Crear job programado para ejecutar diariamente a las 9 AM CST
gcloud scheduler jobs create http bank-marketing-daily \
    --schedule="0 15 * * *" \
    --uri="https://us-central1-BankMarketingVada.cloudfunctions.net/bank-marketing-trigger" \
    --http-method=POST \
    --headers="Content-Type=application/json"
```

#### 5.2 Configurar Cloud Functions
```bash
# Desplegar Cloud Function para notificaciones
gcloud functions deploy bank-marketing-notifications \
    --runtime python39 \
    --trigger-http \
    --allow-unauthenticated \
    --source scripts/cloud_functions \
    --entry-point send_daily_report
```

### Paso 6: Configurar Looker

#### 6.1 Conectar BigQuery
1. En Looker, ir a Admin → Connections
2. Crear nueva conexión BigQuery
3. Configurar con el proyecto `BankMarketingVada`

#### 6.2 Crear Dashboard
1. Crear nuevo dashboard
2. Agregar visualizaciones para KPIs principales
3. Configurar filtros y parámetros

## 🔧 Verificación de Configuración

### Verificar BigQuery
```bash
# Verificar datasets creados
bq ls BankMarketingVada

# Verificar tablas
bq ls BankMarketingVada.raw_data
bq ls BankMarketingVada.staging
bq ls BankMarketingVada.marts
```

### Verificar DBT
```bash
cd dbt
# Verificar conexión
dbt debug

# Ejecutar pruebas
dbt test

# Generar documentación
dbt docs generate
dbt docs serve
```

### Verificar GitHub Actions
1. Ir a GitHub → Actions
2. Verificar que el pipeline se ejecute correctamente
3. Revisar logs de cada job

## 🧪 Pruebas de Funcionamiento

### 1. Prueba de Ingesta
```bash
python scripts/data_ingestion.py
# Debe mostrar: ✅ Data ingestion completed successfully!
```

### 2. Prueba de Calidad
```bash
python scripts/quality_checks.py
# Debe mostrar: ✅ Data Quality Report Generated!
```

### 3. Prueba de Notificaciones
```bash
python scripts/email_notifications.py
# Debe enviar email con reporte
```

### 4. Prueba de DBT
```bash
cd dbt
dbt run --target prod
dbt test --target prod
# Todos los tests deben pasar
```

## 🚨 Solución de Problemas

### Error: Permisos de BigQuery
```bash
# Verificar permisos
gcloud auth list
gcloud config get-value project

# Si es necesario, autenticarse
gcloud auth login
gcloud auth application-default login
```

### Error: DBT Connection
```bash
# Verificar configuración DBT
dbt debug

# Si hay problemas, verificar profiles.yml
cat ~/.dbt/profiles.yml
```

### Error: GitHub Actions
1. Verificar secrets en GitHub
2. Revisar logs de Actions
3. Verificar permisos del service account

### Error: Cloud Functions
```bash
# Verificar logs
gcloud functions logs read bank-marketing-notifications

# Recrear function si es necesario
gcloud functions delete bank-marketing-notifications
gcloud functions deploy bank-marketing-notifications ...
```

## 📞 Soporte

Para problemas técnicos:
- **Email**: jguerrero@deacero.com
- **Issues**: GitHub Issues del repositorio
- **Documentación**: Carpeta `docs/`

## ✅ Checklist de Configuración

- [ ] Proyecto GCP creado y configurado
- [ ] APIs habilitadas
- [ ] Service account creado y configurado
- [ ] Repositorio GitHub clonado
- [ ] Secrets configurados en GitHub
- [ ] Dependencias instaladas
- [ ] DBT configurado
- [ ] Pipeline inicial ejecutado
- [ ] Cloud Scheduler configurado
- [ ] Cloud Functions desplegadas
- [ ] Looker conectado y dashboard creado
- [ ] Todas las pruebas pasan
- [ ] Notificaciones funcionando

---

**¡Configuración completada! 🎉**

El proyecto está listo para procesar datos de marketing bancario y generar reportes automáticos.
