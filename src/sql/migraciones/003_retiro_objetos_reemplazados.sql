/* =========================================================================================
   MIGRACIÓN 003 — Retiro de los objetos de base de datos que reemplazó el MVP
   Re-arquitectura PaladinesFC · Entrega final · ADR-0004 y ADR-0005, issue #19
   -----------------------------------------------------------------------------------------
   Qué hace:
     Elimina los procedimientos y vistas que solo usaban las funciones del MVP retiradas
     de legado/crud.py. Desde la re-arquitectura, toda lectura y escritura de Jugadores,
     Jugador–Tutor, Tutores y Profesores pasa por los repositorios (SQL parametrizado),
     así que estos objetos eran una segunda vía de escritura sin uso (problema P4):
       - SP_InsertarJugadorTutor, SP_ActualizarJugador, SP_InsertarTutor, SP_InsertarProfesor
       - VW_DetalleJugador, VW_DetalleTutor, VW_DetalleProfesor (estas dos mostraban las
         columnas corridas, problema P1)
     Ningún módulo legado los usa (verificado sobre legado/crud.py y presentacion/app.py).
   Cómo aplicarla:
     - Aplicar antes las migraciones 001 y 002.
     - Hacer COPIA DE SEGURIDAD de ClubFutbolDB.
     - Ejecutar este archivo completo en SSMS sobre ClubFutbolDB. Es idempotente.
   ========================================================================================= */
USE ClubFutbolDB;
GO

DROP PROCEDURE IF EXISTS SP_InsertarJugadorTutor;
DROP PROCEDURE IF EXISTS SP_ActualizarJugador;
DROP PROCEDURE IF EXISTS SP_InsertarTutor;
DROP PROCEDURE IF EXISTS SP_InsertarProfesor;
GO

DROP VIEW IF EXISTS VW_DetalleJugador;
DROP VIEW IF EXISTS VW_DetalleTutor;
DROP VIEW IF EXISTS VW_DetalleProfesor;
GO

/* Verificación ------------------------------------------------------------------------- */
SELECT 'Objetos del MVP reemplazados que siguen existiendo' AS verificacion,
       CAST(COUNT(*) AS VARCHAR(10)) AS resultado
FROM sys.objects
WHERE name IN ('SP_InsertarJugadorTutor', 'SP_ActualizarJugador', 'SP_InsertarTutor',
               'SP_InsertarProfesor', 'VW_DetalleJugador', 'VW_DetalleTutor', 'VW_DetalleProfesor');
GO
