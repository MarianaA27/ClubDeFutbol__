"""Utilidades compartidas por los scripts de evaluación (conexión, conteos, tablas en Markdown)."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
for ruta in (RAIZ / "src", RAIZ):
    if str(ruta) not in sys.path:
        sys.path.insert(0, str(ruta))

from tests.integracion import base_prueba as bp  # noqa: E402

CARPETA_RESULTADOS = RAIZ / "docs" / "evaluacion"


def apuntar_legado_a(cfg) -> None:
    """Hace que el código legado (legado/db.py) use la base indicada en vez de la del club."""
    os.environ["PALADINES_DB_DATABASE"] = cfg.database


def filas(cfg, sql: str, parametros=()) -> list[tuple]:
    con = bp.conectar(cfg, autocommit=True)
    try:
        return [tuple(f) for f in con.cursor().execute(sql, parametros).fetchall()]
    finally:
        con.close()


def tablas(cfg) -> list[str]:
    return [f[0] for f in filas(cfg, "SELECT name FROM sys.tables WHERE is_ms_shipped = 0 ORDER BY name")]


def conteo_por_tabla(cfg) -> dict[str, int]:
    return {t: bp.contar(cfg, t) for t in tablas(cfg)}


def filas_huerfanas(cfg, tablas_padre=("JUGADOR", "TUTOR", "PROFESOR")) -> list[tuple[str, str, int]]:
    """Recorre TODAS las llaves foráneas que apuntan a las tablas indicadas y cuenta hijos sin padre."""
    marcadores = ", ".join("?" for _ in tablas_padre)
    llaves = filas(cfg, f"""
        SELECT OBJECT_NAME(fk.parent_object_id), cp.name, OBJECT_NAME(fk.referenced_object_id), cr.name
        FROM sys.foreign_keys fk
        JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
        JOIN sys.columns cp ON cp.object_id = fkc.parent_object_id AND cp.column_id = fkc.parent_column_id
        JOIN sys.columns cr ON cr.object_id = fkc.referenced_object_id AND cr.column_id = fkc.referenced_column_id
        WHERE OBJECT_NAME(fk.referenced_object_id) IN ({marcadores})
        ORDER BY 3, 1""", tuple(tablas_padre))
    resultado = []
    for hija, col_hija, padre, col_padre in llaves:
        n = bp.escalar(cfg, f"SELECT COUNT(*) FROM {hija} h WHERE h.{col_hija} IS NOT NULL AND NOT EXISTS "
                            f"(SELECT 1 FROM {padre} p WHERE p.{col_padre} = h.{col_hija})")
        resultado.append((f"{hija}.{col_hija}", f"{padre}.{col_padre}", int(n)))
    return resultado


def tabla_md(encabezados: list[str], cuerpo: list[list]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(c) for c in fila) + " |" for fila in cuerpo]
    return "\n".join(lineas)


def si_no(condicion: bool) -> str:
    return "Sí" if condicion else "**No**"


def encabezado(titulo: str, script: str, cfg) -> str:
    return (f"# {titulo}\n\nGenerado por `python evaluacion/{script}` el "
            f"{datetime.now():%Y-%m-%d %H:%M} sobre la base `{cfg.database}` "
            f"en `{cfg.server}`.\n")


def guardar(nombre: str, contenido: str) -> Path:
    CARPETA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA_RESULTADOS / nombre
    ruta.write_text(contenido, encoding="utf-8")
    return ruta
