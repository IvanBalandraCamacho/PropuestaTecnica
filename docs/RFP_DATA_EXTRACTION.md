# Especificación de Extracción de Datos - RFP Analyzer

## Objetivo

Este documento define los datos exactos que **Gemini 2.5 Pro (via Vertex AI)** debe extraer de cada RFP subido al sistema. Los datos se almacenan en **Cloud SQL PostgreSQL** y alimentan el Dashboard para toma de decisiones GO/NO GO.

---

## Datos a Extraer por la IA

### 1. Información Básica

| Campo | Descripción | Tipo | Requerido |
|-------|-------------|------|-----------|
| `client_name` | Nombre del cliente/empresa | string | ✅ Sí |
| `country` | País de origen del RFP | string | ✅ Sí |
| `summary` | Resumen/objetivo del proyecto | text | ✅ Sí |
| `category` | Categoría del proyecto (ver lista abajo) | enum | ✅ Sí |

#### Categorías Válidas
- `mantencion_aplicaciones` - Mantención de Aplicaciones
- `desarrollo_software` - Desarrollo de Software
- `analitica` - Analítica / Gobierno de Datos
- `ia_chatbot` - IA: Chatbot
- `ia_documentos` - IA: Análisis de Documentos
- `ia_video` - IA: Análisis de Video
- `otro` - Otra categoría

---

### 2. Información Comercial y Plazos

| Campo | Descripción | Tipo | Requerido |
|-------|-------------|------|-----------|
| `budget` | Presupuesto del cliente | object | No |
| `budget.amount_min` | Monto mínimo | number | No |
| `budget.amount_max` | Monto máximo | number | No |
| `budget.currency` | Moneda (USD, PEN, CLP, etc.) | string | No |
| `project_duration` | Plazo esperado para ejecutar el proyecto | string | No |
| `questions_deadline` | Fecha máxima de entrega de preguntas | date | No |
| `proposal_deadline` | Fecha máxima de entrega de propuesta técnica | date | ✅ Sí |

---

### 3. Requisitos Técnicos

| Campo | Descripción | Tipo | Requerido |
|-------|-------------|------|-----------|
| `tech_stack` | Stack tecnológico requerido | array[string] | No |
| `team_proposal` | ¿El cliente sugiere equipo/personas? | object | No |
| `team_proposal.suggested` | ¿Sugiere equipo? | boolean | No |
| `team_proposal.details` | Detalles del equipo sugerido | string | No |

---

### 4. Requisitos de Experiencia (TIVIT)

| Campo | Descripción | Tipo | Requerido |
|-------|-------------|------|-----------|
| `experience_required` | Experiencias similares exigidas | object | No |
| `experience_required.required` | ¿Es obligatorio? | boolean | No |
| `experience_required.details` | Descripción de experiencias requeridas | string | No |
| `experience_required.is_mandatory` | ¿Es requisito excluyente? | boolean | No |

---

### 5. SLA y Penalidades

| Campo | Descripción | Tipo | Requerido |
|-------|-------------|------|-----------|
| `sla` | Acuerdos de nivel de servicio | array[object] | No |
| `sla[].description` | Descripción del SLA | string | No |
| `sla[].metric` | Métrica (ej: 99.9% uptime) | string | No |
| `sla[].is_aggressive` | ¿Es un SLA agresivo? | boolean | No |
| `penalties` | Penalidades | array[object] | No |
| `penalties[].description` | Descripción de la penalidad | string | No |
| `penalties[].amount` | Monto o porcentaje | string | No |
| `penalties[].is_high` | ¿Es una penalidad alta? | boolean | No |

---

### 6. Análisis de Riesgos (Generado por IA)

| Campo | Descripción | Tipo |
|-------|-------------|------|
| `risks` | Lista de riesgos identificados | array[object] |
| `risks[].category` | Categoría del riesgo | enum |
| `risks[].description` | Descripción del riesgo | string |
| `risks[].severity` | Severidad (low/medium/high/critical) | enum |

#### Categorías de Riesgo
- `budget` - Presupuesto insuficiente o poco claro
- `timeline` - Plazos agresivos o irrealistas
- `technology` - Tecnología compleja o desconocida
- `sla` - SLAs agresivos
- `penalties` - Penalidades altas
- `scope` - Alcance poco definido o muy amplio
- `experience` - Requisitos de experiencia difíciles de cumplir

---

### 7. Recomendación de la IA

| Campo | Descripción | Tipo |
|-------|-------------|------|
| `recommendation` | Recomendación GO/NO GO | enum |
| `recommendation_reasons` | Razones de la recomendación | array[string] |
| `confidence_score` | Nivel de confianza (0-100) | number |

#### Valores de Recomendación
- `strong_go` - Muy recomendable participar
- `go` - Recomendable participar
- `conditional_go` - Participar con condiciones
- `no_go` - No recomendable participar
- `strong_no_go` - Definitivamente no participar

---

## Esquema JSON Completo

```json
{
  "client_name": "Banco Nacional de Chile",
  "country": "Chile",
  "summary": "Desarrollo de plataforma de banca digital con módulos de transferencias, pagos y gestión de cuentas",
  "category": "desarrollo_software",
  
  "budget": {
    "amount_min": 500000,
    "amount_max": 750000,
    "currency": "USD",
    "notes": "Presupuesto referencial, sujeto a negociación"
  },
  
  "project_duration": "18 meses",
  "questions_deadline": "2026-01-20",
  "proposal_deadline": "2026-01-30",
  
  "tech_stack": ["Java", "Spring Boot", "Angular", "PostgreSQL", "AWS"],
  
  "team_proposal": {
    "suggested": true,
    "details": "El cliente sugiere un equipo de 8 personas: 1 PM, 1 Arquitecto, 4 Desarrolladores, 1 QA Lead, 1 DevOps"
  },
  
  "experience_required": {
    "required": true,
    "details": "Mínimo 3 proyectos similares en sector financiero en los últimos 5 años",
    "is_mandatory": true
  },
  
  "sla": [
    {
      "description": "Disponibilidad de la plataforma",
      "metric": "99.95% uptime mensual",
      "is_aggressive": true
    },
    {
      "description": "Tiempo de respuesta de transacciones",
      "metric": "< 2 segundos p99",
      "is_aggressive": false
    }
  ],
  
  "penalties": [
    {
      "description": "Por cada 0.01% bajo el SLA de disponibilidad",
      "amount": "0.5% del valor mensual del contrato",
      "is_high": true
    },
    {
      "description": "Retraso en entrega de hitos",
      "amount": "1% por día de retraso, máximo 10%",
      "is_high": false
    }
  ],
  
  "risks": [
    {
      "category": "sla",
      "description": "SLA de 99.95% es agresivo para una plataforma nueva",
      "severity": "high"
    },
    {
      "category": "penalties",
      "description": "Penalidades acumulativas pueden llegar a ser significativas",
      "severity": "medium"
    },
    {
      "category": "timeline",
      "description": "18 meses para alcance completo es ajustado",
      "severity": "medium"
    }
  ],
  
  "recommendation": "conditional_go",
  "recommendation_reasons": [
    "Presupuesto adecuado para el alcance",
    "TIVIT tiene experiencia en sector financiero",
    "Stack tecnológico conocido por el equipo",
    "Negociar SLA de disponibilidad a 99.9%",
    "Clarificar alcance de fase 1 vs fases posteriores"
  ],
  "confidence_score": 75
}
```

---

## Prompt para Gemini 2.5 Pro

```
Eres un analista experto en RFPs (Request for Proposals) para TIVIT, una empresa de tecnología del grupo Almaviva.

Analiza el documento RFP adjunto y extrae la información según el esquema JSON proporcionado.

## INSTRUCCIONES:

1. **Extracción precisa**: Solo extrae información explícitamente mencionada en el documento
2. **Campos nulos**: Si no encuentras un dato, usa `null`, no inventes
3. **Análisis de riesgos**: Evalúa proactivamente riesgos considerando:
   - ¿El presupuesto es realista para el alcance?
   - ¿Los plazos son alcanzables?
   - ¿Las tecnologías son conocidas/viables?
   - ¿Los SLAs son agresivos?
   - ¿Las penalidades son altas?
4. **Recomendación**: Basándote en el análisis, recomienda GO o NO GO
5. **Idioma**: Responde en español

## ESQUEMA DE RESPUESTA (JSON):
{schema}

## IMPORTANTE:
- El campo `category` debe ser uno de: mantencion_aplicaciones, desarrollo_software, analitica, ia_chatbot, ia_documentos, ia_video, otro
- El campo `recommendation` debe ser uno de: strong_go, go, conditional_go, no_go, strong_no_go
- Las fechas deben estar en formato ISO: YYYY-MM-DD
- Los montos de presupuesto deben ser numéricos (sin símbolos de moneda)
```

---

## Preguntas a Generar (Fase GO)

Cuando el BDM decide **GO**, la IA genera preguntas complementarias basadas en:

1. **Información faltante** detectada durante el análisis
2. **Ambigüedades** en el documento
3. **Riesgos identificados** que requieren clarificación

### Categorías de Preguntas

| Categoría | Descripción |
|-----------|-------------|
| `scope` | Alcance y límites del proyecto |
| `technical` | Stack, integraciones, infraestructura |
| `commercial` | Presupuesto, pagos, facturación |
| `timeline` | Plazos, hitos, entregas |
| `team` | Equipo, roles, disponibilidad |
| `sla` | Niveles de servicio, métricas |
| `legal` | Contratos, confidencialidad, IP |

---

## Mapeo a Base de Datos

### Tabla `rfp_submissions`

```sql
-- Campos indexados (búsqueda rápida)
client_name VARCHAR(255),
country VARCHAR(100),
category VARCHAR(50),
proposal_deadline DATE,
budget_min DECIMAL(15,2),
budget_max DECIMAL(15,2),
recommendation VARCHAR(20),

-- Datos completos extraídos (JSONB)
extracted_data JSONB  -- Contiene todo el JSON de arriba
```

Esto permite:
- **Filtrar rápido** por campos indexados (cliente, país, categoría, fecha)
- **Flexibilidad** para agregar campos sin migraciones (JSONB)
- **Queries complejos** sobre el JSON cuando sea necesario

---

## Ejemplo de Query para Dashboard

```sql
-- RFPs pendientes de decisión, ordenados por deadline
SELECT 
    client_name,
    extracted_data->>'summary' as summary,
    category,
    proposal_deadline,
    budget_min,
    budget_max,
    recommendation,
    extracted_data->'risks' as risks
FROM rfp_submissions
WHERE status = 'analyzed'
  AND decision IS NULL
ORDER BY proposal_deadline ASC;
```
