# Plan de Trabajo: RFP Analyzer (Cloud-Native GCP)

## Resumen Ejecutivo

**Nombre del Proyecto:** RFP Analyzer - Sistema de Análisis Inteligente de Propuestas  
**Objetivo:** Automatizar el análisis de RFPs usando Gemini 2.5 Pro para extraer datos clave, facilitar decisiones GO/NO GO, y generar preguntas inteligentes para clientes.  
**Usuarios:** Business Development Managers (BDMs)  
**Infraestructura:** 100% Google Cloud Platform (Serverless-first)

---

## Arquitectura Cloud-Native GCP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js en Cloud Run)                     │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     DASHBOARD (Landing Principal)                     │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐   │   │
│  │   │ Stats Cards │  │ RFP Table   │  │  Upload     │  │  Filtros  │   │   │
│  │   │ GO/NO GO    │  │ + Búsqueda  │  │  Documento  │  │           │   │   │
│  │   └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                     │                                        │
│              ┌──────────────────────┼──────────────────────┐                │
│              ▼                      ▼                      ▼                │
│  ┌─────────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │   Detalle RFP       │  │   GO → Preguntas │  │   NO GO → Archivado    │  │
│  │   + Análisis        │  │   para Cliente   │  │   (vuelve a Dashboard) │  │
│  └─────────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI en Cloud Run)                       │
│                              Stateless & Serverless                         │
└─────────────────────────────────────────────────────────────────────────────┘
          │                    │                    │                │
          ▼                    ▼                    ▼                ▼
┌──────────────────┐  ┌──────────────────┐  ┌─────────────┐  ┌──────────────┐
│  Cloud Storage   │  │   Vertex AI      │  │  Cloud SQL  │  │ Secret       │
│  (Archivos PDF)  │  │   Gemini 2.5 Pro │  │  PostgreSQL │  │ Manager      │
└──────────────────┘  └──────────────────┘  └─────────────┘  └──────────────┘
```

---

## Por Qué Esta Arquitectura es Cloud-Native

| Componente | Antes (Problemático) | Ahora (Cloud-Native GCP) | Beneficio |
|------------|---------------------|--------------------------|-----------|
| **Compute** | Docker + VMs siempre on | **Cloud Run** | Escala a cero, pago por uso |
| **Archivos** | Filesystem local | **Cloud Storage** | Infinito, barato, CDN |
| **BD** | MySQL local/Docker | **Cloud SQL PostgreSQL** | Backups auto, HA, escalable |
| **Async Tasks** | Celery + Redis | **Cloud Tasks** | Serverless, sin mantener workers |
| **LLM** | API key directa | **Vertex AI** | IAM nativo, sin API keys expuestas |
| **Secrets** | .env files | **Secret Manager** | Rotación, auditoría, seguro |
| **Logs** | Archivos locales | **Cloud Logging** | Centralizado, alertas |
| **Vector DB** | Qdrant local | **❌ NO NECESARIO** | Gemini tiene 1M+ tokens de contexto |

### Decisión Clave: Sin Vector Database

Para este proyecto **NO necesitamos RAG/Vector Search** porque:

1. **Gemini 2.5 Pro** tiene ventana de contexto de **1M+ tokens**
2. Un RFP típico tiene 10-50 páginas (~20K-100K tokens)
3. Podemos enviar el documento **completo** a Gemini
4. Simplifica enormemente la arquitectura
5. Reduce costos y complejidad

---

## Stack Tecnológico GCP

| Servicio | Propósito | Tier Recomendado |
|----------|-----------|------------------|
| **Cloud Run** | Backend + Frontend | CPU always-on para baja latencia |
| **Cloud SQL** | Base de datos | PostgreSQL 15, db-f1-micro (dev) |
| **Cloud Storage** | Almacenamiento de PDFs | Standard |
| **Vertex AI** | Gemini 3 Pro | `gemini-3-pro-preview` (1M tokens context) |
| **Cloud Tasks** | Procesamiento async (opcional) | Default |
| **Secret Manager** | Credenciales | Default |
| **Cloud Build** | CI/CD | Default |
| **Artifact Registry** | Docker images | Default |
| **Cloud Logging** | Logs centralizados | Default |
| **IAM** | Autenticación servicios | Workload Identity |

---

## Estructura de Carpetas

```
v2/
├── backend/
│   ├── api/
│   │   └── routes/
│   │       ├── rfp.py              # CRUD RFP + Upload
│   │       ├── analysis.py         # Trigger análisis
│   │       ├── questions.py        # Preguntas generadas
│   │       └── dashboard.py        # Stats y métricas
│   │
│   ├── core/
│   │   ├── config.py               # Settings con Pydantic
│   │   ├── gcp/
│   │   │   ├── storage.py          # Cloud Storage client
│   │   │   ├── vertex_ai.py        # Gemini via Vertex AI
│   │   │   └── secret_manager.py   # Secrets
│   │   └── services/
│   │       ├── analyzer.py         # Lógica de análisis
│   │       └── question_gen.py     # Generador de preguntas
│   │
│   ├── models/
│   │   ├── rfp.py                  # SQLAlchemy models
│   │   └── schemas/
│   │       └── rfp_schemas.py      # Pydantic schemas
│   │
│   ├── prompts/
│   │   ├── rfp_analysis.txt        # Prompt análisis
│   │   └── question_generation.txt # Prompt preguntas
│   │
│   ├── alembic/                    # Migraciones BD
│   ├── Dockerfile                  # Para Cloud Run
│   ├── requirements.txt
│   └── main.py
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                # Dashboard (LANDING)
│   │   ├── layout.tsx              # Layout principal
│   │   └── rfp/
│   │       └── [id]/
│   │           ├── page.tsx        # Detalle + GO/NO GO
│   │           └── questions/
│   │               └── page.tsx    # Preguntas (solo si GO)
│   │
│   ├── components/
│   │   ├── dashboard/
│   │   │   ├── StatsCards.tsx      # Métricas principales
│   │   │   ├── RFPTable.tsx        # Tabla de RFPs
│   │   │   ├── UploadModal.tsx     # Modal para subir
│   │   │   └── Charts.tsx          # Gráficos
│   │   └── rfp/
│   │       ├── AnalysisView.tsx    # Vista del análisis
│   │       ├── DecisionPanel.tsx   # Botones GO/NO GO
│   │       └── QuestionsList.tsx   # Lista de preguntas
│   │
│   ├── lib/
│   │   └── api.ts                  # Cliente API
│   │
│   ├── Dockerfile                  # Para Cloud Run
│   └── package.json
│
├── infra/                          # Infrastructure as Code
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── cloud_run.tf
│   │   ├── cloud_sql.tf
│   │   ├── storage.tf
│   │   └── iam.tf
│   └── cloudbuild.yaml             # CI/CD pipeline
│
└── docs/
    ├── PLAN_RFP_ANALYZER.md        # Este documento
    └── RFP_DATA_EXTRACTION.md      # Campos a extraer
```

---

## Flujo de Usuario (Corregido)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DASHBOARD (LANDING PRINCIPAL)                        │
│                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │   Total    │ │    GO      │ │   NO GO    │ │  Pending   │               │
│  │    45      │ │    28      │ │    12      │ │     5      │               │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  [+ Subir RFP]  🔍 Buscar...                    Filtros ▼           │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ Cliente     │ Proyecto      │ Budget    │ Deadline  │ Status       │    │
│  │─────────────│───────────────│───────────│───────────│──────────────│    │
│  │ ACME Corp   │ ERP SAP       │ $500K     │ 30 Ene    │ 🟡 Pending   │◄───┼─── Click
│  │ TechStart   │ App Mobile    │ $30K      │ 15 Feb    │ 🟢 GO        │    │
│  │ MegaCorp    │ Data Platform │ $200K     │ 28 Ene    │ 🔴 NO GO     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
         [Click en RFP Pending]              [Click "Subir RFP"]
                    │                                   │
                    ▼                                   ▼
┌─────────────────────────────────┐    ┌─────────────────────────────────────┐
│      DETALLE RFP + ANÁLISIS     │    │          MODAL UPLOAD               │
│  ┌───────────────────────────┐  │    │   ┌─────────────────────────────┐   │
│  │ Cliente: ACME Corp        │  │    │   │                             │   │
│  │ Proyecto: ERP SAP         │  │    │   │   📄 Arrastra tu RFP aquí   │   │
│  │ Presupuesto: $500K-$750K  │  │    │   │      o haz click            │   │
│  │ Deadline: 30 Enero 2026   │  │    │   │                             │   │
│  │ Complejidad: 8/10         │  │    │   │   Formatos: PDF, DOCX       │   │
│  │ Probabilidad: 65%         │  │    │   └─────────────────────────────┘   │
│  │                           │  │    │                                     │
│  │ ⚠️ Info Faltante:         │  │    │   [Cancelar]  [Subir y Analizar]   │
│  │ • Volumen de datos        │  │    └─────────────────────────────────────┘
│  │ • Criterios evaluación    │  │                    │
│  │                           │  │                    ▼
│  │ 💡 Recomendación: GO      │  │         ┌─────────────────┐
│  └───────────────────────────┘  │         │   ANALYZING...   │
│                                  │         │   ⏳ Gemini      │
│   ┌─────────┐    ┌──────────┐   │         └────────┬────────┘
│   │   GO ✓  │    │  NO GO ✗ │   │                  │
│   └────┬────┘    └────┬─────┘   │                  ▼
│        │              │         │         Redirige a Detalle
└────────┼──────────────┼─────────┘
         │              │
         ▼              ▼
┌─────────────────┐   ┌─────────────────┐
│   PREGUNTAS     │   │   DASHBOARD     │
│   PARA CLIENTE  │   │   (Archivado)   │
│                 │   │                 │
│ 📋 Técnicas     │   │  Status: NO GO  │
│ 1. ¿Volumen?    │   │  Razón: [input] │
│ 2. ¿SAP ver?    │   │                 │
│                 │   │                 │
│ 📋 Comerciales  │   │                 │
│ 1. ¿Criterios?  │   │                 │
│                 │   │                 │
│ [📋 Copiar]     │   │                 │
│ [📧 Email]      │   │                 │
└─────────────────┘   └─────────────────┘
```

---

## Modelo de Datos (PostgreSQL)

### Tabla: `rfp_submissions`

```sql
CREATE TABLE rfp_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Archivo
    file_name VARCHAR(255) NOT NULL,
    file_gcs_path VARCHAR(500) NOT NULL,  -- gs://bucket/path/file.pdf
    file_size_bytes INTEGER,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, analyzing, analyzed, go, no_go
    
    -- Datos extraídos (JSONB para flexibilidad)
    extracted_data JSONB,  -- Todo lo extraído por Gemini
    
    -- Campos indexados para búsqueda/filtros
    client_name VARCHAR(255),
    project_name VARCHAR(255),
    budget_min DECIMAL(15,2),
    budget_max DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'USD',
    proposal_deadline DATE,
    
    -- Métricas de análisis
    complexity_score INTEGER CHECK (complexity_score BETWEEN 1 AND 10),
    win_probability INTEGER CHECK (win_probability BETWEEN 0 AND 100),
    recommendation VARCHAR(20),  -- strong_go, go, conditional_go, no_go, strong_no_go
    
    -- Decisión
    decision VARCHAR(10),  -- go, no_go
    decision_reason TEXT,
    decided_at TIMESTAMP WITH TIME ZONE,
    decided_by UUID REFERENCES users(id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analyzed_at TIMESTAMP WITH TIME ZONE
);

-- Índices para performance
CREATE INDEX idx_rfp_user ON rfp_submissions(user_id);
CREATE INDEX idx_rfp_status ON rfp_submissions(status);
CREATE INDEX idx_rfp_created ON rfp_submissions(created_at DESC);
CREATE INDEX idx_rfp_client ON rfp_submissions(client_name);
```

### Tabla: `rfp_questions`

```sql
CREATE TABLE rfp_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfp_id UUID NOT NULL REFERENCES rfp_submissions(id) ON DELETE CASCADE,
    
    question TEXT NOT NULL,
    category VARCHAR(50),  -- technical, commercial, timeline, scope, etc.
    priority VARCHAR(10),  -- high, medium, low
    context TEXT,          -- Por qué surge esta pregunta
    why_important TEXT,    -- Por qué es importante
    
    -- Respuesta (cuando el cliente responde)
    is_answered BOOLEAN DEFAULT FALSE,
    answer TEXT,
    answered_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_questions_rfp ON rfp_questions(rfp_id);
```

---

## API Endpoints

### Dashboard
```
GET  /api/v1/dashboard/stats          # Métricas: totales, GO/NO GO rates
GET  /api/v1/dashboard/rfps           # Lista paginada con filtros
```

### RFP CRUD
```
POST   /api/v1/rfp/upload             # Subir archivo → GCS → Trigger análisis
GET    /api/v1/rfp/{id}               # Detalle con análisis
POST   /api/v1/rfp/{id}/decision      # Registrar GO/NO GO
DELETE /api/v1/rfp/{id}               # Eliminar (soft delete)
```

### Preguntas
```
GET    /api/v1/rfp/{id}/questions     # Obtener preguntas generadas
POST   /api/v1/rfp/{id}/questions/regenerate  # Regenerar con nuevo contexto
```

---

## Integración con Vertex AI (Gemini)

### Configuración

```python
# backend/core/gcp/vertex_ai.py
from google import genai
from google.genai.types import HttpOptions, Part
import json

class GeminiAnalyzer:
    def __init__(self, project_id: str, location: str = "us-central1"):
        # Usar el nuevo SDK google-genai
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
            http_options=HttpOptions(api_version="v1")
        )
        self.model_id = "gemini-3-pro-preview"  # Gemini 3 Pro (1M tokens)
    
    async def analyze_rfp(self, pdf_gcs_uri: str, prompt: str) -> dict:
        """Analiza un RFP directamente desde GCS."""
        
        # Gemini puede leer PDFs directamente desde GCS
        pdf_file = Part.from_uri(
            file_uri=pdf_gcs_uri,
            mime_type="application/pdf"
        )
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[pdf_file, prompt],
            config={
                "temperature": 0.1,  # Baja para extracción precisa
                "max_output_tokens": 8192,
                "response_mime_type": "application/json"
            }
        )
        
        return json.loads(response.text)
```

### Instalación del SDK

```bash
pip install google-genai
```

### Variables de Entorno para Vertex AI

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
export GOOGLE_GENAI_USE_VERTEXAI=True
```
```

### Ventaja: Gemini 3 Pro lee PDFs directo de GCS

```python
# NO necesitas:
# - Descargar el archivo
# - Extraer texto con PyMuPDF
# - Hacer chunking
# - Embeddings
# - Vector search

# Gemini 3 Pro hace TODO esto internamente (1M tokens de contexto):
from google import genai
from google.genai.types import Part

client = genai.Client(vertexai=True, project="my-project", location="us-central1")

pdf_file = Part.from_uri("gs://my-bucket/rfps/document.pdf", mime_type="application/pdf")
response = client.models.generate_content(
    model="gemini-3-pro-preview",
    contents=[pdf_file, "Analiza este RFP y extrae los datos clave"]
)
```

---

## Cloud Storage Structure

```
gs://[PROJECT]-rfp-analyzer/
├── uploads/
│   └── {user_id}/
│       └── {rfp_id}/
│           └── original.pdf          # Archivo original
│
└── exports/                           # Futuro: exportaciones
    └── {rfp_id}/
        └── questions.pdf
```

---

## Variables de Entorno (Secret Manager)

```yaml
# Secrets en Secret Manager
DATABASE_URL: postgresql://user:pass@/rfp_db?host=/cloudsql/project:region:instance
GCP_PROJECT_ID: tivit-rfp-analyzer
GCP_REGION: us-central1
GCS_BUCKET: tivit-rfp-analyzer-uploads
JWT_SECRET_KEY: [auto-generated]

# Config en Cloud Run (no secreta)
ENV: production
LOG_LEVEL: INFO
ALLOWED_ORIGINS: https://rfp-analyzer.tivit.com
```

---

## CI/CD con Cloud Build

```yaml
# infra/cloudbuild.yaml
steps:
  # Build Backend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/rfp-backend', './backend']
  
  # Build Frontend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/rfp-frontend', './frontend']
  
  # Push images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/rfp-backend']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/rfp-frontend']
  
  # Deploy Backend
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    args:
      - 'run'
      - 'deploy'
      - 'rfp-backend'
      - '--image=gcr.io/$PROJECT_ID/rfp-backend'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'
  
  # Deploy Frontend
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    args:
      - 'run'
      - 'deploy'
      - 'rfp-frontend'
      - '--image=gcr.io/$PROJECT_ID/rfp-frontend'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'

# Trigger: Push to main branch
```

---

## Plan de Trabajo por Fases

### FASE 0: Infraestructura GCP (Día 1-2)
| # | Tarea | Prioridad |
|---|-------|-----------|
| 0.1 | Crear proyecto GCP | Alta |
| 0.2 | Habilitar APIs (Cloud Run, Cloud SQL, Storage, Vertex AI) | Alta |
| 0.3 | Crear bucket Cloud Storage | Alta |
| 0.4 | Crear instancia Cloud SQL PostgreSQL | Alta |
| 0.5 | Configurar Secret Manager | Alta |
| 0.6 | Setup Cloud Build (CI/CD) | Media |

### FASE 1: Backend Core (Semana 1)
| # | Tarea | Prioridad |
|---|-------|-----------|
| 1.1 | Modelos SQLAlchemy + Migraciones | Alta |
| 1.2 | Cliente Cloud Storage (upload/download) | Alta |
| 1.3 | Cliente Vertex AI (Gemini) | Alta |
| 1.4 | Endpoint POST /rfp/upload | Alta |
| 1.5 | Prompt de análisis | Alta |
| 1.6 | Endpoint GET /rfp/{id} | Alta |

### FASE 2: Dashboard Frontend (Semana 1-2)
| # | Tarea | Prioridad |
|---|-------|-----------|
| 2.1 | Layout base + navegación | Alta |
| 2.2 | Stats Cards (métricas) | Alta |
| 2.3 | Tabla de RFPs con filtros | Alta |
| 2.4 | Modal de Upload | Alta |
| 2.5 | Integración con API | Alta |

### FASE 3: Detalle + Decisión (Semana 2)
| # | Tarea | Prioridad |
|---|-------|-----------|
| 3.1 | Vista de detalle/análisis | Alta |
| 3.2 | Botones GO/NO GO | Alta |
| 3.3 | Endpoint POST /rfp/{id}/decision | Alta |
| 3.4 | Modal razón NO GO | Alta |
| 3.5 | Actualizar status en tabla | Alta |

### FASE 4: Preguntas (Semana 2-3)
| # | Tarea | Prioridad |
|---|-------|-----------|
| 4.1 | Prompt generación de preguntas | Alta |
| 4.2 | Endpoint GET /rfp/{id}/questions | Alta |
| 4.3 | Vista lista de preguntas | Alta |
| 4.4 | Copiar al portapapeles | Media |
| 4.5 | Exportar a formato | Media |

### FASE 5: Deploy + Polish (Semana 3)
| # | Tarea | Prioridad |
|---|-------|-----------|
| 5.1 | Deploy a Cloud Run | Alta |
| 5.2 | Configurar dominio custom | Media |
| 5.3 | Testing E2E | Alta |
| 5.4 | Optimización de prompts | Media |
| 5.5 | Monitoreo y alertas | Media |

---

## Estimación de Costos GCP (Mensual)

| Servicio | Uso Estimado | Costo |
|----------|--------------|-------|
| **Cloud Run** (Backend) | 100K requests | ~$5-15 |
| **Cloud Run** (Frontend) | 50K requests | ~$3-10 |
| **Cloud SQL** | db-f1-micro, 10GB | ~$10-15 |
| **Cloud Storage** | 10GB, 1K operations | ~$1-2 |
| **Vertex AI** (Gemini) | 500 análisis/mes | ~$50-100 |
| **Otros** | Logging, networking | ~$5 |
| **Total Estimado** | | **~$75-150/mes** |

> Nota: Escala según uso. Con poco tráfico puede ser mucho menor.

---

## Seguridad

- ✅ **IAM**: Service accounts con permisos mínimos
- ✅ **Workload Identity**: No API keys en código
- ✅ **Secret Manager**: Credenciales encriptadas
- ✅ **Cloud SQL**: Conexión via proxy, sin IP pública
- ✅ **HTTPS**: Automático en Cloud Run
- ✅ **VPC**: Opcional para aislamiento

---

## Alcance: Implementación Actual vs Futuro

### ✅ ALCANCE ACTUAL (MVP)

**Lo que implementaremos ahora:**

```
┌─────────────────────────────────────────────────────────────────┐
│                         FASE 1: MVP                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. DASHBOARD (Landing)                                         │
│     ├── Stats Cards (Total, GO, NO GO, Pending)                │
│     ├── Tabla de RFPs con filtros                              │
│     └── Botón "+ Subir RFP"                                    │
│                                                                 │
│  2. UPLOAD + ANÁLISIS                                           │
│     ├── Modal para subir PDF/DOCX                              │
│     ├── Guardar en Cloud Storage                               │
│     └── Análisis automático con Gemini 2.5 Pro                 │
│                                                                 │
│  3. DATOS EXTRAÍDOS POR IA                                      │
│     ├── Cliente                                                │
│     ├── Resumen/Objetivo                                       │
│     ├── SLA y Penalidades                                      │
│     ├── Equipo sugerido por cliente                            │
│     ├── Presupuesto                                            │
│     ├── Stack Tecnológico                                      │
│     ├── Experiencias requeridas (¿obligatorio?)                │
│     ├── Análisis de riesgos (presupuesto, plazos, tech, SLAs)  │
│     ├── Plazo esperado del proyecto                            │
│     ├── Categoría (mantención, desarrollo, analítica, IA)     │
│     ├── Fecha máxima de preguntas                              │
│     ├── Fecha máxima de propuesta técnica                      │
│     └── País de origen                                         │
│                                                                 │
│  4. DECISIÓN GO/NO GO                                           │
│     ├── Botón GO → Continuar a preguntas                       │
│     └── Botón NO GO → Guardar razón y archivar                 │
│                                                                 │
│  5. PREGUNTAS PARA CLIENTE (Solo si GO)                         │
│     ├── IA genera preguntas complementarias                    │
│     ├── Basadas en información faltante                        │
│     └── Copiar al portapapeles / Exportar                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 🔮 FUNCIONALIDADES FUTURAS (Post-MVP)

**Lo que NO implementaremos ahora pero está planificado:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    FASE 2: PROPUESTA TÉCNICA                    │
│                         (FUTURO)                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  6. IA ARMA PROPUESTA TÉCNICA (Documento Word)                  │
│     ├── Carátula                                               │
│     ├── Declaración de Confidencialidad                        │
│     ├── Resumen Ejecutivo                                      │
│     ├── Certificaciones de TIVIT                               │
│     ├── Experiencias de TIVIT                                  │
│     ├── Alcance del Servicio                                   │
│     ├── Organigrama                                            │
│     ├── Aportes de las Partes                                  │
│     ├── Listado de Entregables                                 │
│     └── Capítulos Teóricos (técnicos + RRHH + metodología)     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    FASE 3: BÚSQUEDA DE EQUIPO                   │
│                         (FUTURO)                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  7. BÚSQUEDA AUTOMÁTICA DE RECURSOS                             │
│                                                                 │
│     Si la licitación pide Angular (ejemplo):                   │
│                                                                 │
│     PASO 1: Buscar en CENSUS                                   │
│             (Miguel conoce .NET, Juan conoce Angular, etc.)    │
│                                                                 │
│     PASO 2: Ir a Drive donde están los CVs                     │
│             Buscar personas y obtener sus CVs                  │
│                                                                 │
│     PASO 3: Capital Intelectual                                │
│             Obtener certificaciones relevantes                 │
│                                                                 │
│     PASO 4: Repositorio de Certificaciones                     │
│             Validar y adjuntar certificados                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Resumen de Fases

| Fase | Nombre | Status | Descripción |
|------|--------|--------|-------------|
| **1** | MVP | 🟢 **IMPLEMENTAR AHORA** | Dashboard + Upload + Análisis + GO/NO GO + Preguntas |
| **2** | Propuesta Técnica | 🔮 Futuro | IA genera documento Word completo |
| **3** | Búsqueda de Equipo | 🔮 Futuro | Integración con CENSUS + Drive + Certificaciones |

---

### Integraciones Futuras Requeridas

Para las fases futuras se necesitará:

| Integración | Propósito | Fase |
|-------------|-----------|------|
| **CENSUS** | Base de datos de empleados y skills | 3 |
| **Google Drive** | Repositorio de CVs | 3 |
| **Repositorio de Certificaciones** | Certificados de empleados | 3 |
| **Google Docs API** | Generar documentos Word | 2 |
| **Templates TIVIT** | Plantillas de propuestas | 2 |

---

## Datos a Extraer (Especificación Detallada)

Ver documento: [`RFP_DATA_EXTRACTION.md`](./RFP_DATA_EXTRACTION.md)

### Resumen de Campos

| # | Campo | Descripción |
|---|-------|-------------|
| 1 | `client_name` | Nombre del cliente |
| 2 | `summary` | Resumen/objetivo del proyecto |
| 3 | `sla_penalties` | SLA y penalidades |
| 4 | `team_proposal` | ¿Cliente sugiere equipo? |
| 5 | `budget` | Presupuesto del cliente |
| 6 | `tech_stack` | Stack tecnológico requerido |
| 7 | `experience_required` | Experiencias similares exigidas (¿obligatorio?) |
| 8 | `risks` | Análisis de riesgos (presupuesto, plazos, tech, SLAs, penalidades) |
| 9 | `project_duration` | Plazo esperado del proyecto |
| 10 | `category` | Categoría (mantención, desarrollo, analítica, IA) |
| 11 | `questions_deadline` | Fecha máxima de preguntas |
| 12 | `proposal_deadline` | Fecha máxima de propuesta técnica |
| 13 | `country` | País de origen del RFP |

### Categorías Válidas

| Código | Descripción |
|--------|-------------|
| `mantencion_aplicaciones` | Mantención de Aplicaciones |
| `desarrollo_software` | Desarrollo de Software |
| `analitica` | Analítica / Gobierno de Datos |
| `ia_chatbot` | IA: Chatbot |
| `ia_documentos` | IA: Análisis de Documentos con IA |
| `ia_video` | IA: Análisis de Video con IA |
