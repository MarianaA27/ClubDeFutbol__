"""
Doble de prueba de una conexión pyodbc.

Simula el comportamiento transaccional que importa para ADR-0002:
las sentencias ejecutadas quedan *pendientes* hasta ``commit()``; ``rollback()``
las descarta. ``confirmadas`` representa lo que realmente quedaría en la base.
Permite inyectar un fallo en la N-ésima sentencia.
"""


class FalloInyectado(Exception):
    """Simula la caída de SQL Server a mitad de una operación."""


class CursorFalso:
    def __init__(self, conexion):
        self._conexion = conexion
        self.description = None
        self.rowcount = -1
        self._filas = []

    def execute(self, sql, parametros=()):
        self._conexion.numero_sentencia += 1
        if self._conexion.fallar_en == self._conexion.numero_sentencia:
            raise FalloInyectado(f"Conexión perdida en la sentencia {self._conexion.numero_sentencia}")
        self._conexion.pendientes.append((" ".join(sql.split()), tuple(parametros)))
        respuesta = self._conexion.respuestas.pop(0) if self._conexion.respuestas else ([], [])
        nombres, filas = respuesta
        self.description = [(n,) for n in nombres] if nombres else None
        self._filas = list(filas)
        self.rowcount = self._conexion.filas_afectadas
        return self

    def fetchall(self):
        filas, self._filas = self._filas, []
        return filas

    def fetchone(self):
        return self._filas.pop(0) if self._filas else None


class ConexionFalsa:
    def __init__(self, fallar_en=None, respuestas=None, filas_afectadas=1):
        self.fallar_en = fallar_en
        self.respuestas = list(respuestas or [])
        self.filas_afectadas = filas_afectadas
        self.numero_sentencia = 0
        self.pendientes = []
        self.confirmadas = []
        self.commits = 0
        self.rollbacks = 0
        self.cerrada = False
        self.autocommit = True

    def cursor(self):
        return CursorFalso(self)

    def commit(self):
        self.confirmadas.extend(self.pendientes)
        self.pendientes = []
        self.commits += 1

    def rollback(self):
        self.pendientes = []
        self.rollbacks += 1

    def close(self):
        self.cerrada = True
