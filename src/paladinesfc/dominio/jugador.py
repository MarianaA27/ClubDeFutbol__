"""Entidad Jugador (ADR-0001: reemplaza la tupla posicional de 10 columnas)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from paladinesfc.dominio import validaciones as v
from paladinesfc.dominio.errores import ReglaNegocioError


@dataclass
class Jugador:
    nombres: str
    apellidos: str
    documento: str
    fecha_nacimiento: date
    talla_uniforme: str
    fecha_ingreso: date
    numero_preferido: int | None = None
    estado: str = "activo"
    observaciones: str | None = None
    id_jugador: int | None = None

    # ── creación ───────────────────────────────────────────────────────────
    @classmethod
    def nuevo(cls, nombres, apellidos, documento, fecha_nacimiento, talla_uniforme,
              fecha_ingreso, numero_preferido=None, observaciones=None,
              hoy: date | None = None) -> "Jugador":
        """Crea un jugador validando TODAS las reglas. Siempre nace 'activo'."""
        hoy = hoy or date.today()
        fn = v.fecha(fecha_nacimiento, "Fecha de nacimiento")
        fi = v.fecha(fecha_ingreso, "Fecha de ingreso")
        if fn >= hoy:
            raise ReglaNegocioError("La fecha de nacimiento debe ser anterior a hoy.")
        if fi <= fn:
            raise ReglaNegocioError("La fecha de ingreso debe ser posterior a la fecha de nacimiento.")
        return cls(
            nombres=v.texto(nombres, "Nombres"),
            apellidos=v.texto(apellidos, "Apellidos"),
            documento=v.documento(documento),
            fecha_nacimiento=fn,
            talla_uniforme=v.opcion(talla_uniforme, v.TALLAS, "Talla uniforme", mayusculas=True),
            fecha_ingreso=fi,
            numero_preferido=v.entero_positivo_opcional(numero_preferido, "Número preferido"),
            estado="activo",
            observaciones=v.texto_libre_opcional(observaciones, "Observaciones", 100),
        )

    @classmethod
    def desde_bd(cls, fila: dict) -> "Jugador":
        """Reconstruye la entidad desde una fila (por NOMBRE de columna), sin revalidar."""
        return cls(
            id_jugador=fila["id_jugador"],
            nombres=fila["nombres"],
            apellidos=fila["apellidos"],
            documento=fila["documento"],
            fecha_nacimiento=fila["fecha_nacimiento"],
            numero_preferido=fila.get("numero_preferido"),
            talla_uniforme=fila["talla_uniforme"],
            estado=fila["estado"],
            fecha_ingreso=fila["fecha_ingreso"],
            observaciones=fila.get("observaciones"),
        )

    # ── comportamiento ─────────────────────────────────────────────────────
    def actualizar(self, nombres, apellidos, numero_preferido, talla_uniforme,
                   estado, observaciones) -> None:
        """Edición permitida: documento y fechas NO se modifican (igual que la UI original)."""
        self.nombres = v.texto(nombres, "Nombres")
        self.apellidos = v.texto(apellidos, "Apellidos")
        self.numero_preferido = v.entero_positivo_opcional(numero_preferido, "Número preferido")
        self.talla_uniforme = v.opcion(talla_uniforme, v.TALLAS, "Talla uniforme", mayusculas=True)
        self.estado = v.opcion(estado, v.ESTADOS_JUGADOR, "Estado")
        self.observaciones = v.texto_libre_opcional(observaciones, "Observaciones", 100)

    def inactivar(self) -> None:
        """Baja lógica (ADR-0003): conserva pagos, asistencias e historial."""
        if self.estado == "inactivo":
            raise ReglaNegocioError("El jugador ya está inactivo.")
        self.estado = "inactivo"

    def reactivar(self) -> None:
        if self.estado != "inactivo":
            raise ReglaNegocioError("El jugador ya está activo.")
        self.estado = "activo"

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"
