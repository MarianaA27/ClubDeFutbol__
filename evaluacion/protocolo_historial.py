"""
Issue #16 — Protocolo de preservación del historial (Entregable 1, §3.5) — Escenario E3.

Ejecuta los seis criterios del protocolo sobre una base REAL:

    1. Preparación: conteos iniciales; un profesor con ≥ 3 sesiones y un jugador con
       ≥ 3 pagos y al menos una asistencia.
    2. Conservación: tras la baja, los conteos de historial no cambian y el registro
       existe con estado 'inactivo'.
    3. Exclusión operativa: el profesor no aparece en los desplegables; el jugador no
       aparece entre los convocables ni entre los asignables a plantilla.
    4. Consulta histórica: las sesiones siguen mostrando el nombre del profesor y los
       reportes de asistencia y de ingresos dan los mismos totales.
    5. Reversibilidad: reactivar restituye todo sin reingresar datos.
    6. Integridad referencial: cero filas huérfanas en cada llave foránea hacia
       JUGADOR, TUTOR y PROFESOR.

Las bajas se hacen con los MISMOS servicios que usa la aplicación; las comprobaciones de
los criterios 3 y 4 usan las MISMAS consultas de las pantallas legadas (Sesiones,
Plantillas, Dashboard). Al final se reactiva todo: la base queda como estaba.

Uso:
    python evaluacion/protocolo_historial.py --base ClubFutbolDB_Copia      # copia de la base real (#15)
    python evaluacion/protocolo_historial.py --sembrar                      # base de prueba con datos sembrados
    python evaluacion/protocolo_historial.py --base ClubFutbolDB_Copia --id-profesor 3 --id-jugador 12

Escribe docs/evaluacion/protocolo-historial.md. Termina con código 1 si algún criterio falla.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict

from _comun import (RAIZ, apuntar_legado_a, bp, encabezado, filas, filas_huerfanas, guardar,
                    si_no, tabla_md)

TABLAS = ("SESION", "SESION_JUGADOR", "PLANTILLA_JUGADOR", "PLANTILLA_PROFESOR", "PAGO",
          "MOROSIDAD", "JUGADOR_TUTOR")


def conteos(cfg) -> dict[str, int]:
    return {t: bp.contar(cfg, t) for t in TABLAS}


def elegir_profesor(cfg, forzado):
    if forzado:
        return forzado
    fila = filas(cfg, """SELECT TOP 1 p.id_profesor FROM PROFESOR p JOIN SESION s ON s.id_profesor = p.id_profesor
                         WHERE p.estado = 'activo' GROUP BY p.id_profesor HAVING COUNT(*) >= 3
                         ORDER BY COUNT(*) DESC""")
    return fila[0][0] if fila else None


def elegir_jugador(cfg, forzado):
    if forzado:
        return forzado
    fila = filas(cfg, """SELECT TOP 1 j.id_jugador FROM JUGADOR j
                         WHERE j.estado = 'activo'
                           AND (SELECT COUNT(*) FROM PAGO p WHERE p.id_jugador = j.id_jugador) >= 3
                           AND EXISTS (SELECT 1 FROM SESION_JUGADOR sj WHERE sj.id_jugador = j.id_jugador)
                           AND NOT EXISTS (SELECT 1 FROM PLANTILLA_JUGADOR pj
                                           WHERE pj.id_jugador = j.id_jugador AND pj.estado = 'activo')
                         ORDER BY (SELECT COUNT(*) FROM PAGO p WHERE p.id_jugador = j.id_jugador) DESC""")
    return fila[0][0] if fila else None


def sembrar(cfg):
    """Datos representativos para quien no tiene la base del club: mismo escenario que E3."""
    bp.crear_base(cfg)
    s = bp.Siembra(cfg)
    try:
        id_profesor, plantillas, _ = s.profesor_con_historial(sesiones=12, plantillas=2, jugadores=4)
        j, _, _ = s.jugador_con_dos_tutores()
        concepto = s.concepto()
        s.pago(j, concepto, s.morosidad_de(j), mes=2)
        s.pago(j, concepto, None, mes=3)
        s.pago(j, concepto, None, mes=4)
        cat = int(bp.escalar(cfg, "SELECT MIN(id_categoria) FROM CATEGORIA"))
        cancha = int(bp.escalar(cfg, "SELECT MIN(id_cancha) FROM CANCHA"))
        for dia in (20, 21):
            s.asistencia(s.sesion(id_profesor, cancha, cat, plantillas[0], dia), j)
        s.plantilla_jugador(plantillas[1], j, estado="inactivo")
    finally:
        s.cerrar()


def reportes(legado, id_sesion: int | None, id_categoria: int | None):
    """Las mismas consultas que usan las pantallas legadas de Sesiones, Plantillas y Dashboard."""
    _, asistencia = legado.get_estadisticas_asistencia()
    _, ingresos = legado.get_ingresos_por_concepto()
    return {
        "profesores_activos": {f[0] for f in legado.get_profesores_activos()},
        "convocables": ({f[0] for f in legado.get_jugadores_convocables(id_sesion)[1]} if id_sesion else set()),
        "asignables": ({f[0] for f in legado.filtrar_jugadores_para_plantilla(id_categoria)[1]}
                       if id_categoria else set()),
        "asistencia": sorted((str(f[1]), int(f[2]), int(f[3] or 0)) for f in asistencia),
        "ingresos": sorted(tuple(str(c) for c in f) for f in ingresos),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    origen = parser.add_mutually_exclusive_group(required=True)
    origen.add_argument("--base", help="Copia de la base real (debe empezar por ClubFutbolDB_).")
    origen.add_argument("--sembrar", action="store_true", help="Crear ClubFutbolDB_Protocolo con datos de prueba.")
    parser.add_argument("--id-profesor", type=int)
    parser.add_argument("--id-jugador", type=int)
    args = parser.parse_args()

    cfg = bp.config_prueba(args.base or "ClubFutbolDB_Protocolo")
    if args.sembrar:
        print(f"Creando {cfg.database} con datos de prueba...")
        sembrar(cfg)
    apuntar_legado_a(cfg)
    from paladinesfc.legado import crud as legado      # importado DESPUÉS de apuntar a la base
    servicios = bp.servicios(cfg)

    # ── 1. Preparación ─────────────────────────────────────────────────────
    id_profesor = elegir_profesor(cfg, args.id_profesor)
    id_jugador = elegir_jugador(cfg, args.id_jugador)
    if not id_profesor or not id_jugador:
        print("No hay un profesor con ≥ 3 sesiones o un jugador con ≥ 3 pagos, una asistencia y sin "
              "plantillas activas. Use --id-profesor/--id-jugador o --sembrar.", file=sys.stderr)
        return 1
    profesor_antes = asdict(servicios.profesores.obtener(id_profesor))
    jugador_antes = asdict(servicios.jugadores.obtener(id_jugador))
    sesion = filas(cfg, "SELECT TOP 1 id_sesion, id_categoria FROM SESION ORDER BY id_sesion DESC")
    id_sesion, id_categoria = (sesion[0] if sesion else (None, None))
    # Para el criterio 3 se usa una categoría que incluya el año de nacimiento del jugador
    categoria_jugador = filas(cfg, """SELECT TOP 1 c.id_categoria FROM CATEGORIA c JOIN JUGADOR j
                                      ON YEAR(j.fecha_nacimiento) BETWEEN c.anio_minimo AND c.anio_maximo
                                      WHERE j.id_jugador = ?""", (id_jugador,))
    id_categoria = categoria_jugador[0][0] if categoria_jugador else id_categoria

    inicial = conteos(cfg)
    rep_inicial = reportes(legado, id_sesion, id_categoria)
    sesiones_prof = bp.contar(cfg, "SESION", "id_profesor = ?", (id_profesor,))
    nombre_en_sesiones = bp.contar(cfg, "SESION s JOIN PROFESOR p ON p.id_profesor = s.id_profesor",
                                   "p.id_profesor = ?", (id_profesor,))
    pagos_jug = bp.contar(cfg, "PAGO", "id_jugador = ?", (id_jugador,))
    asist_jug = bp.contar(cfg, "SESION_JUGADOR", "id_jugador = ?", (id_jugador,))

    # ── baja con los servicios de la aplicación ───────────────────────────
    servicios.profesores.inactivar(id_profesor)
    servicios.jugadores.inactivar(id_jugador)
    tras_baja = conteos(cfg)
    rep_baja = reportes(legado, id_sesion, id_categoria)
    estado_prof = bp.escalar(cfg, "SELECT estado FROM PROFESOR WHERE id_profesor = ?", (id_profesor,))
    estado_jug = bp.escalar(cfg, "SELECT estado FROM JUGADOR WHERE id_jugador = ?", (id_jugador,))
    opciones_baja = {p.id_profesor for p in servicios.profesores.opciones()}
    huerfanas = filas_huerfanas(cfg)

    # ── 5. reversibilidad ─────────────────────────────────────────────────
    servicios.profesores.reactivar(id_profesor)
    servicios.jugadores.reactivar(id_jugador)
    profesor_despues = asdict(servicios.profesores.obtener(id_profesor))
    jugador_despues = asdict(servicios.jugadores.obtener(id_jugador))
    opciones_reactivado = {p.id_profesor for p in servicios.profesores.opciones()}
    rep_final = reportes(legado, id_sesion, id_categoria)

    criterios = [
        ("1. Preparación", f"Profesor {id_profesor} con {sesiones_prof} sesiones; jugador {id_jugador} con "
                           f"{pagos_jug} pagos y {asist_jug} asistencias",
         sesiones_prof >= 3 and pagos_jug >= 3 and asist_jug >= 1),
        ("2. Conservación", "Conteos de historial idénticos tras las bajas; estados 'inactivo'",
         tras_baja == inicial and estado_prof == "inactivo" and estado_jug == "inactivo"),
        ("3. Exclusión operativa", "Profesor fuera de los desplegables (servicio y legado); jugador fuera de "
                                   "convocables y asignables",
         id_profesor not in opciones_baja and id_profesor not in rep_baja["profesores_activos"]
         and id_jugador not in rep_baja["convocables"] and id_jugador not in rep_baja["asignables"]),
        ("4. Consulta histórica", "Sesiones con el nombre del profesor; reportes de asistencia e ingresos iguales",
         bp.contar(cfg, "SESION s JOIN PROFESOR p ON p.id_profesor = s.id_profesor", "p.id_profesor = ?",
                   (id_profesor,)) == nombre_en_sesiones
         and rep_baja["asistencia"] == rep_inicial["asistencia"] and rep_baja["ingresos"] == rep_inicial["ingresos"]),
        ("5. Reversibilidad", "Tras reactivar, mismos datos y de nuevo disponible",
         profesor_despues == profesor_antes and jugador_despues == jugador_antes
         and id_profesor in opciones_reactivado and rep_final["asistencia"] == rep_inicial["asistencia"]),
        ("6. Integridad referencial", f"{sum(n for *_, n in huerfanas)} filas huérfanas en {len(huerfanas)} llaves foráneas",
         all(n == 0 for *_, n in huerfanas)),
    ]
    todo_bien = all(ok for *_, ok in criterios)

    md = encabezado("Protocolo de preservación del historial (E3)", "protocolo_historial.py", cfg) + f"""
Origen de los datos: {"datos de prueba sembrados (`--sembrar`)" if args.sembrar else "copia de la base real del club"}.
Las bajas se hicieron con `ProfesorService.inactivar` y `JugadorService.inactivar`; al final
se reactivaron, así que la base quedó como estaba.

## Resultado por criterio (Entregable 1, §3.5)

{tabla_md(["Criterio", "Comprobación", "¿Cumple?"], [[c, d, si_no(ok)] for c, d, ok in criterios])}

**Resultado global: {"CUMPLE los seis criterios" if todo_bien else "NO cumple todos los criterios"}.**

## Conteos de historial

{tabla_md(["Tabla", "Inicial", "Tras las bajas", "Diferencia"],
          [[t, inicial[t], tras_baja[t], tras_baja[t] - inicial[t]] for t in TABLAS])}

## Llaves foráneas revisadas (criterio 6)

{tabla_md(["Columna hija", "Referencia", "Huérfanas"], [list(h) for h in huerfanas])}

## Comparación con el sistema original

En el sistema original la misma baja ejecutaba `SP_EliminarProfesor` y `SP_EliminarJugador`,
que borran en cascada las sesiones, asistencias, pagos y morosidad. La medición antes/después
de ese borrado está en `docs/evaluacion/resultados-mediciones.md` (escenario E3).
"""
    ruta = guardar("protocolo-historial.md", md)
    print(md)
    print(f"Escrito en {ruta.relative_to(RAIZ)}")
    return 0 if todo_bien else 1


if __name__ == "__main__":
    sys.exit(main())
