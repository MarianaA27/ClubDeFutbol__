"""
Prueba de humo de las pantallas del MVP SIN pantalla gráfica ni SQL Server.

Sustituye tkinter/customtkinter/pyodbc por dobles mínimos y conecta la interfaz a
servicios en memoria. Verifica que cada pantalla migrada llama a la capa de
aplicación (no a crud.py) y que las operaciones de punta a punta funcionan.
"""
import importlib
import sys
import types

import pytest

from tests.fakes_repositorios import Almacen, fabrica


# ── dobles de la librería gráfica ─────────────────────────────────────────────
class _Widget:
    def __init__(self, *a, **k):
        self._valor = ""
        self._k = k

    def __getattr__(self, nombre):
        return lambda *a, **k: _Widget()

    # Entry / ComboBox
    def insert(self, _pos, texto):
        self._valor = str(texto) + self._valor

    def get(self):
        return self._valor

    def set(self, valor):
        self._valor = valor

    def delete(self, *a):
        self._valor = ""

    def winfo_children(self):
        return []


class _Treeview(_Widget):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.filas, self._sel = [], ()

    def insert(self, _padre, _pos, values=()):
        iid = f"I{len(self.filas) + 1}"
        self.filas.append((iid, list(values)))
        return iid

    def get_children(self):
        return [iid for iid, _ in self.filas]

    def selection(self):
        return self._sel

    def seleccionar(self, indice):
        self._sel = (self.filas[indice][0],)

    def item(self, iid, **k):
        return {"values": dict(self.filas)[iid]}


class _BooleanVar:
    def __init__(self, value=False):
        self._v = value

    def get(self):
        return self._v

    def set(self, v):
        self._v = v


@pytest.fixture
def app(monkeypatch):
    mensajes = {"error": [], "info": []}
    tk = types.ModuleType("tkinter")
    tk.Canvas, tk.BooleanVar = _Widget, _BooleanVar
    ttk = types.ModuleType("tkinter.ttk")
    ttk.Treeview, ttk.Scrollbar, ttk.Style = _Treeview, _Widget, _Widget
    messagebox = types.ModuleType("tkinter.messagebox")
    messagebox.showerror = lambda t, m: mensajes["error"].append(m)
    messagebox.showinfo = lambda t, m: mensajes["info"].append(m)
    messagebox.askyesno = lambda t, m: True
    tk.ttk, tk.messagebox = ttk, messagebox
    ctk = types.ModuleType("customtkinter")
    for nombre in ("CTk", "CTkFrame", "CTkToplevel", "CTkLabel", "CTkEntry", "CTkComboBox",
                   "CTkButton", "CTkScrollableFrame", "CTkCheckBox", "CTkTabview"):
        setattr(ctk, nombre, _Widget)
    ctk.set_appearance_mode = ctk.set_default_color_theme = lambda *a: None
    pyodbc = types.ModuleType("pyodbc")
    for nombre, modulo in {"tkinter": tk, "tkinter.ttk": ttk, "tkinter.messagebox": messagebox,
                           "customtkinter": ctk, "pyodbc": pyodbc}.items():
        monkeypatch.setitem(sys.modules, nombre, modulo)
    for nombre in [m for m in sys.modules if m.startswith("paladinesfc.presentacion")
                   or m.startswith("paladinesfc.legado")]:
        monkeypatch.delitem(sys.modules, nombre)

    modulo = importlib.import_module("paladinesfc.presentacion.app")
    contenedor = importlib.import_module("paladinesfc.presentacion.contenedor")
    almacen = Almacen()
    monkeypatch.setattr(modulo, "servicios", contenedor.crear_servicios(fabrica(almacen)))

    def _prohibido(*a, **k):
        raise AssertionError("Una pantalla del MVP llamó a crud.py")
    for funcion in ("get_jugadores_con_tutor", "insert_jugador_con_tutor", "update_jugador",
                    "delete_jugador", "get_tutores", "get_tutores_simple", "insert_tutor",
                    "update_tutor", "delete_tutor", "get_profesores", "insert_profesor",
                    "update_profesor", "delete_profesor", "set_acudiente_principal",
                    "insert_jugador_tutor", "delete_jugador_tutor", "get_detalle_jugador_completo"):
        monkeypatch.setattr(modulo.crud, funcion, _prohibido)
    modulo._mensajes, modulo._almacen = mensajes, almacen
    return modulo


def _nuevo_tutor(app, doc, tel, nombre="Carlos"):
    form = app.FormTutor(None)
    for campo, valor in zip((form.e_nombres, form.e_apellidos, form.e_doc, form.e_tel,
                             form.e_email, form.e_dir), (nombre, "Pérez", doc, tel, "c@x.com", "Calle 1")):
        campo.insert(0, valor)
    form._guardar()


def test_flujo_completo_del_mvp_desde_las_pantallas(app):
    _nuevo_tutor(app, "11111", "3001111111")
    _nuevo_tutor(app, "22222", "3002222222")          # homónimo
    assert app._mensajes["error"] == []

    form = app.FormJugador(None, modo="nuevo")
    etiquetas = list(form._tutores_por_etiqueta)
    assert len(etiquetas) == 2 and etiquetas[0] != etiquetas[1]
    for campo, valor in zip((form.e_nombres, form.e_apellidos, form.e_doc, form.e_fnac,
                             form.e_fingreso), ("Samuel", "Rojas", "1020304050", "2015-05-10", "2024-02-01")):
        campo.insert(0, valor)
    form.cb_talla.set("S")
    form.cb_tutor.set(etiquetas[1])                    # se elige el SEGUNDO homónimo
    form.cb_parentesco.set("Padre")
    form._guardar()
    assert app._mensajes["error"] == [], app._mensajes["error"]

    tab = app.TabJugadores(None)
    assert tab._tree.filas, "el listado debe mostrar al jugador"
    tab._tree.seleccionar(0)
    id_jugador = tab._seleccionado()["id_jugador"]
    detalle = app.VentanaDetalleJugador(None, id_jugador)
    vinculo = detalle._vinculos[detalle._tree_tutores.get_children()[0]]
    assert vinculo.id_tutor == form._tutores_por_etiqueta[etiquetas[1]]

    tab._dar_de_baja()
    assert app._almacen.jugadores[id_jugador].estado == "inactivo"


def test_tutores_y_profesores_buscan_y_dan_de_baja(app):
    _nuevo_tutor(app, "11111", "3001111111")
    tab = app.TabTutores(None)
    tab._buscar("111")
    assert len(tab._tree.filas) == 1
    tab._tree.seleccionar(0)
    tab._dar_de_baja()
    assert app._mensajes["error"] == [], app._mensajes["error"]
    assert list(app._almacen.tutores.values())[0].estado == "inactivo"

    fp = app.FormProfesor(None)
    for campo, valor in zip((fp.e_nombres, fp.e_apellidos, fp.e_doc, fp.e_tel, fp.e_email,
                             fp.e_fingreso), ("Luisa", "Gómez", "33333", "3003333333", "l@x.com", "2023-01-15")):
        campo.insert(0, valor)
    fp._guardar()
    tp = app.TabProfesores(None)
    tp._tree.seleccionar(0)
    tp._dar_de_baja()
    assert list(app._almacen.profesores.values())[0].estado == "inactivo"
    assert app._mensajes["error"] == [], app._mensajes["error"]
