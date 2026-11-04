"""Rutas de Jugadores y de la vinculación Jugador–Tutor."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from paladinesfc.dominio.errores import NoEncontradoError
from paladinesfc.presentacion.api import esquemas as e
from paladinesfc.presentacion.api.dependencias import servicios as dep

router = APIRouter(prefix="/jugadores", tags=["Jugadores"])
ERRORES = {400: {"model": e.Error, "description": "Regla de negocio no cumplida"},
           404: {"model": e.Error, "description": "No encontrado"}}


@router.get("", response_model=list[e.JugadorListado], summary="Listar o buscar jugadores")
def listar(documento: str | None = None, s=Depends(dep)):
    """Lista los jugadores con su acudiente principal. `documento` filtra por cédula (en el motor, con WHERE)."""
    return s.jugadores.listar(documento)


@router.post("", response_model=e.IdCreado, status_code=status.HTTP_201_CREATED,
             responses=ERRORES, summary="Registrar jugador con su acudiente principal")
def registrar(datos: e.JugadorNuevo, s=Depends(dep)):
    """Crea el jugador y su vínculo con el acudiente principal en una sola transacción."""
    id_jugador = s.jugadores.registrar_con_tutor(
        datos.nombres, datos.apellidos, datos.documento, datos.fecha_nacimiento,
        datos.numero_preferido, datos.talla_uniforme, datos.fecha_ingreso, datos.observaciones,
        datos.id_tutor, datos.parentesco, eps=datos.eps)
    return {"id": id_jugador}


@router.get("/{id_jugador}", response_model=e.Jugador, responses=ERRORES, summary="Consultar jugador")
def obtener(id_jugador: int, s=Depends(dep)):
    return s.jugadores.obtener(id_jugador)


@router.get("/{id_jugador}/detalle", response_model=e.DetalleJugador, responses=ERRORES,
            summary="Detalle: jugador, tutores y plantillas activas")
def detalle(id_jugador: int, s=Depends(dep)):
    jugador, tutores, plantillas = s.jugadores.detalle(id_jugador)
    return {"jugador": jugador, "tutores": tutores.vinculos, "plantillas_activas": plantillas}


@router.put("/{id_jugador}", response_model=e.Jugador, responses=ERRORES, summary="Editar jugador")
def actualizar(id_jugador: int, datos: e.JugadorEdicion, s=Depends(dep)):
    """Documento y fechas no se modifican (igual que en la aplicación de escritorio)."""
    s.jugadores.actualizar(id_jugador, datos.nombres, datos.apellidos, datos.numero_preferido,
                           datos.talla_uniforme, datos.estado, datos.observaciones, eps=datos.eps)
    return s.jugadores.obtener(id_jugador)


@router.post("/{id_jugador}/baja", response_model=e.Jugador, responses=ERRORES,
             summary="Dar de baja (inactivación lógica)")
def dar_de_baja(id_jugador: int, s=Depends(dep)):
    """No borra nada: conserva pagos, morosidad, asistencias y tutores (ADR-0003)."""
    s.jugadores.inactivar(id_jugador)
    return s.jugadores.obtener(id_jugador)


@router.post("/{id_jugador}/reactivacion", response_model=e.Jugador, responses=ERRORES,
             summary="Reactivar jugador")
def reactivar(id_jugador: int, s=Depends(dep)):
    s.jugadores.reactivar(id_jugador)
    return s.jugadores.obtener(id_jugador)


# ── Jugador–Tutor ──────────────────────────────────────────────────────────
@router.get("/{id_jugador}/tutores", response_model=list[e.Vinculo], tags=["Jugador–Tutor"],
            responses=ERRORES, summary="Tutores del jugador")
def tutores_del_jugador(id_jugador: int, s=Depends(dep)):
    s.jugadores.obtener(id_jugador)   # 404 si el jugador no existe
    return s.vinculacion.tutores_de(id_jugador).vinculos


@router.post("/{id_jugador}/tutores", response_model=e.IdCreado, status_code=status.HTTP_201_CREATED,
             tags=["Jugador–Tutor"], responses=ERRORES, summary="Vincular un tutor")
def vincular(id_jugador: int, datos: e.VinculoNuevo, s=Depends(dep)):
    s.jugadores.obtener(id_jugador)
    id_vinculo = s.vinculacion.vincular(id_jugador, datos.id_tutor, datos.parentesco, datos.como_principal)
    return {"id": id_vinculo}


@router.put("/{id_jugador}/tutores/principal", response_model=list[e.Vinculo], tags=["Jugador–Tutor"],
            responses=ERRORES, summary="Cambiar el acudiente principal")
def cambiar_principal(id_jugador: int, datos: e.CambioPrincipal, s=Depends(dep)):
    """Las dos escrituras (desmarcar y marcar) van en una sola transacción (ADR-0002)."""
    s.vinculacion.cambiar_principal(id_jugador, datos.id_tutor)
    return s.vinculacion.tutores_de(id_jugador).vinculos


@router.delete("/{id_jugador}/tutores/{id_jugador_tutor}", status_code=status.HTTP_204_NO_CONTENT,
               tags=["Jugador–Tutor"], responses=ERRORES, summary="Desvincular un tutor")
def desvincular(id_jugador: int, id_jugador_tutor: int, s=Depends(dep)):
    """No permite desvincular al único tutor ni al acudiente principal."""
    if not any(v.id_jugador_tutor == id_jugador_tutor for v in s.vinculacion.tutores_de(id_jugador).vinculos):
        raise NoEncontradoError("Vínculo tutor-jugador no encontrado para este jugador.")
    s.vinculacion.desvincular(id_jugador_tutor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
