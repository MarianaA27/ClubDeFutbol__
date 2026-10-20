"""
Capa de dominio: entidades y reglas de negocio de los módulos del MVP.

No depende de la interfaz gráfica ni de la base de datos: puede probarse con
``pytest`` en cualquier equipo (escenario de Mantenibilidad).
"""
from paladinesfc.dominio.errores import ReglaNegocioError
from paladinesfc.dominio.jugador import Jugador
from paladinesfc.dominio.profesor import Profesor
from paladinesfc.dominio.tutor import Tutor
from paladinesfc.dominio.vinculo import TutoresDelJugador, VinculoTutor

__all__ = [
    "ReglaNegocioError", "Jugador", "Tutor", "Profesor",
    "VinculoTutor", "TutoresDelJugador",
]
