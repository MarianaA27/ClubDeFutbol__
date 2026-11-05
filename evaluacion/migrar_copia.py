"""
Issue #15 — Aplicar las migraciones sobre una COPIA de la base real del club.

1. Hace una copia de seguridad (COPY_ONLY) de la base del club y la restaura con otro
   nombre (por defecto ClubFutbolDB_Copia). La base original no se modifica.
2. Cuenta las filas de todas las tablas de la copia.
3. Aplica, en orden, todas las migraciones de src/sql/migraciones/ sobre la copia
   (ignorando su "USE ClubFutbolDB", para no tocar la base real).
4. Vuelve a contar y muestra las consultas de verificación de cada migración.
5. Escribe docs/evaluacion/migracion-copia.md.

Uso (en la raíz del repositorio, con config.ini apuntando al servidor del club):
    python evaluacion/migrar_copia.py
    python evaluacion/migrar_copia.py --origen ClubFutbolDB --copia ClubFutbolDB_Copia
    python evaluacion/migrar_copia.py --sin-copiar      # la copia ya existe (p. ej. restaurada en SSMS)

Requiere permisos para BACKUP/RESTORE (el administrador del equipo los tiene).
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace

from _comun import RAIZ, bp, conteo_por_tabla, encabezado, guardar, si_no, tabla_md


def _lit(texto: str) -> str:
    """Literal N'...' de T-SQL (BACKUP/RESTORE no aceptan parámetros en todos los drivers)."""
    return "N'" + str(texto).replace("'", "''") + "'"


def copiar_base(cfg_copia, origen: str) -> str:
    """BACKUP ... WITH COPY_ONLY de la base del club y RESTORE con el nombre de la copia."""
    master = replace(cfg_copia, database="master")
    con = bp.conectar(master, autocommit=True)
    cursor = con.cursor()
    try:
        carpeta = cursor.execute("SELECT CAST(SERVERPROPERTY('InstanceDefaultDataPath') AS NVARCHAR(400))").fetchone()[0]
        carpeta = carpeta if carpeta.endswith(("\\", "/")) else carpeta + ("\\" if "\\" in carpeta else "/")
        respaldo = f"{carpeta}{origen}_antes_migraciones.bak"
        logicos = dict(cursor.execute(
            f"SELECT type_desc, name FROM [{origen}].sys.database_files").fetchall())
        cursor.execute(f"BACKUP DATABASE [{origen}] TO DISK = {_lit(respaldo)} WITH COPY_ONLY, INIT, "
                       f"NAME = N'{origen} antes de migraciones'")
        while cursor.nextset():          # BACKUP/RESTORE informan progreso; hay que consumirlo
            pass
        copia = cfg_copia.database
        cursor.execute(f"IF DB_ID(N'{copia}') IS NOT NULL BEGIN "
                       f"ALTER DATABASE [{copia}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; "
                       f"DROP DATABASE [{copia}]; END")
        cursor.execute(
            f"RESTORE DATABASE [{copia}] FROM DISK = {_lit(respaldo)} WITH "
            f"MOVE {_lit(logicos['ROWS'])} TO {_lit(carpeta + copia + '.mdf')}, "
            f"MOVE {_lit(logicos['LOG'])} TO {_lit(carpeta + copia + '_log.ldf')}, RECOVERY")
        while cursor.nextset():
            pass
        return respaldo
    finally:
        con.close()


def aplicar_con_verificacion(cfg, ruta) -> list[list[tuple]]:
    """Ejecuta una migración lote por lote y devuelve las filas de sus consultas de verificación."""
    con = bp.conectar(cfg, autocommit=True)
    resultados = []
    try:
        cursor = con.cursor()
        for lote in bp.lotes_de(ruta):
            cursor.execute(lote)
            while True:
                if cursor.description is not None:
                    resultados.append([tuple(f) for f in cursor.fetchall()])
                if not cursor.nextset():
                    break
    finally:
        con.close()
    return resultados


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--origen", default="ClubFutbolDB", help="Base real del club (solo se lee y se respalda).")
    parser.add_argument("--copia", default="ClubFutbolDB_Copia", help="Nombre de la copia (debe empezar por ClubFutbolDB_).")
    parser.add_argument("--sin-copiar", action="store_true", help="No respaldar/restaurar: usar una copia ya existente.")
    args = parser.parse_args()

    if not args.origen.replace("_", "").isalnum():
        parser.error("Nombre de base de origen inválido.")
    cfg = bp.config_prueba(args.copia)
    if args.sin_copiar:
        respaldo = "(copia restaurada previamente)"
    else:
        print(f"Respaldando {args.origen} y restaurándola como {args.copia}...")
        respaldo = copiar_base(cfg, args.origen)
        print(f"  copia de seguridad: {respaldo}")

    antes = conteo_por_tabla(cfg)
    verificaciones = []
    for migracion in bp.migraciones():
        print(f"Aplicando {migracion.name}...")
        verificaciones.append((migracion.name, aplicar_con_verificacion(cfg, migracion)))
    despues = conteo_por_tabla(cfg)

    # La segunda ejecución debe ser inocua (idempotencia)
    for migracion in bp.migraciones():
        aplicar_con_verificacion(cfg, migracion)
    idempotente = conteo_por_tabla(cfg) == despues

    cuerpo_conteos = [[t, antes.get(t, "—"), despues.get(t, "—"),
                       "" if antes.get(t) == despues.get(t) else "**cambió**"] for t in sorted(despues)]
    bloques = []
    for nombre, resultados in verificaciones:
        filas_verif = [list(f) for r in resultados[-1:] for f in r]   # la última consulta es la verificación
        bloques.append(f"### {nombre}\n\n" + (tabla_md(["Verificación", "Resultado"], filas_verif)
                                               if filas_verif else "_(sin consulta de verificación)_"))
    cambiadas = [t for t in despues if antes.get(t) != despues.get(t)]

    md = encabezado("Migraciones aplicadas sobre una copia de la base real", "migrar_copia.py", cfg) + f"""
Base de origen (no se modificó): `{args.origen}`. Copia de seguridad: `{respaldo}`.

## 1. Conteo de filas antes y después de las migraciones

{tabla_md(["Tabla", "Antes", "Después", ""], cuerpo_conteos)}

Tablas con cambios: {", ".join(f"`{t}`" for t in cambiadas) or "ninguna"}.
La migración 001 solo puede cambiar `JUGADOR_TUTOR`: borra vínculos duplicados y repara
jugadores sin exactamente un acudiente principal.

## 2. Consultas de verificación de cada migración

{chr(10).join(bloques)}

## 3. Idempotencia

Ejecutar de nuevo todas las migraciones no cambia ningún conteo: {si_no(idempotente)}.
"""
    ruta = guardar("migracion-copia.md", md)
    print(md)
    print(f"Escrito en {ruta.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
