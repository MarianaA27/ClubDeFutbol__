"""
Acceso a datos LEGADO.

Se conserva para los módulos que aún NO se migran (plantillas, sesiones,
finanzas, dashboard). Su único cambio respecto al sistema original es que la
cadena de conexión ya no está fijada en el código: se obtiene de
``paladinesfc.infraestructura.config`` (ver ADR-0002 y README).

Los módulos del MVP (Jugadores, Jugador–Tutor, Tutores, Profesores) NO deben
usar este archivo: usan ``paladinesfc.infraestructura.unidad_trabajo``.
"""
import pyodbc

from paladinesfc.infraestructura.config import cadena_conexion


def obtener_conexion():
    return pyodbc.connect(cadena_conexion())


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
