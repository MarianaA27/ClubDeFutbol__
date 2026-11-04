/* =========================================================================================
   MIGRACIÓN 002 — Campo "entidad de salud (EPS)" del jugador
   Re-arquitectura PaladinesFC · Entrega final · Escenario E1 (Mantenibilidad), issue #17
   -----------------------------------------------------------------------------------------
   Qué hace:
     Agrega JUGADOR.eps, opcional (NULL), de hasta 50 caracteres. No modifica datos
     existentes ni afecta a los módulos legados (ninguno selecciona con SELECT *
     ni inserta en JUGADOR sin lista de columnas).
   Cómo aplicarla:
     - Aplicar antes la migración 001.
     - Hacer COPIA DE SEGURIDAD de ClubFutbolDB.
     - Ejecutar este archivo completo en SSMS sobre ClubFutbolDB.
     - Es idempotente: puede ejecutarse más de una vez sin error.
   ========================================================================================= */
USE ClubFutbolDB;
GO

IF COL_LENGTH('JUGADOR', 'eps') IS NULL
    ALTER TABLE JUGADOR ADD eps VARCHAR(50) NULL;
GO

/* Verificación ------------------------------------------------------------------------- */
SELECT 'JUGADOR.eps' AS verificacion,
       CASE WHEN COL_LENGTH('JUGADOR', 'eps') IS NOT NULL THEN 'OK' ELSE 'FALTA' END AS resultado;
GO
