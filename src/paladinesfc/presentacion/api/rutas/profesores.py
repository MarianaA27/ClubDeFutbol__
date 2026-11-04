"""Rutas de Profesores (cuerpo técnico)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from paladinesfc.presentacion.api import esquemas as e
from paladinesfc.presentacion.api.dependencias import servicios as dep

router = APIRouter(prefix="/profesores", tags=["Profesores"])
ERRORES = {400: {"model": e.Error, "description": "Regla de negocio no cumplida"},
           404: {"model": e.Error, "description": "No encontrado"}}


@router.get("", response_model=list[e.Profesor], summary="Listar o buscar profesores")
def listar(documento: str | None = None, s=Depends(dep)):
    return s.profesores.listar(documento)


@router.get("/activos", response_model=list[e.Profesor], summary="Profesores activos (para listas de selección)")
def activos(s=Depends(dep)):
    """El profesor dado de baja no aparece aquí, pero su historial se conserva (escenario E3)."""
    return s.profesores.opciones()


@router.post("", response_model=e.IdCreado, status_code=status.HTTP_201_CREATED,
             responses=ERRORES, summary="Registrar profesor")
def registrar(datos: e.ProfesorNuevo, s=Depends(dep)):
    return {"id": s.profesores.registrar(datos.nombres, datos.apellidos, datos.documento, datos.telefono,
                                         datos.email, datos.especialidad, datos.fecha_ingreso)}


@router.get("/{id_profesor}", response_model=e.Profesor, responses=ERRORES, summary="Consultar profesor")
def obtener(id_profesor: int, s=Depends(dep)):
    return s.profesores.obtener(id_profesor)


@router.get("/{id_profesor}/plantillas", response_model=list[e.PlantillaACargo], responses=ERRORES,
            summary="Plantillas a cargo del profesor")
def plantillas_a_cargo(id_profesor: int, s=Depends(dep)):
    _, plantillas = s.profesores.detalle(id_profesor)
    return plantillas


@router.put("/{id_profesor}", response_model=e.Profesor, responses=ERRORES, summary="Editar profesor")
def actualizar(id_profesor: int, datos: e.ProfesorEdicion, s=Depends(dep)):
    s.profesores.actualizar(id_profesor, datos.nombres, datos.apellidos, datos.documento, datos.telefono,
                            datos.email, datos.especialidad, datos.estado)
    return s.profesores.obtener(id_profesor)


@router.post("/{id_profesor}/baja", response_model=e.Profesor, responses=ERRORES,
             summary="Dar de baja (inactivación lógica)")
def dar_de_baja(id_profesor: int, s=Depends(dep)):
    """Conserva sus sesiones, asistencias y asignaciones a plantillas (ADR-0003)."""
    s.profesores.inactivar(id_profesor)
    return s.profesores.obtener(id_profesor)


@router.post("/{id_profesor}/reactivacion", response_model=e.Profesor, responses=ERRORES,
             summary="Reactivar profesor")
def reactivar(id_profesor: int, s=Depends(dep)):
    s.profesores.reactivar(id_profesor)
    return s.profesores.obtener(id_profesor)
