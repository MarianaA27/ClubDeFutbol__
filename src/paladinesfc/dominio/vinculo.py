"""
Vinculación Jugador–Tutor.

``TutoresDelJugador`` es el agregado que protege las reglas de la relación
muchos a muchos, que en el sistema original NO se cumplían en ningún sitio:

1. Un jugador tiene al menos un tutor.
2. Exactamente uno de sus tutores es el acudiente principal.
3. Un mismo tutor no se vincula dos veces al mismo jugador.

Defectos originales que corrige (ver docs/arquitectura.md):
* ``delete_jugador_tutor()`` consultaba si el tutor era el principal pero nunca
  usaba ese dato: desvincular al principal dejaba al jugador sin acudiente
  principal.
* ``set_acudiente_principal()`` dejaba al jugador sin principal si el tutor
  indicado no estaba vinculado (el segundo UPDATE no afectaba filas).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from paladinesfc.dominio import validaciones as v
from paladinesfc.dominio.errores import NoEncontradoError, ReglaNegocioError


@dataclass
class VinculoTutor:
    id_jugador: int
    id_tutor: int
    parentesco: str
    acudiente_principal: bool = False
    id_jugador_tutor: int | None = None
    # datos de lectura del tutor (no se persisten desde aquí)
    nombre_tutor: str = ""
    telefono: str | None = None
    email: str | None = None

    @classmethod
    def desde_bd(cls, fila: dict) -> "VinculoTutor":
        return cls(
            id_jugador_tutor=fila["id_jugador_tutor"],
            id_jugador=fila["id_jugador"],
            id_tutor=fila["id_tutor"],
            parentesco=fila["parentesco"],
            acudiente_principal=bool(fila["acudiente_principal"]),
            nombre_tutor=fila.get("tutor", ""),
            telefono=fila.get("telefono"),
            email=fila.get("email"),
        )


@dataclass
class TutoresDelJugador:
    id_jugador: int
    vinculos: list[VinculoTutor] = field(default_factory=list)

    # ── consultas ──────────────────────────────────────────────────────────
    @property
    def principal(self) -> VinculoTutor | None:
        principales = [x for x in self.vinculos if x.acudiente_principal]
        return principales[0] if len(principales) == 1 else None

    def esta_vinculado(self, id_tutor: int) -> bool:
        return any(x.id_tutor == id_tutor for x in self.vinculos)

    def es_consistente(self) -> bool:
        return bool(self.vinculos) and sum(x.acudiente_principal for x in self.vinculos) == 1

    # ── comandos ───────────────────────────────────────────────────────────
    def vincular(self, id_tutor: int, parentesco: str, como_principal: bool) -> VinculoTutor:
        if id_tutor is None:
            raise ReglaNegocioError("Selecciona un tutor válido de la lista.")
        parentesco = v.opcion(parentesco, v.PARENTESCOS, "Parentesco")
        if self.esta_vinculado(id_tutor):
            raise ReglaNegocioError("Este tutor ya está vinculado a este jugador.")
        # Si el jugador no tiene principal (p. ej. dato heredado inconsistente),
        # el nuevo tutor pasa a serlo para restablecer la regla 2.
        sera_principal = como_principal or self.principal is None
        if sera_principal:
            for existente in self.vinculos:
                existente.acudiente_principal = False
        nuevo = VinculoTutor(self.id_jugador, id_tutor, parentesco, sera_principal)
        self.vinculos.append(nuevo)
        return nuevo

    def cambiar_principal(self, id_tutor: int) -> None:
        if not self.esta_vinculado(id_tutor):
            raise NoEncontradoError("El tutor seleccionado no está vinculado a este jugador.")
        for vinculo in self.vinculos:
            vinculo.acudiente_principal = (vinculo.id_tutor == id_tutor)

    def desvincular(self, id_jugador_tutor: int) -> VinculoTutor:
        vinculo = next((x for x in self.vinculos if x.id_jugador_tutor == id_jugador_tutor), None)
        if vinculo is None:
            raise NoEncontradoError("Vínculo tutor-jugador no encontrado.")
        if len(self.vinculos) <= 1:
            raise ReglaNegocioError(
                "No se puede desvincular el único tutor del jugador. Primero agregue otro tutor.")
        if vinculo.acudiente_principal:
            raise ReglaNegocioError(
                "No se puede desvincular al acudiente principal. "
                "Primero marque a otro tutor como principal.")
        self.vinculos.remove(vinculo)
        return vinculo
