"""
Repositorios SQL Server de los módulos del MVP (ADR-0001 y ADR-0005).

* Devuelven ENTIDADES o diccionarios por nombre de columna, nunca tuplas posicionales.
* Todo filtro se resuelve en el motor con WHERE (se acabó traer la tabla
  completa y filtrar en Python).
* No abren conexiones: trabajan dentro de la transacción de la unidad de trabajo.
"""
from paladinesfc.infraestructura.repositorios.jugadores import RepositorioJugadoresSql
from paladinesfc.infraestructura.repositorios.profesores import RepositorioProfesoresSql
from paladinesfc.infraestructura.repositorios.tutores import RepositorioTutoresSql
from paladinesfc.infraestructura.repositorios.vinculos import RepositorioVinculosSql

__all__ = [
    "RepositorioJugadoresSql", "RepositorioTutoresSql",
    "RepositorioProfesoresSql", "RepositorioVinculosSql",
]
