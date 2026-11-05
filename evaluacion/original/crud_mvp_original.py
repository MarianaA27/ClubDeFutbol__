"""
Copia FIEL del código original del MVP (carpeta "Trabajo final": crud.py y db.py).

Se usa SOLO para medir el "antes" en evaluacion/medir_escenarios.py. Las funciones se
copiaron sin cambios; lo único distinto es ``obtener_conexion()``: en el original la
cadena estaba fijada en el código (``SERVER=GIANY``) y aquí apunta a la base de
medición que se le indique con ``configurar()``.

No lo importa la aplicación. El código legado que sí usa la aplicación está en
src/paladinesfc/legado/.
"""
import pyodbc

_CADENA = None


def configurar(cadena_conexion: str) -> None:
    global _CADENA
    _CADENA = cadena_conexion


def obtener_conexion():
    return pyodbc.connect(_CADENA)


# ─── Copiado sin cambios de db.py original ───────────────────────────────────

def ejecutar_query(query, params=None, fetch=False):
    conn   = obtener_conexion()
    cursor = conn.cursor()
    try:

        if params is not None:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if fetch:
            cols = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return cols, rows

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ─── Copiado sin cambios de crud.py original ─────────────────────────────────

def get_jugadores_con_tutor():
    q = """
    SELECT
        j.id_jugador,
        j.nombres + ' ' + j.apellidos              AS jugador,
        j.documento,
        j.estado,
        j.fecha_nacimiento,
        j.talla_uniforme,
        ISNULL(t.nombres + ' ' + t.apellidos, 'Sin tutor') AS tutor_principal,
        ISNULL(jt.parentesco, '-')                          AS parentesco,
        ISNULL(t.telefono, '-')                             AS telefono_tutor
    FROM JUGADOR j
    LEFT JOIN JUGADOR_TUTOR jt
        ON j.id_jugador = jt.id_jugador AND jt.acudiente_principal = 1
    LEFT JOIN TUTOR t
        ON jt.id_tutor = t.id_tutor
    ORDER BY j.apellidos, j.nombres
    """
    return ejecutar_query(q, fetch=True)


def get_tutores():
    q = """
    SELECT id_tutor, nombres, apellidos, documento,
           telefono, email, direccion
    FROM TUTOR
    ORDER BY apellidos, nombres
    """
    return ejecutar_query(q, fetch=True)


def get_profesores():
    q = """
    SELECT id_profesor, nombres, apellidos, documento,
           telefono, email, especialidad, estado, fecha_ingreso
    FROM PROFESOR
    ORDER BY apellidos, nombres
    """
    return ejecutar_query(q, fetch=True)


def set_acudiente_principal(id_jugador, id_tutor):
    ejecutar_query(
        "UPDATE JUGADOR_TUTOR SET acudiente_principal = 0 WHERE id_jugador = ?",
        (int(id_jugador),)
    )
    ejecutar_query(
        "UPDATE JUGADOR_TUTOR SET acudiente_principal = 1 "
        "WHERE id_jugador = ? AND id_tutor = ?",
        (int(id_jugador), int(id_tutor))
    )


def delete_jugador(id_j):
    """
    Borrado físico completo mediante SP_EliminarJugador.
    El SP elimina en cascada: SESION_JUGADOR → PLANTILLA_JUGADOR →
    MOROSIDAD → PAGO → JUGADOR_TUTOR → JUGADOR.

    Si el jugador tiene plantillas activas, se bloquea antes de llamar al SP
    para dar un mensaje claro al usuario.
    """
    id_j = int(id_j)

    _, rows = ejecutar_query(
        "SELECT COUNT(*) FROM PLANTILLA_JUGADOR WHERE id_jugador = ? AND estado = 'activo'",
        (id_j,), fetch=True
    )
    if rows[0][0] > 0:
        raise ValueError(
            "El jugador tiene plantillas activas. "
            "Retíralo de todas las plantillas antes de eliminarlo."
        )

    ejecutar_query("EXEC SP_EliminarJugador ?", (id_j,))


def delete_profesor(id_p):
    """
    Borrado físico completo mediante SP_EliminarProfesor.
    El SP elimina en cascada: SESION_JUGADOR → SESION →
    PLANTILLA_PROFESOR → PROFESOR.
    """
    ejecutar_query("EXEC SP_EliminarProfesor ?", (int(id_p),))
