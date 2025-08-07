# Bank Marketing Analytics Engineering Project

## 📋 Descripción del Proyecto

Este proyecto implementa una solución completa del análisis de campañas de marketing bancario, utilizando tecnologías modernas de Google Cloud Platform.

### 🎯 Objetivos del Proyecto

1. **Data Mart para Marketing**: Crear un Data Mart que permita analizar la efectividad de campañas de marketing
2. **KPIs Clave**: 
   - Tasa de conversión
   - Número de contactos exitosos
   - Segmentación de clientes
3. **Calidad de Datos**: Implementar pruebas unitarias y validaciones
4. **Automatización**: Pipeline CI/CD con notificaciones por email
5. **Monitoreo**: Dashboard en Looker con métricas en tiempo real

## 🏗️ Arquitectura de la Solución

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Source   │    │   Cloud Shell   │    │   BigQuery      │
│   (UCI Dataset) │───▶│   (Processing)  │───▶│   (Data Mart)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub        │◀───│   DBT           │    │   Looker        │
│   (CI/CD)       │    │   (Transforms)  │───▶│   (Dashboard)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐
│   Email         │◀───│   Cloud         │
│   (Alerts)      │    │   Functions     │
└─────────────────┘    └─────────────────┘
```

## 🛠️ Tecnologías Utilizadas

- **Python**: Procesamiento de datos y automatización
- **BigQuery**: Almacenamiento y consulta de datos
- **DBT**: Transformaciones de datos
- **GitHub Actions**: CI/CD Pipeline
- **Cloud Functions**: Automatización y notificaciones
- **Looker**: Dashboard y visualizaciones
- **Cloud Shell**: Entorno de desarrollo

## 📁 Estructura del Proyecto

```
Bank_Marketing/
├── README.md                           # Documentación principal
├── requirements.txt                    # Dependencias Python
├── config/
│   ├── dbt_project.yml                # Configuración DBT
│   └── profiles.yml                   # Perfiles de conexión
├── dbt/
│   ├── models/
│   │   ├── staging/                   # Modelos de staging
│   │   ├── intermediate/              # Modelos intermedios
│   │   └── marts/                    # Modelos finales
│   ├── tests/                        # Pruebas unitarias
│   └── macros/                       # Macros reutilizables
├── scripts/
│   ├── data_ingestion.py             # Ingesta de datos
│   ├── quality_checks.py             # Validaciones de calidad
│   └── email_notifications.py        # Notificaciones por email
├── tests/
│   ├── unit_tests/                   # Pruebas unitarias Python
│   └── integration_tests/            # Pruebas de integración
├── looker/
│   └── dashboard/                    # Archivos de Looker
├── .github/
│   └── workflows/                    # GitHub Actions
└── docs/
    ├── setup_guide.md               # Guía de configuración
    ├── architecture.md              # Documentación de arquitectura
    └── kpis_documentation.md       # Documentación de KPIs
```

## 🚀 Configuración Rápida

### Prerrequisitos

1. **Google Cloud Platform**:
   - Proyecto: `BankMarketingVada`
   - APIs habilitadas: BigQuery, Cloud Functions, Cloud Scheduler

2. **GitHub**:
   - Repositorio: https://github.com/VdelaRosaAbad/BankMark

3. **Herramientas**:
   - Cloud Shell
   - DBT CLI
   - Python 3.8+

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/VdelaRosaAbad/BankMark.git
cd BankMark

# 2. Configurar Cloud Shell
gcloud config set project BankMarketingVada

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar DBT
dbt deps

# 5. Ejecutar pipeline inicial
python scripts/data_ingestion.py
dbt run
dbt test
```

## 📊 KPIs Implementados

### 1. Tasa de Conversión
```sql
-- Conversión por campaña
SELECT 
    campaign,
    ROUND(COUNT(CASE WHEN y = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as conversion_rate
FROM {{ ref('fct_campaign_performance') }}
GROUP BY campaign
```

### 2. Contactos Exitosos
```sql
-- Total de conversiones
SELECT 
    COUNT(*) as successful_contacts,
    COUNT(DISTINCT customer_id) as unique_customers
FROM {{ ref('fct_campaign_performance') }}
WHERE y = 'yes'
```

### 3. Segmentación de Clientes
```sql
-- Segmentación por edad y ocupación
SELECT 
    age_group,
    job_category,
    COUNT(*) as customer_count,
    ROUND(COUNT(CASE WHEN y = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as segment_conversion_rate
FROM {{ ref('dim_customer_segments') }}
GROUP BY age_group, job_category
```

## 🔧 Automatización

### Pipeline CI/CD
- **Trigger**: Push a main branch
- **Validaciones**: 
  - Linting de código
  - Pruebas unitarias
  - Validación de modelos DBT
- **Despliegue**: Automático a BigQuery
- **Notificaciones**: Email diario a las 9 AM CST

### Monitoreo
- **Alertas**: Fallos en pipeline
- **Auditoría**: Calidad de datos semanal
- **Dashboard**: Métricas en tiempo real

## 📈 Dashboard Looker

### KPIs Principales
1. **Tasa de Conversión por Campaña**
2. **Evolución Temporal de Conversiones**
3. **Segmentación de Clientes**
4. **Análisis de Ocupaciones**
5. **Distribución por Edad**

### Filtros Disponibles
- Rango de fechas
- Tipo de campaña
- Segmento de cliente
- Ocupación

## 🧪 Pruebas Implementadas

### Pruebas Unitarias Python
- Validación de tipos de datos
- Verificación de rangos
- Comprobación de valores nulos
- Tests de unicidad

### Pruebas DBT
- `not_null`: Campos obligatorios
- `unique`: Claves únicas
- `accepted_values`: Valores permitidos
- `relationships`: Integridad referencial

## 📧 Notificaciones por Email

### Configuración
- **Horario**: 9:00 AM CST diario
- **Contenido**: 
  - KPIs del día anterior
  - Estado de pruebas
  - Alertas de calidad
  - Resumen de errores

### Destinatarios
- Equipo de Analytics
- Stakeholders de Marketing
- Administradores del sistema

## 📚 Documentación Detallada

### Guías Disponibles
1. **[Setup Guide](docs/setup_guide.md)**: Configuración paso a paso
2. **[Architecture Guide](docs/architecture.md)**: Diseño técnico detallado
3. **[KPIs Documentation](docs/kpis_documentation.md)**: Métricas y cálculos
4. **[Troubleshooting](docs/troubleshooting.md)**: Solución de problemas

## 🔍 Monitoreo y Alertas

### Métricas Clave
- **Pipeline Health**: Estado de ejecución
- **Data Quality**: Porcentaje de datos válidos
- **Performance**: Tiempo de ejecución
- **Errors**: Tasa de errores

### Alertas Configuradas
- Pipeline fallido
- Calidad de datos < 95%
- Tiempo de ejecución > 30 min
- Errores críticos en transformaciones

## 🤝 Contribución

1. Fork del repositorio
2. Crear feature branch
3. Implementar cambios
4. Ejecutar pruebas
5. Crear Pull Request

## 📞 Soporte

Para soporte técnico o preguntas sobre el proyecto:
- **Email**: jguerrero@deacero.com
- **Issues**: GitHub Issues del repositorio
- **Documentación**: Carpeta `docs/`

---

**Desarrollado con ❤️ usando Cloud Shell y GitHub**
