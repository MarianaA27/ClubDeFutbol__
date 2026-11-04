/* =========================================================================================
   MIGRACIÓN 004 — Reparar SP_AsignarJugadorPlantilla en bases creadas con el script original
   Re-arquitectura PaladinesFC · Entrega final · hallazgo de las pruebas de integración
   -----------------------------------------------------------------------------------------
   Problema:
     En ClubFutbolDB.sql original faltaba un GO antes de "CREATE OR ALTER PROCEDURE
     SP_AsignarJugadorPlantilla". SQL Server rechazaba ese lote, así que en las bases
     creadas con ese script el procedimiento quedó con 3 parámetros (sin @tipo), mientras
     que legado/crud.py lo llama con 4. Resultado: "Añadir titular" y "Añadir a banca" en
     Plantillas fallaban con el error 8144 ("has too many arguments specified").
     El script ya se corrigió (paso 12); esta migración repara las bases EXISTENTES.
   Qué hace:
     1. Agrega PLANTILLA_JUGADOR.tipo ('titular' | 'banca') si no existe.
     2. Recrea SP_AsignarJugadorPlantilla con el parámetro @tipo.
   Cómo aplicarla:
     - Hacer COPIA DE SEGURIDAD de ClubFutbolDB.
     - Ejecutar este archivo completo en SSMS sobre ClubFutbolDB. Es idempotente.
   ========================================================================================= */
USE ClubFutbolDB;
GO

IF COL_LENGTH('PLANTILLA_JUGADOR', 'tipo') IS NULL
    ALTER TABLE PLANTILLA_JUGADOR
        ADD tipo VARCHAR(10) NOT NULL CONSTRAINT DF_PJ_tipo DEFAULT 'titular';
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CK_PJ_tipo')
    ALTER TABLE PLANTILLA_JUGADOR ADD CONSTRAINT CK_PJ_tipo CHECK (tipo IN ('titular', 'banca'));
GO

CREATE OR ALTER PROCEDURE SP_AsignarJugadorPlantilla
    @id_plantilla   INT,
    @id_jugador     INT,
    @fecha          DATE,
    @tipo           VARCHAR(10) = 'titular'
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO PLANTILLA_JUGADOR
        (id_plantilla, id_jugador, fecha_asignacion, estado, tipo)
    VALUES
        (@id_plantilla, @id_jugador, @fecha, 'activo', @tipo);
END;
GO

/* Verificación ------------------------------------------------------------------------- */
SELECT 'Parámetros de SP_AsignarJugadorPlantilla (deben ser 4)' AS verificacion,
       CAST(COUNT(*) AS VARCHAR(10)) AS resultado
FROM sys.parameters WHERE object_id = OBJECT_ID('SP_AsignarJugadorPlantilla')
UNION ALL
SELECT 'PLANTILLA_JUGADOR.tipo',
       CASE WHEN COL_LENGTH('PLANTILLA_JUGADOR', 'tipo') IS NOT NULL THEN 'OK' ELSE 'FALTA' END;
GO
