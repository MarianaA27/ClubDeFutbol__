"""
Esquemas de entrada y salida de la API (Pydantic).

Solo describen el formato JSON. Las reglas de negocio NO se repiten aquí: siguen
en el dominio (ADR-0004). Por eso los campos son texto o números simples y la
validación real la hacen las entidades al pasar por los servicios.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class _Salida(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Error(BaseModel):
    detalle: str = Field(examples=["Ya existe un tutor con el documento '11111'."])


class IdCreado(BaseModel):
    id: int = Field(examples=[12])


# ── Jugadores ──────────────────────────────────────────────────────────────
class JugadorNuevo(BaseModel):
    nombres: str = Field(examples=["Samuel"])
    apellidos: str = Field(examples=["Rojas"])
    documento: str = Field(examples=["1020304050"])
    fecha_nacimiento: date = Field(examples=["2015-05-10"])
    fecha_ingreso: date = Field(examples=["2024-02-01"])
    talla_uniforme: str = Field(examples=["S"])
    numero_preferido: int | None = Field(default=None, examples=[9])
    observaciones: str | None = Field(default=None, examples=[None])
    eps: str | None = Field(default=None, examples=["Sura"])
    id_tutor: int = Field(description="Acudiente principal (debe existir).", examples=[1])
    parentesco: str = Field(examples=["Padre"])


class JugadorEdicion(BaseModel):
    nombres: str = Field(examples=["Samuel"])
    apellidos: str = Field(examples=["Rojas"])
    talla_uniforme: str = Field(examples=["M"])
    estado: str = Field(examples=["activo"], description="activo | inactivo | lesionado")
    numero_preferido: int | None = Field(default=None, examples=[10])
    observaciones: str | None = Field(default=None, examples=["Lateral derecho"])
    eps: str | None = Field(default=None, examples=["Sura"])


class Jugador(_Salida):
    id_jugador: int = Field(examples=[1])
    nombres: str = Field(examples=["Samuel"])
    apellidos: str = Field(examples=["Rojas"])
    documento: str = Field(examples=["1020304050"])
    fecha_nacimiento: date = Field(examples=["2015-05-10"])
    fecha_ingreso: date = Field(examples=["2024-02-01"])
    talla_uniforme: str = Field(examples=["S"])
    numero_preferido: int | None = Field(default=None, examples=[9])
    estado: str = Field(examples=["activo"])
    observaciones: str | None = None
    eps: str | None = Field(default=None, examples=["Sura"])


class JugadorListado(BaseModel):
    id_jugador: int = Field(examples=[1])
    jugador: str = Field(examples=["Samuel Rojas"])
    documento: str = Field(examples=["1020304050"])
    estado: str = Field(examples=["activo"])
    fecha_nacimiento: date = Field(examples=["2015-05-10"])
    talla_uniforme: str = Field(examples=["S"])
    eps: str = Field(examples=["Sura"])
    tutor_principal: str = Field(examples=["Carlos Pérez"])
    parentesco: str = Field(examples=["Padre"])
    telefono_tutor: str = Field(examples=["3001111111"])


class Vinculo(_Salida):
    id_jugador_tutor: int = Field(examples=[5])
    id_tutor: int = Field(examples=[1])
    nombre_tutor: str = Field(examples=["Carlos Pérez"])
    parentesco: str = Field(examples=["Padre"])
    acudiente_principal: bool = Field(examples=[True])
    telefono: str | None = Field(default=None, examples=["3001111111"])
    email: str | None = Field(default=None, examples=["carlos@correo.com"])


class PlantillaDeJugador(BaseModel):
    id_plantilla: int
    nombre_plantilla: str
    nombre_categoria: str
    temporada: str | None = None
    estado: str
    fecha_asignacion: date | None = None


class DetalleJugador(BaseModel):
    jugador: Jugador
    tutores: list[Vinculo]
    plantillas_activas: list[PlantillaDeJugador]


class VinculoNuevo(BaseModel):
    id_tutor: int = Field(examples=[2])
    parentesco: str = Field(examples=["Madre"])
    como_principal: bool = Field(default=False, examples=[False])


class CambioPrincipal(BaseModel):
    id_tutor: int = Field(examples=[2])


# ── Tutores ────────────────────────────────────────────────────────────────
class TutorDatos(BaseModel):
    nombres: str = Field(examples=["Carlos"])
    apellidos: str = Field(examples=["Pérez"])
    documento: str = Field(examples=["11111"])
    telefono: str = Field(examples=["3001111111"])
    email: str = Field(examples=["carlos@correo.com"])
    direccion: str = Field(examples=["Calle 10 # 20-30"])


class Tutor(_Salida):
    id_tutor: int = Field(examples=[1])
    nombres: str = Field(examples=["Carlos"])
    apellidos: str = Field(examples=["Pérez"])
    documento: str = Field(examples=["11111"])
    telefono: str = Field(examples=["3001111111"])
    email: str = Field(examples=["carlos@correo.com"])
    direccion: str = Field(examples=["Calle 10 # 20-30"])
    estado: str = Field(examples=["activo"])
    etiqueta: str = Field(examples=["Carlos Pérez — CC 11111"],
                          description="Texto para listas de selección: distingue homónimos.")


class JugadorACargo(BaseModel):
    id_jugador: int
    jugador: str
    documento: str
    estado: str
    parentesco: str
    acudiente_principal: bool


# ── Profesores ─────────────────────────────────────────────────────────────
class ProfesorNuevo(BaseModel):
    nombres: str = Field(examples=["Andrés"])
    apellidos: str = Field(examples=["Gómez"])
    documento: str = Field(examples=["80001"])
    telefono: str = Field(examples=["3101234567"])
    email: str = Field(examples=["andres@correo.com"])
    especialidad: str | None = Field(default=None, examples=["Técnico"])
    fecha_ingreso: date = Field(examples=["2023-01-15"])


class ProfesorEdicion(BaseModel):
    nombres: str = Field(examples=["Andrés"])
    apellidos: str = Field(examples=["Gómez"])
    documento: str = Field(examples=["80001"])
    telefono: str = Field(examples=["3101234567"])
    email: str = Field(examples=["andres@correo.com"])
    especialidad: str | None = Field(default=None, examples=["Preparador físico"])
    estado: str = Field(examples=["activo"], description="activo | inactivo")


class Profesor(_Salida):
    id_profesor: int = Field(examples=[1])
    nombres: str = Field(examples=["Andrés"])
    apellidos: str = Field(examples=["Gómez"])
    documento: str = Field(examples=["80001"])
    telefono: str = Field(examples=["3101234567"])
    email: str = Field(examples=["andres@correo.com"])
    especialidad: str | None = Field(default=None, examples=["Técnico"])
    estado: str = Field(examples=["activo"])
    fecha_ingreso: date = Field(examples=["2023-01-15"])


class PlantillaACargo(BaseModel):
    id_plantilla: int
    nombre_plantilla: str
    estado_plantilla: str
    cargo: str | None = None
    fecha_asignacion: date | None = None
