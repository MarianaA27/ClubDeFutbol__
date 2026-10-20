CREATE DATABASE ClubFutbolDB
GO
USE ClubFutbolDB
GO



CREATE TABLE TUTOR (
    id_tutor   INT PRIMARY KEY IDENTITY(1,1),
    nombres    VARCHAR(50)  NOT NULL,
    apellidos  VARCHAR(50)  NOT NULL,
    documento  VARCHAR(20)  NOT NULL UNIQUE,
    telefono   VARCHAR(20)  NOT NULL UNIQUE,
    email      VARCHAR(100) NOT NULL,
    direccion  VARCHAR(100) NOT NULL
);
GO

CREATE TABLE JUGADOR (
    id_jugador       INT PRIMARY KEY IDENTITY(1,1),
    nombres          VARCHAR(50)  NOT NULL,
    apellidos        VARCHAR(50)  NOT NULL,
    documento        VARCHAR(20)  NOT NULL UNIQUE,
    fecha_nacimiento DATE         NOT NULL,
    numero_preferido INT,
    talla_uniforme   VARCHAR(20)  NOT NULL,
    estado           VARCHAR(20)  NOT NULL CHECK (estado IN ('activo', 'inactivo', 'lesionado')),
    fecha_ingreso    DATE         NOT NULL,
    observaciones    VARCHAR(100)
);
GO

CREATE TABLE PROFESOR (
    id_profesor  INT PRIMARY KEY IDENTITY(1,1),
    nombres      VARCHAR(50)  NOT NULL,
    apellidos    VARCHAR(50)  NOT NULL,
    documento    VARCHAR(20)  NOT NULL UNIQUE,
    telefono     VARCHAR(20)  NOT NULL UNIQUE,
    email        VARCHAR(100) NOT NULL,
    especialidad VARCHAR(20),
    estado       VARCHAR(20)  NOT NULL CHECK (estado IN ('activo', 'inactivo')),
    fecha_ingreso DATE        NOT NULL
);
GO

CREATE TABLE JUGADOR_TUTOR (
    id_jugador_tutor    INT PRIMARY KEY IDENTITY(1,1),
    id_jugador          INT         NOT NULL,
    id_tutor            INT         NOT NULL,
    parentesco          VARCHAR(50) NOT NULL,
    acudiente_principal BIT         NOT NULL DEFAULT 0,
    FOREIGN KEY (id_jugador) REFERENCES JUGADOR(id_jugador),
    FOREIGN KEY (id_tutor)   REFERENCES TUTOR(id_tutor)
);
GO

CREATE TABLE CONCEPTO_PAGO (
    id_concepto     INT PRIMARY KEY IDENTITY(1,1),
    nombre_concepto VARCHAR(50)    NOT NULL,
    descripcion     VARCHAR(100),
    valor_base      DECIMAL(10,2)  NOT NULL,
    eliminable      BIT            NOT NULL,
    estado          VARCHAR(20)    NOT NULL CHECK (estado IN ('activo', 'inactivo'))
);
GO

CREATE TABLE MOROSIDAD (
    id_morosidad      INT PRIMARY KEY IDENTITY(1,1),
    id_jugador        INT           NOT NULL,
    fecha_vencimiento DATE          NOT NULL,
    recargo           DECIMAL(10,2) DEFAULT 0,
    fecha_recargo     DATE,
    motivo_recargo    VARCHAR(150),
    estado_mora       VARCHAR(20)   NOT NULL CHECK (estado_mora IN ('pendiente', 'pagada', 'en mora')),
    observaciones     VARCHAR(100),
    FOREIGN KEY (id_jugador) REFERENCES JUGADOR(id_jugador)
);
GO

CREATE TABLE PAGO (
    id_pago          INT PRIMARY KEY IDENTITY(1,1),
    id_jugador       INT           NOT NULL,
    id_concepto      INT           NOT NULL,
    id_morosidad     INT           NULL,
    fecha_pago       DATE          NOT NULL,
    fecha_expiracion DATE,
    valor_pagado     DECIMAL(10,2) NOT NULL,
    metodo_pago      VARCHAR(50)   NOT NULL,
    observaciones    VARCHAR(100),
    FOREIGN KEY (id_jugador)   REFERENCES JUGADOR(id_jugador),
    FOREIGN KEY (id_concepto)  REFERENCES CONCEPTO_PAGO(id_concepto),
    FOREIGN KEY (id_morosidad) REFERENCES MOROSIDAD(id_morosidad)
);
GO

CREATE TABLE CATEGORIA (
    id_categoria     INT PRIMARY KEY IDENTITY(1,1),
    nombre_categoria VARCHAR(50) NOT NULL,
    anio_minimo      INT         NOT NULL,
    anio_maximo      INT         NOT NULL,
    estado           VARCHAR(20) NOT NULL CHECK (estado IN ('activa', 'inactiva')),
    descripcion      VARCHAR(100)
);
GO

CREATE TABLE PLANTILLA (
    id_plantilla     INT PRIMARY KEY IDENTITY(1,1),
    nombre_plantilla VARCHAR(50) NOT NULL,
    id_categoria     INT         NOT NULL,
    fecha_creacion   DATE        NOT NULL,
    temporada        VARCHAR(20),
    estado           VARCHAR(20) NOT NULL CHECK (estado IN ('activa', 'inactiva')),
    FOREIGN KEY (id_categoria) REFERENCES CATEGORIA(id_categoria)
);
GO

CREATE TABLE PLANTILLA_JUGADOR (
    id_plantilla_jugador INT PRIMARY KEY IDENTITY(1,1),
    id_plantilla         INT         NOT NULL,
    id_jugador           INT         NOT NULL,
    fecha_asignacion     DATE        NOT NULL,
    estado               VARCHAR(20) NOT NULL CHECK (estado IN ('activo', 'inactivo')),
    FOREIGN KEY (id_plantilla) REFERENCES PLANTILLA(id_plantilla),
    FOREIGN KEY (id_jugador)   REFERENCES JUGADOR(id_jugador)
);
GO

CREATE TABLE PLANTILLA_PROFESOR (
    id_plantilla_profesor INT PRIMARY KEY IDENTITY(1,1),
    id_plantilla          INT         NOT NULL,
    id_profesor           INT         NOT NULL,
    fecha_asignacion      DATE        NOT NULL,
    cargo                 VARCHAR(20),
    FOREIGN KEY (id_plantilla) REFERENCES PLANTILLA(id_plantilla),
    FOREIGN KEY (id_profesor)  REFERENCES PROFESOR(id_profesor)
);
GO

CREATE TABLE CANCHA (
    id_cancha       INT PRIMARY KEY IDENTITY(1,1),
    nombre_cancha   VARCHAR(50)  NOT NULL,
    direccion       VARCHAR(100),
    tipo_superficie VARCHAR(50),
    capacidad       INT,
    estado          VARCHAR(20)  NOT NULL CHECK (estado IN ('disponible', 'no disponible', 'mantenimiento'))
);
GO

CREATE TABLE SESION (
    id_sesion    INT PRIMARY KEY IDENTITY(1,1),
    fecha_sesion DATETIME    NOT NULL,
    id_profesor  INT         NOT NULL,
    id_cancha    INT         NOT NULL,
    id_categoria INT         NOT NULL,
    id_plantilla INT         NOT NULL,
    observaciones VARCHAR(100),
    tipo_sesion  VARCHAR(50) NOT NULL CHECK (tipo_sesion IN ('Torneo', 'Partido', 'Entrenamiento')),
    estado       VARCHAR(20) NOT NULL CHECK (estado IN ('programada', 'realizada', 'cancelada')),
    marcador     VARCHAR(20),
    resultado    VARCHAR(20),
    FOREIGN KEY (id_categoria) REFERENCES CATEGORIA(id_categoria),
    FOREIGN KEY (id_profesor)  REFERENCES PROFESOR(id_profesor),
    FOREIGN KEY (id_cancha)    REFERENCES CANCHA(id_cancha),
    FOREIGN KEY (id_plantilla) REFERENCES PLANTILLA(id_plantilla)
);
GO

CREATE TABLE SESION_JUGADOR (
    id_sesion_jugador INT PRIMARY KEY IDENTITY(1,1),
    id_sesion         INT         NOT NULL,
    id_jugador        INT         NOT NULL,
    asistencia        BIT         NOT NULL,
    convocado         BIT         NOT NULL,
    numero_camiseta   INT,
    observaciones     VARCHAR(100),
    FOREIGN KEY (id_sesion)  REFERENCES SESION(id_sesion),
    FOREIGN KEY (id_jugador) REFERENCES JUGADOR(id_jugador)
);
GO
    CREATE TABLE PLANTILLA_ALINEACION (
        id_alineacion   INT          PRIMARY KEY IDENTITY(1,1),
        id_plantilla    INT          NOT NULL,
        id_jugador      INT          NOT NULL,
        formacion       VARCHAR(20)  NOT NULL,
        slot_index      INT          NOT NULL,
        posicion        VARCHAR(60)  NOT NULL,
        FOREIGN KEY (id_plantilla) REFERENCES PLANTILLA(id_plantilla),
        FOREIGN KEY (id_jugador)   REFERENCES JUGADOR(id_jugador),
        CONSTRAINT UQ_Alineacion_Slot UNIQUE (id_plantilla, slot_index)
    );
GO
/* =========================================================================================
   SECCIÓN 1: GESTIÓN DE USUARIOS (Niños, Tutores y Profesores)
   ========================================================================================= */

-- SP_InsertarJugadorTutor
CREATE PROCEDURE SP_InsertarJugadorTutor
    @nombres             VARCHAR(50),
    @apellidos           VARCHAR(50),
    @documento           VARCHAR(20),
    @fecha_nacimiento    DATE,
    @numero_preferido    INT,
    @talla_uniforme      VARCHAR(20),
    @fecha_ingreso       DATE,
    @observaciones       VARCHAR(100),
    @id_tutor            INT,
    @parentesco          VARCHAR(50),
    @acudiente_principal BIT
AS
BEGIN
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @id_jugador INT;

        INSERT INTO JUGADOR (nombres, apellidos, documento, fecha_nacimiento, numero_preferido, talla_uniforme, estado, fecha_ingreso, observaciones)
        VALUES (@nombres, @apellidos, @documento, @fecha_nacimiento, @numero_preferido, @talla_uniforme, 'activo', @fecha_ingreso, @observaciones);

        SET @id_jugador = SCOPE_IDENTITY();

        INSERT INTO JUGADOR_TUTOR (id_jugador, id_tutor, parentesco, acudiente_principal)
        VALUES (@id_jugador, @id_tutor, @parentesco, @acudiente_principal);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

-- SP_ActualizarJugador
CREATE PROCEDURE SP_ActualizarJugador
    @id_jugador      INT,
    @nombres         VARCHAR(50),
    @apellidos       VARCHAR(50),
    @numero_preferido INT,
    @talla_uniforme  VARCHAR(20),
    @estado          VARCHAR(20),
    @observaciones   VARCHAR(100)
AS
BEGIN
    IF @estado NOT IN ('activo', 'inactivo', 'lesionado')
    BEGIN
        RAISERROR('El estado debe ser activo, inactivo o lesionado.', 16, 1);
        RETURN;
    END

    UPDATE JUGADOR
    SET nombres          = @nombres,
        apellidos        = @apellidos,
        numero_preferido = @numero_preferido,
        talla_uniforme   = @talla_uniforme,
        estado           = @estado,
        observaciones    = @observaciones
    WHERE id_jugador = @id_jugador;
END;
GO

-- SP_EliminarJugador (Borrado FÍSICO con cascada manual)
CREATE PROCEDURE SP_EliminarJugador
    @id_jugador INT
AS
BEGIN
    BEGIN TRY
        BEGIN TRANSACTION;

        DELETE FROM SESION_JUGADOR    WHERE id_jugador = @id_jugador;
        DELETE FROM PLANTILLA_JUGADOR WHERE id_jugador = @id_jugador;
        DELETE FROM MOROSIDAD         WHERE id_jugador = @id_jugador;
        DELETE FROM PAGO              WHERE id_jugador = @id_jugador;
        DELETE FROM JUGADOR_TUTOR     WHERE id_jugador = @id_jugador;
        DELETE FROM JUGADOR           WHERE id_jugador = @id_jugador;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

-- SP_InsertarTutor
CREATE PROCEDURE SP_InsertarTutor
    @nombres   VARCHAR(50),
    @apellidos VARCHAR(50),
    @documento VARCHAR(20),
    @telefono  VARCHAR(20),
    @email     VARCHAR(100),
    @direccion VARCHAR(100)
AS
BEGIN
    INSERT INTO TUTOR (nombres, apellidos, documento, telefono, email, direccion)
    VALUES (@nombres, @apellidos, @documento, @telefono, @email, @direccion);
END;
GO

-- SP_EliminarTutor (Borrado FÍSICO)
CREATE PROCEDURE SP_EliminarTutor
    @id_tutor INT
AS
BEGIN
    IF EXISTS (SELECT 1 FROM JUGADOR_TUTOR WHERE id_tutor = @id_tutor)
    BEGIN
        RAISERROR('No se puede eliminar el tutor porque tiene jugadores a cargo.', 16, 1);
        RETURN;
    END

    DELETE FROM TUTOR WHERE id_tutor = @id_tutor;
END;
GO

-- SP_InsertarProfesor
CREATE PROCEDURE SP_InsertarProfesor
    @nombres      VARCHAR(50),
    @apellidos    VARCHAR(50),
    @documento    VARCHAR(20),
    @telefono     VARCHAR(20),
    @email        VARCHAR(100),
    @especialidad VARCHAR(20),
    @fecha_ingreso DATE
AS
BEGIN
    INSERT INTO PROFESOR (nombres, apellidos, documento, telefono, email, especialidad, estado, fecha_ingreso)
    VALUES (@nombres, @apellidos, @documento, @telefono, @email, @especialidad, 'activo', @fecha_ingreso);
END;
GO

-- SP_ActualizarProfesor
CREATE PROCEDURE SP_ActualizarProfesor
    @id_profesor  INT,
    @nombres      VARCHAR(50),
    @apellidos    VARCHAR(50),
    @telefono     VARCHAR(20),
    @email        VARCHAR(100),
    @especialidad VARCHAR(20),
    @estado       VARCHAR(20)
AS
BEGIN
    UPDATE PROFESOR
    SET nombres      = @nombres,
        apellidos    = @apellidos,
        telefono     = @telefono,
        email        = @email,
        especialidad = @especialidad,
        estado       = @estado
    WHERE id_profesor = @id_profesor;
END;
GO

-- SP_EliminarProfesor (Borrado FÍSICO con cascada manual)
CREATE PROCEDURE SP_EliminarProfesor
    @id_profesor INT
AS
BEGIN
    BEGIN TRY
        BEGIN TRANSACTION;

        DELETE SJ
        FROM SESION_JUGADOR SJ
        INNER JOIN SESION S ON SJ.id_sesion = S.id_sesion
        WHERE S.id_profesor = @id_profesor;

        DELETE FROM SESION             WHERE id_profesor = @id_profesor;
        DELETE FROM PLANTILLA_PROFESOR WHERE id_profesor = @id_profesor;
        DELETE FROM PROFESOR           WHERE id_profesor = @id_profesor;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO


/* =========================================================================================
   SECCIÓN 2: VISUALIZACIÓN DE DATOS (Vistas)
   ========================================================================================= */

-- VW_DetalleJugador
CREATE VIEW VW_DetalleJugador AS
SELECT
    J.id_jugador,
    J.nombres                      AS Jugador_Nombres,
    J.apellidos                    AS Jugador_Apellidos,
    J.documento,
    J.estado,
    T.nombres + ' ' + T.apellidos  AS Tutor_Nombre,
    T.telefono                     AS Tutor_Telefono,
    JT.parentesco,
    C.nombre_categoria             AS Categoria,
    P.nombre_plantilla             AS Plantilla
FROM JUGADOR J
LEFT JOIN JUGADOR_TUTOR    JT ON J.id_jugador   = JT.id_jugador
LEFT JOIN TUTOR             T ON JT.id_tutor     = T.id_tutor
LEFT JOIN PLANTILLA_JUGADOR PJ ON J.id_jugador   = PJ.id_jugador AND PJ.estado = 'activo'
LEFT JOIN PLANTILLA         P  ON PJ.id_plantilla = P.id_plantilla
LEFT JOIN CATEGORIA         C  ON P.id_categoria  = C.id_categoria;
GO

-- VW_DetalleTutor
CREATE VIEW VW_DetalleTutor AS
SELECT
    T.id_tutor,
    T.nombres + ' ' + T.apellidos AS Tutor_Nombre,
    T.telefono,
    T.email,
    J.nombres + ' ' + J.apellidos AS Jugador_ACargo,
    JT.parentesco
FROM TUTOR T
LEFT JOIN JUGADOR_TUTOR JT ON T.id_tutor   = JT.id_tutor
LEFT JOIN JUGADOR        J ON JT.id_jugador = J.id_jugador;
GO

-- VW_DetalleProfesor
CREATE VIEW VW_DetalleProfesor AS
SELECT
    PR.id_profesor,
    PR.nombres + ' ' + PR.apellidos AS Profesor_Nombre,
    PR.especialidad,
    PR.estado,
    PL.nombre_plantilla             AS Equipo_A_Cargo,
    PP.cargo
FROM PROFESOR PR
LEFT JOIN PLANTILLA_PROFESOR PP ON PR.id_profesor  = PP.id_profesor
LEFT JOIN PLANTILLA          PL ON PP.id_plantilla = PL.id_plantilla;
GO


/* =========================================================================================
   SECCIÓN 3: GESTIÓN DEPORTIVA
   ========================================================================================= */

-- SP_InsertarCancha
CREATE PROCEDURE SP_InsertarCancha
    @nombre_cancha   VARCHAR(50),
    @direccion       VARCHAR(100),
    @tipo_superficie VARCHAR(50),
    @capacidad       INT
AS
BEGIN
    INSERT INTO CANCHA (nombre_cancha, direccion, tipo_superficie, capacidad, estado)
    VALUES (@nombre_cancha, @direccion, @tipo_superficie, @capacidad, 'disponible');
END;
GO

-- SP_InsertarCategoria
CREATE PROCEDURE SP_InsertarCategoria
    @nombre_categoria VARCHAR(50),
    @anio_minimo      INT,
    @anio_maximo      INT,
    @descripcion      VARCHAR(100)
AS
BEGIN
    INSERT INTO CATEGORIA (nombre_categoria, anio_minimo, anio_maximo, estado, descripcion)
    VALUES (@nombre_categoria, @anio_minimo, @anio_maximo, 'activa', @descripcion);
END;
GO

-- SP_CrearPlantilla
CREATE PROCEDURE SP_CrearPlantilla
    @nombre_plantilla VARCHAR(50),
    @id_categoria     INT,
    @fecha_creacion   DATE,
    @temporada        VARCHAR(20)
AS
BEGIN
    INSERT INTO PLANTILLA (nombre_plantilla, id_categoria, fecha_creacion, temporada, estado)
    VALUES (@nombre_plantilla, @id_categoria, @fecha_creacion, @temporada, 'activa');
END;
GO

-- SP_EliminarPlantilla (Borrado FÍSICO con cascada manual)
CREATE PROCEDURE SP_EliminarPlantilla
    @id_plantilla INT
AS
BEGIN
    BEGIN TRY
        BEGIN TRANSACTION;

        -- 1. Eliminar asistencias de sesiones de esta plantilla
        DELETE SJ
        FROM SESION_JUGADOR SJ
        INNER JOIN SESION S ON SJ.id_sesion = S.id_sesion
        WHERE S.id_plantilla = @id_plantilla;

        -- 2. Eliminar sesiones de esta plantilla
        DELETE FROM SESION WHERE id_plantilla = @id_plantilla;

        -- 3. Desvincular jugadores de la plantilla
        DELETE FROM PLANTILLA_JUGADOR WHERE id_plantilla = @id_plantilla;

        -- 4. Desvincular profesores de la plantilla
        DELETE FROM PLANTILLA_PROFESOR WHERE id_plantilla = @id_plantilla;

        -- 5. Eliminar la plantilla
        DELETE FROM PLANTILLA WHERE id_plantilla = @id_plantilla;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

-- FN_FiltrarJugadoresParaPlantilla
CREATE FUNCTION FN_FiltrarJugadoresParaPlantilla (@id_categoria INT, @filtro_texto VARCHAR(50) = NULL)
RETURNS TABLE
AS
RETURN (
    SELECT J.id_jugador, J.nombres, J.apellidos, J.documento, J.fecha_nacimiento
    FROM JUGADOR J
    INNER JOIN CATEGORIA C ON C.id_categoria = @id_categoria
    WHERE J.estado = 'activo'
      AND YEAR(J.fecha_nacimiento) BETWEEN C.anio_minimo AND C.anio_maximo
      AND (@filtro_texto IS NULL
           OR J.nombres   LIKE '%' + @filtro_texto + '%'
           OR J.documento LIKE '%' + @filtro_texto + '%')
);
GO

-- SP_AsignarJugadorPlantilla
CREATE PROCEDURE SP_AsignarJugadorPlantilla
    @id_plantilla    INT,
    @id_jugador      INT,
    @fecha_asignacion DATE
AS
BEGIN
    INSERT INTO PLANTILLA_JUGADOR (id_plantilla, id_jugador, fecha_asignacion, estado)
    VALUES (@id_plantilla, @id_jugador, @fecha_asignacion, 'activo');
END;
GO

-- SP_AsignarProfesorPlantilla
CREATE PROCEDURE SP_AsignarProfesorPlantilla
    @id_plantilla     INT,
    @id_profesor      INT,
    @fecha_asignacion DATE,
    @cargo            VARCHAR(20)
AS
BEGIN
    INSERT INTO PLANTILLA_PROFESOR (id_plantilla, id_profesor, fecha_asignacion, cargo)
    VALUES (@id_plantilla, @id_profesor, @fecha_asignacion, @cargo);
END;
GO

-- SP_CrearSesion
CREATE PROCEDURE SP_CrearSesion
    @fecha_sesion  DATETIME,
    @id_profesor   INT,
    @id_cancha     INT,
    @id_categoria  INT,
    @id_plantilla  INT,
    @tipo_sesion   VARCHAR(50),
    @observaciones VARCHAR(100)
AS
BEGIN
    INSERT INTO SESION (fecha_sesion, id_profesor, id_cancha, id_categoria, id_plantilla, observaciones, tipo_sesion, estado)
    VALUES (@fecha_sesion, @id_profesor, @id_cancha, @id_categoria, @id_plantilla, @observaciones, @tipo_sesion, 'programada');

    SELECT SCOPE_IDENTITY() AS id_sesion;
END;
GO

-- SP_RegistrarAsistencia
CREATE PROCEDURE SP_RegistrarAsistencia
    @id_sesion      INT,
    @id_jugador     INT,
    @asistencia     BIT,
    @convocado      BIT,
    @numero_camiseta INT = NULL
AS
BEGIN
    INSERT INTO SESION_JUGADOR (id_sesion, id_jugador, asistencia, convocado, numero_camiseta)
    VALUES (@id_sesion, @id_jugador, @asistencia, @convocado, @numero_camiseta);
END;
GO

-- SP_FiltrarSesiones
CREATE PROCEDURE SP_FiltrarSesiones
    @id_categoria INT         = NULL,
    @id_plantilla INT         = NULL,
    @tipo_sesion  VARCHAR(50) = NULL
AS
BEGIN
    SELECT
        S.id_sesion,
        S.fecha_sesion,
        S.tipo_sesion,
        C.nombre_categoria,
        CA.nombre_cancha,
        P.nombre_plantilla,
        S.estado,
        S.marcador,
        S.resultado
    FROM SESION S
    INNER JOIN CATEGORIA C  ON S.id_categoria = C.id_categoria
    INNER JOIN CANCHA    CA ON S.id_cancha    = CA.id_cancha
    LEFT  JOIN PLANTILLA P  ON S.id_plantilla = P.id_plantilla
    WHERE (@id_categoria IS NULL OR S.id_categoria = @id_categoria)
      AND (@id_plantilla IS NULL OR S.id_plantilla = @id_plantilla)
      AND (@tipo_sesion  IS NULL OR S.tipo_sesion  = @tipo_sesion)
    ORDER BY S.fecha_sesion DESC;
END;
GO



--   SECCIÓN 4: PAGOS Y MOROSIDAD (Finanzas)


-- SP_InsertarConceptoPago
CREATE PROCEDURE SP_InsertarConceptoPago
    @nombre_concepto VARCHAR(50),
    @descripcion     VARCHAR(100),
    @valor_base      DECIMAL(10,2),
    @eliminable      BIT
AS
BEGIN
    INSERT INTO CONCEPTO_PAGO (nombre_concepto, descripcion, valor_base, eliminable, estado)
    VALUES (@nombre_concepto, @descripcion, @valor_base, @eliminable, 'activo');
END;
GO

-- SP_EliminarConceptoPago (Borrado FÍSICO)
CREATE PROCEDURE SP_EliminarConceptoPago
    @id_concepto INT
AS
BEGIN
    IF EXISTS (SELECT 1 FROM CONCEPTO_PAGO WHERE id_concepto = @id_concepto AND eliminable = 0)
    BEGIN
        RAISERROR('Este concepto de pago está protegido y no puede ser eliminado.', 16, 1);
        RETURN;
    END

    IF EXISTS (SELECT 1 FROM PAGO WHERE id_concepto = @id_concepto)
    BEGIN
        RAISERROR('No se puede eliminar el concepto porque tiene pagos registrados.', 16, 1);
        RETURN;
    END

    DELETE FROM CONCEPTO_PAGO WHERE id_concepto = @id_concepto;
END;
GO

-- FN_BuscarJugadorParaPago
CREATE FUNCTION FN_BuscarJugadorParaPago (@documento VARCHAR(20))
RETURNS TABLE
AS
RETURN (
    SELECT id_jugador, nombres + ' ' + apellidos AS Nombre_Completo, documento, estado
    FROM JUGADOR
    WHERE documento LIKE '%' + @documento + '%' AND estado = 'activo'
);
GO

-- SP_RegistrarPago
CREATE PROCEDURE SP_RegistrarPago
    @id_jugador      INT,
    @id_concepto     INT,
    @id_morosidad    INT           = NULL,
    @fecha_pago      DATE,
    @fecha_expiracion DATE         = NULL,
    @valor_pagado    DECIMAL(10,2),
    @metodo_pago     VARCHAR(50),
    @observaciones   VARCHAR(100)
AS
BEGIN
    BEGIN TRY
        BEGIN TRANSACTION;

        INSERT INTO PAGO (id_jugador, id_concepto, id_morosidad, fecha_pago, fecha_expiracion, valor_pagado, metodo_pago, observaciones)
        VALUES (@id_jugador, @id_concepto, @id_morosidad, @fecha_pago, @fecha_expiracion, @valor_pagado, @metodo_pago, @observaciones);

        IF @id_morosidad IS NOT NULL
        BEGIN
            UPDATE MOROSIDAD SET estado_mora = 'pagada' WHERE id_morosidad = @id_morosidad;
        END

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

-- TR_NuevoJugador_Morosidad
CREATE TRIGGER TR_NuevoJugador_Morosidad
ON JUGADOR
AFTER INSERT
AS
BEGIN
    INSERT INTO MOROSIDAD (id_jugador, fecha_vencimiento, estado_mora, observaciones)
    SELECT id_jugador, GETDATE(), 'pendiente', 'Matrícula / Primer mes'
    FROM inserted;
END;
GO

-- SP_ActualizarMorosos
CREATE PROCEDURE SP_ActualizarMorosos
AS
BEGIN
    INSERT INTO MOROSIDAD (id_jugador, fecha_vencimiento, estado_mora, observaciones)
    SELECT J.id_jugador, GETDATE(), 'en mora', 'Vencimiento automático'
    FROM JUGADOR J
    WHERE J.estado = 'activo'
      AND NOT EXISTS (
          SELECT 1 FROM MOROSIDAD M
          WHERE M.id_jugador = J.id_jugador
            AND M.estado_mora IN ('en mora', 'pendiente')
      )
      AND EXISTS (
          SELECT 1 FROM PAGO P
          INNER JOIN CONCEPTO_PAGO CP ON P.id_concepto = CP.id_concepto
          WHERE P.id_jugador = J.id_jugador
            AND CP.nombre_concepto LIKE '%Mensualidad%'
          HAVING MAX(P.fecha_expiracion) < GETDATE()
      );
END;
GO

-- VW_ListaMorosos
CREATE VIEW VW_ListaMorosos AS
SELECT
    M.id_morosidad,
    J.nombres + ' ' + J.apellidos AS Jugador,
    J.documento,
    M.fecha_vencimiento,
    M.recargo,
    M.estado_mora,
    M.observaciones
FROM MOROSIDAD M
INNER JOIN JUGADOR J ON M.id_jugador = J.id_jugador
WHERE M.estado_mora IN ('en mora', 'pendiente');
GO

-- SP_AgregarRecargoMora
CREATE PROCEDURE SP_AgregarRecargoMora
    @id_morosidad  INT,
    @valor_recargo DECIMAL(10,2),
    @motivo        VARCHAR(150)
AS
BEGIN
    UPDATE MOROSIDAD
    SET recargo        = @valor_recargo,
        motivo_recargo = @motivo,
        fecha_recargo  = GETDATE()
    WHERE id_morosidad = @id_morosidad;
END;
GO


   --SECCIÓN 5: DASHBOARD Y ANALÍTICA


-- SP_ObtenerDatosDashboard
CREATE PROCEDURE SP_ObtenerDatosDashboard
AS
BEGIN
    DECLARE @Ingresos_Mes       DECIMAL(10,2);
    DECLARE @Jugadores_Activos  INT;
    DECLARE @Profesores_Activos INT;
    DECLARE @Sesiones_Mes       INT;
    DECLARE @Total_Morosos      INT;

    SELECT @Ingresos_Mes = ISNULL(SUM(valor_pagado), 0)
    FROM PAGO
    WHERE MONTH(fecha_pago) = MONTH(GETDATE())
      AND YEAR(fecha_pago)  = YEAR(GETDATE());

    SELECT @Jugadores_Activos  = COUNT(*) FROM JUGADOR  WHERE estado = 'activo';
    SELECT @Profesores_Activos = COUNT(*) FROM PROFESOR WHERE estado = 'activo';

    SELECT @Sesiones_Mes = COUNT(*) FROM SESION
    WHERE MONTH(fecha_sesion) = MONTH(GETDATE())
      AND YEAR(fecha_sesion)  = YEAR(GETDATE());

    SELECT @Total_Morosos = COUNT(*) FROM MOROSIDAD WHERE estado_mora = 'en mora';

    -- KPIs
    SELECT
        @Ingresos_Mes       AS Ingresos_Mes,
        @Jugadores_Activos  AS Jugadores_Activos,
        @Profesores_Activos AS Profesores_Activos,
        @Sesiones_Mes       AS Sesiones_Mes,
        @Total_Morosos      AS Total_Morosos;

    -- Histórico de ingresos por mes
    SELECT
        YEAR(fecha_pago)  AS Anio,
        MONTH(fecha_pago) AS Mes,
        SUM(valor_pagado) AS Total_Ingresos
    FROM PAGO
    GROUP BY YEAR(fecha_pago), MONTH(fecha_pago)
    ORDER BY Anio DESC, Mes DESC;
END;
GO



-- 1. Añadir columna tipo con valor por defecto 'titular'
ALTER TABLE PLANTILLA_JUGADOR
    ADD tipo VARCHAR(10) NOT NULL
        CONSTRAINT DF_PJ_tipo DEFAULT 'titular';

-- 2. Restricción CHECK para garantizar integridad
ALTER TABLE PLANTILLA_JUGADOR
    ADD CONSTRAINT CK_PJ_tipo CHECK (tipo IN ('titular', 'banca'));

-- 3. Verificar que quedó bien
SELECT COLUMN_NAME, DATA_TYPE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'PLANTILLA_JUGADOR' AND COLUMN_NAME = 'tipo';

-- ============================================================
-- ACTUALIZAR SP_AsignarJugadorPlantilla para aceptar @tipo
-- (Ajustar si el SP existente no admite el 4.° parámetro)
-- ===========================================================

CREATE OR ALTER PROCEDURE SP_AsignarJugadorPlantilla
    @id_plantilla   INT,
    @id_jugador     INT,
    @fecha          DATE,
    @tipo           VARCHAR(10) = 'titular'   -- valor por defecto
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO PLANTILLA_JUGADOR
        (id_plantilla, id_jugador, fecha_asignacion, estado, tipo)
    VALUES
        (@id_plantilla, @id_jugador, @fecha, 'activo', @tipo);
END;


IF OBJECT_ID('ALINEACION', 'U') IS NOT NULL
    DROP TABLE ALINEACION;
GO

-- Actualizar SP_EliminarPlantilla para incluir PLANTILLA_ALINEACION
CREATE OR ALTER PROCEDURE SP_EliminarPlantilla
    @id_plantilla INT
AS
BEGIN
    BEGIN TRY
        BEGIN TRANSACTION;

        -- 1. Asistencias de sesiones de esta plantilla
        DELETE SJ
        FROM SESION_JUGADOR SJ
        INNER JOIN SESION S ON SJ.id_sesion = S.id_sesion
        WHERE S.id_plantilla = @id_plantilla;

        -- 2. Sesiones de esta plantilla
        DELETE FROM SESION WHERE id_plantilla = @id_plantilla;

        -- 3. Alineación guardada
        DELETE FROM PLANTILLA_ALINEACION WHERE id_plantilla = @id_plantilla;

        -- 4. Jugadores y profesores vinculados
        DELETE FROM PLANTILLA_JUGADOR  WHERE id_plantilla = @id_plantilla;
        DELETE FROM PLANTILLA_PROFESOR WHERE id_plantilla = @id_plantilla;

        -- 5. La plantilla en sí
        DELETE FROM PLANTILLA WHERE id_plantilla = @id_plantilla;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO