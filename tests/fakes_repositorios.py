"""
Unidad de trabajo y repositorios EN MEMORIA para probar los servicios sin SQL Server.

Simula la atomicidad: los cambios se aplican sobre una copia y solo se
publican en el "almacén" al hacer ``commit()``.
"""
import copy
from dataclasses import dataclass, field

from paladinesfc.dominio.vinculo import TutoresDelJugador


@dataclass
class Almacen:
    jugadores: dict = field(default_factory=dict)
    tutores: dict = field(default_factory=dict)
    profesores: dict = field(default_factory=dict)
    vinculos: dict = field(default_factory=dict)
    plantillas_activas: dict = field(default_factory=dict)   # id_jugador -> n
    secuencia: int = 100
    commits: int = 0


class _Repo:
    def __init__(self, datos, almacen, clave_id):
        self._d, self._a, self._k = datos, almacen, clave_id

    def _nuevo_id(self):
        self._a.secuencia += 1
        return self._a.secuencia

    def obtener(self, i):
        return copy.deepcopy(self._d.get(int(i)))

    def _existe(self, atributo, valor, excluir):
        return any(getattr(x, atributo) == valor and getattr(x, self._k) != excluir
                   for x in self._d.values())

    def existe_documento(self, documento, excluir_id=None):
        return self._existe("documento", documento, excluir_id)

    def existe_telefono(self, telefono, excluir_id=None):
        return self._existe("telefono", telefono, excluir_id)

    def agregar(self, entidad):
        nuevo = self._nuevo_id()
        setattr(entidad, self._k, nuevo)
        self._d[nuevo] = copy.deepcopy(entidad)
        return nuevo

    def actualizar(self, entidad):
        self._d[getattr(entidad, self._k)] = copy.deepcopy(entidad)

    def listar(self, documento=None, solo_activos=False):
        return [copy.deepcopy(x) for x in self._d.values()
                if (not documento or documento in x.documento)
                and (not solo_activos or x.estado == "activo")]


class RepoJugadores(_Repo):
    def listar_con_tutor_principal(self, documento=None):
        """Mismas columnas (por nombre) que la consulta SQL real."""
        filas = []
        for j in self.listar(documento):
            principal = next((v for v in self._a.vinculos.values()
                              if v.id_jugador == j.id_jugador and v.acudiente_principal), None)
            tutor = self._a.tutores.get(principal.id_tutor) if principal else None
            filas.append({
                "id_jugador": j.id_jugador, "jugador": j.nombre_completo,
                "documento": j.documento, "estado": j.estado,
                "fecha_nacimiento": j.fecha_nacimiento, "talla_uniforme": j.talla_uniforme,
                "tutor_principal": tutor.nombre_completo if tutor else "Sin tutor",
                "parentesco": principal.parentesco if principal else "-",
                "telefono_tutor": tutor.telefono if tutor else "-",
            })
        return filas

    def contar_plantillas_activas(self, i):
        return self._a.plantillas_activas.get(int(i), 0)

    def plantillas_activas(self, i):
        return []


class RepoTutores(_Repo):
    def contar_jugadores_activos(self, i):
        return sum(1 for v in self._a.vinculos.values()
                   if v.id_tutor == int(i) and self._a.jugadores[v.id_jugador].estado != "inactivo")

    def jugadores_a_cargo(self, i):
        return []


class RepoProfesores(_Repo):
    def plantillas_a_cargo(self, i):
        return []


class RepoVinculos:
    def __init__(self, almacen):
        self._a = almacen

    def de_jugador(self, id_jugador):
        return TutoresDelJugador(id_jugador, [copy.deepcopy(v) for v in self._a.vinculos.values()
                                              if v.id_jugador == id_jugador])

    def de_vinculo(self, id_jt):
        v = self._a.vinculos.get(id_jt)
        return None if v is None else self.de_jugador(v.id_jugador)

    def agregar(self, vinculo):
        if vinculo.acudiente_principal:
            for v in self._a.vinculos.values():
                if v.id_jugador == vinculo.id_jugador:
                    v.acudiente_principal = False
        self._a.secuencia += 1
        vinculo.id_jugador_tutor = self._a.secuencia
        self._a.vinculos[vinculo.id_jugador_tutor] = copy.deepcopy(vinculo)
        return vinculo.id_jugador_tutor

    def establecer_principal(self, id_jugador, id_tutor):
        for v in self._a.vinculos.values():
            if v.id_jugador == id_jugador:
                v.acudiente_principal = (v.id_tutor == id_tutor)

    def eliminar(self, id_jt):
        del self._a.vinculos[id_jt]


class UoWMemoria:
    def __init__(self, almacen: Almacen, operacion: str = ""):
        self._original = almacen
        self.operacion = operacion

    def __enter__(self):
        self._trabajo = copy.deepcopy(self._original)
        a = self._trabajo
        self.jugadores = RepoJugadores(a.jugadores, a, "id_jugador")
        self.tutores = RepoTutores(a.tutores, a, "id_tutor")
        self.profesores = RepoProfesores(a.profesores, a, "id_profesor")
        self.vinculos = RepoVinculos(a)
        return self

    def __exit__(self, *exc):
        return False   # sin commit no se publica nada (rollback implícito)

    def commit(self):
        commits = self._original.commits + 1
        self._original.__dict__.update(copy.deepcopy(self._trabajo).__dict__)
        self._original.commits = commits


def fabrica(almacen):
    return lambda operacion: UoWMemoria(almacen, operacion)
