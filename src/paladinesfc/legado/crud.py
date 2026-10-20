from paladinesfc.legado.db import ejecutar_query
import re
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES DE VALIDACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def _validar_fecha(valor, campo="Fecha"):
    if not valor or not str(valor).strip():
        raise ValueError(f"'{campo}' es obligatorio.")
    try:
        datetime.strptime(str(valor).strip(), "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"'{campo}' debe tener formato AAAA-MM-DD (ej: 2005-03-21).")


def _validar_requerido(valor, campo):
    if not valor or not str(valor).strip():
        raise ValueError(f"El campo '{campo}' es obligatorio.")


def _validar_solo_texto(valor, campo):
    _validar_requerido(valor, campo)
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s\-']+$", valor.strip()):
        raise ValueError(f"'{campo}' solo debe contener letras y espacios.")


def _validar_documento(valor, campo="Documento"):
    _validar_requerido(valor, campo)
    if not re.match(r"^\d{5,15}$", str(valor).strip()):
        raise ValueError(f"'{campo}' debe contener entre 5 y 15 dígitos numéricos.")


def _validar_telefono(valor, campo="Teléfono"):
    if valor and str(valor).strip():
        if not re.match(r"^[+]?\d{7,15}$", str(valor).strip()):
            raise ValueError(f"'{campo}' inválido. Ej: 3001234567 o +573001234567.")


def _validar_email(valor, campo="Email"):
    if valor and str(valor).strip():
        if not re.match(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$", str(valor).strip()):
            raise ValueError(f"'{campo}' no tiene un formato válido (ej: nombre@correo.com).")


def _validar_numero_entero_positivo(valor, campo, obligatorio=False):
    if not valor or not str(valor).strip():
        if obligatorio:
            raise ValueError(f"'{campo}' es obligatorio.")
        return None
    try:
        n = int(str(valor).strip())
        if n <= 0:
            raise ValueError()
        return n
    except ValueError:
        raise ValueError(f"'{campo}' debe ser un número mayor a 0.")


def _validar_decimal_positivo(valor, campo):
    _validar_requerido(valor, campo)
    try:
        n = float(str(valor).strip())
        if n < 0:
            raise ValueError()
        return n
    except ValueError:
        raise ValueError(f"'{campo}' debe ser un número positivo (ej: 150000 o 75000.50).")


def _documento_existe(tabla, id_col, documento, excluir_id=None):
    q = f"SELECT {id_col} FROM {tabla} WHERE documento = ?"
    _, rows = ejecutar_query(q, (str(documento).strip(),), fetch=True)
    if excluir_id:
        rows = [r for r in rows if r[0] != excluir_id]
    return len(rows) > 0


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — JUGADORES
# ─────────────────────────────────────────────────────────────────────────────

def get_jugadores():
    q = """
    SELECT id_jugador, nombres, apellidos, documento,
           fecha_nacimiento, numero_preferido, talla_uniforme,
           estado, fecha_ingreso, observaciones
    FROM JUGADOR
    ORDER BY apellidos, nombres
    """
    return ejecutar_query(q, fetch=True)


def get_jugadores_activos():
    cols, rows = ejecutar_query(
        "SELECT id_jugador, nombres + ' ' + apellidos AS nombre_completo, documento "
        "FROM JUGADOR WHERE estado = 'activo' ORDER BY apellidos, nombres",
        fetch=True
    )
    return rows


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


def get_detalle_jugador(id_jugador):
    q = """
    SELECT
        id_jugador, nombres, apellidos, documento,
        fecha_nacimiento, numero_preferido, talla_uniforme,
        estado, fecha_ingreso, observaciones
    FROM JUGADOR
    WHERE id_jugador = ?
    """
    return ejecutar_query(q, (int(id_jugador),), fetch=True)


def get_detalle_jugador_completo(id_jugador):
    id_jugador = int(id_jugador)

    datos = ejecutar_query(
        """
        SELECT id_jugador, nombres, apellidos, documento,
               fecha_nacimiento, numero_preferido, talla_uniforme,
               estado, fecha_ingreso, observaciones
        FROM JUGADOR WHERE id_jugador = ?
        """,
        (id_jugador,), fetch=True
    )

    tutores = ejecutar_query(
        """
        SELECT
            jt.id_jugador_tutor,
            t.id_tutor,
            t.nombres + ' ' + t.apellidos AS tutor,
            t.telefono,
            t.email,
            jt.parentesco,
            jt.acudiente_principal
        FROM JUGADOR_TUTOR jt
        INNER JOIN TUTOR t ON jt.id_tutor = t.id_tutor
        WHERE jt.id_jugador = ?
        ORDER BY jt.acudiente_principal DESC, t.apellidos
        """,
        (id_jugador,), fetch=True
    )

    plantillas = ejecutar_query(
        """
        SELECT
            p.id_plantilla,
            p.nombre_plantilla,
            c.nombre_categoria,
            p.temporada,
            p.estado,
            pj.fecha_asignacion
        FROM PLANTILLA_JUGADOR pj
        INNER JOIN PLANTILLA p ON pj.id_plantilla = p.id_plantilla
        INNER JOIN CATEGORIA c ON p.id_categoria  = c.id_categoria
        WHERE pj.id_jugador = ? AND pj.estado = 'activo'
        ORDER BY c.nombre_categoria, p.nombre_plantilla
        """,
        (id_jugador,), fetch=True
    )

    return datos, tutores, plantillas


def _validar_jugador(nombres, apellidos, documento, fecha_nac, num_pref,
                     talla, estado, fecha_ing, excluir_id=None):
    _validar_solo_texto(nombres, "Nombres")
    _validar_solo_texto(apellidos, "Apellidos")
    _validar_documento(documento)
    _validar_fecha(fecha_nac, "Fecha de nacimiento")
    _validar_fecha(fecha_ing, "Fecha de ingreso")

    fn = datetime.strptime(fecha_nac.strip(), "%Y-%m-%d")
    fi = datetime.strptime(fecha_ing.strip(), "%Y-%m-%d")

    if fn >= datetime.today():
        raise ValueError("La fecha de nacimiento debe ser anterior a hoy.")
    if fi <= fn:
        raise ValueError("La fecha de ingreso debe ser posterior a la fecha de nacimiento.")

    if num_pref:
        _validar_numero_entero_positivo(num_pref, "Número preferido")

    _validar_requerido(talla, "Talla uniforme")
    tallas_validas = ["XS", "S", "M", "L", "XL", "XXL"]
    if str(talla).strip().upper() not in tallas_validas:
        raise ValueError(f"Talla inválida. Opciones: {', '.join(tallas_validas)}.")

    estados_validos = ["activo", "inactivo", "lesionado"]
    if estado not in estados_validos:
        raise ValueError(f"Estado inválido. Opciones: {', '.join(estados_validos)}.")

    if _documento_existe("JUGADOR", "id_jugador", documento, excluir_id):
        raise ValueError(f"Ya existe un jugador con el documento '{documento}'.")


def insert_jugador_con_tutor(nombres, apellidos, documento, fecha_nac, num_pref,
                              talla, fecha_ing, obs, id_tutor, parentesco,
                              acudiente_principal):
    _validar_jugador(nombres, apellidos, documento, fecha_nac,
                     num_pref, talla, "activo", fecha_ing)
    _validar_requerido(parentesco, "Parentesco")
    _validar_requerido(id_tutor, "Tutor")

    ejecutar_query(
        "EXEC SP_InsertarJugadorTutor ?,?,?,?,?,?,?,?,?,?,?",
        (
            nombres.strip(),
            apellidos.strip(),
            documento.strip(),
            fecha_nac.strip(),
            int(num_pref) if num_pref and str(num_pref).strip() else None,
            str(talla).strip().upper(),
            fecha_ing.strip(),
            obs.strip() if obs else None,
            int(id_tutor),
            parentesco.strip(),
            1 if acudiente_principal else 0,
        )
    )


def update_jugador(id_j, nombres, apellidos, num_pref, talla, estado, obs):
    _validar_solo_texto(nombres, "Nombres")
    _validar_solo_texto(apellidos, "Apellidos")

    if num_pref:
        _validar_numero_entero_positivo(num_pref, "Número preferido")

    _validar_requerido(talla, "Talla uniforme")
    tallas_validas = ["XS", "S", "M", "L", "XL", "XXL"]
    if str(talla).strip().upper() not in tallas_validas:
        raise ValueError(f"Talla inválida. Opciones: {', '.join(tallas_validas)}.")

    estados_validos = ["activo", "inactivo", "lesionado"]
    if estado not in estados_validos:
        raise ValueError(f"Estado inválido. Opciones: {', '.join(estados_validos)}.")

    ejecutar_query(
        "EXEC SP_ActualizarJugador ?,?,?,?,?,?,?",
        (
            int(id_j),
            nombres.strip(),
            apellidos.strip(),
            int(num_pref) if num_pref and str(num_pref).strip() else None,
            str(talla).strip().upper(),
            estado,
            obs.strip() if obs else None,
        )
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


def insert_jugador_en_plantilla(nombres, apellidos, documento, fecha_nac,
                                 num_pref, talla, fecha_ing, obs,
                                 id_tutor, parentesco, id_plantilla, fecha_asignacion):
    insert_jugador_con_tutor(nombres, apellidos, documento, fecha_nac,
                              num_pref, talla, fecha_ing, obs,
                              id_tutor, parentesco, True)

    _, rows = ejecutar_query(
        "SELECT id_jugador FROM JUGADOR WHERE documento = ?",
        (str(documento).strip(),), fetch=True
    )
    if not rows:
        raise ValueError("No se pudo obtener el ID del jugador recién creado.")

    id_jugador = rows[0][0]
    asignar_jugador_plantilla(id_plantilla, id_jugador, fecha_asignacion)
    return id_jugador


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — RELACIÓN JUGADOR ↔ TUTOR
# ─────────────────────────────────────────────────────────────────────────────

def get_tutores_de_jugador(id_jugador):
    q = """
    SELECT
        jt.id_jugador_tutor,
        t.id_tutor,
        t.nombres + ' ' + t.apellidos AS tutor,
        t.telefono,
        t.email,
        jt.parentesco,
        jt.acudiente_principal
    FROM JUGADOR_TUTOR jt
    INNER JOIN TUTOR t ON jt.id_tutor = t.id_tutor
    WHERE jt.id_jugador = ?
    ORDER BY jt.acudiente_principal DESC, t.apellidos
    """
    return ejecutar_query(q, (int(id_jugador),), fetch=True)


def insert_jugador_tutor(id_jugador, id_tutor, parentesco, acudiente_principal=None):
    _validar_requerido(parentesco, "Parentesco")

    _, rows = ejecutar_query(
        "SELECT COUNT(*) FROM JUGADOR_TUTOR WHERE id_jugador = ? AND id_tutor = ?",
        (int(id_jugador), int(id_tutor)), fetch=True
    )
    if rows[0][0] > 0:
        raise ValueError("Este tutor ya está vinculado a este jugador.")

    if acudiente_principal:
        ejecutar_query(
            "UPDATE JUGADOR_TUTOR SET acudiente_principal = 0 WHERE id_jugador = ?",
            (int(id_jugador),)
        )
    ejecutar_query(
        "INSERT INTO JUGADOR_TUTOR (id_jugador, id_tutor, parentesco, acudiente_principal) "
        "VALUES (?, ?, ?, ?)",
        (int(id_jugador), int(id_tutor), parentesco.strip(), 1 if acudiente_principal else 0)
    )


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


def delete_jugador_tutor(id_jugador_tutor):
    _, rows = ejecutar_query(
        "SELECT id_jugador, acudiente_principal FROM JUGADOR_TUTOR WHERE id_jugador_tutor = ?",
        (int(id_jugador_tutor),), fetch=True
    )
    if not rows:
        raise ValueError("Vínculo tutor-jugador no encontrado.")

    id_jugador = rows[0][0]

    _, cnt = ejecutar_query(
        "SELECT COUNT(*) FROM JUGADOR_TUTOR WHERE id_jugador = ?",
        (int(id_jugador),), fetch=True
    )
    if cnt[0][0] <= 1:
        raise ValueError(
            "No se puede desvincular el único tutor del jugador. "
            "Primero agregue otro tutor."
        )

    ejecutar_query(
        "DELETE FROM JUGADOR_TUTOR WHERE id_jugador_tutor = ?",
        (int(id_jugador_tutor),)
    )


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — TUTORES
# ─────────────────────────────────────────────────────────────────────────────

def get_tutores():
    q = """
    SELECT id_tutor, nombres, apellidos, documento,
           telefono, email, direccion
    FROM TUTOR
    ORDER BY apellidos, nombres
    """
    return ejecutar_query(q, fetch=True)


def get_tutores_simple():
    cols, rows = ejecutar_query(
        "SELECT id_tutor, nombres + ' ' + apellidos AS nombre_completo "
        "FROM TUTOR ORDER BY apellidos, nombres",
        fetch=True
    )
    return rows


def get_detalle_tutor(id_tutor):
    q = "SELECT * FROM VW_DetalleTutor WHERE id_tutor = ?"
    return ejecutar_query(q, (int(id_tutor),), fetch=True)


def _validar_tutor(nombres, apellidos, documento, telefono, email,
                   direccion, excluir_id=None):
    _validar_solo_texto(nombres, "Nombres")
    _validar_solo_texto(apellidos, "Apellidos")
    _validar_documento(documento)
    _validar_requerido(telefono, "Teléfono")
    _validar_telefono(telefono)
    _validar_requerido(email, "Email")
    _validar_email(email)
    _validar_requerido(direccion, "Dirección")

    if _documento_existe("TUTOR", "id_tutor", documento, excluir_id):
        raise ValueError(f"Ya existe un tutor con el documento '{documento}'.")


def insert_tutor(nombres, apellidos, documento, telefono, email, direccion):
    _validar_tutor(nombres, apellidos, documento, telefono, email, direccion)
    ejecutar_query(
        "EXEC SP_InsertarTutor ?,?,?,?,?,?",
        (
            nombres.strip(),
            apellidos.strip(),
            documento.strip(),
            telefono.strip(),
            email.strip().lower(),
            direccion.strip(),
        )
    )


def update_tutor(id_t, nombres, apellidos, documento, telefono, email, direccion):
    _validar_tutor(nombres, apellidos, documento, telefono, email,
                   direccion, excluir_id=int(id_t))
    ejecutar_query(
        "UPDATE TUTOR "
        "SET nombres=?, apellidos=?, documento=?, telefono=?, email=?, direccion=? "
        "WHERE id_tutor=?",
        (
            nombres.strip(),
            apellidos.strip(),
            documento.strip(),
            telefono.strip(),
            email.strip().lower(),
            direccion.strip(),
            int(id_t),
        )
    )


def delete_tutor(id_t):
    ejecutar_query("EXEC SP_EliminarTutor ?", (int(id_t),))


def buscar_tutores(texto):
    filtro = f"%{texto.strip()}%"
    q = """
    SELECT id_tutor,
           nombres + ' ' + apellidos AS nombre_completo,
           documento, telefono
    FROM TUTOR
    WHERE nombres   LIKE ?
       OR apellidos LIKE ?
       OR documento LIKE ?
    ORDER BY apellidos, nombres
    """
    return ejecutar_query(q, (filtro, filtro, filtro), fetch=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — PROFESORES
# ─────────────────────────────────────────────────────────────────────────────

def get_profesores():
    q = """
    SELECT id_profesor, nombres, apellidos, documento,
           telefono, email, especialidad, estado, fecha_ingreso
    FROM PROFESOR
    ORDER BY apellidos, nombres
    """
    return ejecutar_query(q, fetch=True)


def get_profesores_activos():
    cols, rows = ejecutar_query(
        "SELECT id_profesor, nombres + ' ' + apellidos AS nombre_completo "
        "FROM PROFESOR WHERE estado = 'activo' ORDER BY apellidos, nombres",
        fetch=True
    )
    return rows


def get_detalle_profesor(id_profesor):
    q = "SELECT * FROM VW_DetalleProfesor WHERE id_profesor = ?"
    return ejecutar_query(q, (int(id_profesor),), fetch=True)


def _validar_profesor(nombres, apellidos, documento, telefono, email,
                      especialidad, estado, fecha_ing, excluir_id=None):
    _validar_solo_texto(nombres, "Nombres")
    _validar_solo_texto(apellidos, "Apellidos")
    _validar_documento(documento)
    _validar_requerido(telefono, "Teléfono")
    _validar_telefono(telefono)
    _validar_requerido(email, "Email")
    _validar_email(email)
    _validar_fecha(fecha_ing, "Fecha de ingreso")

    estados_validos = ["activo", "inactivo"]
    if estado not in estados_validos:
        raise ValueError(f"Estado inválido. Opciones: {', '.join(estados_validos)}.")

    if _documento_existe("PROFESOR", "id_profesor", documento, excluir_id):
        raise ValueError(f"Ya existe un profesor con el documento '{documento}'.")


def insert_profesor(nombres, apellidos, documento, telefono, email,
                    especialidad, fecha_ing):
    _validar_profesor(nombres, apellidos, documento, telefono, email,
                      especialidad, "activo", fecha_ing)
    ejecutar_query(
        "EXEC SP_InsertarProfesor ?,?,?,?,?,?,?",
        (
            nombres.strip(),
            apellidos.strip(),
            documento.strip(),
            telefono.strip(),
            email.strip().lower(),
            especialidad.strip() if especialidad else None,
            fecha_ing.strip(),
        )
    )


def update_profesor(id_p, nombres, apellidos, documento, telefono, email,
                    especialidad, estado):
    _validar_solo_texto(nombres, "Nombres")
    _validar_solo_texto(apellidos, "Apellidos")
    _validar_documento(documento)
    _validar_requerido(telefono, "Teléfono")
    _validar_telefono(telefono)
    _validar_requerido(email, "Email")
    _validar_email(email)

    estados_validos = ["activo", "inactivo"]
    if estado not in estados_validos:
        raise ValueError(f"Estado inválido. Opciones: {', '.join(estados_validos)}.")

    if _documento_existe("PROFESOR", "id_profesor", documento, excluir_id=int(id_p)):
        raise ValueError(f"Ya existe otro profesor con el documento '{documento}'.")

    ejecutar_query(
        "UPDATE PROFESOR "
        "SET nombres=?, apellidos=?, documento=?, telefono=?, email=?, "
        "    especialidad=?, estado=? "
        "WHERE id_profesor=?",
        (
            nombres.strip(),
            apellidos.strip(),
            documento.strip(),
            telefono.strip(),
            email.strip().lower(),
            especialidad.strip() if especialidad else None,
            estado,
            int(id_p),
        )
    )


def delete_profesor(id_p):
    """
    Borrado físico completo mediante SP_EliminarProfesor.
    El SP elimina en cascada: SESION_JUGADOR → SESION →
    PLANTILLA_PROFESOR → PROFESOR.
    """
    ejecutar_query("EXEC SP_EliminarProfesor ?", (int(id_p),))


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — CANCHAS
# ─────────────────────────────────────────────────────────────────────────────

def get_canchas():
    q = """
    SELECT id_cancha, nombre_cancha, direccion,
           tipo_superficie, capacidad, estado
    FROM CANCHA
    ORDER BY nombre_cancha
    """
    return ejecutar_query(q, fetch=True)


def get_canchas_disponibles():
    cols, rows = ejecutar_query(
        "SELECT id_cancha, nombre_cancha "
        "FROM CANCHA WHERE estado = 'disponible' ORDER BY nombre_cancha",
        fetch=True
    )
    return rows


def insert_cancha(nombre, direccion, tipo_superficie, capacidad):
    _validar_requerido(nombre, "Nombre de cancha")
    if capacidad:
        _validar_numero_entero_positivo(capacidad, "Capacidad")
    ejecutar_query(
        "EXEC SP_InsertarCancha ?,?,?,?",
        (
            nombre.strip(),
            direccion.strip() if direccion else None,
            tipo_superficie.strip() if tipo_superficie else None,
            int(capacidad) if capacidad else None,
        )
    )


def update_cancha(id_c, nombre, direccion, tipo_superficie, capacidad, estado):
    _validar_requerido(nombre, "Nombre de cancha")
    estados_validos = ["disponible", "no disponible", "mantenimiento"]
    if estado not in estados_validos:
        raise ValueError(f"Estado inválido. Opciones: {', '.join(estados_validos)}.")
    if capacidad:
        _validar_numero_entero_positivo(capacidad, "Capacidad")
    ejecutar_query(
        "UPDATE CANCHA "
        "SET nombre_cancha=?, direccion=?, tipo_superficie=?, capacidad=?, estado=? "
        "WHERE id_cancha=?",
        (
            nombre.strip(),
            direccion.strip() if direccion else None,
            tipo_superficie.strip() if tipo_superficie else None,
            int(capacidad) if capacidad else None,
            estado,
            int(id_c),
        )
    )


def delete_cancha(id_c):
    _, rows = ejecutar_query(
        "SELECT COUNT(*) FROM SESION WHERE id_cancha = ?",
        (int(id_c),), fetch=True
    )
    if rows[0][0] > 0:
        raise ValueError(
            "No se puede eliminar: la cancha tiene sesiones registradas. "
            "Puede cambiar su estado a 'no disponible' o 'mantenimiento'."
        )
    ejecutar_query("DELETE FROM CANCHA WHERE id_cancha = ?", (int(id_c),))


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — CATEGORÍAS
# ─────────────────────────────────────────────────────────────────────────────

def get_categorias():
    q = """
    SELECT id_categoria, nombre_categoria,
           anio_minimo, anio_maximo, estado, descripcion
    FROM CATEGORIA
    ORDER BY nombre_categoria
    """
    return ejecutar_query(q, fetch=True)


def get_categorias_activas():
    cols, rows = ejecutar_query(
        "SELECT id_categoria, nombre_categoria "
        "FROM CATEGORIA WHERE estado = 'activa' ORDER BY nombre_categoria",
        fetch=True
    )
    return rows


def insert_categoria(nombre, anio_minimo, anio_maximo, descripcion):
    _validar_requerido(nombre, "Nombre de categoría")
    _validar_numero_entero_positivo(anio_minimo, "Año mínimo", obligatorio=True)
    _validar_numero_entero_positivo(anio_maximo, "Año máximo", obligatorio=True)

    if int(anio_minimo) > int(anio_maximo):
        raise ValueError("El año mínimo no puede ser mayor al año máximo.")

    ejecutar_query(
        "EXEC SP_InsertarCategoria ?,?,?,?",
        (
            nombre.strip(),
            int(anio_minimo),
            int(anio_maximo),
            descripcion.strip() if descripcion else None,
        )
    )


def update_categoria(id_cat, nombre, anio_minimo, anio_maximo, estado, descripcion):
    _validar_requerido(nombre, "Nombre de categoría")
    _validar_numero_entero_positivo(anio_minimo, "Año mínimo", obligatorio=True)
    _validar_numero_entero_positivo(anio_maximo, "Año máximo", obligatorio=True)

    if int(anio_minimo) > int(anio_maximo):
        raise ValueError("El año mínimo no puede ser mayor al año máximo.")

    estados_validos = ["activa", "inactiva"]
    if estado not in estados_validos:
        raise ValueError(f"Estado inválido. Opciones: {', '.join(estados_validos)}.")

    ejecutar_query(
        "UPDATE CATEGORIA "
        "SET nombre_categoria=?, anio_minimo=?, anio_maximo=?, estado=?, descripcion=? "
        "WHERE id_categoria=?",
        (
            nombre.strip(),
            int(anio_minimo),
            int(anio_maximo),
            estado,
            descripcion.strip() if descripcion else None,
            int(id_cat),
        )
    )


def delete_categoria(id_cat):
    _, rows = ejecutar_query(
        "SELECT COUNT(*) FROM PLANTILLA WHERE id_categoria = ?",
        (int(id_cat),), fetch=True
    )
    if rows[0][0] > 0:
        raise ValueError(
            "No se puede eliminar: la categoría tiene plantillas asociadas. "
            "Elimina primero todas las plantillas de esta categoría."
        )
    ejecutar_query("DELETE FROM CATEGORIA WHERE id_categoria = ?", (int(id_cat),))


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — PLANTILLAS  (crud.py — reemplaza el bloque anterior)
# ─────────────────────────────────────────────────────────────────────────────
#
# CAMBIO EN BD REQUERIDO (ejecutar una sola vez):
#   ALTER TABLE PLANTILLA_JUGADOR
#       ADD tipo VARCHAR(10) NOT NULL DEFAULT 'titular'
#       CHECK (tipo IN ('titular', 'banca'));
#
# Esto permite distinguir jugadores titulares (candidatos a alineación)
# de jugadores de banca (suplentes gestionados aparte).
# ─────────────────────────────────────────────────────────────────────────────


def get_plantillas():
    q = """
    SELECT
        p.id_plantilla,
        p.nombre_plantilla,
        c.nombre_categoria,
        p.fecha_creacion,
        p.temporada,
        p.estado
    FROM PLANTILLA p
    INNER JOIN CATEGORIA c ON p.id_categoria = c.id_categoria
    ORDER BY p.nombre_plantilla
    """
    return ejecutar_query(q, fetch=True)


def insert_plantilla(nombre, id_categoria, fecha_creacion, temporada):
    _validar_requerido(nombre, "Nombre de plantilla")
    _validar_requerido(id_categoria, "Categoría")
    _validar_fecha(fecha_creacion, "Fecha de creación")
    ejecutar_query(
        "EXEC SP_CrearPlantilla ?,?,?,?",
        (
            nombre.strip(),
            int(id_categoria),
            fecha_creacion.strip(),
            temporada.strip() if temporada else None,
        )
    )


def update_plantilla(id_pl, nombre, id_categoria, temporada, estado):
    _validar_requerido(nombre, "Nombre de plantilla")
    estados_validos = ["activa", "inactiva"]
    if estado not in estados_validos:
        raise ValueError(f"Estado inválido. Opciones: {', '.join(estados_validos)}.")
    ejecutar_query(
        "UPDATE PLANTILLA "
        "SET nombre_plantilla=?, id_categoria=?, temporada=?, estado=? "
        "WHERE id_plantilla=?",
        (
            nombre.strip(),
            int(id_categoria),
            temporada.strip() if temporada else None,
            estado,
            int(id_pl),
        )
    )


def delete_plantilla(id_pl):
    """
    Borrado físico completo de la plantilla y TODO lo enlazado:
      1. SESION_JUGADOR  (asistencias de cada sesión)
      2. SESION          (sesiones de la plantilla, sin importar estado)
      3. ALINEACION      (alineación guardada)
      4. PLANTILLA_JUGADOR / PLANTILLA_PROFESOR
      5. PLANTILLA       (vía SP_EliminarPlantilla)

    Se pide confirmación en la capa visual; aquí solo se ejecuta el borrado.
    """
    id_pl = int(id_pl)

    # 1. Borrar asistencias de todas las sesiones de esta plantilla
    ejecutar_query(
        """
        DELETE sj
        FROM SESION_JUGADOR sj
        INNER JOIN SESION s ON sj.id_sesion = s.id_sesion
        WHERE s.id_plantilla = ?
        """,
        (id_pl,)
    )

    # 2. Borrar las sesiones en sí
    ejecutar_query(
        "DELETE FROM SESION WHERE id_plantilla = ?",
        (id_pl,)
    )

    # 3. Borrar la alineación guardada
    ejecutar_query(
        "DELETE FROM PLANTILLA_ALINEACION WHERE id_plantilla = ?",
        (id_pl,)
    )

    # 4 + 5. SP elimina PLANTILLA_JUGADOR, PLANTILLA_PROFESOR y PLANTILLA
    ejecutar_query("EXEC SP_EliminarPlantilla ?", (id_pl,))


def filtrar_jugadores_para_plantilla(id_categoria, filtro_texto=None):
    q = "SELECT * FROM FN_FiltrarJugadoresParaPlantilla(?, ?)"
    return ejecutar_query(
        q, (int(id_categoria), filtro_texto.strip() if filtro_texto else None),
        fetch=True
    )


# ── Jugadores: titulares ──────────────────────────────────────────────────────

def asignar_jugador_plantilla(id_plantilla, id_jugador, fecha_asignacion, tipo="titular"):
    """
    Asigna un jugador a la plantilla.
    tipo = 'titular' → lista principal (candidatos a alineación).
    tipo = 'banca'   → lista de banca (suplentes).
    Un mismo jugador no puede aparecer en ambas listas a la vez.
    """
    _validar_fecha(fecha_asignacion, "Fecha de asignación")

    if tipo not in ("titular", "banca"):
        raise ValueError("tipo debe ser 'titular' o 'banca'.")

    # Verificar que no exista ya en cualquier tipo activo
    _, rows = ejecutar_query(
        "SELECT COUNT(*) FROM PLANTILLA_JUGADOR "
        "WHERE id_plantilla = ? AND id_jugador = ? AND estado = 'activo'",
        (int(id_plantilla), int(id_jugador)), fetch=True
    )
    if rows[0][0] > 0:
        raise ValueError("El jugador ya está asignado activamente a esta plantilla.")

    ejecutar_query(
        "EXEC SP_AsignarJugadorPlantilla ?,?,?,?",
        (int(id_plantilla), int(id_jugador), fecha_asignacion.strip(), tipo)
    )
    # Si el SP no acepta el 4.° parámetro todavía, usar el UPDATE inline:
    # ejecutar_query(
    #     "INSERT INTO PLANTILLA_JUGADOR (id_plantilla, id_jugador, fecha_asignacion, estado, tipo) "
    #     "VALUES (?,?,?,'activo',?)",
    #     (int(id_plantilla), int(id_jugador), fecha_asignacion.strip(), tipo)
    # )


def get_jugadores_de_plantilla(id_plantilla, solo_activos=False, tipo=None):
    """
    Retorna jugadores de una plantilla.
    tipo=None       → todos (titulares + banca).
    tipo='titular'  → solo titulares.
    tipo='banca'    → solo banca.
    solo_activos=True → filtra por estado='activo'.
    """
    condiciones = ["pj.id_plantilla = ?"]
    params = [int(id_plantilla)]

    if solo_activos:
        condiciones.append("pj.estado = 'activo'")
    if tipo in ("titular", "banca"):
        condiciones.append("pj.tipo = ?")
        params.append(tipo)

    where = " AND ".join(condiciones)
    q = f"""
    SELECT
        pj.id_plantilla_jugador,
        j.id_jugador,
        j.nombres + ' ' + j.apellidos AS jugador,
        j.documento,
        pj.fecha_asignacion,
        pj.estado,
        pj.tipo
    FROM PLANTILLA_JUGADOR pj
    INNER JOIN JUGADOR j ON pj.id_jugador = j.id_jugador
    WHERE {where}
    ORDER BY j.apellidos, j.nombres
    """
    return ejecutar_query(q, tuple(params), fetch=True)


def get_titulares_de_plantilla(id_plantilla, solo_activos=True):
    """Alias conveniente para jugadores titulares (candidatos a alineación)."""
    return get_jugadores_de_plantilla(id_plantilla, solo_activos=solo_activos, tipo="titular")


def get_banca_de_plantilla(id_plantilla):
    """Alias conveniente para jugadores de banca."""
    return get_jugadores_de_plantilla(id_plantilla, solo_activos=True, tipo="banca")


def asignar_jugador_banca(id_plantilla, id_jugador, fecha_asignacion):
    """
    Añade un jugador a la banca.
    El jugador debe existir previamente como titular en la plantilla;
    no puede estar ya en la banca.
    """
    # Verificar que sea titular activo de esta plantilla
    _, rows = ejecutar_query(
        "SELECT COUNT(*) FROM PLANTILLA_JUGADOR "
        "WHERE id_plantilla = ? AND id_jugador = ? AND estado = 'activo' AND tipo = 'titular'",
        (int(id_plantilla), int(id_jugador)), fetch=True
    )
    if rows[0][0] == 0:
        raise ValueError(
            "El jugador debe estar primero en la lista de titulares de esta plantilla."
        )

    # Verificar que no esté ya en banca
    _, rows2 = ejecutar_query(
        "SELECT COUNT(*) FROM PLANTILLA_JUGADOR "
        "WHERE id_plantilla = ? AND id_jugador = ? AND tipo = 'banca'",
        (int(id_plantilla), int(id_jugador)), fetch=True
    )
    if rows2[0][0] > 0:
        raise ValueError("El jugador ya está en la banca de esta plantilla.")

    ejecutar_query(
        "INSERT INTO PLANTILLA_JUGADOR (id_plantilla, id_jugador, fecha_asignacion, estado, tipo) "
        "VALUES (?,?,?,'activo','banca')",
        (int(id_plantilla), int(id_jugador), fecha_asignacion.strip())
    )


def quitar_jugador_de_alineacion(id_plantilla, id_jugador):
    """Antes este DELETE se escribía a mano en la capa de presentación (P5)."""
    ejecutar_query(
        "DELETE FROM PLANTILLA_ALINEACION WHERE id_plantilla = ? AND id_jugador = ?",
        (int(id_plantilla), int(id_jugador))
    )


def quitar_jugador_plantilla(id_plantilla_jugador):
    """Borrado físico del registro de jugador en la plantilla (titular o banca)."""
    ejecutar_query(
        "DELETE FROM PLANTILLA_JUGADOR WHERE id_plantilla_jugador = ?",
        (int(id_plantilla_jugador),)
    )


# ── Profesores ────────────────────────────────────────────────────────────────

def asignar_profesor_plantilla(id_plantilla, id_profesor, fecha_asignacion, cargo):
    _validar_fecha(fecha_asignacion, "Fecha de asignación")

    _, rows = ejecutar_query(
        "SELECT COUNT(*) FROM PLANTILLA_PROFESOR "
        "WHERE id_plantilla = ? AND id_profesor = ?",
        (int(id_plantilla), int(id_profesor)), fetch=True
    )
    if rows[0][0] > 0:
        raise ValueError("Este profesor ya está asignado a esta plantilla.")

    ejecutar_query(
        "EXEC SP_AsignarProfesorPlantilla ?,?,?,?",
        (
            int(id_plantilla),
            int(id_profesor),
            fecha_asignacion.strip(),
            cargo.strip() if cargo else None,
        )
    )


def get_profesores_de_plantilla(id_plantilla):
    q = """
    SELECT
        pp.id_plantilla_profesor,
        p.id_profesor,
        p.nombres + ' ' + p.apellidos AS profesor,
        p.especialidad,
        pp.cargo,
        pp.fecha_asignacion
    FROM PLANTILLA_PROFESOR pp
    INNER JOIN PROFESOR p ON pp.id_profesor = p.id_profesor
    WHERE pp.id_plantilla = ?
    ORDER BY p.apellidos, p.nombres
    """
    return ejecutar_query(q, (int(id_plantilla),), fetch=True)


def quitar_profesor_plantilla(id_plantilla_profesor):
    ejecutar_query(
        "DELETE FROM PLANTILLA_PROFESOR WHERE id_plantilla_profesor = ?",
        (int(id_plantilla_profesor),)
    )


# ── Historial ─────────────────────────────────────────────────────────────────

def get_plantillas_de_jugador(id_jugador):
    q = """
    SELECT
        p.id_plantilla,
        p.nombre_plantilla,
        c.nombre_categoria,
        p.temporada,
        p.estado         AS estado_plantilla,
        pj.fecha_asignacion,
        pj.estado        AS estado_asignacion,
        pj.tipo
    FROM PLANTILLA_JUGADOR pj
    INNER JOIN PLANTILLA p ON pj.id_plantilla = p.id_plantilla
    INNER JOIN CATEGORIA c ON p.id_categoria  = c.id_categoria
    WHERE pj.id_jugador = ? AND pj.estado = 'activo'
    ORDER BY c.nombre_categoria, p.nombre_plantilla
    """
    return ejecutar_query(q, (int(id_jugador),), fetch=True)


# ── Alineación ────────────────────────────────────────────────────────────────

def guardar_alineacion(id_plantilla, formacion, slots):
    """
    Persiste la alineación en BD usando la tabla PLANTILLA_ALINEACION.
    slots: lista de dicts {id_jugador, slot_index, posicion}
    """
    # Borrar alineación anterior de esta plantilla
    ejecutar_query(
        "DELETE FROM PLANTILLA_ALINEACION WHERE id_plantilla = ?",
        (int(id_plantilla),)
    )
    # Insertar cada slot
    for s in slots:
        ejecutar_query(
            "INSERT INTO PLANTILLA_ALINEACION "
            "(id_plantilla, id_jugador, formacion, slot_index, posicion) "
            "VALUES (?,?,?,?,?)",
            (int(id_plantilla), int(s["id_jugador"]), formacion,
             int(s["slot_index"]), s["posicion"])
        )
 
 
def get_alineacion(id_plantilla):
    """
    Devuelve la alineación guardada de una plantilla.
    Columnas retornadas:
        id_plantilla, id_jugador, jugador, formacion, slot_index, posicion
    """
    q = """
    SELECT
        a.id_plantilla,
        a.id_jugador,
        j.nombres + ' ' + j.apellidos AS jugador,
        a.formacion,
        a.slot_index,
        a.posicion
    FROM PLANTILLA_ALINEACION a
    INNER JOIN JUGADOR j ON a.id_jugador = j.id_jugador
    WHERE a.id_plantilla = ?
    ORDER BY a.slot_index
    """
    return ejecutar_query(q, (int(id_plantilla),), fetch=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — SESIONES
# ─────────────────────────────────────────────────────────────────────────────

def get_sesiones(id_categoria=None, id_plantilla=None, tipo_sesion=None):
    """
    Filtra sesiones por categoría, plantilla y/o tipo mediante SP_FiltrarSesiones.
    Los tres parámetros son opcionales: None = sin filtro.
    """
    return ejecutar_query(
        "EXEC SP_FiltrarSesiones ?,?,?",
        (id_categoria, id_plantilla, tipo_sesion),
        fetch=True
    )


def get_sesion_detalle(id_sesion):
    return ejecutar_query(
        """
        SELECT
            s.id_sesion,
            s.fecha_sesion,
            s.tipo_sesion,
            s.estado,
            s.marcador,
            s.resultado,
            s.observaciones,
            p.nombres + ' ' + p.apellidos AS profesor,
            ca.nombre_cancha,
            cat.nombre_categoria,
            pl.nombre_plantilla
        FROM SESION s
        INNER JOIN PROFESOR  p   ON s.id_profesor  = p.id_profesor
        INNER JOIN CANCHA    ca  ON s.id_cancha    = ca.id_cancha
        INNER JOIN CATEGORIA cat ON s.id_categoria = cat.id_categoria
        INNER JOIN PLANTILLA pl  ON s.id_plantilla = pl.id_plantilla
        WHERE s.id_sesion = ?
        """,
        (int(id_sesion),), fetch=True
    )


def crear_sesion(fecha_sesion, id_profesor, id_cancha, id_categoria,
                 id_plantilla, tipo_sesion, observaciones):
    """
    Crea una sesión mediante SP_CrearSesion.
    Requiere id_plantilla (FK añadida a la tabla SESION).
    Valida conflicto de cancha en la misma fecha.
    Usa conexión directa para leer SCOPE_IDENTITY() correctamente con pyodbc.
    """
    _validar_requerido(fecha_sesion, "Fecha de sesión")
    _validar_requerido(id_plantilla, "Plantilla")

    tipos_validos = ["Torneo", "Partido", "Entrenamiento"]
    if tipo_sesion not in tipos_validos:
        raise ValueError(f"Tipo de sesión inválido. Opciones: {', '.join(tipos_validos)}.")

    _, rows = ejecutar_query(
        """
        SELECT COUNT(*) FROM SESION
        WHERE id_cancha = ?
          AND CAST(fecha_sesion AS DATE) = CAST(? AS DATE)
          AND estado != 'cancelada'
        """,
        (int(id_cancha), str(fecha_sesion)), fetch=True
    )
    if rows[0][0] > 0:
        raise ValueError(
            "La cancha seleccionada ya tiene una sesión programada o realizada "
            "en esa fecha. Elige otra cancha u otra fecha."
        )

    from paladinesfc.legado.db import obtener_conexion
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "EXEC SP_CrearSesion ?,?,?,?,?,?,?",
            (
                fecha_sesion,
                int(id_profesor),
                int(id_cancha),
                int(id_categoria),
                int(id_plantilla),
                tipo_sesion,
                observaciones.strip() if observaciones else None,
            )
        )
        id_sesion = None
        # Navegar por todos los resultsets hasta encontrar el que trae el ID
        while True:
            try:
                row = cursor.fetchone()
                if row is not None:
                    id_sesion = row[0]
                    break
            except Exception:
                pass
            if not cursor.nextset():
                break
        conn.commit()
        return id_sesion
    finally:
        conn.close()


def crear_sesion_completa(fecha_sesion, id_profesor, id_cancha, id_categoria,
                          id_plantilla, tipo_sesion, observaciones, convocados):
    """
    Crea la sesión y registra la convocatoria de todos los jugadores en un solo paso.

    convocados: lista de dicts:
        [{"id_jugador": 5, "asistencia": False, "numero_camiseta": 10}, ...]
    """
    id_sesion = crear_sesion(
        fecha_sesion, id_profesor, id_cancha, id_categoria,
        id_plantilla, tipo_sesion, observaciones
    )
    if not id_sesion:
        raise RuntimeError("No se pudo obtener el ID de la sesión recién creada.")

    for conv in convocados:
        registrar_asistencia(
            id_sesion=id_sesion,
            id_jugador=conv["id_jugador"],
            convocado=True,
            asistencia=conv.get("asistencia", False),
            numero_camiseta=conv.get("numero_camiseta"),
        )

    return id_sesion


def registrar_asistencia(id_sesion, id_jugador, convocado, asistencia,
                         numero_camiseta=None):
    _, rows = ejecutar_query(
        "SELECT COUNT(*) FROM SESION_JUGADOR WHERE id_sesion = ? AND id_jugador = ?",
        (int(id_sesion), int(id_jugador)), fetch=True
    )
    if rows[0][0] > 0:
        raise ValueError("Este jugador ya fue registrado en esta sesión.")

    ejecutar_query(
        "EXEC SP_RegistrarAsistencia ?,?,?,?,?",
        (
            int(id_sesion),
            int(id_jugador),
            1 if asistencia else 0,
            1 if convocado else 0,
            int(numero_camiseta) if numero_camiseta else None,
        )
    )


def update_asistencia(id_sesion_jugador, convocado, asistencia,
                      numero_camiseta=None, observaciones=None):
    ejecutar_query(
        "UPDATE SESION_JUGADOR "
        "SET convocado=?, asistencia=?, numero_camiseta=?, observaciones=? "
        "WHERE id_sesion_jugador=?",
        (
            1 if convocado else 0,
            1 if asistencia else 0,
            int(numero_camiseta) if numero_camiseta else None,
            observaciones.strip() if observaciones else None,
            int(id_sesion_jugador),
        )
    )


def get_jugadores_sesion(id_sesion):
    q = """
    SELECT
        sj.id_sesion_jugador,
        j.id_jugador,
        j.nombres + ' ' + j.apellidos AS jugador,
        j.documento,
        sj.convocado,
        sj.asistencia,
        sj.numero_camiseta,
        sj.observaciones
    FROM SESION_JUGADOR sj
    INNER JOIN JUGADOR j ON sj.id_jugador = j.id_jugador
    WHERE sj.id_sesion = ?
    ORDER BY sj.convocado DESC, j.apellidos
    """
    return ejecutar_query(q, (int(id_sesion),), fetch=True)


def update_sesion_estado(id_sesion, estado, marcador=None, resultado=None):
    estados_validos = ["programada", "realizada", "cancelada"]
    if estado not in estados_validos:
        raise ValueError(f"Estado inválido. Opciones: {', '.join(estados_validos)}.")
    ejecutar_query(
        "UPDATE SESION SET estado=?, marcador=?, resultado=? WHERE id_sesion=?",
        (
            estado,
            marcador.strip() if marcador else None,
            resultado.strip() if resultado else None,
            int(id_sesion),
        )
    )


def get_jugadores_convocables(id_sesion):
    q = """
    SELECT j.id_jugador, j.nombres + ' ' + j.apellidos AS jugador, j.documento
    FROM JUGADOR j
    INNER JOIN SESION s ON s.id_sesion = ?
    INNER JOIN CATEGORIA c ON s.id_categoria = c.id_categoria
    WHERE j.estado = 'activo'
      AND YEAR(j.fecha_nacimiento) BETWEEN c.anio_minimo AND c.anio_maximo
      AND j.id_jugador NOT IN (
          SELECT id_jugador FROM SESION_JUGADOR WHERE id_sesion = ?
      )
    ORDER BY j.apellidos, j.nombres
    """
    return ejecutar_query(q, (int(id_sesion), int(id_sesion)), fetch=True)




# ─────────────────────────────────────────────────────────────────────────────
# ALINEACIÓN DE PLANTILLA
# ─────────────────────────────────────────────────────────────────────────────

def guardar_alineacion(id_plantilla, formacion, slots):
    """
    Guarda la alineación de una plantilla.
    slots: lista de dicts con {id_jugador, posicion, slot_index}
    Borra la alineación anterior y guarda la nueva.
    """
    ejecutar_query(
        "DELETE FROM PLANTILLA_ALINEACION WHERE id_plantilla = ?",
        (int(id_plantilla),)
    )
    for s in slots:
        ejecutar_query(
            "INSERT INTO PLANTILLA_ALINEACION "
            "(id_plantilla, id_jugador, formacion, slot_index, posicion) "
            "VALUES (?, ?, ?, ?, ?)",
            (int(id_plantilla), int(s["id_jugador"]),
             formacion, int(s["slot_index"]), s["posicion"])
        )


def get_alineacion(id_plantilla):
    """
    Retorna la alineación guardada de una plantilla.
    Columnas: id_plantilla, id_jugador, jugador, formacion, slot_index, posicion
    """
    q = """
    SELECT
        pa.id_plantilla,
        pa.id_jugador,
        j.nombres + ' ' + j.apellidos AS jugador,
        pa.formacion,
        pa.slot_index,
        pa.posicion
    FROM PLANTILLA_ALINEACION pa
    INNER JOIN JUGADOR j ON pa.id_jugador = j.id_jugador
    WHERE pa.id_plantilla = ?
    ORDER BY pa.slot_index
    """
    return ejecutar_query(q, (int(id_plantilla),), fetch=True)
# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4 — CONCEPTOS DE PAGO
# ─────────────────────────────────────────────────────────────────────────────

def get_conceptos():
    cols, rows = ejecutar_query(
        "SELECT id_concepto, nombre_concepto, valor_base "
        "FROM CONCEPTO_PAGO WHERE estado = 'activo' ORDER BY nombre_concepto",
        fetch=True
    )
    return rows


def get_conceptos_todos():
    return ejecutar_query(
        "SELECT id_concepto, nombre_concepto, valor_base, "
        "       descripcion, estado, eliminable "
        "FROM CONCEPTO_PAGO ORDER BY nombre_concepto",
        fetch=True
    )


def get_concepto_mensualidad():
    cols, rows = ejecutar_query(
        "SELECT id_concepto, nombre_concepto, valor_base "
        "FROM CONCEPTO_PAGO "
        "WHERE nombre_concepto LIKE '%Mensualidad%' AND estado = 'activo'",
        fetch=True
    )
    return rows[0] if rows else None


def insert_concepto(nombre, valor_base, descripcion, eliminable=True):
    _validar_requerido(nombre, "Nombre del concepto")
    if len(nombre.strip()) > 50:
        raise ValueError("El nombre del concepto no puede superar los 50 caracteres.")
    valor_num = _validar_decimal_positivo(str(valor_base), "Valor base")
    ejecutar_query(
        "EXEC SP_InsertarConceptoPago ?,?,?,?",
        (
            nombre.strip(),
            descripcion.strip() if descripcion else None,
            valor_num,
            1 if eliminable else 0,
        )
    )


def update_concepto(id_c, nombre, valor_base, descripcion, estado):
    _validar_requerido(nombre, "Nombre del concepto")
    if len(nombre.strip()) > 50:
        raise ValueError("El nombre del concepto no puede superar los 50 caracteres.")
    valor_num = _validar_decimal_positivo(str(valor_base), "Valor base")
    estados_validos = ["activo", "inactivo"]
    if estado not in estados_validos:
        raise ValueError(f"Estado inválido. Opciones: {', '.join(estados_validos)}.")
    ejecutar_query(
        "UPDATE CONCEPTO_PAGO "
        "SET nombre_concepto=?, valor_base=?, descripcion=?, estado=? "
        "WHERE id_concepto=?",
        (
            nombre.strip(),
            valor_num,
            descripcion.strip() if descripcion else None,
            estado,
            int(id_c),
        )
    )


def delete_concepto(id_c):
    ejecutar_query("EXEC SP_EliminarConceptoPago ?", (int(id_c),))


def es_concepto_mensualidad(id_concepto):
    _, rows = ejecutar_query(
        "SELECT nombre_concepto FROM CONCEPTO_PAGO WHERE id_concepto = ?",
        (int(id_concepto),), fetch=True
    )
    if not rows:
        return False
    return "mensualidad" in rows[0][0].lower()


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4 — PAGOS
# ─────────────────────────────────────────────────────────────────────────────

def buscar_jugador_para_pago(documento):
    return ejecutar_query(
        "SELECT * FROM FN_BuscarJugadorParaPago(?)",
        (str(documento).strip(),), fetch=True
    )


def get_pagos():
    q = """
    SELECT
        p.id_pago,
        j.nombres + ' ' + j.apellidos AS jugador,
        j.documento,
        cp.nombre_concepto,
        p.fecha_pago,
        p.fecha_expiracion,
        p.valor_pagado,
        p.metodo_pago,
        p.observaciones,
        p.id_morosidad
    FROM PAGO p
    INNER JOIN JUGADOR       j  ON p.id_jugador  = j.id_jugador
    INNER JOIN CONCEPTO_PAGO cp ON p.id_concepto = cp.id_concepto
    ORDER BY p.fecha_pago DESC
    """
    return ejecutar_query(q, fetch=True)


def get_pagos_jugador(id_jugador):
    q = """
    SELECT
        p.id_pago,
        cp.nombre_concepto,
        p.fecha_pago,
        p.fecha_expiracion,
        p.valor_pagado,
        p.metodo_pago,
        p.observaciones
    FROM PAGO p
    INNER JOIN CONCEPTO_PAGO cp ON p.id_concepto = cp.id_concepto
    WHERE p.id_jugador = ?
    ORDER BY p.fecha_pago DESC
    """
    return ejecutar_query(q, (int(id_jugador),), fetch=True)


def _validar_pago(fecha_pago, fecha_exp, valor, metodo, requiere_expiracion=False):
    _validar_fecha(fecha_pago, "Fecha de pago")

    if requiere_expiracion:
        _validar_requerido(fecha_exp, "Fecha de expiración (obligatoria para Mensualidad)")
        _validar_fecha(fecha_exp, "Fecha de expiración")
        if datetime.strptime(fecha_exp.strip(), "%Y-%m-%d") <= \
           datetime.strptime(fecha_pago.strip(), "%Y-%m-%d"):
            raise ValueError("La fecha de expiración debe ser posterior a la fecha de pago.")
    else:
        if fecha_exp and str(fecha_exp).strip():
            _validar_fecha(fecha_exp, "Fecha de expiración")
            if datetime.strptime(fecha_exp.strip(), "%Y-%m-%d") <= \
               datetime.strptime(fecha_pago.strip(), "%Y-%m-%d"):
                raise ValueError("La fecha de expiración debe ser posterior a la fecha de pago.")
        else:
            fecha_exp = None

    valor_num = _validar_decimal_positivo(str(valor), "Valor pagado")
    if valor_num <= 0:
        raise ValueError("El valor pagado debe ser mayor a cero.")

    metodos_validos = ["Efectivo", "Transferencia", "Tarjeta", "Nequi", "Daviplata"]
    if metodo not in metodos_validos:
        raise ValueError(f"Método de pago inválido. Opciones: {', '.join(metodos_validos)}.")

    return fecha_exp, valor_num


def insert_pago(id_jugador, id_concepto, fecha_pago, fecha_exp,
                valor, metodo, obs, id_morosidad=None):
    es_mensualidad = es_concepto_mensualidad(id_concepto)
    fecha_exp, valor_num = _validar_pago(
        fecha_pago, fecha_exp, valor, metodo,
        requiere_expiracion=es_mensualidad
    )
    ejecutar_query(
        "EXEC SP_RegistrarPago ?,?,?,?,?,?,?,?",
        (
            int(id_jugador),
            int(id_concepto),
            int(id_morosidad) if id_morosidad else None,
            fecha_pago.strip(),
            fecha_exp,
            valor_num,
            metodo,
            obs.strip() if obs else None,
        )
    )


def delete_pago(id_p):
    _, rows = ejecutar_query(
        "SELECT id_morosidad FROM PAGO WHERE id_pago = ?",
        (int(id_p),), fetch=True
    )
    if not rows:
        raise ValueError(f"No se encontró el pago con ID {id_p}.")

    id_morosidad = rows[0][0]
    ejecutar_query("DELETE FROM PAGO WHERE id_pago = ?", (int(id_p),))

    if id_morosidad:
        ejecutar_query(
            "UPDATE MOROSIDAD SET estado_mora = 'pendiente' "
            "WHERE id_morosidad = ? AND estado_mora = 'pagada'",
            (int(id_morosidad),)
        )


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4 — MOROSIDAD
# ─────────────────────────────────────────────────────────────────────────────

def get_morosos():
    return ejecutar_query(
        "SELECT * FROM VW_ListaMorosos ORDER BY fecha_vencimiento",
        fetch=True
    )


def get_morosidad_jugador(id_jugador):
    q = """
    SELECT
        id_morosidad,
        fecha_vencimiento,
        recargo,
        fecha_recargo,
        motivo_recargo,
        estado_mora,
        observaciones
    FROM MOROSIDAD
    WHERE id_jugador = ?
    ORDER BY fecha_vencimiento DESC
    """
    return ejecutar_query(q, (int(id_jugador),), fetch=True)


def actualizar_morosos():
    ejecutar_query("EXEC SP_ActualizarMorosos")


def agregar_recargo_mora(id_morosidad, valor_recargo, motivo):
    valor_num = _validar_decimal_positivo(str(valor_recargo), "Valor de recargo")
    if valor_num <= 0:
        raise ValueError("El recargo debe ser mayor a cero.")
    _validar_requerido(motivo, "Motivo del recargo")

    _, rows = ejecutar_query(
        "SELECT recargo, motivo_recargo FROM MOROSIDAD WHERE id_morosidad = ?",
        (int(id_morosidad),), fetch=True
    )
    if not rows:
        raise ValueError(f"No se encontró el registro de mora con ID {id_morosidad}.")

    recargo_actual = float(rows[0][0] or 0)
    motivo_actual  = rows[0][1] or ""
    recargo_acumulado = recargo_actual + valor_num

    hoy = datetime.today().strftime("%d/%m/%Y")
    motivo_concatenado = f"{motivo_actual} | {hoy}: {motivo.strip()}" if motivo_actual \
                         else f"{hoy}: {motivo.strip()}"
    motivo_concatenado = motivo_concatenado[-150:]

    ejecutar_query(
        "UPDATE MOROSIDAD "
        "SET recargo = ?, motivo_recargo = ?, fecha_recargo = GETDATE() "
        "WHERE id_morosidad = ?",
        (recargo_acumulado, motivo_concatenado, int(id_morosidad))
    )


def update_morosidad(id_morosidad, estado_mora, observaciones=None):
    estados_validos = ["pendiente", "pagada", "en mora"]
    if estado_mora not in estados_validos:
        raise ValueError(f"Estado de mora inválido. Opciones: {', '.join(estados_validos)}.")
    ejecutar_query(
        "UPDATE MOROSIDAD SET estado_mora=?, observaciones=? WHERE id_morosidad=?",
        (
            estado_mora,
            observaciones.strip() if observaciones else None,
            int(id_morosidad),
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 5 — DASHBOARD Y ANALÍTICA
# ─────────────────────────────────────────────────────────────────────────────

def get_datos_dashboard():

    from paladinesfc.legado.db import obtener_conexion, ejecutar_query
 
    conn = obtener_conexion()
    cursor = conn.cursor()
 
    kpis_cols = []
    kpis_rows = []
    hist_cols  = []
    hist_rows  = []
 
    try:

        cursor.execute("EXEC SP_ObtenerDatosDashboard")
 
        if cursor.description:
            kpis_cols = [d[0] for d in cursor.description]
            kpis_rows = cursor.fetchall()
 
   
        hay_siguiente = cursor.nextset()
        if hay_siguiente and cursor.description:
            hist_cols = [d[0] for d in cursor.description]
            hist_rows = cursor.fetchall()
 
    finally:
        conn.close()
 

    try:
        _, total_morosos_rows = ejecutar_query(
            """
            SELECT COUNT(DISTINCT id_jugador) AS Total_Morosos
            FROM MOROSIDAD
            WHERE estado_mora IN ('en mora', 'pendiente')
            """,
            fetch=True
        )
        total_morosos = total_morosos_rows[0][0] if total_morosos_rows else 0
    except Exception:
        # Si la query falla, dejamos el valor que trajo el SP (mejor que crash)
        total_morosos = kpis_rows[0][4] if kpis_rows else 0
 

    if kpis_rows:
        fila_original = list(kpis_rows[0])
        fila_original[4] = total_morosos
        kpis_rows = [tuple(fila_original)]
 
    return (kpis_cols, kpis_rows), (hist_cols, hist_rows)
 
 

 
def get_estadisticas_asistencia(id_categoria=None):
    from paladinesfc.legado.db import ejecutar_query
    q = """
    SELECT
        j.nombres + ' ' + j.apellidos              AS jugador,
        j.documento,
        COUNT(sj.id_sesion_jugador)                AS sesiones_convocado,
        SUM(CAST(sj.asistencia AS INT))            AS sesiones_asistidas,
        CAST(
            SUM(CAST(sj.asistencia AS INT)) * 100.0
            / NULLIF(COUNT(sj.id_sesion_jugador), 0)
        AS DECIMAL(5,1))                           AS porcentaje_asistencia
    FROM SESION_JUGADOR sj
    INNER JOIN JUGADOR j ON sj.id_jugador = j.id_jugador
    INNER JOIN SESION  s ON sj.id_sesion  = s.id_sesion
    WHERE sj.convocado = 1
      AND (? IS NULL OR s.id_categoria = ?)
    GROUP BY j.id_jugador, j.nombres, j.apellidos, j.documento
    ORDER BY porcentaje_asistencia DESC
    """
    return ejecutar_query(q, (id_categoria, id_categoria), fetch=True)
 
 
def get_ingresos_por_concepto(anio=None):
    from paladinesfc.legado.db import ejecutar_query
    q = """
    SELECT
        cp.nombre_concepto,
        COUNT(p.id_pago)    AS cantidad_pagos,
        SUM(p.valor_pagado) AS total_recaudado
    FROM PAGO p
    INNER JOIN CONCEPTO_PAGO cp ON p.id_concepto = cp.id_concepto
    WHERE (? IS NULL OR YEAR(p.fecha_pago) = ?)
    GROUP BY cp.id_concepto, cp.nombre_concepto
    ORDER BY total_recaudado DESC
    """
    return ejecutar_query(q, (anio, anio), fetch=True)
 
 
def get_ranking_morosos():
    """
    Devuelve los jugadores con deuda activa.
    Incluye 'en mora' Y 'pendiente' (jugadores nuevos con matrícula sin pagar).
    """
    from paladinesfc.legado.db import ejecutar_query
    q = """
    SELECT
        j.nombres + ' ' + j.apellidos AS jugador,
        j.documento,
        COUNT(m.id_morosidad)         AS registros_mora,
        SUM(ISNULL(m.recargo, 0))     AS total_recargos,
        MAX(m.fecha_vencimiento)      AS ultimo_vencimiento
    FROM MOROSIDAD m
    INNER JOIN JUGADOR j ON m.id_jugador = j.id_jugador
    WHERE m.estado_mora IN ('en mora', 'pendiente')
    GROUP BY j.id_jugador, j.nombres, j.apellidos, j.documento
    ORDER BY total_recargos DESC, registros_mora DESC
    """
    return ejecutar_query(q, fetch=True)
 
 
def get_resumen_sesiones_por_categoria():
    from paladinesfc.legado.db import ejecutar_query
    q = """
    SELECT
        c.nombre_categoria,
        s.tipo_sesion,
        COUNT(s.id_sesion) AS total_sesiones,
        SUM(CASE WHEN s.estado = 'realizada' THEN 1 ELSE 0 END) AS realizadas,
        SUM(CASE WHEN s.estado = 'cancelada' THEN 1 ELSE 0 END) AS canceladas
    FROM SESION s
    INNER JOIN CATEGORIA c ON s.id_categoria = c.id_categoria
    GROUP BY c.id_categoria, c.nombre_categoria, s.tipo_sesion
    ORDER BY c.nombre_categoria, s.tipo_sesion
    """
    return ejecutar_query(q, fetch=True)
 
 
def get_jugadores_sin_pago_reciente(meses=1):
    from paladinesfc.legado.db import ejecutar_query
    q = """
    SELECT
        j.id_jugador,
        j.nombres + ' ' + j.apellidos AS jugador,
        j.documento,
        j.estado,
        MAX(p.fecha_pago)             AS ultimo_pago_mensualidad
    FROM JUGADOR j
    LEFT JOIN PAGO p
        ON p.id_jugador = j.id_jugador
        AND p.id_concepto IN (
            SELECT id_concepto FROM CONCEPTO_PAGO
            WHERE nombre_concepto LIKE '%Mensualidad%'
        )
    WHERE j.estado = 'activo'
    GROUP BY j.id_jugador, j.nombres, j.apellidos, j.documento, j.estado
    HAVING MAX(p.fecha_pago) < DATEADD(MONTH, -?, GETDATE())
        OR MAX(p.fecha_pago) IS NULL
    ORDER BY ultimo_pago_mensualidad ASC
    """
    return ejecutar_query(q, (int(meses),), fetch=True)