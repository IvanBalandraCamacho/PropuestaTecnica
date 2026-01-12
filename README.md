# RFP Analyzer v2

Sistema de análisis inteligente de RFPs (Request for Proposals) usando **Gemini AI** con **Thinking Mode High**.

## Stack Tecnológico

- **Frontend**: React 19 + Vite + Ant Design (Dark Theme: Negro/Rojo)
- **Backend**: FastAPI + Python 3.12
- **Database**: PostgreSQL 16
- **AI**: Google Gemini 2.0 Flash Thinking
- **Container**: Docker + Docker Compose

## Inicio Rápido

### 1. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar y agregar tu GOOGLE_API_KEY
# Obtener desde: https://aistudio.google.com/app/apikey
```

### 2. Iniciar con Docker Compose

```bash
# Iniciar todos los servicios
docker-compose up --build

# O en background
docker-compose up --build -d

# Ver logs
docker-compose logs -f
```

### 3. Acceder a la Aplicación

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| PgAdmin (opcional) | http://localhost:5050 |

## Desarrollo Local

### Frontend (sin Docker)

```bash
cd frontend
npm install
npm run dev
```

### Backend (sin Docker)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Monitoreo de Consumo de API

El sistema incluye un logger de consumo de Gemini AI:

```bash
# Ver consumo en los logs
docker-compose logs backend | grep "GEMINI API CONSUMPTION"

# O via API
curl http://localhost:8000/api/v1/dashboard/api-consumption
```

### Métricas Disponibles

- Total de requests
- Input/Output tokens
- Thinking tokens (para modelos con thinking mode)
- Latencia promedio
- Tasa de éxito/error

## Modelo de Gemini

El sistema usa `gemini-2.0-flash-thinking-exp` con **Thinking Mode High** para:

- Análisis profundo de documentos RFP
- Extracción estructurada de 13 campos clave
- Generación inteligente de preguntas para el cliente
- Recomendaciones GO/NO GO basadas en riesgos

## Tema Visual

**Dark Mode Premium** con colores TIVIT:

- Fondo principal: `#0A0A0B`
- Cards: `#141416`
- Rojo primario: `#E31837`
- Rojo hover: `#FF2D4D`

## Estructura del Proyecto

```
v2/
├── docker-compose.yml     # Orquestación Docker
├── .env.example           # Variables de entorno
│
├── frontend/              # React + Vite
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── pages/         # LoginPage, DashboardPage, etc.
│       ├── components/    # StatsCards, RFPTable, etc.
│       ├── context/       # AuthContext
│       └── lib/           # API client
│
└── backend/               # FastAPI
    ├── Dockerfile
    ├── main.py
    ├── api/routes/        # auth, rfp, dashboard
    ├── core/
    │   ├── config.py
    │   ├── database.py
    │   └── gcp/
    │       └── vertex_ai.py  # Gemini client + Logger
    └── models/            # SQLAlchemy models
```

## Comandos Útiles

```bash
# Reiniciar solo backend
docker-compose restart backend

# Ver logs de un servicio específico
docker-compose logs -f backend

# Ejecutar migraciones (si Alembic está configurado)
docker-compose exec backend alembic upgrade head

# Acceder al contenedor
docker-compose exec backend bash

# Limpiar todo
docker-compose down -v
```

## Endpoints Principales

### Auth
- `POST /api/v1/auth/register` - Registro
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Usuario actual

### RFP
- `POST /api/v1/rfp/upload` - Subir RFP
- `GET /api/v1/rfp` - Listar RFPs
- `GET /api/v1/rfp/{id}` - Detalle RFP
- `POST /api/v1/rfp/{id}/decision` - GO/NO GO
- `GET /api/v1/rfp/{id}/questions` - Preguntas generadas

### Dashboard
- `GET /api/v1/dashboard/stats` - Estadísticas
- `GET /api/v1/dashboard/api-consumption` - Consumo Gemini

## Licencia

Proyecto privado para TIVIT.
