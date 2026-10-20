"""Entidad Tutor (acudiente)."""
from __future__ import annotations

from dataclasses import dataclass

from paladinesfc.dominio import validaciones as v
from paladinesfc.dominio.errores import ReglaNegocioError


@dataclass
class Tutor:
    nombres: str
    apellidos: str
    documento: str
    telefono: str
    email: str
    direccion: str
    estado: str = "activo"
    id_tutor: int | None = None

    @classmethod
    def nuevo(cls, nombres, apellidos, documento, telefono, email, direccion) -> "Tutor":
        tutor = cls("", "", "", "", "", "")
        tutor.actualizar(nombres, apellidos, documento, telefono, email, direccion)
        return tutor

    @classmethod
    def desde_bd(cls, fila: dict) -> "Tutor":
        return cls(
            id_tutor=fila["id_tutor"],
            nombres=fila["nombres"],
            apellidos=fila["apellidos"],
            documento=fila["documento"],
            telefono=fila["telefono"],
            email=fila["email"],
            direccion=fila["direccion"],
            estado=fila.get("estado") or "activo",
        )

    def actualizar(self, nombres, apellidos, documento, telefono, email, direccion) -> None:
        self.nombres = v.texto(nombres, "Nombres")
        self.apellidos = v.texto(apellidos, "Apellidos")
        self.documento = v.documento(documento)
        self.telefono = v.telefono(telefono)
        self.email = v.email(email)
        self.direccion = v.requerido(direccion, "Dirección")
        if len(self.direccion) > 100:
            raise ReglaNegocioError("'Dirección' no puede superar 100 caracteres.")

    def inactivar(self, jugadores_activos_a_cargo: int) -> None:
        """Baja lógica (ADR-0003). Se conserva la regla original: no si tiene jugadores a cargo."""
        if jugadores_activos_a_cargo > 0:
            raise ReglaNegocioError(
                "No se puede inactivar el tutor porque tiene jugadores activos a cargo.")
        if self.estado == "inactivo":
            raise ReglaNegocioError("El tutor ya está inactivo.")
        self.estado = "inactivo"

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"

    @property
    def etiqueta(self) -> str:
        """Texto para desplegables: incluye el documento para distinguir homónimos (P1)."""
        return f"{self.nombre_completo} — CC {self.documento}"
