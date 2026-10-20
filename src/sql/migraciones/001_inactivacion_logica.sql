/* =========================================================================================
   MIGRACIÓN 001 — Inactivación lógica y reglas de la vinculación Jugador–Tutor
   Re-arquitectura PaladinesFC · Entregable 3 · ADR-0003 y ADR-0004
   -----------------------------------------------------------------------------------------
   Qué hace:
     1. Agrega TUTOR.estado ('activo' | 'inactivo'). JUGADOR y PROFESOR ya tenían estado.
     2. Repara datos heredados de JUGADOR_TUTOR que violan las reglas (vínculos duplicados,
        jugadores sin acudiente principal o con más de uno).
     3. Crea índices únicos que hacen cumplir las reglas también en el motor:
          - un mismo tutor no se vincula dos veces al mismo jugador;
          - exactamente un acudiente principal por jugador (índice filtrado).
     4. Retira las vías de escritura que la nueva arquitectura reemplaza:
          - SP_ActualizarProfesor (nunca se invocaba y no recibía el documento);
          - SP_EliminarJugador / SP_EliminarProfesor / SP_EliminarTutor (borrado físico
            en cascada, problema P3).
   Cómo aplicarla:
     - Hacer COPIA DE SEGURIDAD de ClubFutbolDB.
     - Ejecutar este archivo completo en SSMS sobre ClubFutbolDB.
     - Es idempotente: puede ejecutarse más de una vez sin error.
   Requiere SQL Server 2016 o superior (DROP ... IF EXISTS).
   ========================================================================================= */
USE ClubFutbolDB;
GO

/* 1. TUTOR.estado ----------------------------------------------------------------------- */
IF COL_LENGTH('TUTOR', 'estado') IS NULL
BEGIN
    ALTER TABLE TUTOR
        ADD estado VARCHAR(20) NOT NULL
            CONSTRAINT DF_TUTOR_estado DEFAULT 'activo' WITH VALUES;
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CK_TUTOR_estado')
    ALTER TABLE TUTOR ADD CONSTRAINT CK_TUTOR_estado CHECK (estado IN ('activo', 'inactivo'));
GO

/* 2. Reparación de datos heredados ------------------------------------------------------ */
-- 2a. Vínculos duplicados (mismo jugador y mismo tutor): se conserva el más antiguo.
;WITH duplicados AS (
    SELECT id_jugador_tutor,
           ROW_NUMBER() OVER (PARTITION BY id_jugador, id_tutor
                              ORDER BY acudiente_principal DESC, id_jugador_tutor) AS n
    FROM JUGADOR_TUTOR
)
DELETE FROM duplicados WHERE n > 1;
GO

-- 2b. Jugadores con más de un acudiente principal: se conserva el vínculo más antiguo.
;WITH principales AS (
    SELECT id_jugador_tutor,
           ROW_NUMBER() OVER (PARTITION BY id_jugador ORDER BY id_jugador_tutor) AS n
    FROM JUGADOR_TUTOR
    WHERE acudiente_principal = 1
)
UPDATE JUGADOR_TUTOR SET acudiente_principal = 0
WHERE id_jugador_tutor IN (SELECT id_jugador_tutor FROM principales WHERE n > 1);
GO

-- 2c. Jugadores con tutores pero sin acudiente principal (defecto de delete_jugador_tutor):
--     se marca como principal el vínculo más antiguo.
UPDATE jt SET acudiente_principal = 1
FROM JUGADOR_TUTOR jt
WHERE jt.id_jugador_tutor IN (
    SELECT MIN(id_jugador_tutor)
    FROM JUGADOR_TUTOR
    GROUP BY id_jugador
    HAVING SUM(CAST(acudiente_principal AS INT)) = 0
);
GO

/* 3. Índices que hacen cumplir las reglas --------------------------------------------- */
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_JT_jugador_tutor')
    CREATE UNIQUE INDEX UX_JT_jugador_tutor ON JUGADOR_TUTOR (id_jugador, id_tutor);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_JT_un_principal')
    CREATE UNIQUE INDEX UX_JT_un_principal ON JUGADOR_TUTOR (id_jugador)
        WHERE acudiente_principal = 1;
GO

/* 4. Retiro de vías de escritura reemplazadas ------------------------------------------ */
DROP PROCEDURE IF EXISTS SP_ActualizarProfesor;
DROP PROCEDURE IF EXISTS SP_EliminarJugador;
DROP PROCEDURE IF EXISTS SP_EliminarProfesor;
DROP PROCEDURE IF EXISTS SP_EliminarTutor;
GO

/* 5. Verificación ---------------------------------------------------------------------- */
SELECT 'TUTOR.estado'                    AS verificacion,
       CASE WHEN COL_LENGTH('TUTOR','estado') IS NOT NULL THEN 'OK' ELSE 'FALTA' END AS resultado
UNION ALL
SELECT 'Jugadores sin exactamente un principal',
       CAST(COUNT(*) AS VARCHAR(10))
FROM (SELECT id_jugador FROM JUGADOR_TUTOR GROUP BY id_jugador
      HAVING SUM(CAST(acudiente_principal AS INT)) <> 1) x
UNION ALL
SELECT 'Índices de reglas creados',
       CAST(COUNT(*) AS VARCHAR(10))
FROM sys.indexes WHERE name IN ('UX_JT_jugador_tutor', 'UX_JT_un_principal');
GO
