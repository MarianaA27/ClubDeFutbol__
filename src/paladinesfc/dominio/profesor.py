"""Entidad Profesor (cuerpo técnico)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from paladinesfc.dominio import validaciones as v
from paladinesfc.dominio.errores import ReglaNegocioError


@dataclass
class Profesor:
    nombres: str
    apellidos: str
    documento: str
    telefono: str
    email: str
    fecha_ingreso: date
    especialidad: str | None = None
    estado: str = "activo"
    id_profesor: int | None = None

    @classmethod
    def nuevo(cls, nombres, apellidos, documento, telefono, email,
              especialidad, fecha_ingreso) -> "Profesor":
        profesor = cls("", "", "", "", "", v.fecha(fecha_ingreso, "Fecha de ingreso"))
        profesor.actualizar(nombres, apellidos, documento, telefono, email, especialidad, "activo")
        return profesor

    @classmethod
    def desde_bd(cls, fila: dict) -> "Profesor":
        return cls(
            id_profesor=fila["id_profesor"],
            nombres=fila["nombres"],
            apellidos=fila["apellidos"],
            documento=fila["documento"],
            telefono=fila["telefono"],
            email=fila["email"],
            especialidad=fila.get("especialidad"),
            estado=fila["estado"],
            fecha_ingreso=fila["fecha_ingreso"],
        )

    def actualizar(self, nombres, apellidos, documento, telefono, email,
                   especialidad, estado) -> None:
        """Una sola validación para registrar y editar (antes estaba duplicada)."""
        self.nombres = v.texto(nombres, "Nombres")
        self.apellidos = v.texto(apellidos, "Apellidos")
        self.documento = v.documento(documento)
        self.telefono = v.telefono(telefono)
        self.email = v.email(email)
        self.especialidad = v.texto_libre_opcional(especialidad, "Especialidad", 20)
        self.estado = v.opcion(estado, v.ESTADOS_PERSONA, "Estado")

    def inactivar(self) -> None:
        """Baja lógica (ADR-0003): sus sesiones y asistencias se conservan."""
        if self.estado == "inactivo":
            raise ReglaNegocioError("El profesor ya está inactivo.")
        self.estado = "inactivo"

    def reactivar(self) -> None:
        if self.estado == "activo":
            raise ReglaNegocioError("El profesor ya está activo.")
        self.estado = "activo"

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"

    @property
    def etiqueta(self) -> str:
        return f"{self.nombre_completo} — CC {self.documento}"
