"""
Validaciones y catálogos del dominio — FUENTE ÚNICA (ADR-0004, problema P4).

En el sistema original la misma regla vivía en varios lugares a la vez:
``_validar_jugador()``, una copia dentro de ``update_jugador()``, la restricción
CHECK de la tabla y el interior de ``SP_ActualizarJugador``; y
``update_profesor()`` reimplementaba ``_validar_profesor()``. Aquí cada regla se
escribe una sola vez y todas las entidades la reutilizan.
"""
from __future__ import annotations

import re
from datetime import date, datetime

from paladinesfc.dominio.errores import ReglaNegocioError

TALLAS = ("XS", "S", "M", "L", "XL", "XXL")
ESTADOS_JUGADOR = ("activo", "inactivo", "lesionado")
ESTADOS_PERSONA = ("activo", "inactivo")
PARENTESCOS = ("Padre", "Madre", "Abuelo/a", "Tío/a", "Hermano/a", "Acudiente", "Otro")

_RE_TEXTO = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s\-']+$")
_RE_DOCUMENTO = re.compile(r"^\d{5,15}$")
_RE_TELEFONO = re.compile(r"^[+]?\d{7,15}$")
_RE_EMAIL = re.compile(r"^[\w\.\+\-]+@[\w\-]+(\.[\w\-]+)*\.[a-zA-Z]{2,}$")


def requerido(valor, campo: str) -> str:
    if valor is None or not str(valor).strip():
        raise ReglaNegocioError(f"El campo '{campo}' es obligatorio.")
    return str(valor).strip()


def texto(valor, campo: str, maximo: int = 50) -> str:
    valor = requerido(valor, campo)
    if not _RE_TEXTO.match(valor):
        raise ReglaNegocioError(f"'{campo}' solo debe contener letras y espacios.")
    if len(valor) > maximo:
        raise ReglaNegocioError(f"'{campo}' no puede superar {maximo} caracteres.")
    return valor


def documento(valor, campo: str = "Documento") -> str:
    valor = requerido(valor, campo)
    if not _RE_DOCUMENTO.match(valor):
        raise ReglaNegocioError(f"'{campo}' debe contener entre 5 y 15 dígitos numéricos.")
    return valor


def telefono(valor, campo: str = "Teléfono", obligatorio: bool = True) -> str | None:
    if not obligatorio and (valor is None or not str(valor).strip()):
        return None
    valor = requerido(valor, campo)
    if not _RE_TELEFONO.match(valor):
        raise ReglaNegocioError(f"'{campo}' inválido. Ej: 3001234567 o +573001234567.")
    return valor


def email(valor, campo: str = "Email", obligatorio: bool = True) -> str | None:
    if not obligatorio and (valor is None or not str(valor).strip()):
        return None
    valor = requerido(valor, campo).lower()
    if not _RE_EMAIL.match(valor) or len(valor) > 100:
        raise ReglaNegocioError(f"'{campo}' no tiene un formato válido (ej: nombre@correo.com).")
    return valor


def fecha(valor, campo: str = "Fecha") -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    valor = requerido(valor, campo)
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        raise ReglaNegocioError(f"'{campo}' debe tener formato AAAA-MM-DD (ej: 2005-03-21).") from None


def entero_positivo_opcional(valor, campo: str) -> int | None:
    if valor is None or not str(valor).strip():
        return None
    try:
        numero = int(str(valor).strip())
    except ValueError:
        raise ReglaNegocioError(f"'{campo}' debe ser un número mayor a 0.") from None
    if numero <= 0:
        raise ReglaNegocioError(f"'{campo}' debe ser un número mayor a 0.")
    return numero


def opcion(valor, opciones: tuple[str, ...], campo: str, mayusculas: bool = False) -> str:
    valor = requerido(valor, campo)
    valor = valor.upper() if mayusculas else valor
    if valor not in opciones:
        raise ReglaNegocioError(f"Valor inválido para '{campo}'. Opciones: {', '.join(opciones)}.")
    return valor


def texto_libre_opcional(valor, campo: str, maximo: int) -> str | None:
    if valor is None or not str(valor).strip():
        return None
    valor = str(valor).strip()
    if len(valor) > maximo:
        raise ReglaNegocioError(f"'{campo}' no puede superar {maximo} caracteres.")
    return valor
