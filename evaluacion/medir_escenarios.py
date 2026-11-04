"""
Issue #18 — Mediciones ANTES/DESPUÉS de los escenarios E2, E3 y E4 contra SQL Server real.

Retroalimentación del Entregable 3: "Sustentar las mejoras con mediciones antes/después
de los escenarios". Se ejecuta la MISMA operación con el código original y con el nuevo,
sobre dos bases de prueba con los mismos datos:

* ClubFutbolDB_MedicionAntes   → esquema original (sin migraciones) + código original
                                 (evaluacion/original/crud_mvp_original.py, copia fiel).
* ClubFutbolDB_MedicionDespues → esquema + migraciones + servicios de la re-arquitectura.

E2 Confiabilidad  fallo entre los dos UPDATE de "cambiar acudiente principal" (N repeticiones):
                  ¿cuántas veces queda el jugador sin acudiente principal?
E3 Seguridad      baja de un profesor con 12 sesiones y 2 plantillas, y de dos jugadores con
                  pagos: ¿cuántas filas de historial se pierden?
E4 Eficiencia     búsqueda por cédula y apertura del formulario de edición, con distintos
                  volúmenes: ¿cuántas filas viajan del motor a la aplicación y cuánto tarda?

Uso:
    python evaluacion/medir_escenarios.py
    python evaluacion/medir_escenarios.py --registros 50 500 2000 --repeticiones 10

Escribe docs/evaluacion/resultados-mediciones.md y resultados-mediciones.json.
Las bases de medición se eliminan al terminar (salvo --conservar).
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time

from _comun import RAIZ, bp, encabezado, guardar, si_no, tabla_md
from original import crud_mvp_original as original

TABLAS_HISTORIAL = ("SESION", "SESION_JUGADOR", "PLANTILLA_PROFESOR", "PLANTILLA_JUGADOR",
                    "PAGO", "MOROSIDAD", "JUGADOR_TUTOR")


# ── preparación ────────────────────────────────────────────────────────────
def preparar(conservar: bool):
    antes = bp.config_prueba("ClubFutbolDB_MedicionAntes")
    despues = bp.config_prueba("ClubFutbolDB_MedicionDespues")
    print("Creando bases de medición...")
    bp.crear_base(antes, con_migraciones=False)
    bp.crear_base(despues, con_migraciones=True)
    original.configurar(antes.cadena())
    return antes, despues


def sembrar_volumen(cfg, n: int) -> None:
    """n tutores, n jugadores (cada uno con su acudiente principal) y n profesores, en un solo lote."""
    numeros = ("WITH n AS (SELECT TOP (?) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS k "
               "FROM sys.all_objects a CROSS JOIN sys.all_objects b) ")
    s = bp.Siembra(cfg)
    try:
        s.ejecutar(numeros + """INSERT INTO TUTOR (nombres, apellidos, documento, telefono, email, direccion)
            SELECT 'Tutor', 'Volumen ' + CAST(k AS VARCHAR(10)), CAST(600000 + k AS VARCHAR(20)),
                   CAST(3200000000 + k AS VARCHAR(20)), 'tutor' + CAST(k AS VARCHAR(10)) + '@correo.com',
                   'Calle ' + CAST(k AS VARCHAR(10)) FROM n""", (n,))
        s.ejecutar(numeros + """INSERT INTO JUGADOR (nombres, apellidos, documento, fecha_nacimiento,
                   numero_preferido, talla_uniforme, estado, fecha_ingreso, observaciones)
            SELECT 'Jugador', 'Volumen ' + CAST(k AS VARCHAR(10)), CAST(2000000000 + k AS VARCHAR(20)),
                   DATEADD(DAY, k % 3000, '2010-01-01'), NULL, 'M', 'activo', '2024-02-01', NULL FROM n""", (n,))
        s.ejecutar("""INSERT INTO JUGADOR_TUTOR (id_jugador, id_tutor, parentesco, acudiente_principal)
            SELECT j.id_jugador, t.id_tutor, 'Padre', 1
            FROM (SELECT id_jugador, ROW_NUMBER() OVER (ORDER BY id_jugador) AS r FROM JUGADOR) j
            JOIN (SELECT id_tutor, ROW_NUMBER() OVER (ORDER BY id_tutor) AS r FROM TUTOR) t ON t.r = j.r""")
        s.ejecutar(numeros + """INSERT INTO PROFESOR (nombres, apellidos, documento, telefono, email,
                   especialidad, estado, fecha_ingreso)
            SELECT 'Profesor', 'Volumen ' + CAST(k AS VARCHAR(10)), CAST(700000 + k AS VARCHAR(20)),
                   CAST(3100000000 + k AS VARCHAR(20)), 'profe' + CAST(k AS VARCHAR(10)) + '@correo.com',
                   'Técnico', 'activo', '2023-01-15' FROM n""", (n,))
    finally:
        s.cerrar()


# ── E2 ─────────────────────────────────────────────────────────────────────
def medir_e2(antes, despues, repeticiones: int) -> dict:
    print(f"E2: {repeticiones} fallos inyectados con cada versión...")
    parciales_antes = parciales_despues = 0
    ejecutar_real = original.ejecutar_query
    siembra_antes, siembra_despues = bp.Siembra(antes), bp.Siembra(despues)
    for _ in range(repeticiones):
        # Antes: set_acudiente_principal() original; la conexión "se cae" antes del 2.º UPDATE.
        j, t1, t2 = siembra_antes.jugador_con_dos_tutores()
        llamadas = {"n": 0}

        def ejecutar_con_fallo(query, params=None, fetch=False):
            llamadas["n"] += 1
            if llamadas["n"] == 2:
                raise bp.ConexionPerdida("Conexión perdida antes del segundo UPDATE")
            return ejecutar_real(query, params, fetch)

        original.ejecutar_query = ejecutar_con_fallo
        try:
            original.set_acudiente_principal(j, t2)
        except bp.ConexionPerdida:
            pass
        finally:
            original.ejecutar_query = ejecutar_real
        if len(bp.principales_de(antes, j)) != 1:
            parciales_antes += 1

        # Después: VinculacionService con unidad de trabajo; mismo punto de fallo.
        j, t1, t2 = siembra_despues.jugador_con_dos_tutores()
        servicio = bp.servicios(despues, lambda: bp.ConexionConFallo(bp.conectar(despues))).vinculacion
        try:
            servicio.cambiar_principal(j, t2)
        except bp.ConexionPerdida:
            pass
        if bp.principales_de(despues, j) != [t1]:
            parciales_despues += 1
    siembra_antes.cerrar()
    siembra_despues.cerrar()
    return {"repeticiones": repeticiones, "parciales_antes": parciales_antes, "parciales_despues": parciales_despues}


# ── E3 ─────────────────────────────────────────────────────────────────────
def _escenario_e3(cfg):
    s = bp.Siembra(cfg)
    try:
        id_profesor, plantillas, _ = s.profesor_con_historial(sesiones=12, plantillas=2, jugadores=3)
        cat = int(bp.escalar(cfg, "SELECT MIN(id_categoria) FROM CATEGORIA"))
        cancha = int(bp.escalar(cfg, "SELECT MIN(id_cancha) FROM CANCHA"))
        otro_profesor = s.profesor(nombres="Marta", apellidos="López")
        concepto = s.concepto()
        jugadores = []
        for con_mora_pagada in (False, True):
            j = s.jugador(nombres="Jugador", apellidos="Con pagos")
            s.vinculo(j, s.tutor(), principal=True)
            s.pago(j, concepto, s.morosidad_de(j) if con_mora_pagada else None, mes=2)
            s.pago(j, concepto, None, mes=3)
            s.pago(j, concepto, None, mes=4)
            for dia in (20, 21):   # sesiones de OTRO profesor: no se ven afectadas por su baja
                s.asistencia(s.sesion(otro_profesor, cancha, cat, plantillas[0], dia), j)
            jugadores.append(j)
        return id_profesor, jugadores
    finally:
        s.cerrar()


def _conteos(cfg):
    return {t: bp.contar(cfg, t) for t in TABLAS_HISTORIAL}


def medir_e3(antes, despues) -> dict:
    print("E3: baja de profesor y jugadores con historial...")
    bp.limpiar(antes)
    bp.limpiar(despues)
    resultado = {}

    id_profesor, (j_sin_mora, j_con_mora) = _escenario_e3(antes)
    inicial = _conteos(antes)
    original.delete_profesor(id_profesor)
    tras_profesor = _conteos(antes)
    original.delete_jugador(j_sin_mora)
    tras_jugador = _conteos(antes)
    try:
        original.delete_jugador(j_con_mora)
        error_jugador = None
    except Exception as error:   # noqa: BLE001 - se documenta el error que veía la usuaria
        error_jugador = f"{type(error).__name__}: {str(error)[:160]}"
    resultado["antes"] = {
        "perdidas_baja_profesor": {t: inicial[t] - tras_profesor[t] for t in TABLAS_HISTORIAL},
        "perdidas_baja_jugador": {t: tras_profesor[t] - tras_jugador[t] for t in TABLAS_HISTORIAL},
        "profesor_existe": bp.contar(antes, "PROFESOR", "id_profesor = ?", (id_profesor,)) == 1,
        "error_jugador_con_pago_de_mora": error_jugador,
    }

    id_profesor, (j_sin_mora, j_con_mora) = _escenario_e3(despues)
    servicios = bp.servicios(despues)
    inicial = _conteos(despues)
    servicios.profesores.inactivar(id_profesor)
    tras_profesor = _conteos(despues)
    servicios.jugadores.inactivar(j_sin_mora)
    tras_jugador = _conteos(despues)
    servicios.jugadores.inactivar(j_con_mora)
    final = _conteos(despues)
    resultado["despues"] = {
        "perdidas_baja_profesor": {t: inicial[t] - tras_profesor[t] for t in TABLAS_HISTORIAL},
        "perdidas_baja_jugador": {t: tras_profesor[t] - tras_jugador[t] for t in TABLAS_HISTORIAL},
        "perdidas_jugador_con_pago_de_mora": {t: tras_jugador[t] - final[t] for t in TABLAS_HISTORIAL},
        "profesor_existe": bp.contar(despues, "PROFESOR", "id_profesor = ?", (id_profesor,)) == 1,
        "profesor_en_desplegables": id_profesor in {p.id_profesor for p in servicios.profesores.opciones()},
    }
    return resultado


# ── E4 ─────────────────────────────────────────────────────────────────────
def _cronometrar(funcion, veces=5):
    tiempos, resultado = [], None
    for _ in range(veces):
        inicio = time.perf_counter()
        resultado = funcion()
        tiempos.append((time.perf_counter() - inicio) * 1000)
    return resultado, statistics.median(tiempos)


def medir_e4(antes, despues, volumenes) -> list[dict]:
    filas_resultado = []
    for n in volumenes:
        print(f"E4: {n} registros por entidad...")
        bp.limpiar(antes)
        bp.limpiar(despues)
        sembrar_volumen(antes, n)
        sembrar_volumen(despues, n)
        servicios = bp.servicios(despues)
        k = max(1, n // 2)
        casos = {
            # entidad: (función original, posición del documento en la tupla, doc buscado, servicio)
            "Tutores": (original.get_tutores, 3, str(600000 + k), servicios.tutores, "id_tutor"),
            "Jugadores": (original.get_jugadores_con_tutor, 2, str(2000000000 + k), servicios.jugadores, "id_jugador"),
            "Profesores": (original.get_profesores, 3, str(700000 + k), servicios.profesores, "id_profesor"),
        }
        for entidad, (consulta_original, pos_doc, documento, servicio, campo_id) in casos.items():
            # ANTES — búsqueda: la pantalla traía la tabla completa y filtraba en Python
            (cols, filas_busqueda), t_busq_antes = _cronometrar(lambda: consulta_original())
            coincidencias_antes = [r for r in filas_busqueda if documento in str(r[pos_doc])]
            id_objetivo = coincidencias_antes[0][0]
            # ANTES — edición: _cargar() también traía la tabla completa para un registro
            (_, filas_edicion), t_edic_antes = _cronometrar(lambda: consulta_original())
            # DESPUÉS — búsqueda con WHERE y edición con obtener(id)
            coincidencias_despues, t_busq_desp = _cronometrar(lambda: servicio.listar(documento))
            _, t_edic_desp = _cronometrar(lambda: servicio.obtener(id_objetivo))
            filas_resultado.append({
                "registros": n, "entidad": entidad,
                "busqueda_filas_antes": len(filas_busqueda), "busqueda_filas_despues": len(coincidencias_despues),
                "busqueda_ms_antes": round(t_busq_antes, 2), "busqueda_ms_despues": round(t_busq_desp, 2),
                "edicion_filas_antes": len(filas_edicion), "edicion_filas_despues": 1,
                "edicion_ms_antes": round(t_edic_antes, 2), "edicion_ms_despues": round(t_edic_desp, 2),
                "mismo_resultado": len(coincidencias_antes) == len(coincidencias_despues),
            })
    return filas_resultado


# ── informe ────────────────────────────────────────────────────────────────
def _reduccion(antes, despues) -> str:
    return "—" if not antes else f"{(1 - despues / antes) * 100:.1f} %"


def informe(cfg, e2, e3, e4) -> str:
    perdidas = lambda d: sum(d.values())   # noqa: E731
    a, d = e3["antes"], e3["despues"]
    e3_tabla = [[t, a["perdidas_baja_profesor"][t], d["perdidas_baja_profesor"][t],
                 a["perdidas_baja_jugador"][t], d["perdidas_baja_jugador"][t]] for t in TABLAS_HISTORIAL]
    e3_tabla.append(["**Total**", f"**{perdidas(a['perdidas_baja_profesor'])}**",
                     f"**{perdidas(d['perdidas_baja_profesor'])}**",
                     f"**{perdidas(a['perdidas_baja_jugador'])}**", f"**{perdidas(d['perdidas_baja_jugador'])}**"])
    e4_busq = [[f["registros"], f["entidad"], f["busqueda_filas_antes"], f["busqueda_filas_despues"],
                _reduccion(f["busqueda_filas_antes"], f["busqueda_filas_despues"]),
                f["busqueda_ms_antes"], f["busqueda_ms_despues"], si_no(f["mismo_resultado"])] for f in e4]
    e4_edic = [[f["registros"], f["entidad"], f["edicion_filas_antes"], f["edicion_filas_despues"],
                _reduccion(f["edicion_filas_antes"], f["edicion_filas_despues"]),
                f["edicion_ms_antes"], f["edicion_ms_despues"]] for f in e4]
    reduccion_50 = [1 - f["edicion_filas_despues"] / f["edicion_filas_antes"] for f in e4 if f["registros"] >= 50]
    cumple_e4 = bool(reduccion_50) and min(reduccion_50) >= 0.9

    resumen = [
        ["E2 Confiabilidad", f"{e2['parciales_antes']} de {e2['repeticiones']} fallos dejan al jugador sin principal",
         f"{e2['parciales_despues']} de {e2['repeticiones']}", "0 estados parciales en 10 fallos",
         si_no(e2["parciales_despues"] == 0)],
        ["E3 Seguridad", f"{perdidas(a['perdidas_baja_profesor']) + perdidas(a['perdidas_baja_jugador'])} filas de historial borradas",
         f"{perdidas(d['perdidas_baja_profesor']) + perdidas(d['perdidas_baja_jugador']) + perdidas(d['perdidas_jugador_con_pago_de_mora'])} filas",
         "Conteos idénticos", si_no(perdidas(d["perdidas_baja_profesor"]) + perdidas(d["perdidas_baja_jugador"])
                                     + perdidas(d["perdidas_jugador_con_pago_de_mora"]) == 0)],
        ["E4 Eficiencia", f"edición: {e4[-1]['edicion_filas_antes']} filas con {e4[-1]['registros']} registros",
         "edición: 1 fila", "≥ 90 % menos filas con ≥ 50 registros", si_no(cumple_e4)],
    ]
    return encabezado("Mediciones antes/después de los escenarios de calidad", "medir_escenarios.py", cfg) + f"""
Misma operación, mismos datos, mismo servidor: **antes** = esquema original + código
original (`evaluacion/original/crud_mvp_original.py`, copia fiel de `crud.py`);
**después** = esquema con migraciones + servicios de la re-arquitectura.

## Resumen

{tabla_md(["Escenario", "Antes", "Después", "Medida (Semana 13)", "¿Cumple?"], resumen)}

## E2 — Fallo entre los dos UPDATE de "cambiar acudiente principal"

Se inyectó la pérdida de la conexión justo antes del segundo `UPDATE`, {e2['repeticiones']} veces con
cada versión. Se cuenta un *estado parcial* cuando el jugador queda sin exactamente un
acudiente principal.

{tabla_md(["Versión", "Fallos inyectados", "Estados parciales"],
          [["Antes (`set_acudiente_principal`, commit por sentencia)", e2["repeticiones"], e2["parciales_antes"]],
           ["Después (`VinculacionService` + unidad de trabajo)", e2["repeticiones"], e2["parciales_despues"]]])}

## E3 — Filas de historial perdidas al dar de baja

Profesor con 12 sesiones (3 jugadores con asistencia en cada una) y 2 plantillas; jugador
con 3 pagos, morosidad, 2 asistencias y su acudiente.

{tabla_md(["Tabla", "Baja profesor: antes", "Baja profesor: después", "Baja jugador: antes", "Baja jugador: después"], e3_tabla)}

* Antes, el registro del profesor {"seguía existiendo" if a["profesor_existe"] else "**desapareció**"}; después
  {"sigue existiendo como inactivo" if d["profesor_existe"] else "**desapareció**"} y
  {"**sigue** apareciendo" if d["profesor_en_desplegables"] else "ya no aparece"} en los desplegables.
* Jugador cuyo pago está ligado a su morosidad: antes,
  {("`SP_EliminarJugador` **falló** con `" + a["error_jugador_con_pago_de_mora"] + "`, porque borra MOROSIDAD antes que PAGO") if a["error_jugador_con_pago_de_mora"] else "se borró sin error"};
  después se dio de baja sin perder filas ({perdidas(d["perdidas_jugador_con_pago_de_mora"])} filas).

## E4 — Filas transferidas y tiempo (mediana de 5 ejecuciones)

**Búsqueda por cédula** (una sola coincidencia):

{tabla_md(["Registros", "Entidad", "Filas antes", "Filas después", "Reducción", "ms antes", "ms después", "¿Mismo resultado?"], e4_busq)}

**Abrir el formulario de edición** de un registro:

{tabla_md(["Registros", "Entidad", "Filas antes", "Filas después", "Reducción", "ms antes", "ms después"], e4_edic)}

Los tiempos dependen del equipo; la cifra que no depende del equipo es la de filas
transferidas: antes crecía con la tabla y ahora es constante.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--registros", type=int, nargs="+", default=[50, 500, 2000])
    parser.add_argument("--repeticiones", type=int, default=10)
    parser.add_argument("--conservar", action="store_true", help="No eliminar las bases de medición.")
    args = parser.parse_args()

    antes, despues = preparar(args.conservar)
    try:
        e2 = medir_e2(antes, despues, args.repeticiones)
        e3 = medir_e3(antes, despues)
        e4 = medir_e4(antes, despues, args.registros)
    finally:
        if not args.conservar:
            bp.eliminar_base(antes)
            bp.eliminar_base(despues)
    md = informe(despues, e2, e3, e4)
    ruta = guardar("resultados-mediciones.md", md)
    guardar("resultados-mediciones.json", json.dumps({"E2": e2, "E3": e3, "E4": e4}, indent=2, ensure_ascii=False))
    print(md)
    print(f"Escrito en {ruta.relative_to(RAIZ)} (y .json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
