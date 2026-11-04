"""Rutas de Tutores (acudientes)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from paladinesfc.presentacion.api import esquemas as e
from paladinesfc.presentacion.api.dependencias import servicios as dep

router = APIRouter(prefix="/tutores", tags=["Tutores"])
ERRORES = {400: {"model": e.Error, "description": "Regla de negocio no cumplida"},
           404: {"model": e.Error, "description": "No encontrado"}}


@router.get("", response_model=list[e.Tutor], summary="Listar o buscar tutores")
def listar(documento: str | None = None, s=Depends(dep)):
    return s.tutores.listar(documento)


@router.get("/activos", response_model=list[e.Tutor], summary="Tutores activos (para listas de selección)")
def activos(s=Depends(dep)):
    return s.tutores.opciones()


@router.post("", response_model=e.IdCreado, status_code=status.HTTP_201_CREATED,
             responses=ERRORES, summary="Registrar tutor")
def registrar(datos: e.TutorDatos, s=Depends(dep)):
    return {"id": s.tutores.registrar(datos.nombres, datos.apellidos, datos.documento,
                                      datos.telefono, datos.email, datos.direccion)}


@router.get("/{id_tutor}", response_model=e.Tutor, responses=ERRORES, summary="Consultar tutor")
def obtener(id_tutor: int, s=Depends(dep)):
    return s.tutores.obtener(id_tutor)


@router.get("/{id_tutor}/jugadores", response_model=list[e.JugadorACargo], responses=ERRORES,
            summary="Jugadores a cargo del tutor")
def jugadores_a_cargo(id_tutor: int, s=Depends(dep)):
    _, jugadores = s.tutores.detalle(id_tutor)
    return jugadores


@router.put("/{id_tutor}", response_model=e.Tutor, responses=ERRORES, summary="Editar tutor")
def actualizar(id_tutor: int, datos: e.TutorDatos, s=Depends(dep)):
    s.tutores.actualizar(id_tutor, datos.nombres, datos.apellidos, datos.documento,
                         datos.telefono, datos.email, datos.direccion)
    return s.tutores.obtener(id_tutor)


@router.post("/{id_tutor}/baja", response_model=e.Tutor, responses=ERRORES,
             summary="Dar de baja (inactivación lógica)")
def dar_de_baja(id_tutor: int, s=Depends(dep)):
    """Solo si no tiene jugadores activos a cargo. Requiere la migración 001."""
    s.tutores.inactivar(id_tutor)
    return s.tutores.obtener(id_tutor)
