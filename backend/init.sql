-- init.sql - Inicialización de la base de datos PostgreSQL
-- Este script se ejecuta automáticamente al crear el contenedor

-- Extensiones útiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully for RFP Analyzer!';
END $$;
