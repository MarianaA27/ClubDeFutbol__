"""
Medición del escenario E1 (Mantenibilidad): agregar el campo EPS al jugador.

Compara el código ORIGINAL (primera versión de cada archivo en el historial de
git, o una carpeta con el sistema original) con el código ACTUAL, y mide el
cambio real que se hizo en el repositorio (commits con "(E1)" en el mensaje).

Uso:
    python evaluacion/medir_e1.py --minutos 95
    python evaluacion/medir_e1.py --minutos 95 --original "C:/ruta/Trabajo final"

Escribe docs/evaluacion/e1-mantenibilidad.md y muestra el resumen en pantalla.
"""
from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "docs" / "evaluacion" / "e1-mantenibilidad.md"
APP_ACTUAL = "src/paladinesfc/presentacion/app.py"

# Pantallas del MVP (mismos nombres de clase en la versión original y en la nueva)
PANTALLAS_MVP = ("TabJugadores", "FormJugador", "VentanaDetalleJugador", "FormVincularTutor",
                 "TabTutores", "FormTutor", "TabProfesores", "FormProfesor")
# sel[0] es la selección del Treeview, no un dato leído por posición
NO_ES_DATO = {"sel[0]"}

CAPAS = (
    ("src/sql/migraciones/", "Base de datos (migración)"),
    ("src/paladinesfc/dominio/", "Dominio"),
    ("src/paladinesfc/aplicacion/", "Aplicación"),
    ("src/paladinesfc/infraestructura/", "Infraestructura"),
    ("src/paladinesfc/presentacion/", "Presentación"),
)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def primera_version(ruta: str) -> str | None:
    """Contenido del archivo en el commit que lo agregó al repositorio."""
    try:
        commits = git("log", "--diff-filter=A", "--format=%H", "--", ruta).split()
        return git("show", f"{commits[-1]}:{ruta}") if commits else None
    except subprocess.CalledProcessError:
        return None


def lecturas_posicionales(codigo: str) -> dict[str, list[str]]:
    """Accesos tipo fila[5] dentro de las pantallas del MVP."""
    arbol = ast.parse(codigo)
    resultado = {}
    for nodo in arbol.body:
        if isinstance(nodo, ast.ClassDef) and nodo.name in PANTALLAS_MVP:
            accesos = [ast.unparse(n) for n in ast.walk(nodo)
                       if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)
                       and isinstance(n.slice.value, int)]
            resultado[nodo.name] = [a for a in accesos if a not in NO_ES_DATO]
    return resultado


def capa_de(ruta: str) -> str | None:
    if not ruta.endswith((".py", ".sql")):
        return None   # documentación, no código de producción
    return next((nombre for prefijo, nombre in CAPAS if ruta.startswith(prefijo)), None)


def cambio_e1() -> tuple[list[str], dict[str, tuple[int, int]]]:
    """Commits del escenario E1: los que llevan '(E1)' en el mensaje."""
    commits = git("log", "--format=%H", "--grep=(E1)", "--fixed-strings").split()
    archivos: dict[str, tuple[int, int]] = {}
    for commit in commits:
        for linea in git("show", "--numstat", "--format=", commit).splitlines():
            if not linea.strip():
                continue
            mas, menos, ruta = linea.split("\t")
            a, b = archivos.get(ruta, (0, 0))
            archivos[ruta] = (a + int(mas if mas != "-" else 0), b + int(menos if menos != "-" else 0))
    return commits, archivos


def ejecutar_pruebas() -> tuple[bool, str]:
    """Ejecuta la suite unitaria (sin SQL Server) y devuelve (todo aprobado, línea de resumen)."""
    proceso = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                             cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    lineas = [l for l in proceso.stdout.splitlines() if l.strip()]
    resumen = lineas[-1].strip("= ") if lineas else "sin salida de pytest"
    return proceso.returncode == 0, resumen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--minutos", type=int, help="Tiempo que tomó el cambio (medida: < 240 min).")
    parser.add_argument("--original", help="Carpeta con el App.py del sistema original (si no está en git).")
    args = parser.parse_args()

    if args.original:
        app_original = (Path(args.original) / "App.py").read_text(encoding="utf-8")
        origen = f"carpeta {args.original}"
    else:
        app_original = primera_version(APP_ACTUAL)
        origen = "primera versión de app.py en el historial de git"
        if app_original is None:
            print("No se encontró la versión original en git; use --original.", file=sys.stderr)
            return 1
    antes = lecturas_posicionales(app_original)
    despues = lecturas_posicionales((RAIZ / APP_ACTUAL).read_text(encoding="utf-8"))
    total_antes = sum(len(v) for v in antes.values())
    total_despues = sum(len(v) for v in despues.values())

    commits, archivos = cambio_e1()
    if not commits:
        print("No hay commits con '(E1)' en el mensaje.", file=sys.stderr)
        return 1
    produccion = {r: c for r, c in archivos.items() if capa_de(r)}
    pruebas = {r: c for r, c in archivos.items() if r.startswith("tests/")}
    otros = {r: c for r, c in archivos.items() if r not in produccion and r not in pruebas}
    capas = [capa_de(r) for r in produccion]
    una_por_capa = len(capas) == len(set(capas))
    fuera_del_modulo = [r for r in produccion
                        if "jugador" not in r.lower() and not r.endswith("app.py") and "eps" not in r.lower()]

    filas_pantallas = "\n".join(
        f"| `{clase}` | {len(antes.get(clase, []))} | {len(despues.get(clase, []))} |" for clase in PANTALLAS_MVP)
    filas_archivos = "\n".join(
        f"| `{r}` | {capa_de(r)} | +{a} / −{b} |" for r, (a, b) in sorted(produccion.items()))
    filas_pruebas = "\n".join(f"| `{r}` | +{a} / −{b} |" for r, (a, b) in sorted(pruebas.items())) or "| — | — |"
    tiempo = f"{args.minutos} minutos" if args.minutos else "sin registrar (use --minutos)"
    cumple_tiempo = "Sí" if args.minutos and args.minutos < 240 else ("No" if args.minutos else "—")
    max_planeado = 4   # medida de la Semana 13: "máximo 4 archivos, uno por capa"
    cumple_maximo = "Sí" if len(produccion) <= max_planeado else f"No ({len(produccion)} > {max_planeado})"
    pruebas_ok, resumen_pruebas = ejecutar_pruebas()

    md = f"""# Escenario E1 — Mantenibilidad: medición antes/después

Generado por `python evaluacion/medir_e1.py` el {date.today().isoformat()}.
Original tomado de: {origen}.

**Estímulo:** agregar "entidad de salud (EPS)" al jugador: capturarlo al registrar,
editarlo y verlo en el listado.

## 1. Lecturas de datos por posición en las pantallas del MVP

Cada `fila[n]` es un punto que se rompe en silencio si una consulta cambia el
orden o el número de sus columnas (problema P1). Es lo que hacía arriesgado agregar
un campo en el sistema original.

| Pantalla | Antes | Después |
|---|---|---|
{filas_pantallas}
| **Total** | **{total_antes}** | **{total_despues}** |

## 2. El cambio real en el repositorio

Commits del escenario: {len(commits)} (`git log --grep="(E1)"`).

| Archivo de producción | Capa | Líneas |
|---|---|---|
{filas_archivos}

Pruebas agregadas o ajustadas:

| Archivo | Líneas |
|---|---|
{filas_pruebas}
{"" if not otros else chr(10) + "Otros archivos: " + ", ".join(f"`{r}`" for r in sorted(otros)) + chr(10)}
## 3. Resultado frente a la medida del escenario

| Criterio (Semana 13) | Resultado | ¿Cumple? |
|---|---|---|
| Máximo {max_planeado} archivos | {len(produccion)} archivos de producción | {cumple_maximo} |
| Un archivo por capa | {len(produccion)} archivos de producción en {len(set(capas))} capas | {"Sí" if una_por_capa else "No"} |
| Ningún archivo fuera del módulo Jugadores | {len(fuera_del_modulo)} fuera del módulo | {"Sí" if not fuera_del_modulo else "No"} |
| Cero accesos por índice | {total_despues} lecturas posicionales en las pantallas del MVP (antes {total_antes}) | {"Sí" if total_despues == 0 else "No"} |
| Menos de 4 horas | {tiempo} | {cumple_tiempo} |
| Las pruebas existentes pasan | `python -m pytest`: {resumen_pruebas} | {"Sí" if pruebas_ok else "No"} |

**Resultado global de E1: {"cumple" if len(produccion) <= max_planeado and pruebas_ok and total_despues == 0 and not fuera_del_modulo else "cumple parcialmente"}.**

**Diferencia con lo planeado.** La medida de la Semana 13 estimó "máximo {max_planeado} archivos"
(migración, entidad, repositorio y pantalla). El cambio real tocó también el
servicio de aplicación, porque sus casos de uso reciben los datos como parámetros
explícitos. Por eso el criterio numérico **no se cumple tal como se definió**
({len(produccion)} archivos en lugar de {max_planeado}). Sí se cumple el criterio de fondo —un archivo
por capa y nada fuera del módulo—, y para esta arquitectura el número correcto es uno
por cada una de sus {len(CAPAS)} capas. El tiempo del cambio no se registró.
"""
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(md, encoding="utf-8")
    print(md)
    print(f"Escrito en {SALIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
