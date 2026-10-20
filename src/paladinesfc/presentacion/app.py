"""
App.py — Club Fútbol DB
Interfaz gráfica completa usando CustomTkinter.

CAMBIOS EN ESTA VERSIÓN:
  - TabJugadores reescrita desde cero (formulario limpio y robusto)
  - VentanaDetalleJugador mejorada: muestra tutores + plantillas + opción agregar tutor
  - FormJugador: selector de tutor siempre visible, validación completa
  - FormSesion: corregido para usar id_plantilla (requerido por el nuevo crud)
  - TabMorosidad: eliminadas referencias a funciones inexistentes en crud
  - TabSesiones: filtro por plantilla añadido
  - Toda la app funciona con el nuevo esquema ClubFutbolDB
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime
import threading

from paladinesfc.legado import crud

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

VERDE       = "#1DB954"
VERDE_DARK  = "#158a3e"
ROJO        = "#e74c3c"
AZUL        = "#2980b9"
NARANJA     = "#e67e22"
GRIS_FONDO  = "#1e1e2e"
GRIS_PANEL  = "#2a2a3e"
GRIS_CARD   = "#313149"
BLANCO      = "#ffffff"
TEXTO_SEC   = "#a0a0b0"
AMARILLO    = "#f1c40f"

FONT_TITULO  = ("Segoe UI", 20, "bold")
FONT_SUBTIT  = ("Segoe UI", 14, "bold")
FONT_NORMAL  = ("Segoe UI", 12)
FONT_SMALL   = ("Segoe UI", 10)
FONT_BOLD    = ("Segoe UI", 12, "bold")

FORMACIONES = {
    "4-4-2": [
        "Portero",
        "Lateral Derecho", "Central Derecho", "Central Izquierdo", "Lateral Izquierdo",
        "Mediocampista Derecho", "Mediocampista Central", "Mediocampista Central", "Mediocampista Izquierdo",
        "Delantero Derecho", "Delantero Izquierdo",
    ],
    "4-3-3": [
        "Portero",
        "Lateral Derecho", "Central Derecho", "Central Izquierdo", "Lateral Izquierdo",
        "Mediocampista Derecho", "Mediocampista Central", "Mediocampista Izquierdo",
        "Delantero Derecho", "Delantero Centro", "Delantero Izquierdo",
    ],
    "3-5-2": [
        "Portero",
        "Central Derecho", "Central Centro", "Central Izquierdo",
        "Carrilero Derecho", "Volante Defensivo", "Mediocampista Central", "Volante Ofensivo", "Carrilero Izquierdo",
        "Delantero Derecho", "Delantero Izquierdo",
    ],
    "4-2-3-1": [
        "Portero",
        "Lateral Derecho", "Central Derecho", "Central Izquierdo", "Lateral Izquierdo",
        "Volante Defensivo Derecho", "Volante Defensivo Izquierdo",
        "Mediapunta Derecho", "Mediapunta Central", "Mediapunta Izquierdo",
        "Delantero Centro",
    ],
}

COORDS_FORMACION = {
    "4-4-2": [
        (50, 88),
        (15, 70), (38, 70), (62, 70), (85, 70),
        (15, 48), (38, 48), (62, 48), (85, 48),
        (33, 22), (67, 22),
    ],
    "4-3-3": [
        (50, 88),
        (15, 70), (38, 70), (62, 70), (85, 70),
        (25, 50), (50, 50), (75, 50),
        (20, 22), (50, 22), (80, 22),
    ],
    "3-5-2": [
        (50, 88),
        (22, 70), (50, 70), (78, 70),
        (10, 52), (30, 52), (50, 52), (70, 52), (90, 52),
        (33, 22), (67, 22),
    ],
    "4-2-3-1": [
        (50, 88),
        (15, 72), (38, 72), (62, 72), (85, 72),
        (35, 57), (65, 57),
        (20, 38), (50, 38), (80, 38),
        (50, 18),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def mostrar_error(msg):
    messagebox.showerror("Error", str(msg))

def mostrar_info(msg):
    messagebox.showinfo("Información", str(msg))

def confirmar(msg):
    return messagebox.askyesno("Confirmar", str(msg))

def limpiar_frame(frame):
    for w in frame.winfo_children():
        w.destroy()

def hacer_tabla(parent, columnas, datos, altura=10, ancho_col=None):
    frame = ctk.CTkFrame(parent, fg_color=GRIS_CARD, corner_radius=8)
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.Treeview",
        background=GRIS_CARD, foreground=BLANCO, rowheight=28,
        fieldbackground=GRIS_CARD, borderwidth=0, font=("Segoe UI", 11))
    style.configure("Custom.Treeview.Heading",
        background=GRIS_PANEL, foreground=VERDE,
        font=("Segoe UI", 11, "bold"), relief="flat")
    style.map("Custom.Treeview",
        background=[("selected", AZUL)], foreground=[("selected", BLANCO)])

    tree = ttk.Treeview(frame, columns=columnas, show="headings",
                        height=altura, style="Custom.Treeview")
    for col in columnas:
        w = (ancho_col or {}).get(col, 120)
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center")

    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
    sb.pack(side="right", fill="y", pady=6, padx=(0, 4))

    for row in datos:
        tree.insert("", "end", values=[str(v) if v is not None else "" for v in row])
    return frame, tree


def campo_form(parent, label, row, col=0, ancho=200, placeholder=""):
    ctk.CTkLabel(parent, text=label, font=FONT_NORMAL, text_color=TEXTO_SEC
                 ).grid(row=row, column=col*2, sticky="e", padx=(10, 4), pady=4)
    e = ctk.CTkEntry(parent, width=ancho, placeholder_text=placeholder,
                     fg_color=GRIS_PANEL, border_color=VERDE)
    e.grid(row=row, column=col*2+1, sticky="w", padx=(0, 14), pady=4)
    return e


def combo_form(parent, label, row, valores, col=0, ancho=200):
    ctk.CTkLabel(parent, text=label, font=FONT_NORMAL, text_color=TEXTO_SEC
                 ).grid(row=row, column=col*2, sticky="e", padx=(10, 4), pady=4)
    c = ctk.CTkComboBox(parent, values=valores, width=ancho,
                        fg_color=GRIS_PANEL, border_color=VERDE,
                        button_color=VERDE, dropdown_fg_color=GRIS_PANEL)
    c.grid(row=row, column=col*2+1, sticky="w", padx=(0, 14), pady=4)
    return c


def boton(parent, texto, comando, color=VERDE, ancho=130):
    return ctk.CTkButton(parent, text=texto, command=comando,
                         fg_color=color, hover_color=VERDE_DARK if color == VERDE else color,
                         font=FONT_BOLD, width=ancho, corner_radius=8)


def tarjeta_kpi(parent, titulo, valor, color=VERDE):
    f = ctk.CTkFrame(parent, fg_color=GRIS_CARD, corner_radius=12)
    ctk.CTkLabel(f, text=titulo, font=FONT_SMALL, text_color=TEXTO_SEC).pack(pady=(12, 2))
    ctk.CTkLabel(f, text=str(valor), font=("Segoe UI", 26, "bold"),
                 text_color=color).pack(pady=(0, 12))
    return f


def barra_busqueda(parent, placeholder, on_buscar, on_limpiar):
    ff = ctk.CTkFrame(parent, fg_color=GRIS_CARD, corner_radius=8, height=44)
    ff.pack(fill="x", padx=14, pady=(6, 0))
    ctk.CTkLabel(ff, text="Buscar por cédula:", font=FONT_SMALL,
                 text_color=TEXTO_SEC).pack(side="left", padx=10, pady=8)
    e = ctk.CTkEntry(ff, placeholder_text=placeholder, width=200,
                     fg_color=GRIS_PANEL, border_color=VERDE)
    e.pack(side="left", padx=4, pady=8)
    boton(ff, "Buscar", lambda: on_buscar(e.get()), ancho=80).pack(side="left", padx=4, pady=8)
    boton(ff, "Limpiar", on_limpiar, color="#555577", ancho=80).pack(side="left", padx=4, pady=8)
    return e


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — JUGADORES (REESCRITA DESDE CERO)
# ─────────────────────────────────────────────────────────────────────────────

class TabJugadores(ctk.CTkFrame):
    """
    Tab principal de jugadores.
    Funciones: listar, buscar por cédula, ver detalle, registrar, editar, eliminar.
    """
    def __init__(self, master):
        super().__init__(master, fg_color=GRIS_FONDO)
        self._tree = None
        self._construir()

    def _construir(self):
        # ── Barra superior ──
        top = ctk.CTkFrame(self, fg_color=GRIS_PANEL, corner_radius=0, height=52)
        top.pack(fill="x")
        ctk.CTkLabel(top, text="  Jugadores", font=FONT_TITULO,
                     text_color=BLANCO).pack(side="left", padx=18, pady=10)
        boton(top, "Actualizar", self.cargar, color="#555577", ancho=110).pack(side="right", padx=8, pady=8)
        boton(top, "Ver Detalle", self._ver_detalle, color=NARANJA).pack(side="right", padx=4, pady=8)
        boton(top, "Eliminar", self._eliminar, color=ROJO).pack(side="right", padx=4, pady=8)
        boton(top, "Editar", self._editar, color=AZUL).pack(side="right", padx=4, pady=8)
        boton(top, "+ Registrar", self._form_nuevo).pack(side="right", padx=4, pady=8)

        # ── Búsqueda por cédula ──
        barra_busqueda(self, "Cédula del jugador...", self._buscar, self.cargar)

        # ── Área de tabla ──
        self._area = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area.pack(fill="both", expand=True, padx=14, pady=6)
        self.cargar()

    def cargar(self):
        limpiar_frame(self._area)
        try:
            cols, rows = crud.get_jugadores_con_tutor()
        except Exception as e:
            ctk.CTkLabel(self._area, text=f"Error: {e}", text_color=ROJO,
                         font=FONT_NORMAL).pack(pady=20)
            return
        self._renderizar_tabla(rows)

    def _buscar(self, cedula):
        if not cedula.strip():
            self.cargar()
            return
        limpiar_frame(self._area)
        try:
            cols, rows = crud.get_jugadores_con_tutor()
            filtrados = [r for r in rows if cedula.strip() in str(r[2])]
        except Exception as e:
            ctk.CTkLabel(self._area, text=f"Error: {e}", text_color=ROJO).pack()
            return
        if not filtrados:
            ctk.CTkLabel(self._area, text="Sin resultados para esa cédula.",
                         text_color=TEXTO_SEC, font=FONT_NORMAL).pack(pady=20)
            return
        self._renderizar_tabla(filtrados)

    def _renderizar_tabla(self, rows):
        cols_nombres = ["ID", "Jugador", "Documento", "Estado", "Nacimiento",
                        "Talla", "Tutor Principal", "Parentesco", "Tel. Tutor"]
        anchos = {"ID": 40, "Jugador": 180, "Documento": 110, "Estado": 80,
                  "Nacimiento": 100, "Talla": 60, "Tutor Principal": 180,
                  "Parentesco": 100, "Tel. Tutor": 120}
        ft, self._tree = hacer_tabla(self._area, cols_nombres, rows, altura=22, ancho_col=anchos)
        ft.pack(fill="both", expand=True)

    def _seleccionado(self):
        if not self._tree:
            return None
        sel = self._tree.selection()
        if not sel:
            mostrar_error("Selecciona un jugador primero.")
            return None
        return self._tree.item(sel[0])["values"]

    def _ver_detalle(self):
        v = self._seleccionado()
        if v:
            VentanaDetalleJugador(self, v[0])

    def _form_nuevo(self):
        FormJugador(self, modo="nuevo", on_save=self.cargar)

    def _editar(self):
        v = self._seleccionado()
        if v:
            FormJugador(self, modo="editar", id_jugador=v[0], on_save=self.cargar)

    def _eliminar(self):
        v = self._seleccionado()
        if not v:
            return
        nombre = v[1]
        if confirmar(f"¿ELIMINAR al jugador '{nombre}'?\n\n"
                     "Solo es posible si no tiene plantillas activas.\n"
                     "Esta acción eliminará también su historial de pagos y morosidad."):
            try:
                crud.delete_jugador(v[0])
                mostrar_info("Jugador eliminado correctamente.")
                self.cargar()
            except Exception as e:
                mostrar_error(e)


class FormJugador(ctk.CTkToplevel):
    """
    Formulario para registrar o editar un jugador.
    - Modo nuevo: requiere seleccionar un tutor ya existente y el parentesco.
    - Modo editar: permite cambiar nombre, apellido, número, talla, estado y obs.
    """
    def __init__(self, master, modo="nuevo", id_jugador=None, on_save=None):
        super().__init__(master)
        self.modo = modo
        self.id_jugador = id_jugador
        self.on_save = on_save
        self._tutores_data = []
        self.title("Registrar Jugador" if modo == "nuevo" else "Editar Jugador")
        self.geometry("600x720")
        self.configure(fg_color=GRIS_FONDO)
        self.grab_set()
        self._construir()
        if modo == "editar":
            self._cargar_datos()

    def _construir(self):
        ctk.CTkLabel(self, text="Datos del Jugador", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=(16, 6))

        scroll = ctk.CTkScrollableFrame(self, fg_color=GRIS_CARD, corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=20, pady=6)

        # Campos comunes
        self.e_nombres   = campo_form(scroll, "Nombres *", 0, ancho=260)
        self.e_apellidos = campo_form(scroll, "Apellidos *", 1, ancho=260)
        self.e_doc       = campo_form(scroll, "Documento *", 2, ancho=200)
        self.e_fnac      = campo_form(scroll, "Fec. Nacimiento *", 3,
                                      placeholder="AAAA-MM-DD", ancho=180)
        self.e_fingreso  = campo_form(scroll, "Fec. Ingreso *", 4,
                                      placeholder="AAAA-MM-DD", ancho=180)
        # Número preferido
        self.e_num_pref  = campo_form(scroll, "Nº Preferido", 5,
                                      placeholder="Opcional (1-99)", ancho=140)
        # Talla uniforme
        self.cb_talla    = combo_form(scroll, "Talla Uniforme *", 6,
                                      ["XS", "S", "M", "L", "XL", "XXL"], ancho=140)
        # Estado (solo en edición)
        self.cb_estado   = combo_form(scroll, "Estado *", 7,
                                      ["activo", "inactivo", "lesionado"], ancho=160)
        self.e_obs       = campo_form(scroll, "Observaciones", 8,
                                      ancho=340, placeholder="Opcional")

        # Selector de tutor — solo en modo nuevo
        if self.modo == "nuevo":
            sep = ctk.CTkFrame(scroll, fg_color=VERDE, height=2)
            sep.grid(row=9, column=0, columnspan=2, sticky="ew", padx=10, pady=(12, 6))

            ctk.CTkLabel(scroll, text="Tutor *", font=FONT_NORMAL,
                         text_color=TEXTO_SEC).grid(
                row=10, column=0, sticky="e", padx=(10, 4), pady=4)

            try:
                self._tutores_data = crud.get_tutores_simple()
            except Exception:
                self._tutores_data = []

            if self._tutores_data:
                tutor_names = [f"{r[1]}" for r in self._tutores_data]
            else:
                tutor_names = ["-- No hay tutores registrados --"]

            self.cb_tutor = ctk.CTkComboBox(
                scroll, values=tutor_names, width=300,
                fg_color=GRIS_PANEL, border_color=VERDE,
                button_color=VERDE, dropdown_fg_color=GRIS_PANEL)
            self.cb_tutor.grid(row=10, column=1, sticky="w", padx=(0, 14), pady=4)

            self.cb_parentesco = combo_form(
                scroll, "Parentesco *", 11,
                ["Padre", "Madre", "Abuelo/a", "Tío/a", "Hermano/a", "Acudiente", "Otro"],
                ancho=200)

            if not self._tutores_data:
                ctk.CTkLabel(
                    scroll,
                    text="⚠ Registra un tutor primero antes de crear un jugador.",
                    font=FONT_SMALL, text_color=NARANJA
                ).grid(row=12, column=0, columnspan=2, pady=4)

        # En modo edición, doc/fnac/fingreso no se pueden modificar
        if self.modo == "editar":
            self.e_doc.configure(state="disabled")
            self.e_fnac.configure(state="disabled")
            self.e_fingreso.configure(state="disabled")

        # Botones FUERA del scroll — siempre visibles
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=10, side="bottom")
        boton(bf, "Guardar", self._guardar).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=8)

    def _cargar_datos(self):
        try:
            datos, tutores, plantillas = crud.get_detalle_jugador_completo(self.id_jugador)
            if not datos[1]:
                return
            j = datos[1][0]
            # j: id, nombres, apellidos, doc, fnac, num_pref, talla, estado, fingreso, obs
            self.e_nombres.insert(0, j[1])
            self.e_apellidos.insert(0, j[2])
            self.e_doc.insert(0, j[3])
            self.e_fnac.insert(0, str(j[4]))
            self.e_fingreso.insert(0, str(j[8]))
            if j[5]:
                self.e_num_pref.insert(0, str(j[5]))
            self.cb_talla.set(j[6])
            self.cb_estado.set(j[7])
            if j[9]:
                self.e_obs.insert(0, j[9])
        except Exception as e:
            mostrar_error(e)

    def _guardar(self):
        try:
            nombres   = self.e_nombres.get().strip()
            apellidos = self.e_apellidos.get().strip()
            num_pref  = self.e_num_pref.get().strip() or None
            talla     = self.cb_talla.get()
            estado    = self.cb_estado.get()
            obs       = self.e_obs.get().strip() or None

            if self.modo == "nuevo":
                doc      = self.e_doc.get().strip()
                fnac     = self.e_fnac.get().strip()
                fingreso = self.e_fingreso.get().strip()

                if not self._tutores_data:
                    mostrar_error("No hay tutores registrados.\n"
                                  "Ve a la pestaña Tutores y registra uno primero.")
                    return

                tutor_txt = self.cb_tutor.get()
                id_tutor = None
                for r in self._tutores_data:
                    if str(r[1]) == tutor_txt:
                        id_tutor = r[0]
                        break
                if not id_tutor:
                    mostrar_error("Selecciona un tutor válido de la lista.")
                    return

                parentesco = self.cb_parentesco.get()
                if not parentesco:
                    mostrar_error("Selecciona el parentesco del tutor.")
                    return

                crud.insert_jugador_con_tutor(
                    nombres, apellidos, doc, fnac,
                    num_pref, talla, fingreso, obs,
                    id_tutor, parentesco, True
                )
                mostrar_info("Jugador registrado exitosamente.\n"
                             "Fue añadido automáticamente a la lista de morosidad.")
            else:
                crud.update_jugador(
                    self.id_jugador, nombres, apellidos,
                    num_pref, talla, estado, obs
                )
                mostrar_info("Jugador actualizado correctamente.")

            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            mostrar_error(e)


class VentanaDetalleJugador(ctk.CTkToplevel):
    """
    Ventana de detalle completo de un jugador:
    - Datos personales
    - Tutores vinculados (con opción de cambiar acudiente principal y agregar nuevos)
    - Plantillas activas
    """
    def __init__(self, master, id_jugador):
        super().__init__(master)
        self.title("Detalle del Jugador")
        self.geometry("860x680")
        self.configure(fg_color=GRIS_FONDO)
        self.grab_set()
        self.id_jugador = id_jugador
        self._cargar()

    def _cargar(self):
        limpiar_frame(self)
        try:
            datos, tutores, plantillas = crud.get_detalle_jugador_completo(self.id_jugador)
        except Exception as e:
            mostrar_error(e)
            self.destroy()
            return

        if not datos[1]:
            mostrar_error("Jugador no encontrado.")
            self.destroy()
            return

        j = datos[1][0]
        # j: id, nombres, apellidos, doc, fnac, num_pref, talla, estado, fingreso, obs

        # ── Título ──
        ctk.CTkLabel(self, text=f"  {j[1]} {j[2]}", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=(18, 4))

        # ── Info personal ──
        fp = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=10)
        fp.pack(fill="x", padx=20, pady=6)
        info = [
            ("Documento", j[3]),
            ("Nacimiento", str(j[4])),
            ("Talla", j[6]),
            ("Nº Preferido", j[5] or "—"),
            ("Estado", j[7]),
            ("Ingreso", str(j[8])),
            ("Observaciones", j[9] or "—"),
        ]
        for i, (lbl, val) in enumerate(info):
            r, c = divmod(i, 3)
            ctk.CTkLabel(fp, text=f"{lbl}:", font=FONT_SMALL,
                         text_color=TEXTO_SEC).grid(
                row=r*2, column=c, sticky="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(fp, text=str(val), font=FONT_BOLD,
                         text_color=BLANCO).grid(
                row=r*2+1, column=c, sticky="w", padx=12, pady=(0, 8))

        # ── Tutores ──
        hdr_t = ctk.CTkFrame(self, fg_color="transparent")
        hdr_t.pack(fill="x", padx=22, pady=(12, 2))
        ctk.CTkLabel(hdr_t, text="Tutores a cargo", font=FONT_SUBTIT,
                     text_color=VERDE).pack(side="left")
        boton(hdr_t, "+ Agregar tutor", self._agregar_tutor,
              ancho=150).pack(side="right", padx=4)
        boton(hdr_t, "★ Cambiar principal", self._cambiar_principal,
              color=NARANJA, ancho=160).pack(side="right", padx=4)
        boton(hdr_t, "Desvincular", self._desvincular_tutor,
              color=ROJO, ancho=120).pack(side="right", padx=4)

        self._tutores_data = tutores[1]
        cols_t = ["ID_JT", "ID Tutor", "Nombre", "Teléfono", "Email", "Parentesco", "Principal"]
        datos_t = [
            (r[0], r[1], r[2], r[3], r[4], r[5], "✓ Principal" if r[6] else "")
            for r in tutores[1]
        ]
        ft, self._tree_tutores = hacer_tabla(
            self, cols_t, datos_t, altura=4,
            ancho_col={"ID_JT": 50, "ID Tutor": 60, "Nombre": 180,
                       "Teléfono": 110, "Email": 160, "Parentesco": 90, "Principal": 80})
        ft.pack(fill="x", padx=20, pady=2)

        # ── Plantillas ──
        ctk.CTkLabel(self, text="Plantillas activas", font=FONT_SUBTIT,
                     text_color=VERDE).pack(anchor="w", padx=22, pady=(12, 2))
        cols_p = ["Plantilla", "Categoría", "Temporada", "Estado", "Desde"]
        datos_p = [(r[1], r[2], r[3] or "—", r[4], str(r[5])) for r in plantillas[1]]
        fp2, _ = hacer_tabla(self, cols_p, datos_p, altura=4,
                             ancho_col={"Plantilla": 200, "Categoría": 150,
                                        "Estado": 80, "Temporada": 90})
        fp2.pack(fill="x", padx=20, pady=(2, 16))

    def _cambiar_principal(self):
        sel = self._tree_tutores.selection()
        if not sel:
            mostrar_error("Selecciona un tutor de la lista.")
            return
        v = self._tree_tutores.item(sel[0])["values"]
        id_tutor = v[1]
        nombre = v[2]
        if confirmar(f"¿Establecer a '{nombre}' como acudiente principal?"):
            try:
                crud.set_acudiente_principal(self.id_jugador, id_tutor)
                mostrar_info(f"'{nombre}' es ahora el acudiente principal.")
                self._cargar()
            except Exception as e:
                mostrar_error(e)

    def _agregar_tutor(self):
        FormVincularTutor(self, self.id_jugador, on_save=self._cargar)

    def _desvincular_tutor(self):
        sel = self._tree_tutores.selection()
        if not sel:
            mostrar_error("Selecciona un tutor de la lista.")
            return
        v = self._tree_tutores.item(sel[0])["values"]
        id_jt = v[0]
        nombre = v[2]
        if confirmar(f"¿Desvincular a '{nombre}' de este jugador?\n"
                     "No es posible si es el único tutor del jugador."):
            try:
                crud.delete_jugador_tutor(id_jt)
                mostrar_info("Tutor desvinculado.")
                self._cargar()
            except Exception as e:
                mostrar_error(e)


class FormVincularTutor(ctk.CTkToplevel):
    """Permite vincular un tutor existente a un jugador."""
    def __init__(self, master, id_jugador, on_save=None):
        super().__init__(master)
        self.id_jugador = id_jugador
        self.on_save = on_save
        self.title("Vincular Tutor al Jugador")
        self.geometry("520x360")
        self.configure(fg_color=GRIS_FONDO)
        self.grab_set()
        self._tutores_data = []
        self._construir()

    def _construir(self):
        ctk.CTkLabel(self, text="Agregar Tutor al Jugador", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=(16, 8))

        try:
            self._tutores_data = crud.get_tutores_simple()
        except Exception:
            self._tutores_data = []

        form = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=10)
        form.pack(fill="both", expand=True, padx=20, pady=6)

        tutor_names = [f"{r[1]}" for r in self._tutores_data] if self._tutores_data else ["-- Sin tutores --"]
        ctk.CTkLabel(form, text="Tutor *", font=FONT_NORMAL, text_color=TEXTO_SEC
                     ).grid(row=0, column=0, sticky="e", padx=(10, 4), pady=8)
        self.cb_tutor = ctk.CTkComboBox(form, values=tutor_names, width=280,
                                         fg_color=GRIS_PANEL, border_color=VERDE,
                                         button_color=VERDE, dropdown_fg_color=GRIS_PANEL)
        self.cb_tutor.grid(row=0, column=1, sticky="w", padx=(0, 14), pady=8)

        self.cb_parentesco = combo_form(form, "Parentesco *", 1,
            ["Padre", "Madre", "Abuelo/a", "Tío/a", "Hermano/a", "Acudiente", "Otro"], ancho=200)

        self.var_principal = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(form, text="Establecer como acudiente principal",
                        variable=self.var_principal, fg_color=VERDE,
                        font=FONT_NORMAL, text_color=BLANCO
                        ).grid(row=2, column=0, columnspan=2, padx=14, pady=8)

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=10)
        boton(bf, "Vincular", self._guardar).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=8)

    def _guardar(self):
        if not self._tutores_data:
            mostrar_error("No hay tutores disponibles.")
            return
        tutor_txt = self.cb_tutor.get()
        id_tutor = next((r[0] for r in self._tutores_data if str(r[1]) == tutor_txt), None)
        if not id_tutor:
            mostrar_error("Selecciona un tutor válido.")
            return
        try:
            crud.insert_jugador_tutor(
                self.id_jugador, id_tutor,
                self.cb_parentesco.get(),
                self.var_principal.get()
            )
            mostrar_info("Tutor vinculado exitosamente.")
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — TUTORES
# ─────────────────────────────────────────────────────────────────────────────

class TabTutores(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=GRIS_FONDO)
        self._tree = None
        self._construir()

    def _construir(self):
        top = ctk.CTkFrame(self, fg_color=GRIS_PANEL, corner_radius=0, height=52)
        top.pack(fill="x")
        ctk.CTkLabel(top, text="  Tutores", font=FONT_TITULO, text_color=BLANCO
                     ).pack(side="left", padx=18, pady=10)
        boton(top, "Actualizar", self.cargar, color="#555577", ancho=100).pack(side="right", padx=8, pady=8)
        boton(top, "Ver Detalle", self._ver_detalle, color=NARANJA).pack(side="right", padx=4, pady=8)
        boton(top, "Eliminar", self._eliminar, color=ROJO).pack(side="right", padx=4, pady=8)
        boton(top, "Editar", self._editar, color=AZUL).pack(side="right", padx=4, pady=8)
        boton(top, "+ Registrar", self._form_nuevo).pack(side="right", padx=4, pady=8)

        barra_busqueda(self, "Cédula del tutor...", self._buscar, self.cargar)

        self._area = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area.pack(fill="both", expand=True, padx=14, pady=6)
        self.cargar()

    def cargar(self):
        limpiar_frame(self._area)
        try:
            cols, rows = crud.get_tutores()
        except Exception as e:
            ctk.CTkLabel(self._area, text=f"Error: {e}", text_color=ROJO).pack()
            return
        nombres = ["ID", "Nombres", "Apellidos", "Documento", "Teléfono", "Email", "Dirección"]
        anchos = {"ID": 40, "Nombres": 150, "Apellidos": 150, "Documento": 110,
                  "Teléfono": 120, "Email": 200, "Dirección": 200}
        ft, self._tree = hacer_tabla(self._area, nombres, rows, altura=22, ancho_col=anchos)
        ft.pack(fill="both", expand=True)

    def _buscar(self, cedula):
        if not cedula.strip():
            self.cargar()
            return
        limpiar_frame(self._area)
        try:
            cols, rows = crud.get_tutores()
            filtrados = [r for r in rows if cedula.strip() in str(r[3])]
        except Exception as e:
            ctk.CTkLabel(self._area, text=f"Error: {e}", text_color=ROJO).pack()
            return
        if not filtrados:
            ctk.CTkLabel(self._area, text="Sin resultados para esa cédula.",
                         text_color=TEXTO_SEC, font=FONT_NORMAL).pack(pady=20)
            return
        nombres = ["ID", "Nombres", "Apellidos", "Documento", "Teléfono", "Email", "Dirección"]
        anchos = {"ID": 40, "Nombres": 150, "Apellidos": 150, "Documento": 110,
                  "Teléfono": 120, "Email": 200, "Dirección": 200}
        ft, self._tree = hacer_tabla(self._area, nombres, filtrados, altura=22, ancho_col=anchos)
        ft.pack(fill="both", expand=True)

    def _seleccionado(self):
        sel = self._tree.selection() if self._tree else []
        if not sel:
            mostrar_error("Selecciona un tutor primero.")
            return None
        return self._tree.item(sel[0])["values"]

    def _ver_detalle(self):
        v = self._seleccionado()
        if not v:
            return
        try:
            cols, rows = crud.get_detalle_tutor(v[0])
        except Exception as e:
            mostrar_error(e)
            return
        win = ctk.CTkToplevel(self)
        win.title(f"Detalle Tutor — {v[1]} {v[2]}")
        win.geometry("640x420")
        win.configure(fg_color=GRIS_FONDO)
        win.grab_set()
        ctk.CTkLabel(win, text=f"  {v[1]} {v[2]}", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=14)
        ctk.CTkLabel(win, text=f"Documento: {v[3]}  |  Teléfono: {v[4]}  |  Email: {v[5]}",
                     font=FONT_NORMAL, text_color=TEXTO_SEC).pack()
        ctk.CTkLabel(win, text=f"Dirección: {v[6]}", font=FONT_SMALL,
                     text_color=TEXTO_SEC).pack(pady=(0, 8))
        ctk.CTkLabel(win, text="Jugadores a cargo", font=FONT_SUBTIT,
                     text_color=VERDE).pack(anchor="w", padx=16)
        nombres_c = ["Tutor", "Teléfono", "Email", "Jugador a cargo", "Parentesco"]
        ft, _ = hacer_tabla(win, nombres_c, rows, altura=10)
        ft.pack(fill="both", expand=True, padx=16, pady=8)

    def _form_nuevo(self):
        FormTutor(self, on_save=self.cargar)

    def _editar(self):
        v = self._seleccionado()
        if v:
            FormTutor(self, id_tutor=v[0], on_save=self.cargar)

    def _eliminar(self):
        v = self._seleccionado()
        if not v:
            return
        if confirmar(f"¿ELIMINAR al tutor '{v[1]} {v[2]}'?\n"
                     "Solo posible si no tiene jugadores a cargo."):
            try:
                crud.delete_tutor(v[0])
                mostrar_info("Tutor eliminado.")
                self.cargar()
            except Exception as e:
                mostrar_error(e)


class FormTutor(ctk.CTkToplevel):
    def __init__(self, master, id_tutor=None, on_save=None):
        super().__init__(master)
        self.id_tutor = id_tutor
        self.on_save = on_save
        self.title("Registrar Tutor" if not id_tutor else "Editar Tutor")
        self.geometry("480x440")
        self.configure(fg_color=GRIS_FONDO)
        self.grab_set()
        self._construir()
        if id_tutor:
            self._cargar()

    def _construir(self):
        ctk.CTkLabel(self, text="Datos del Tutor", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=(16, 8))
        form = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=10)
        form.pack(fill="both", expand=True, padx=20, pady=6)
        self.e_nombres   = campo_form(form, "Nombres *", 0, ancho=240)
        self.e_apellidos = campo_form(form, "Apellidos *", 1, ancho=240)
        self.e_doc       = campo_form(form, "Documento *", 2, ancho=200)
        self.e_tel       = campo_form(form, "Teléfono *", 3, ancho=200)
        self.e_email     = campo_form(form, "Email *", 4, ancho=280)
        self.e_dir       = campo_form(form, "Dirección *", 5, ancho=280)
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=10)
        boton(bf, "Guardar", self._guardar).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=8)

    def _cargar(self):
        try:
            cols, rows = crud.get_tutores()
            for r in rows:
                if r[0] == self.id_tutor:
                    self.e_nombres.insert(0, r[1])
                    self.e_apellidos.insert(0, r[2])
                    self.e_doc.insert(0, r[3])
                    self.e_tel.insert(0, r[4])
                    self.e_email.insert(0, r[5])
                    self.e_dir.insert(0, r[6])
                    break
        except Exception as e:
            mostrar_error(e)

    def _guardar(self):
        try:
            n = self.e_nombres.get(); a = self.e_apellidos.get()
            d = self.e_doc.get(); t = self.e_tel.get()
            em = self.e_email.get(); di = self.e_dir.get()
            if self.id_tutor:
                crud.update_tutor(self.id_tutor, n, a, d, t, em, di)
                mostrar_info("Tutor actualizado.")
            else:
                crud.insert_tutor(n, a, d, t, em, di)
                mostrar_info("Tutor registrado.")
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — PROFESORES
# ─────────────────────────────────────────────────────────────────────────────

class TabProfesores(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=GRIS_FONDO)
        self._tree = None
        self._construir()

    def _construir(self):
        top = ctk.CTkFrame(self, fg_color=GRIS_PANEL, corner_radius=0, height=52)
        top.pack(fill="x")
        ctk.CTkLabel(top, text="  Profesores", font=FONT_TITULO, text_color=BLANCO
                     ).pack(side="left", padx=18, pady=10)
        boton(top, "Actualizar", self.cargar, color="#555577", ancho=100).pack(side="right", padx=8, pady=8)
        boton(top, "Ver Detalle", self._ver_detalle, color=NARANJA).pack(side="right", padx=4, pady=8)
        boton(top, "Eliminar", self._eliminar, color=ROJO).pack(side="right", padx=4, pady=8)
        boton(top, "Editar", self._editar, color=AZUL).pack(side="right", padx=4, pady=8)
        boton(top, "+ Registrar", self._form_nuevo).pack(side="right", padx=4, pady=8)

        barra_busqueda(self, "Cédula del profesor...", self._buscar, self.cargar)

        self._area = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area.pack(fill="both", expand=True, padx=14, pady=6)
        self.cargar()

    def cargar(self):
        limpiar_frame(self._area)
        try:
            cols, rows = crud.get_profesores()
        except Exception as e:
            ctk.CTkLabel(self._area, text=f"Error: {e}", text_color=ROJO).pack()
            return
        nombres = ["ID", "Nombres", "Apellidos", "Documento", "Teléfono",
                   "Email", "Especialidad", "Estado", "Fec. Ingreso"]
        anchos = {"ID": 40, "Nombres": 140, "Apellidos": 140, "Documento": 110,
                  "Teléfono": 120, "Email": 180, "Especialidad": 120,
                  "Estado": 80, "Fec. Ingreso": 100}
        ft, self._tree = hacer_tabla(self._area, nombres, rows, altura=22, ancho_col=anchos)
        ft.pack(fill="both", expand=True)

    def _buscar(self, cedula):
        if not cedula.strip():
            self.cargar()
            return
        limpiar_frame(self._area)
        try:
            cols, rows = crud.get_profesores()
            filtrados = [r for r in rows if cedula.strip() in str(r[3])]
        except Exception as e:
            ctk.CTkLabel(self._area, text=f"Error: {e}", text_color=ROJO).pack()
            return
        if not filtrados:
            ctk.CTkLabel(self._area, text="Sin resultados para esa cédula.",
                         text_color=TEXTO_SEC, font=FONT_NORMAL).pack(pady=20)
            return
        nombres = ["ID", "Nombres", "Apellidos", "Documento", "Teléfono",
                   "Email", "Especialidad", "Estado", "Fec. Ingreso"]
        anchos = {"ID": 40, "Nombres": 140, "Apellidos": 140, "Documento": 110,
                  "Teléfono": 120, "Email": 180, "Especialidad": 120,
                  "Estado": 80, "Fec. Ingreso": 100}
        ft, self._tree = hacer_tabla(self._area, nombres, filtrados, altura=22, ancho_col=anchos)
        ft.pack(fill="both", expand=True)

    def _seleccionado(self):
        sel = self._tree.selection() if self._tree else []
        if not sel:
            mostrar_error("Selecciona un profesor primero.")
            return None
        return self._tree.item(sel[0])["values"]

    def _ver_detalle(self):
        v = self._seleccionado()
        if not v:
            return
        try:
            cols, rows = crud.get_detalle_profesor(v[0])
        except Exception as e:
            mostrar_error(e)
            return
        win = ctk.CTkToplevel(self)
        win.title("Detalle Profesor")
        win.geometry("680x420")
        win.configure(fg_color=GRIS_FONDO)
        win.grab_set()
        ctk.CTkLabel(win, text=f"  {v[1]} {v[2]}", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=14)
        ctk.CTkLabel(win, text=f"Documento: {v[3]}  |  Especialidad: {v[6] or '—'}  |  Estado: {v[7]}",
                     font=FONT_NORMAL, text_color=TEXTO_SEC).pack()
        ctk.CTkLabel(win, text="Plantillas a cargo", font=FONT_SUBTIT,
                     text_color=VERDE).pack(anchor="w", padx=16, pady=(10, 2))
        nombres_c = ["Profesor", "Especialidad", "Estado", "Plantilla a cargo", "Cargo"]
        ft, _ = hacer_tabla(win, nombres_c, rows, altura=10)
        ft.pack(fill="both", expand=True, padx=16, pady=8)

    def _form_nuevo(self):
        FormProfesor(self, on_save=self.cargar)

    def _editar(self):
        v = self._seleccionado()
        if v:
            FormProfesor(self, id_profesor=v[0], on_save=self.cargar)

    def _eliminar(self):
        v = self._seleccionado()
        if not v:
            return
        if confirmar(f"¿ELIMINAR al profesor '{v[1]} {v[2]}'?\n"
                     "Se eliminarán también sus sesiones y vínculos de plantilla."):
            try:
                crud.delete_profesor(v[0])
                mostrar_info("Profesor eliminado.")
                self.cargar()
            except Exception as e:
                mostrar_error(str(e))


class FormProfesor(ctk.CTkToplevel):
    def __init__(self, master, id_profesor=None, on_save=None):
        super().__init__(master)
        self.id_profesor = id_profesor
        self.on_save = on_save
        self.title("Registrar Profesor" if not id_profesor else "Editar Profesor")
        self.geometry("500x500")
        self.configure(fg_color=GRIS_FONDO)
        self.grab_set()
        self._construir()
        if id_profesor:
            self._cargar()

    def _construir(self):
        ctk.CTkLabel(self, text="Datos del Profesor", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=(16, 8))
        form = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=10)
        form.pack(fill="both", expand=True, padx=20, pady=6)
        self.e_nombres      = campo_form(form, "Nombres *", 0, ancho=240)
        self.e_apellidos    = campo_form(form, "Apellidos *", 1, ancho=240)
        self.e_doc          = campo_form(form, "Documento *", 2, ancho=200)
        self.e_tel          = campo_form(form, "Teléfono *", 3, ancho=200)
        self.e_email        = campo_form(form, "Email *", 4, ancho=280)
        self.e_especialidad = campo_form(form, "Especialidad", 5, ancho=240, placeholder="Opcional")
        self.e_fingreso     = campo_form(form, "Fec. Ingreso *", 6, placeholder="AAAA-MM-DD", ancho=180)
        self.cb_estado      = combo_form(form, "Estado *", 7, ["activo", "inactivo"], ancho=160)
        if self.id_profesor:
            self.e_fingreso.configure(state="disabled")
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=10)
        boton(bf, "Guardar", self._guardar).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=8)

    def _cargar(self):
        try:
            cols, rows = crud.get_profesores()
            for r in rows:
                if r[0] == self.id_profesor:
                    self.e_nombres.insert(0, r[1])
                    self.e_apellidos.insert(0, r[2])
                    self.e_doc.insert(0, r[3])
                    self.e_tel.insert(0, r[4])
                    self.e_email.insert(0, r[5])
                    if r[6]: self.e_especialidad.insert(0, r[6])
                    self.e_fingreso.insert(0, str(r[8]))
                    self.cb_estado.set(r[7])
                    break
        except Exception as e:
            mostrar_error(e)

    def _guardar(self):
        try:
            n = self.e_nombres.get(); a = self.e_apellidos.get()
            d = self.e_doc.get(); t = self.e_tel.get()
            em = self.e_email.get(); esp = self.e_especialidad.get() or None
            est = self.cb_estado.get()
            if self.id_profesor:
                crud.update_profesor(self.id_profesor, n, a, d, t, em, esp, est)
                mostrar_info("Profesor actualizado.")
            else:
                fi = self.e_fingreso.get()
                crud.insert_profesor(n, a, d, t, em, esp, fi)
                mostrar_info("Profesor registrado.")
            if self.on_save: self.on_save()
            self.destroy()
        except Exception as e:
            mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — PLANTILLAS 
# ─────────────────────────────────────────────────────────────────────────────


class TabPlantillas(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=GRIS_FONDO)
        self._construir()

    def _construir(self):
        top = ctk.CTkFrame(self, fg_color=GRIS_PANEL, corner_radius=0, height=52)
        top.pack(fill="x")
        ctk.CTkLabel(top, text="  Plantillas", font=FONT_TITULO, text_color=BLANCO
                     ).pack(side="left", padx=18, pady=10)
        boton(top, "+ Nueva Plantilla", self._nueva_plantilla).pack(side="right", padx=8, pady=8)
        boton(top, "Editar", self._editar_plantilla, color=AZUL).pack(side="right", padx=4, pady=8)
        boton(top, "Eliminar", self._eliminar, color=ROJO).pack(side="right", padx=4, pady=8)
        boton(top, "Actualizar", self.cargar, color="#555577", ancho=100).pack(side="right", padx=4, pady=8)

        cuerpo = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=3)
        cuerpo.rowconfigure(0, weight=1)

        izq = ctk.CTkFrame(cuerpo, fg_color=GRIS_PANEL, corner_radius=10)
        izq.grid(row=0, column=0, sticky="nsew", padx=(10, 4), pady=10)
        ctk.CTkLabel(izq, text="Plantillas", font=FONT_SUBTIT, text_color=VERDE).pack(pady=8)
        self._area_lista = ctk.CTkFrame(izq, fg_color=GRIS_PANEL)
        self._area_lista.pack(fill="both", expand=True, padx=4, pady=4)
        self._tree_plantillas = None

        der = ctk.CTkFrame(cuerpo, fg_color=GRIS_PANEL, corner_radius=10)
        der.grid(row=0, column=1, sticky="nsew", padx=(4, 10), pady=10)
        self._panel_der = der
        ctk.CTkLabel(der, text="Selecciona una plantilla →", font=FONT_NORMAL,
                     text_color=TEXTO_SEC).pack(expand=True)

        self.cargar()

    def cargar(self):
        limpiar_frame(self._area_lista)
        try:
            cols, rows = crud.get_plantillas()
        except Exception as e:
            ctk.CTkLabel(self._area_lista, text=f"Error: {e}", text_color=ROJO).pack()
            return
        nombres = ["ID", "Plantilla", "Categoría", "Temporada", "Estado"]
        anchos = {"ID": 40, "Plantilla": 150, "Categoría": 120, "Temporada": 80, "Estado": 70}
        ft, self._tree_plantillas = hacer_tabla(self._area_lista, nombres, rows,
                                                altura=26, ancho_col=anchos)
        ft.pack(fill="both", expand=True)
        self._tree_plantillas.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, event):
        sel = self._tree_plantillas.selection()
        if not sel:
            return
        v = self._tree_plantillas.item(sel[0])["values"]
        self._mostrar_detalle(v[0], v[1])

    def _mostrar_detalle(self, id_plantilla, nombre_plantilla):
        limpiar_frame(self._panel_der)
        ctk.CTkLabel(self._panel_der, text=f"  {nombre_plantilla}",
                     font=FONT_SUBTIT, text_color=VERDE).pack(pady=8)

        tabs = ctk.CTkTabview(self._panel_der, fg_color=GRIS_FONDO,
                              segmented_button_fg_color=GRIS_PANEL,
                              segmented_button_selected_color=VERDE)
        tabs.pack(fill="both", expand=True, padx=6, pady=4)
        tabs.add("Alineación")
        tabs.add("Banca / Cuerpo Técnico")
        tabs.add("Gestionar")

        PanelAlineacion(tabs.tab("Alineación"), id_plantilla)
        PanelBancaCuerpoTecnico(tabs.tab("Banca / Cuerpo Técnico"), id_plantilla)
        PanelGestionPlantilla(tabs.tab("Gestionar"), id_plantilla, on_refresh=self.cargar)

    def _seleccionado(self):
        sel = self._tree_plantillas.selection() if self._tree_plantillas else []
        if not sel:
            mostrar_error("Selecciona una plantilla.")
            return None
        return self._tree_plantillas.item(sel[0])["values"]

    def _nueva_plantilla(self):
        FormPlantilla(self, on_save=self.cargar)

    def _editar_plantilla(self):
        v = self._seleccionado()
        if v:
            FormPlantilla(self, id_plantilla=v[0], on_save=self.cargar)

    def _eliminar(self):
        v = self._seleccionado()
        if not v:
            return
        if confirmar(f"¿ELIMINAR la plantilla '{v[1]}'?\n\nEsta acción es irreversible y borrará todos sus datos asociados."):
            try:
                crud.delete_plantilla(v[0])
                mostrar_info("Plantilla eliminada correctamente.")
                limpiar_frame(self._panel_der)
                ctk.CTkLabel(self._panel_der, text="Selecciona una plantilla →",
                             font=FONT_NORMAL, text_color=TEXTO_SEC).pack(expand=True)
                self.cargar()
            except Exception as e:
                mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# Panel Gestionar: solo gestiona la lista de TITULARES de la plantilla.
# La banca se gestiona en PanelBancaCuerpoTecnico.
# ─────────────────────────────────────────────────────────────────────────────

class PanelGestionPlantilla(ctk.CTkFrame):
    def __init__(self, master, id_plantilla, on_refresh=None):
        super().__init__(master, fg_color=GRIS_FONDO)
        self.id_plantilla = id_plantilla
        self.on_refresh = on_refresh
        self.pack(fill="both", expand=True)
        self._construir()

    def _construir(self):
        hdr_j = ctk.CTkFrame(self, fg_color="transparent")
        hdr_j.pack(fill="x", padx=14, pady=(10, 2))
        ctk.CTkLabel(hdr_j, text="Jugadores en plantilla (titulares)",
                     font=FONT_SUBTIT, text_color=VERDE).pack(side="left")
        boton(hdr_j, "+ Añadir titular", self._agregar_jugador, ancho=140).pack(side="right", padx=4)
        boton(hdr_j, "Quitar titular", self._quitar_jugador, color=ROJO, ancho=120).pack(side="right", padx=4)

        self._area_j = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area_j.pack(fill="x", padx=12, pady=4)
        self._tree_j = None
        self._cargar_jugadores()

        hdr_p = ctk.CTkFrame(self, fg_color="transparent")
        hdr_p.pack(fill="x", padx=14, pady=(10, 2))
        ctk.CTkLabel(hdr_p, text="Profesores", font=FONT_SUBTIT,
                     text_color=VERDE).pack(side="left")
        boton(hdr_p, "+ Añadir profesor", self._agregar_profesor, ancho=150).pack(side="right", padx=4)
        boton(hdr_p, "Quitar profesor", self._quitar_profesor, color=ROJO, ancho=130).pack(side="right", padx=4)

        self._area_p = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area_p.pack(fill="x", padx=12, pady=4)
        self._tree_p = None
        self._cargar_profesores()

    def _cargar_jugadores(self):
        limpiar_frame(self._area_j)
        try:
            cols, rows = crud.get_titulares_de_plantilla(self.id_plantilla)
        except Exception:
            rows = []
        nombres = ["ID_PJ", "ID_J", "Jugador", "Documento", "Desde", "Estado", "Tipo"]
        ft, self._tree_j = hacer_tabla(self._area_j, nombres, rows, altura=7,
                                       ancho_col={"Jugador": 200, "Documento": 110, "Tipo": 70})
        ft.pack(fill="x")

    def _cargar_profesores(self):
        limpiar_frame(self._area_p)
        try:
            cols, rows = crud.get_profesores_de_plantilla(self.id_plantilla)
        except Exception:
            rows = []
        nombres = ["ID_PP", "ID_P", "Profesor", "Especialidad", "Cargo", "Desde"]
        ft, self._tree_p = hacer_tabla(self._area_p, nombres, rows, altura=5,
                                       ancho_col={"Profesor": 200, "Especialidad": 120})
        ft.pack(fill="x")

    def _agregar_jugador(self):
        FormAsignarJugadorPlantilla(self, self.id_plantilla,
                                    tipo="titular", on_save=self._cargar_jugadores)

    def _quitar_jugador(self):
        if not self._tree_j:
            return
        sel = self._tree_j.selection()
        if not sel:
            mostrar_error("Selecciona un jugador.")
            return
        v = self._tree_j.item(sel[0])["values"]
        if confirmar("¿Quitar este titular de la plantilla?\n"
                     "Si el jugador está en la banca o en la alineación también será removido."):
            try:
                # 1. Quitar de banca si existe
                _, rows = crud.get_jugadores_de_plantilla(
                    self.id_plantilla, tipo="banca"
                )
                for r in rows:
                    if r[1] == v[1]:
                        crud.quitar_jugador_plantilla(r[0])

                # 2. Quitar de alineación guardada — tabla correcta
                crud.ejecutar_query(
                    "DELETE FROM PLANTILLA_ALINEACION "
                    "WHERE id_plantilla = ? AND id_jugador = ?",
                    (int(self.id_plantilla), int(v[1]))
                )

                # 3. Quitar de titulares
                crud.quitar_jugador_plantilla(v[0])
                mostrar_info("Jugador retirado de la plantilla.")
                self._cargar_jugadores()
            except Exception as e:
                mostrar_error(e)

    def _agregar_profesor(self):
        FormAsignarProfesorPlantilla(self, self.id_plantilla, on_save=self._cargar_profesores)

    def _quitar_profesor(self):
        if not self._tree_p:
            return
        sel = self._tree_p.selection()
        if not sel:
            mostrar_error("Selecciona un profesor.")
            return
        v = self._tree_p.item(sel[0])["values"]
        if confirmar("¿Quitar este profesor de la plantilla?"):
            try:
                crud.quitar_profesor_plantilla(v[0])
                mostrar_info("Profesor retirado.")
                self._cargar_profesores()
            except Exception as e:
                mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# Panel Alineación
# ─────────────────────────────────────────────────────────────────────────────

class PanelAlineacion(ctk.CTkFrame):
    def __init__(self, master, id_plantilla):
        super().__init__(master, fg_color=GRIS_FONDO)
        self.id_plantilla = id_plantilla
        self.formacion_actual = "4-4-2"
        self.alineacion = {}
        self.slot_seleccionado = None
        self._jugadores_plantilla = []
        self._ids_en_banca = set()
        self._construir()

    def _construir(self):
        self.pack(fill="both", expand=True)

        barra = ctk.CTkFrame(self, fg_color=GRIS_PANEL, height=44)
        barra.pack(fill="x")
        ctk.CTkLabel(barra, text="Formación:", font=FONT_NORMAL,
                     text_color=TEXTO_SEC).pack(side="left", padx=10, pady=8)
        self.cb_form = ctk.CTkComboBox(
            barra, values=list(FORMACIONES.keys()), width=130,
            fg_color=GRIS_PANEL, border_color=VERDE, button_color=VERDE,
            command=self._cambiar_formacion
        )
        self.cb_form.set(self.formacion_actual)
        self.cb_form.pack(side="left", padx=6, pady=8)
        boton(barra, "Limpiar", self._limpiar, color=ROJO, ancho=90).pack(side="right", padx=8, pady=8)
        boton(barra, "Guardar alineación", self._guardar, ancho=160).pack(side="right", padx=4, pady=8)

        cuerpo = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(0, weight=3)
        cuerpo.columnconfigure(1, weight=2)
        cuerpo.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(cuerpo, bg="#2d6a2d", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        self.canvas.bind("<Configure>", self._dibujar_cancha)
        self.canvas.bind("<Button-1>", self._click_cancha)

        panel_der = ctk.CTkFrame(cuerpo, fg_color=GRIS_CARD, corner_radius=8)
        panel_der.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        ctk.CTkLabel(panel_der, text="Titulares disponibles",
                     font=FONT_SUBTIT, text_color=VERDE).pack(pady=6)
        ctk.CTkLabel(panel_der,
                     text="(Los jugadores en banca no aparecen aquí)",
                     font=FONT_SMALL, text_color=TEXTO_SEC).pack()
        self.e_filtro = ctk.CTkEntry(panel_der, placeholder_text="Buscar jugador...",
                                      width=200, fg_color=GRIS_PANEL, border_color=VERDE)
        self.e_filtro.pack(padx=8, pady=4)
        self.e_filtro.bind("<KeyRelease>", self._filtrar_jugadores)
        self._area_jugadores = ctk.CTkScrollableFrame(
            panel_der, fg_color=GRIS_PANEL, corner_radius=6
        )
        self._area_jugadores.pack(fill="both", expand=True, padx=8, pady=4)
        ctk.CTkLabel(panel_der,
                     text="① Clic en posición  ② Selecciona jugador",
                     font=FONT_SMALL, text_color=TEXTO_SEC, wraplength=200
                     ).pack(padx=8, pady=(0, 6))

        self._cargar_jugadores()

    def _cargar_jugadores(self):
        try:
            cols, rows = crud.get_titulares_de_plantilla(
                self.id_plantilla, solo_activos=True
            )
            self._jugadores_plantilla = list(rows) if rows else []
        except Exception:
            self._jugadores_plantilla = []

        try:
            cols_b, rows_b = crud.get_banca_de_plantilla(self.id_plantilla)
            self._ids_en_banca = {r[1] for r in rows_b} if rows_b else set()
        except Exception:
            self._ids_en_banca = set()

        self._cargar_alineacion_guardada()
        self._mostrar_jugadores(self._jugadores_plantilla)

    def _cargar_alineacion_guardada(self):
        try:
            cols, rows = crud.get_alineacion(self.id_plantilla)
            if not rows:
                return
            formacion = rows[0][3]
            if formacion in FORMACIONES:
                self.formacion_actual = formacion
                self.cb_form.set(formacion)
            self.alineacion = {}
            for r in rows:
                slot = r[4]
                self.alineacion[slot] = {
                    "id_jugador": r[1],
                    "nombre": r[2],
                    "posicion": r[5],
                }
        except Exception:
            pass

    def _jugadores_disponibles(self, lista):
        return [r for r in lista if r[1] not in self._ids_en_banca]

    def _mostrar_jugadores(self, lista):
        limpiar_frame(self._area_jugadores)
        disponibles = self._jugadores_disponibles(lista)
        if not disponibles:
            ctk.CTkLabel(self._area_jugadores,
                         text="Sin titulares disponibles",
                         font=FONT_SMALL, text_color=TEXTO_SEC).pack(pady=8)
            return
        for r in disponibles:
            id_j = r[1]
            nombre = r[2]
            ya_en_cancha = any(v["id_jugador"] == id_j for v in self.alineacion.values())
            color = TEXTO_SEC if ya_en_cancha else BLANCO
            sufijo = " ✓" if ya_en_cancha else ""
            ctk.CTkButton(
                self._area_jugadores,
                text=f"  {nombre}{sufijo}",
                font=FONT_SMALL,
                fg_color="transparent",
                text_color=color,
                hover_color=GRIS_CARD,
                anchor="w",
                command=lambda i=id_j, n=nombre: self._seleccionar_jugador(i, n)
            ).pack(fill="x", pady=1)

    def _filtrar_jugadores(self, event=None):
        txt = self.e_filtro.get().lower()
        filtrados = [r for r in self._jugadores_plantilla
                     if txt in r[2].lower() or txt in str(r[3]).lower()]
        self._mostrar_jugadores(filtrados)

    def _seleccionar_jugador(self, id_jugador, nombre):
        if self.slot_seleccionado is None:
            mostrar_error("Primero haz clic en una posición de la cancha.")
            return
        for slot, dato in self.alineacion.items():
            if dato["id_jugador"] == id_jugador and slot != self.slot_seleccionado:
                mostrar_error(f"{nombre} ya está asignado a otra posición.\n"
                              "Haz clic en esa posición para removerlo primero.")
                return
        pos_nombre = (
            FORMACIONES[self.formacion_actual][self.slot_seleccionado]
            if self.slot_seleccionado < len(FORMACIONES[self.formacion_actual])
            else "Desconocida"
        )
        self.alineacion[self.slot_seleccionado] = {
            "id_jugador": id_jugador,
            "nombre": nombre,
            "posicion": pos_nombre,
        }
        self.slot_seleccionado = None
        self._dibujar_cancha()
        self._mostrar_jugadores(self._jugadores_plantilla)

    def _cambiar_formacion(self, valor=None):
        self.formacion_actual = self.cb_form.get()
        self.alineacion = {}
        self.slot_seleccionado = None
        self._dibujar_cancha()
        self._mostrar_jugadores(self._jugadores_plantilla)

    def _limpiar(self):
        """Limpia la alineación en memoria Y persiste el vaciado en BD."""
        if not self.alineacion:
            mostrar_info("La alineación ya está vacía.")
            return
        if confirmar("¿Limpiar toda la alineación actual?\n"
                     "Esto también borrará la alineación guardada."):
            self.alineacion = {}
            self.slot_seleccionado = None
            try:
                crud.guardar_alineacion(self.id_plantilla, self.formacion_actual, [])
            except Exception as e:
                mostrar_error(f"Error al limpiar alineación en BD: {e}")
                return
            self._dibujar_cancha()
            self._mostrar_jugadores(self._jugadores_plantilla)
            mostrar_info("Alineación limpiada y guardada.")

    def _click_cancha(self, event):
        if not hasattr(self, "_slot_rects"):
            return
        for i, (sx, sy, sr) in enumerate(self._slot_rects):
            if ((event.x - sx) ** 2 + (event.y - sy) ** 2) ** 0.5 <= sr:
                if i in self.alineacion:
                    nombre = self.alineacion[i]["nombre"]
                    if confirmar(f"¿Remover a {nombre} de la posición '{self.alineacion[i]['posicion']}'?"):
                        del self.alineacion[i]
                        self.slot_seleccionado = None
                        self._dibujar_cancha()
                        self._mostrar_jugadores(self._jugadores_plantilla)
                else:
                    self.slot_seleccionado = i
                    self._dibujar_cancha()
                return

    def _dibujar_cancha(self, event=None):
        c = self.canvas
        c.delete("all")
        W = c.winfo_width() or 400
        H = c.winfo_height() or 560
        m = 16; lw = 2; verde_claro = "#3a8a3a"

        c.create_rectangle(0, 0, W, H, fill="#2d6a2d", outline="")
        for i in range(8):
            x0 = m + i * ((W - 2 * m) / 8)
            x1 = x0 + (W - 2 * m) / 16
            c.create_rectangle(x0, m, x1, H - m, fill=verde_claro, outline="")

        c.create_rectangle(m, m, W - m, H - m, outline="white", width=lw)
        c.create_line(m, H // 2, W - m, H // 2, fill="white", width=lw)
        cx, cy, r = W // 2, H // 2, min(W, H) // 10
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="white", width=lw)
        c.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill="white")
        ag_w = (W - 2 * m) * 0.5
        ag_h = (H - 2 * m) * 0.12
        c.create_rectangle(W // 2 - ag_w // 2, m,
                            W // 2 + ag_w // 2, m + ag_h, outline="white", width=lw)
        c.create_rectangle(W // 2 - ag_w // 2, H - m - ag_h,
                            W // 2 + ag_w // 2, H - m, outline="white", width=lw)

        coords = COORDS_FORMACION[self.formacion_actual]
        posiciones_form = FORMACIONES[self.formacion_actual]
        self._slot_rects = []
        for i, (px, py) in enumerate(coords):
            x = m + (W - 2 * m) * px / 100
            y = m + (H - 2 * m) * py / 100
            r_slot = min(W, H) // 14
            self._slot_rects.append((x, y, r_slot))

            es_sel = (i == self.slot_seleccionado)
            tiene = i in self.alineacion
            color_c = VERDE if tiene else (AMARILLO if es_sel else "#1a4a8a")
            color_b = "#ffffff" if (tiene or es_sel) else "#4a80cc"

            c.create_oval(x - r_slot, y - r_slot, x + r_slot, y + r_slot,
                          fill=color_c, outline=color_b, width=2)
            if tiene:
                c.create_text(x, y - 4,
                              text=self.alineacion[i]["nombre"].split()[0],
                              fill=BLANCO, font=("Segoe UI", 8, "bold"),
                              width=r_slot * 2)
                c.create_text(x, y + 8, text="✕",
                              fill="#ffaaaa", font=("Segoe UI", 7))
            else:
                abrev = (posiciones_form[i] if i < len(posiciones_form)
                         else str(i)).split()[0][:3].upper()
                c.create_text(x, y, text=abrev, fill=BLANCO,
                              font=("Segoe UI", 7), width=r_slot * 2)

    def _guardar(self):
        """Guarda la alineación actual (permite guardar vacía para borrar todos los slots)."""
        try:
            slots = [
                {"id_jugador": dato["id_jugador"],
                 "slot_index": slot,
                 "posicion": dato["posicion"]}
                for slot, dato in self.alineacion.items()
            ]
            crud.guardar_alineacion(self.id_plantilla, self.formacion_actual, slots)
            if slots:
                resumen = f"Formación: {self.formacion_actual}\n\n"
                for slot, dato in sorted(self.alineacion.items()):
                    resumen += f"  {dato['posicion']}: {dato['nombre']}\n"
                mostrar_info("Alineación guardada exitosamente:\n\n" + resumen)
            else:
                mostrar_info("Alineación guardada vacía (sin jugadores asignados).")
        except Exception as e:
            mostrar_error(f"Error al guardar alineación: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Panel Banca / Cuerpo Técnico
# ─────────────────────────────────────────────────────────────────────────────

class PanelBancaCuerpoTecnico(ctk.CTkFrame):
    def __init__(self, master, id_plantilla):
        super().__init__(master, fg_color=GRIS_FONDO)
        self.id_plantilla = id_plantilla
        self.pack(fill="both", expand=True)
        self._construir()

    def _construir(self):
        cuerpo = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        izq = ctk.CTkFrame(cuerpo, fg_color=GRIS_CARD, corner_radius=8)
        izq.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        ctk.CTkLabel(izq, text="Banca (suplentes)",
                     font=FONT_SUBTIT, text_color=VERDE).pack(pady=6)
        ctk.CTkLabel(izq,
                     text="Solo titulares no alineados",
                     font=FONT_SMALL, text_color=TEXTO_SEC).pack()

        barra_izq = ctk.CTkFrame(izq, fg_color="transparent")
        barra_izq.pack(fill="x", padx=6, pady=(4, 0))
        boton(barra_izq, "+ Agregar a banca", self._agregar_banca, ancho=140
              ).pack(side="left", pady=4)
        boton(barra_izq, "Quitar de banca", self._quitar_de_banca,
              color=ROJO, ancho=120).pack(side="left", padx=4, pady=4)

        self._area_banca = ctk.CTkFrame(izq, fg_color=GRIS_PANEL, corner_radius=6)
        self._area_banca.pack(fill="both", expand=True, padx=8, pady=6)
        self._tree_banca = None
        self._cargar_banca()

        der = ctk.CTkFrame(cuerpo, fg_color=GRIS_CARD, corner_radius=8)
        der.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        ctk.CTkLabel(der, text="Cuerpo Técnico",
                     font=FONT_SUBTIT, text_color=VERDE).pack(pady=6)

        barra_der = ctk.CTkFrame(der, fg_color="transparent")
        barra_der.pack(fill="x", padx=6, pady=(4, 0))
        boton(barra_der, "+ Agregar", self._agregar_profesor, ancho=120
              ).pack(side="left", pady=4)
        boton(barra_der, "Quitar", self._quitar_profesor,
              color=ROJO, ancho=80).pack(side="left", padx=4, pady=4)

        self._area_ct = ctk.CTkFrame(der, fg_color=GRIS_PANEL, corner_radius=6)
        self._area_ct.pack(fill="both", expand=True, padx=8, pady=6)
        self._tree_ct = None
        self._cargar_ct()

    def _cargar_banca(self):
        limpiar_frame(self._area_banca)
        try:
            cols, rows = crud.get_banca_de_plantilla(self.id_plantilla)
        except Exception:
            rows = []
        ft, self._tree_banca = hacer_tabla(
            self._area_banca,
            ["ID_PJ", "ID_J", "Jugador", "Documento", "Desde", "Estado", "Tipo"],
            rows, altura=10,
            ancho_col={"ID_PJ": 50, "ID_J": 40, "Jugador": 160,
                       "Documento": 100, "Estado": 70, "Tipo": 60}
        )
        ft.pack(fill="both", expand=True)

    def _agregar_banca(self):
        FormAsignarJugadorBanca(self, self.id_plantilla, on_save=self._cargar_banca)

    def _quitar_de_banca(self):
        if not self._tree_banca:
            return
        sel = self._tree_banca.selection()
        if not sel:
            mostrar_error("Selecciona un jugador de la banca.")
            return
        v = self._tree_banca.item(sel[0])["values"]
        if confirmar(f"¿Quitar a {v[2]} de la banca?"):
            try:
                crud.quitar_jugador_plantilla(v[0])
                mostrar_info("Jugador retirado de la banca.")
                self._cargar_banca()
            except Exception as e:
                mostrar_error(e)

    def _cargar_ct(self):
        limpiar_frame(self._area_ct)
        try:
            cols, rows = crud.get_profesores_de_plantilla(self.id_plantilla)
        except Exception:
            rows = []
        ft, self._tree_ct = hacer_tabla(
            self._area_ct,
            ["ID_PP", "ID_P", "Profesor", "Especialidad", "Cargo"],
            [(r[0], r[1], r[2], r[3], r[4]) for r in rows],
            altura=10,
            ancho_col={"ID_PP": 50, "ID_P": 40, "Profesor": 160,
                       "Especialidad": 110, "Cargo": 90}
        )
        ft.pack(fill="both", expand=True)

    def _agregar_profesor(self):
        FormAsignarProfesorPlantilla(self, self.id_plantilla, on_save=self._cargar_ct)

    def _quitar_profesor(self):
        if not self._tree_ct:
            return
        sel = self._tree_ct.selection()
        if not sel:
            mostrar_error("Selecciona un profesor.")
            return
        v = self._tree_ct.item(sel[0])["values"]
        if confirmar("¿Quitar este profesor de la plantilla?"):
            try:
                crud.quitar_profesor_plantilla(v[0])
                mostrar_info("Profesor retirado.")
                self._cargar_ct()
            except Exception as e:
                mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# Formulario para agregar jugador a la BANCA
# ─────────────────────────────────────────────────────────────────────────────

class FormAsignarJugadorBanca(ctk.CTkToplevel):
    def __init__(self, master, id_plantilla, on_save=None):
        super().__init__(master)
        self.id_plantilla = id_plantilla
        self.on_save = on_save
        self.title("Agregar jugador a la banca")
        self.geometry("500x460")
        self.configure(fg_color=GRIS_FONDO)
        self.grab_set()
        self._construir()

    def _construir(self):
        ctk.CTkLabel(self, text="Seleccionar titular para banca",
                     font=FONT_TITULO, text_color=VERDE).pack(pady=12)

        ff = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=8)
        ff.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(ff, text="Buscar:", font=FONT_SMALL,
                     text_color=TEXTO_SEC).pack(side="left", padx=8)
        self.e_filtro = ctk.CTkEntry(ff, width=200, placeholder_text="Nombre o documento",
                                      fg_color=GRIS_PANEL, border_color=VERDE)
        self.e_filtro.pack(side="left", padx=4, pady=6)
        self.e_filtro.bind("<KeyRelease>", self._filtrar)

        self._area = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area.pack(fill="both", expand=True, padx=16)
        self._tree = None
        self._todos = []
        self._cargar()

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=8)
        ctk.CTkLabel(bf, text="Fecha:", font=FONT_NORMAL,
                     text_color=TEXTO_SEC).pack(side="left", padx=6)
        self.e_fecha = ctk.CTkEntry(bf, width=130, placeholder_text="AAAA-MM-DD",
                                     fg_color=GRIS_PANEL, border_color=VERDE)
        self.e_fecha.insert(0, datetime.today().strftime("%Y-%m-%d"))
        self.e_fecha.pack(side="left", padx=4)
        boton(bf, "Agregar a banca", self._agregar).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=4)

    def _cargar(self):
        try:
            cols, rows_t = crud.get_titulares_de_plantilla(
                self.id_plantilla, solo_activos=True
            )
            titulares = list(rows_t) if rows_t else []
        except Exception:
            titulares = []

        try:
            cols_b, rows_b = crud.get_banca_de_plantilla(self.id_plantilla)
            ids_banca = {r[1] for r in rows_b} if rows_b else set()
        except Exception:
            ids_banca = set()

        try:
            cols_a, rows_a = crud.get_alineacion(self.id_plantilla)
            ids_alineados = {r[1] for r in rows_a} if rows_a else set()
        except Exception:
            ids_alineados = set()

        self._todos = [
            r for r in titulares
            if r[1] not in ids_banca and r[1] not in ids_alineados
        ]
        self._renderizar(self._todos)

    def _filtrar(self, event=None):
        txt = self.e_filtro.get().lower()
        filtrados = [r for r in self._todos
                     if txt in r[2].lower() or txt in str(r[3]).lower()]
        self._renderizar(filtrados)

    def _renderizar(self, lista):
        limpiar_frame(self._area)
        nombres = ["ID_PJ", "ID_J", "Jugador", "Documento", "Desde", "Estado", "Tipo"]
        ft, self._tree = hacer_tabla(self._area, nombres, lista, altura=10,
                                     ancho_col={"Jugador": 200, "Documento": 110})
        ft.pack(fill="both", expand=True)

    def _agregar(self):
        if not self._tree:
            return
        sel = self._tree.selection()
        if not sel:
            mostrar_error("Selecciona un jugador.")
            return
        v = self._tree.item(sel[0])["values"]
        try:
            crud.asignar_jugador_banca(
                self.id_plantilla, v[1], self.e_fecha.get()
            )
            mostrar_info(f"{v[2]} agregado a la banca.")
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# Formulario para asignar jugador TITULAR a la plantilla
# ─────────────────────────────────────────────────────────────────────────────

class FormAsignarJugadorPlantilla(ctk.CTkToplevel):
    def __init__(self, master, id_plantilla, tipo="titular", on_save=None):
        super().__init__(master)
        self.id_plantilla = id_plantilla
        self.tipo = tipo
        self.on_save = on_save
        self.title("Añadir Jugador a Plantilla")
        self.geometry("520x520")
        self.configure(fg_color=GRIS_FONDO)
        self.grab_set()
        self._id_cat = self._obtener_id_categoria()
        self._construir()

    def _obtener_id_categoria(self):
        try:
            cols, rows = crud.get_plantillas()
            for r in rows:
                if r[0] == self.id_plantilla:
                    cat_nombre = r[2]
                    cols2, rows2 = crud.get_categorias()
                    for r2 in rows2:
                        if r2[1] == cat_nombre:
                            return r2[0]
        except Exception:
            pass
        return None

    def _construir(self):
        ctk.CTkLabel(self, text="Añadir Titular a Plantilla",
                     font=FONT_TITULO, text_color=VERDE).pack(pady=12)
        ff = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=8)
        ff.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(ff, text="Filtrar:", font=FONT_SMALL,
                     text_color=TEXTO_SEC).pack(side="left", padx=8)
        self.e_filtro = ctk.CTkEntry(ff, width=200, placeholder_text="Nombre o documento",
                                      fg_color=GRIS_PANEL, border_color=VERDE)
        self.e_filtro.pack(side="left", padx=4, pady=6)
        boton(ff, "Buscar", self._cargar, ancho=80).pack(side="left", padx=4, pady=6)

        self._area = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area.pack(fill="both", expand=True, padx=16)
        self._tree = None
        self._cargar()

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=8)
        ctk.CTkLabel(bf, text="Fecha asignación:", font=FONT_NORMAL,
                     text_color=TEXTO_SEC).pack(side="left", padx=6)
        self.e_fecha = ctk.CTkEntry(bf, width=130, placeholder_text="AAAA-MM-DD",
                                     fg_color=GRIS_PANEL, border_color=VERDE)
        self.e_fecha.insert(0, datetime.today().strftime("%Y-%m-%d"))
        self.e_fecha.pack(side="left", padx=4)
        boton(bf, "Asignar como titular", self._asignar).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=4)

    def _cargar(self):
        limpiar_frame(self._area)
        filtro = self.e_filtro.get() if hasattr(self, "e_filtro") else None
        try:
            if self._id_cat:
                cols, rows = crud.filtrar_jugadores_para_plantilla(
                    self._id_cat, filtro or None
                )
                nombres = ["ID", "Nombres", "Apellidos", "Documento", "Nacimiento"]
            else:
                rows = crud.get_jugadores_activos()
                nombres = ["ID", "Nombre Completo", "Documento"]
        except Exception:
            rows = []
            nombres = ["ID", "Jugador", "Documento"]
        ft, self._tree = hacer_tabla(self._area, nombres, rows, altura=10)
        ft.pack(fill="both", expand=True)

    def _asignar(self):
        if not self._tree:
            return
        sel = self._tree.selection()
        if not sel:
            mostrar_error("Selecciona un jugador.")
            return
        v = self._tree.item(sel[0])["values"]
        try:
            crud.asignar_jugador_plantilla(
                self.id_plantilla, v[0], self.e_fecha.get(), tipo="titular"
            )
            mostrar_info("Jugador añadido como titular correctamente.")
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# Formulario Asignar Profesor
# ─────────────────────────────────────────────────────────────────────────────

class FormAsignarProfesorPlantilla(ctk.CTkToplevel):
    def __init__(self, master, id_plantilla, on_save=None):
        super().__init__(master)
        self.id_plantilla = id_plantilla
        self.on_save = on_save
        self.title("Asignar Profesor al Cuerpo Técnico")
        self.geometry("480x320")
        self.configure(fg_color=GRIS_FONDO)
        self.grab_set()
        self._construir()

    def _construir(self):
        ctk.CTkLabel(self, text="Asignar Profesor", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=12)
        try:
            rows = crud.get_profesores_activos()
        except Exception:
            rows = []
        self._profs = rows
        names = [f"{r[1]}" for r in rows]
        form = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=8)
        form.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(form, text="Profesor *:", font=FONT_NORMAL,
                     text_color=TEXTO_SEC).grid(row=0, column=0, sticky="e", padx=8, pady=8)
        self.cb_prof = ctk.CTkComboBox(
            form, values=names, width=260,
            fg_color=GRIS_PANEL, border_color=VERDE,
            button_color=VERDE, dropdown_fg_color=GRIS_PANEL
        )
        self.cb_prof.grid(row=0, column=1, sticky="w", padx=6, pady=8)
        self.e_cargo = campo_form(form, "Cargo:", 1, ancho=260)
        self.e_cargo.insert(0, "Entrenador")
        self.e_fecha = campo_form(form, "Fecha asignación:", 2, ancho=180)
        self.e_fecha.insert(0, datetime.today().strftime("%Y-%m-%d"))
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=10)
        boton(bf, "Asignar", self._asignar).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=8)

    def _asignar(self):
        txt = self.cb_prof.get()
        id_prof = next((r[0] for r in self._profs if str(r[1]) == txt), None)
        if not id_prof:
            mostrar_error("Selecciona un profesor válido.")
            return
        try:
            crud.asignar_profesor_plantilla(
                self.id_plantilla, id_prof, self.e_fecha.get(), self.e_cargo.get()
            )
            mostrar_info("Profesor asignado al cuerpo técnico.")
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# Formulario Plantilla
# ─────────────────────────────────────────────────────────────────────────────

class FormPlantilla(ctk.CTkToplevel):
    def __init__(self, master, id_plantilla=None, on_save=None):
        super().__init__(master)
        self.id_plantilla = id_plantilla
        self.on_save = on_save
        self.title("Nueva Plantilla" if not id_plantilla else "Editar Plantilla")
        self.geometry("460x360")
        self.configure(fg_color=GRIS_FONDO)
        self.grab_set()
        self._construir()
        if id_plantilla:
            self._cargar()

    def _construir(self):
        ctk.CTkLabel(self, text="Datos de Plantilla", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=(16, 8))
        form = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=10)
        form.pack(fill="both", expand=True, padx=20, pady=6)
        self.e_nombre = campo_form(form, "Nombre *", 0)
        try:
            cats = crud.get_categorias_activas()
            cat_names = [f"{r[1]}" for r in cats]
            self._cats = cats
        except Exception:
            cat_names = []
            self._cats = []
        self.cb_cat = combo_form(form, "Categoría *", 1, cat_names)
        self.e_fecha = campo_form(form, "Fec. Creación *", 2, placeholder="AAAA-MM-DD")
        self.e_fecha.insert(0, datetime.today().strftime("%Y-%m-%d"))
        self.e_temporada = campo_form(form, "Temporada", 3, placeholder="Ej: 2025")
        self.cb_estado = combo_form(form, "Estado *", 4, ["activa", "inactiva"])
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=10)
        boton(bf, "Guardar", self._guardar).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=8)

    def _cargar(self):
        try:
            cols, rows = crud.get_plantillas()
            for r in rows:
                if r[0] == self.id_plantilla:
                    self.e_nombre.insert(0, r[1])
                    self.cb_cat.set(r[2])
                    self.e_fecha.insert(0, str(r[3]))
                    if r[4]:
                        self.e_temporada.insert(0, str(r[4]))
                    self.cb_estado.set(r[5])
                    break
        except Exception as e:
            mostrar_error(e)

    def _guardar(self):
        try:
            nombre = self.e_nombre.get()
            cat_txt = self.cb_cat.get()
            id_cat = next((r[0] for r in self._cats if str(r[1]) == cat_txt), None)
            if not id_cat:
                mostrar_error("Selecciona una categoría válida.")
                return
            fecha = self.e_fecha.get()
            temporada = self.e_temporada.get() or None
            estado = self.cb_estado.get()
            if self.id_plantilla:
                crud.update_plantilla(self.id_plantilla, nombre, id_cat, temporada, estado)
                mostrar_info("Plantilla actualizada.")
            else:
                crud.insert_plantilla(nombre, id_cat, fecha, temporada)
                mostrar_info("Plantilla creada.")
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            mostrar_error(e)

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — CATEGORÍAS  
# ─────────────────────────────────────────────────────────────────────────────

class TabCategorias(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=GRIS_FONDO)
        self._tree = None
        self._construir()

    def _construir(self):
        top = ctk.CTkFrame(self, fg_color=GRIS_PANEL, corner_radius=0, height=52)
        top.pack(fill="x")
        ctk.CTkLabel(top, text="  Categorías", font=FONT_TITULO, text_color=BLANCO
                     ).pack(side="left", padx=18, pady=10)
        boton(top, "+ Nueva", self._form_nuevo).pack(side="right", padx=8, pady=8)
        boton(top, "Editar", self._editar, color=AZUL).pack(side="right", padx=4, pady=8)
        boton(top, "Eliminar", self._eliminar, color=ROJO).pack(side="right", padx=4, pady=8)
        boton(top, "Actualizar", self.cargar, color="#555577", ancho=100).pack(side="right", padx=4, pady=8)
        self._area = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area.pack(fill="both", expand=True, padx=14, pady=10)
        self.cargar()

    def cargar(self):
        limpiar_frame(self._area)
        try:
            cols, rows = crud.get_categorias()
        except Exception as e:
            ctk.CTkLabel(self._area, text=f"Error: {e}", text_color=ROJO).pack()
            return
        nombres = ["ID", "Nombre", "Año Mín.", "Año Máx.", "Estado", "Descripción"]
        anchos = {"ID": 40, "Nombre": 180, "Año Mín.": 80, "Año Máx.": 80,
                  "Estado": 80, "Descripción": 300}
        ft, self._tree = hacer_tabla(self._area, nombres, rows, altura=20, ancho_col=anchos)
        ft.pack(fill="both", expand=True)

    def _seleccionado(self):
        sel = self._tree.selection() if self._tree else []
        if not sel:
            mostrar_error("Selecciona una categoría.")
            return None
        return self._tree.item(sel[0])["values"]

    def _form_nuevo(self):
        FormCategoria(self, on_save=self.cargar)

    def _editar(self):
        v = self._seleccionado()
        if v:
            FormCategoria(self, id_cat=v[0], on_save=self.cargar)

    def _eliminar(self):
        v = self._seleccionado()
        if not v:
            return
        if confirmar(f"¿ELIMINAR la categoría '{v[1]}'?"):
            try:
                crud.delete_categoria(v[0])
                mostrar_info("Categoría eliminada.")
                self.cargar()
            except Exception as e:
                mostrar_error(e)


class FormCategoria(ctk.CTkToplevel):
    def __init__(self, master, id_cat=None, on_save=None):
        super().__init__(master)
        self.id_cat = id_cat
        self.on_save = on_save
        self.title("Nueva Categoría" if not id_cat else "Editar Categoría")
        self.geometry("440x360")
        self.configure(fg_color=GRIS_FONDO)
        self.grab_set()
        self._construir()
        if id_cat:
            self._cargar()

    def _construir(self):
        ctk.CTkLabel(self, text="Datos de Categoría", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=(16, 8))
        form = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=10)
        form.pack(fill="both", expand=True, padx=20, pady=6)
        self.e_nombre   = campo_form(form, "Nombre *", 0, ancho=240)
        self.e_anio_min = campo_form(form, "Año Mínimo *", 1, placeholder="Ej: 2010", ancho=140)
        self.e_anio_max = campo_form(form, "Año Máximo *", 2, placeholder="Ej: 2015", ancho=140)
        self.cb_estado  = combo_form(form, "Estado *", 3, ["activa", "inactiva"], ancho=140)
        self.e_desc     = campo_form(form, "Descripción", 4, ancho=280)
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=10)
        boton(bf, "Guardar", self._guardar).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=8)

    def _cargar(self):
        try:
            cols, rows = crud.get_categorias()
            for r in rows:
                if r[0] == self.id_cat:
                    self.e_nombre.insert(0, r[1])
                    self.e_anio_min.insert(0, str(r[2]))
                    self.e_anio_max.insert(0, str(r[3]))
                    self.cb_estado.set(r[4])
                    if r[5]:
                        self.e_desc.insert(0, r[5])
                    break
        except Exception as e:
            mostrar_error(e)

    def _guardar(self):
        try:
            n = self.e_nombre.get()
            am = self.e_anio_min.get()
            ax = self.e_anio_max.get()
            est = self.cb_estado.get()
            desc = self.e_desc.get() or None
            if self.id_cat:
                crud.update_categoria(self.id_cat, n, am, ax, est, desc)
                mostrar_info("Categoría actualizada.")
            else:
                crud.insert_categoria(n, am, ax, desc)
                mostrar_info("Categoría creada.")
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — CANCHAS
# ─────────────────────────────────────────────────────────────────────────────

class TabCanchas(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=GRIS_FONDO)
        self._tree = None
        self._construir()

    def _construir(self):
        top = ctk.CTkFrame(self, fg_color=GRIS_PANEL, corner_radius=0, height=52)
        top.pack(fill="x")
        ctk.CTkLabel(top, text="  Canchas", font=FONT_TITULO, text_color=BLANCO
                     ).pack(side="left", padx=18, pady=10)
        boton(top, "+ Nueva", self._form_nuevo).pack(side="right", padx=8, pady=8)
        boton(top, "Editar", self._editar, color=AZUL).pack(side="right", padx=4, pady=8)
        boton(top, "Eliminar", self._eliminar, color=ROJO).pack(side="right", padx=4, pady=8)
        boton(top, "Actualizar", self.cargar, color="#555577", ancho=100).pack(side="right", padx=4, pady=8)
        self._area = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area.pack(fill="both", expand=True, padx=14, pady=10)
        self.cargar()

    def cargar(self):
        limpiar_frame(self._area)
        try:
            cols, rows = crud.get_canchas()
        except Exception as e:
            ctk.CTkLabel(self._area, text=f"Error: {e}", text_color=ROJO).pack(); return
        nombres = ["ID", "Nombre", "Dirección", "Superficie", "Capacidad", "Estado"]
        anchos = {"ID": 40, "Nombre": 160, "Dirección": 200, "Superficie": 120, "Capacidad": 80, "Estado": 100}
        ft, self._tree = hacer_tabla(self._area, nombres, rows, altura=20, ancho_col=anchos)
        ft.pack(fill="both", expand=True)

    def _seleccionado(self):
        sel = self._tree.selection() if self._tree else []
        if not sel:
            mostrar_error("Selecciona una cancha."); return None
        return self._tree.item(sel[0])["values"]

    def _form_nuevo(self): FormCancha(self, on_save=self.cargar)
    def _editar(self):
        v = self._seleccionado()
        if v: FormCancha(self, id_cancha=v[0], on_save=self.cargar)

    def _eliminar(self):
        v = self._seleccionado()
        if not v: return
        if confirmar(f"¿ELIMINAR la cancha '{v[1]}'?"):
            try:
                crud.delete_cancha(v[0]); mostrar_info("Cancha eliminada."); self.cargar()
            except Exception as e: mostrar_error(e)


class FormCancha(ctk.CTkToplevel):
    def __init__(self, master, id_cancha=None, on_save=None):
        super().__init__(master)
        self.id_cancha = id_cancha; self.on_save = on_save
        self.title("Nueva Cancha" if not id_cancha else "Editar Cancha")
        self.geometry("440x380"); self.configure(fg_color=GRIS_FONDO); self.grab_set()
        self._construir()
        if id_cancha: self._cargar()

    def _construir(self):
        ctk.CTkLabel(self, text="Datos de Cancha", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=(16, 8))
        form = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=10)
        form.pack(fill="both", expand=True, padx=20, pady=6)
        self.e_nombre  = campo_form(form, "Nombre *", 0, ancho=240)
        self.e_dir     = campo_form(form, "Dirección", 1, ancho=280, placeholder="Opcional")
        self.e_sup     = campo_form(form, "Superficie", 2, placeholder="Ej: Pasto sintético", ancho=220)
        self.e_cap     = campo_form(form, "Capacidad", 3, placeholder="Nro. personas", ancho=140)
        self.cb_estado = combo_form(form, "Estado *", 4, ["disponible", "no disponible", "mantenimiento"])
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(pady=10)
        boton(bf, "Guardar", self._guardar).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=8)

    def _cargar(self):
        try:
            cols, rows = crud.get_canchas()
            for r in rows:
                if r[0] == self.id_cancha:
                    self.e_nombre.insert(0, r[1])
                    if r[2]: self.e_dir.insert(0, r[2])
                    if r[3]: self.e_sup.insert(0, r[3])
                    if r[4]: self.e_cap.insert(0, str(r[4]))
                    self.cb_estado.set(r[5]); break
        except Exception as e: mostrar_error(e)

    def _guardar(self):
        try:
            n = self.e_nombre.get(); d = self.e_dir.get() or None
            s = self.e_sup.get() or None; cap = self.e_cap.get() or None; est = self.cb_estado.get()
            if self.id_cancha:
                crud.update_cancha(self.id_cancha, n, d, s, cap, est); mostrar_info("Cancha actualizada.")
            else:
                crud.insert_cancha(n, d, s, cap); mostrar_info("Cancha registrada.")
            if self.on_save: self.on_save()
            self.destroy()
        except Exception as e: mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — SESIONES
# ─────────────────────────────────────────────────────────────────────────────

class TabSesiones(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=GRIS_FONDO)
        self._tree = None
        self._cats = []
        self._construir()

    def _construir(self):
        top = ctk.CTkFrame(self, fg_color=GRIS_PANEL, corner_radius=0, height=52)
        top.pack(fill="x")
        ctk.CTkLabel(top, text="  Sesiones", font=FONT_TITULO, text_color=BLANCO
                     ).pack(side="left", padx=18, pady=10)
        boton(top, "+ Nueva Sesión", self._nueva_sesion).pack(side="right", padx=8, pady=8)
        boton(top, "Asistencia", self._gestionar_asistencia, color=NARANJA).pack(side="right", padx=4, pady=8)
        boton(top, "Cambiar Estado", self._cambiar_estado, color=AZUL).pack(side="right", padx=4, pady=8)
        boton(top, "Actualizar", self.cargar, color="#555577", ancho=100).pack(side="right", padx=4, pady=8)

        ff = ctk.CTkFrame(self, fg_color=GRIS_CARD, height=44)
        ff.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(ff, text="Filtrar:", font=FONT_SMALL, text_color=TEXTO_SEC
                     ).pack(side="left", padx=8, pady=8)
        try:
            cats = crud.get_categorias_activas(); self._cats = cats
            cat_names = ["Todas"] + [r[1] for r in cats]
        except:
            cat_names = ["Todas"]; self._cats = []
        self.cb_cat_f = ctk.CTkComboBox(ff, values=cat_names, width=180,
                                         fg_color=GRIS_PANEL, border_color=VERDE,
                                         button_color=VERDE, command=self._filtrar)
        self.cb_cat_f.pack(side="left", padx=6, pady=8)
        self.cb_tipo_f = ctk.CTkComboBox(ff, values=["Todos", "Torneo", "Partido", "Entrenamiento"],
                                          width=160, fg_color=GRIS_PANEL, border_color=VERDE,
                                          button_color=VERDE, command=self._filtrar)
        self.cb_tipo_f.pack(side="left", padx=6, pady=8)

        self._area = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area.pack(fill="both", expand=True, padx=14, pady=4)
        self.cargar()

    def cargar(self): self._filtrar()

    def _filtrar(self, _=None):
        limpiar_frame(self._area)
        cat_txt = self.cb_cat_f.get() if hasattr(self, 'cb_cat_f') else "Todas"
        tipo_txt = self.cb_tipo_f.get() if hasattr(self, 'cb_tipo_f') else "Todos"
        id_cat = next((r[0] for r in self._cats if r[1] == cat_txt), None)
        tipo = None if tipo_txt == "Todos" else tipo_txt
        try:
            cols, rows = crud.get_sesiones(id_cat, None, tipo)
        except Exception as e:
            ctk.CTkLabel(self._area, text=f"Error: {e}", text_color=ROJO).pack(); return
        nombres = ["ID", "Fecha", "Tipo", "Categoría", "Cancha", "Plantilla", "Estado", "Marcador", "Resultado"]
        anchos = {"ID": 40, "Fecha": 130, "Tipo": 110, "Categoría": 130,
                  "Cancha": 130, "Plantilla": 130, "Estado": 90, "Marcador": 80, "Resultado": 80}
        ft, self._tree = hacer_tabla(self._area, nombres, rows, altura=20, ancho_col=anchos)
        ft.pack(fill="both", expand=True)

    def _seleccionado(self):
        sel = self._tree.selection() if self._tree else []
        if not sel:
            mostrar_error("Selecciona una sesión."); return None
        return self._tree.item(sel[0])["values"]

    def _nueva_sesion(self): FormSesion(self, on_save=self.cargar)
    def _gestionar_asistencia(self):
        v = self._seleccionado()
        if v: PanelAsistencia(self, v[0])
    def _cambiar_estado(self):
        v = self._seleccionado()
        if v: FormEstadoSesion(self, v[0], on_save=self.cargar)


class FormSesion(ctk.CTkToplevel):
    """
    Formulario para crear una sesión en 2 pasos:
    Paso 1: datos básicos (fecha, tipo, categoría, cancha, profesor, plantilla)
    Paso 2: convocatoria de jugadores
    """
    def __init__(self, master, on_save=None):
        super().__init__(master)
        self.on_save = on_save
        self.title("Nueva Sesión")
        self.geometry("660x720")
        self.configure(fg_color=GRIS_FONDO)
        self.grab_set()
        self._id_sesion_creada = None
        self._id_cat = None
        self._id_plantilla = None
        self._construir_paso1()

    def _construir_paso1(self):
        limpiar_frame(self)
        ctk.CTkLabel(self, text="Nueva Sesión — Paso 1/2: Datos",
                     font=FONT_TITULO, text_color=VERDE).pack(pady=(16, 8))
        form = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=10)
        form.pack(fill="x", padx=20, pady=6)
        self.e_fecha = campo_form(form, "Fecha *", 0, placeholder="AAAA-MM-DD HH:MM", ancho=200)
        self.e_fecha.insert(0, datetime.today().strftime("%Y-%m-%d 08:00"))
        self.cb_tipo = combo_form(form, "Tipo *", 1, ["Torneo", "Partido", "Entrenamiento"])

        try:
            cats = crud.get_categorias_activas(); self._cats = cats
            cat_names = [r[1] for r in cats]
        except:
            self._cats = []; cat_names = []
        self.cb_cat = combo_form(form, "Categoría *", 2, cat_names)
        self.cb_cat.configure(command=self._actualizar_plantillas)

        # Plantillas (se filtran según categoría seleccionada)
        ctk.CTkLabel(form, text="Plantilla *", font=FONT_NORMAL, text_color=TEXTO_SEC
                     ).grid(row=3, column=0, sticky="e", padx=(10, 4), pady=4)
        self._plantillas_data = []
        self.cb_plantilla = ctk.CTkComboBox(form, values=["— Selecciona categoría primero —"],
                                             width=260, fg_color=GRIS_PANEL, border_color=VERDE,
                                             button_color=VERDE, dropdown_fg_color=GRIS_PANEL)
        self.cb_plantilla.grid(row=3, column=1, sticky="w", padx=(0, 14), pady=4)

        try:
            canchas = crud.get_canchas_disponibles(); self._canchas = canchas
            cancha_names = [r[1] for r in canchas]
        except:
            self._canchas = []; cancha_names = []
        self.cb_cancha = combo_form(form, "Cancha *", 4, cancha_names)

        try:
            profs = crud.get_profesores_activos(); self._profs = profs
            prof_names = [r[1] for r in profs]
        except:
            self._profs = []; prof_names = []
        self.cb_prof = combo_form(form, "Profesor *", 5, prof_names)
        self.e_obs = campo_form(form, "Observaciones", 6, ancho=320, placeholder="Opcional")

        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(pady=10)
        boton(bf, "Siguiente →", self._paso1_siguiente).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=8)

        # Auto-cargar plantillas con la primera categoría disponible
        if cat_names:
            self._actualizar_plantillas(cat_names[0])

    def _actualizar_plantillas(self, cat_txt=None):
        cat_txt = cat_txt or self.cb_cat.get()
        id_cat = next((r[0] for r in self._cats if r[1] == cat_txt), None)
        if not id_cat:
            return
        try:
            cols, rows = crud.get_plantillas()
            self._plantillas_data = [
                r for r in rows
                if r[2] == cat_txt and str(r[5]).strip().lower() == "activa"
            ]
            names = [r[1] for r in self._plantillas_data]
            self.cb_plantilla.configure(values=names if names else ["— Sin plantillas activas —"])
            if names:
                self.cb_plantilla.set(names[0])
            else:
                self.cb_plantilla.set("— Sin plantillas activas —")
        except Exception as e:
            mostrar_error(f"Error cargando plantillas: {e}")

    def _paso1_siguiente(self):
        try:
            fecha = self.e_fecha.get(); tipo = self.cb_tipo.get()
            cat_txt = self.cb_cat.get(); cancha_txt = self.cb_cancha.get(); prof_txt = self.cb_prof.get()
            plantilla_txt = self.cb_plantilla.get()
            obs = self.e_obs.get() or None

            id_cat = next((r[0] for r in self._cats if r[1] == cat_txt), None)
            id_cancha = next((r[0] for r in self._canchas if r[1] == cancha_txt), None)
            id_prof = next((r[0] for r in self._profs if r[1] == prof_txt), None)
            id_plantilla = next((r[0] for r in self._plantillas_data if r[1] == plantilla_txt), None)

            if not all([id_cat, id_cancha, id_prof, id_plantilla]):
                mostrar_error("Selecciona categoría, plantilla, cancha y profesor válidos.")
                return

            self._id_cat = id_cat
            self._id_plantilla = id_plantilla

            id_sesion = crud.crear_sesion(fecha, id_prof, id_cancha, id_cat,
                                          id_plantilla, tipo, obs)
            if not id_sesion:
                mostrar_error("No se pudo crear la sesión."); return

            self._id_sesion_creada = id_sesion
            self._construir_paso2()
        except Exception as e:
            mostrar_error(e)

    def _construir_paso2(self):
        limpiar_frame(self)
        ctk.CTkLabel(self, text="Nueva Sesión — Paso 2/2: Convocatoria",
                     font=FONT_TITULO, text_color=VERDE).pack(pady=(16, 8))
        ctk.CTkLabel(self, text="Selecciona los jugadores convocados",
                     font=FONT_NORMAL, text_color=TEXTO_SEC).pack()
        ff = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=6)
        ff.pack(fill="x", padx=16, pady=6)
        self.e_filtro2 = ctk.CTkEntry(ff, placeholder_text="Buscar jugador...",
                                       width=220, fg_color=GRIS_PANEL, border_color=VERDE)
        self.e_filtro2.pack(side="left", padx=8, pady=6)
        self.e_filtro2.bind("<KeyRelease>", self._filtrar_jugadores2)
        self._area2 = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area2.pack(fill="both", expand=True, padx=16)
        self._tree2 = None; self._convocados = {}; self._jugadores_conv = []
        self._cargar_convocables()
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(pady=6)
        boton(bf, "Convocar seleccionado", self._convocar).pack(side="left", padx=4)
        boton(bf, "Finalizar", self._finalizar).pack(side="left", padx=8)
        ctk.CTkLabel(self, text="Convocados:", font=FONT_SUBTIT, text_color=VERDE).pack(anchor="w", padx=18)
        self._area_conv = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=6)
        self._area_conv.pack(fill="x", padx=16, pady=4)
        self._tree_conv = None; self._actualizar_tabla_convocados()

    def _cargar_convocables(self):
        limpiar_frame(self._area2)
        filtro = self.e_filtro2.get() if hasattr(self, 'e_filtro2') else None
        try:
            cols, rows = crud.get_jugadores_convocables(self._id_sesion_creada)
            self._jugadores_conv = rows
        except:
            rows = []
        if filtro:
            txt = filtro.lower()
            rows = [r for r in rows if txt in str(r[1]).lower() or txt in str(r[2]).lower()]
        ft, self._tree2 = hacer_tabla(self._area2, ["ID", "Jugador", "Documento"],
                                      rows, altura=8, ancho_col={"ID": 50, "Jugador": 240, "Documento": 120})
        ft.pack(fill="both", expand=True)

    def _filtrar_jugadores2(self, event=None): self._cargar_convocables()

    def _convocar(self):
        if not self._tree2: return
        sel = self._tree2.selection()
        if not sel:
            mostrar_error("Selecciona un jugador."); return
        v = self._tree2.item(sel[0])["values"]
        try:
            crud.registrar_asistencia(self._id_sesion_creada, v[0], convocado=True, asistencia=False)
            self._convocados[v[0]] = v[1]
            self._actualizar_tabla_convocados(); self._cargar_convocables()
        except Exception as e:
            mostrar_error(e)

    def _actualizar_tabla_convocados(self):
        limpiar_frame(self._area_conv)
        datos = [(id_j, nom) for id_j, nom in self._convocados.items()]
        ft, self._tree_conv = hacer_tabla(self._area_conv, ["ID", "Jugador"], datos,
                                          altura=4, ancho_col={"ID": 50, "Jugador": 280})
        ft.pack(fill="both", expand=True)

    def _finalizar(self):
        mostrar_info(f"Sesión #{self._id_sesion_creada} creada con {len(self._convocados)} convocados.")
        if self.on_save: self.on_save()
        self.destroy()


class PanelAsistencia(ctk.CTkToplevel):
    def __init__(self, master, id_sesion):
        super().__init__(master)
        self.id_sesion = id_sesion
        self.title(f"Asistencia — Sesión #{id_sesion}")
        self.geometry("680x580"); self.configure(fg_color=GRIS_FONDO); self.grab_set()
        self._checks = {}
        self._construir()

    def _construir(self):
        ctk.CTkLabel(self, text=f"  Asistencia — Sesión #{self.id_sesion}",
                     font=FONT_TITULO, text_color=VERDE).pack(pady=(16, 8))
        ctk.CTkLabel(self, text="Marca los jugadores que asistieron",
                     font=FONT_NORMAL, text_color=TEXTO_SEC).pack()
        bf_extra = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=6)
        bf_extra.pack(fill="x", padx=16, pady=6)
        boton(bf_extra, "+ Agregar convocado", self._agregar_extra, ancho=160).pack(side="left", padx=8, pady=6)
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=GRIS_PANEL, corner_radius=8, height=320)
        self._scroll.pack(fill="both", expand=True, padx=16, pady=6)
        self._cargar()
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(pady=10)
        boton(bf, "Guardar asistencias", self._guardar).pack(side="left", padx=8)
        boton(bf, "Cerrar", self.destroy, color=ROJO).pack(side="left", padx=8)

    def _cargar(self):
        limpiar_frame(self._scroll); self._checks = {}
        try:
            cols, rows = crud.get_jugadores_sesion(self.id_sesion)
        except Exception as e:
            ctk.CTkLabel(self._scroll, text=f"Error: {e}", text_color=ROJO).pack(); return
        for r in rows:
            id_sj = r[0]; nombre = r[2]; asistio = bool(r[5])
            var = tk.BooleanVar(value=asistio)
            fila = ctk.CTkFrame(self._scroll, fg_color=GRIS_CARD if asistio else GRIS_PANEL, corner_radius=6)
            fila.pack(fill="x", padx=4, pady=2)
            ctk.CTkCheckBox(fila, text=f"  {nombre}  ({r[3]})", variable=var, font=FONT_NORMAL,
                            fg_color=VERDE, hover_color=VERDE_DARK, text_color=BLANCO
                            ).pack(side="left", padx=10, pady=6)
            estado = "Asistió" if asistio else "Sin confirmar"
            ctk.CTkLabel(fila, text=estado, font=FONT_SMALL,
                         text_color=VERDE if asistio else TEXTO_SEC).pack(side="right", padx=10)
            self._checks[id_sj] = (var, r[1])

    def _agregar_extra(self):
        try:
            cols, rows = crud.get_jugadores_convocables(self.id_sesion)
        except:
            rows = []
        if not rows:
            mostrar_info("No hay más jugadores disponibles."); return
        win = ctk.CTkToplevel(self)
        win.title("Agregar convocado extra"); win.geometry("460x360")
        win.configure(fg_color=GRIS_FONDO); win.grab_set()
        ctk.CTkLabel(win, text="Selecciona jugador a convocar",
                     font=FONT_SUBTIT, text_color=VERDE).pack(pady=12)
        area = ctk.CTkFrame(win, fg_color=GRIS_FONDO)
        area.pack(fill="both", expand=True, padx=14)
        ft, tree = hacer_tabla(area, ["ID", "Jugador", "Documento"], rows, altura=10)
        ft.pack(fill="both", expand=True)
        def _confirmar():
            sel = tree.selection()
            if not sel:
                mostrar_error("Selecciona un jugador."); return
            v = tree.item(sel[0])["values"]
            try:
                crud.registrar_asistencia(self.id_sesion, v[0], convocado=True, asistencia=True)
                mostrar_info(f"{v[1]} agregado."); win.destroy(); self._cargar()
            except Exception as e: mostrar_error(e)
        boton(win, "Convocar", _confirmar).pack(pady=8)

    def _guardar(self):
        errores = 0
        for id_sj, (var, id_j) in self._checks.items():
            try:
                crud.update_asistencia(id_sj, convocado=True, asistencia=var.get())
            except:
                errores += 1
        if errores:
            mostrar_error(f"Hubo {errores} errores al guardar.")
        else:
            mostrar_info("Asistencias guardadas correctamente.")
        self._cargar()


class FormEstadoSesion(ctk.CTkToplevel):
    def __init__(self, master, id_sesion, on_save=None):
        super().__init__(master)
        self.id_sesion = id_sesion; self.on_save = on_save
        self.title(f"Actualizar Estado — Sesión #{id_sesion}")
        self.geometry("420x300"); self.configure(fg_color=GRIS_FONDO); self.grab_set()
        self._construir()

    def _construir(self):
        ctk.CTkLabel(self, text="Actualizar Estado de Sesión",
                     font=FONT_TITULO, text_color=VERDE).pack(pady=(16, 8))
        form = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=10)
        form.pack(fill="x", padx=20, pady=6)
        self.cb_estado   = combo_form(form, "Estado *", 0, ["programada", "realizada", "cancelada"])
        self.e_marcador  = campo_form(form, "Marcador", 1, placeholder="Ej: 2-1")
        self.e_resultado = combo_form(form, "Resultado", 2, ["", "Victoria", "Derrota", "Empate"])
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(pady=10)
        boton(bf, "Guardar", self._guardar).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=8)

    def _guardar(self):
        try:
            crud.update_sesion_estado(self.id_sesion, self.cb_estado.get(),
                                      self.e_marcador.get() or None, self.e_resultado.get() or None)
            mostrar_info("Estado actualizado.")
            if self.on_save: self.on_save()
            self.destroy()
        except Exception as e: mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4 — CONCEPTOS DE PAGO
# ─────────────────────────────────────────────────────────────────────────────

class TabConceptos(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=GRIS_FONDO)
        self._tree = None
        self._construir()

    def _construir(self):
        top = ctk.CTkFrame(self, fg_color=GRIS_PANEL, corner_radius=0, height=52)
        top.pack(fill="x")
        ctk.CTkLabel(top, text="  Conceptos de Pago", font=FONT_TITULO, text_color=BLANCO
                     ).pack(side="left", padx=18, pady=10)
        boton(top, "+ Nuevo", self._form_nuevo).pack(side="right", padx=8, pady=8)
        boton(top, "Editar", self._editar, color=AZUL).pack(side="right", padx=4, pady=8)
        boton(top, "Eliminar", self._eliminar, color=ROJO).pack(side="right", padx=4, pady=8)
        boton(top, "Actualizar", self.cargar, color="#555577", ancho=100).pack(side="right", padx=4, pady=8)

        info = ctk.CTkFrame(self, fg_color=GRIS_CARD, height=36)
        info.pack(fill="x", padx=14, pady=(6, 0))
        ctk.CTkLabel(info, text="ℹ  'Mensualidad' es un concepto protegido y nunca puede eliminarse.",
                     font=FONT_SMALL, text_color=NARANJA).pack(side="left", padx=10, pady=6)

        self._area = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area.pack(fill="both", expand=True, padx=14, pady=10)
        self.cargar()

    def cargar(self):
        limpiar_frame(self._area)
        try:
            cols, rows = crud.get_conceptos_todos()
        except Exception as e:
            ctk.CTkLabel(self._area, text=f"Error: {e}", text_color=ROJO).pack(); return
        nombres = ["ID", "Nombre", "Valor Base", "Descripción", "Estado", "Eliminable"]
        anchos = {"ID": 40, "Nombre": 160, "Valor Base": 100, "Descripción": 260, "Estado": 80, "Eliminable": 80}
        ft, self._tree = hacer_tabla(self._area, nombres, rows, altura=18, ancho_col=anchos)
        ft.pack(fill="both", expand=True)

    def _seleccionado(self):
        sel = self._tree.selection() if self._tree else []
        if not sel:
            mostrar_error("Selecciona un concepto."); return None
        return self._tree.item(sel[0])["values"]

    def _form_nuevo(self): FormConcepto(self, on_save=self.cargar)
    def _editar(self):
        v = self._seleccionado()
        if v: FormConcepto(self, id_concepto=v[0], on_save=self.cargar)

    def _eliminar(self):
        v = self._seleccionado()
        if not v: return
        if confirmar(f"¿ELIMINAR el concepto '{v[1]}'?"):
            try:
                crud.delete_concepto(v[0]); mostrar_info("Concepto eliminado."); self.cargar()
            except Exception as e: mostrar_error(e)


class FormConcepto(ctk.CTkToplevel):
    def __init__(self, master, id_concepto=None, on_save=None):
        super().__init__(master)
        self.id_concepto = id_concepto; self.on_save = on_save
        self.title("Nuevo Concepto" if not id_concepto else "Editar Concepto")
        self.geometry("420x340"); self.configure(fg_color=GRIS_FONDO); self.grab_set()
        self._construir()
        if id_concepto: self._cargar()

    def _construir(self):
        ctk.CTkLabel(self, text="Concepto de Pago", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=(16, 8))
        form = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=10)
        form.pack(fill="both", expand=True, padx=20, pady=6)
        self.e_nombre  = campo_form(form, "Nombre *", 0, ancho=240)
        self.e_valor   = campo_form(form, "Valor Base *", 1, placeholder="Ej: 80000", ancho=160)
        self.e_desc    = campo_form(form, "Descripción", 2, ancho=280)
        self.cb_estado = combo_form(form, "Estado *", 3, ["activo", "inactivo"], ancho=140)
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(pady=10)
        boton(bf, "Guardar", self._guardar).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=8)

    def _cargar(self):
        try:
            cols, rows = crud.get_conceptos_todos()
            for r in rows:
                if r[0] == self.id_concepto:
                    self.e_nombre.insert(0, r[1]); self.e_valor.insert(0, str(r[2]))
                    if r[3]: self.e_desc.insert(0, r[3]); self.cb_estado.set(r[4]); break
        except Exception as e: mostrar_error(e)

    def _guardar(self):
        try:
            n = self.e_nombre.get(); v = self.e_valor.get(); d = self.e_desc.get() or None; est = self.cb_estado.get()
            if self.id_concepto:
                crud.update_concepto(self.id_concepto, n, v, d, est); mostrar_info("Concepto actualizado.")
            else:
                crud.insert_concepto(n, v, d); mostrar_info("Concepto creado.")
            if self.on_save: self.on_save()
            self.destroy()
        except Exception as e: mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4 — PAGOS
# ─────────────────────────────────────────────────────────────────────────────

class TabPagos(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=GRIS_FONDO)
        self._tree = None
        self._construir()

    def _construir(self):
        top = ctk.CTkFrame(self, fg_color=GRIS_PANEL, corner_radius=0, height=52)
        top.pack(fill="x")
        ctk.CTkLabel(top, text="  Caja de Pagos", font=FONT_TITULO, text_color=BLANCO
                     ).pack(side="left", padx=18, pady=10)
        boton(top, "+ Registrar Pago", self._form_pago).pack(side="right", padx=8, pady=8)
        boton(top, "Eliminar", self._eliminar_pago, color=ROJO).pack(side="right", padx=4, pady=8)
        boton(top, "Actualizar", self.cargar, color="#555577", ancho=100).pack(side="right", padx=4, pady=8)
        self._area = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area.pack(fill="both", expand=True, padx=14, pady=10)
        self.cargar()

    def cargar(self):
        limpiar_frame(self._area)
        try:
            cols, rows = crud.get_pagos()
        except Exception as e:
            ctk.CTkLabel(self._area, text=f"Error: {e}", text_color=ROJO).pack(); return
        nombres = ["ID", "Jugador", "Documento", "Concepto", "Fecha Pago",
                   "Fec. Expiración", "Valor", "Método", "Observaciones"]
        anchos = {"ID": 40, "Jugador": 180, "Documento": 100, "Concepto": 130,
                  "Fecha Pago": 100, "Fec. Expiración": 110, "Valor": 100,
                  "Método": 100, "Observaciones": 200}
        ft, self._tree = hacer_tabla(self._area, nombres, rows, altura=22, ancho_col=anchos)
        ft.pack(fill="both", expand=True)

    def _seleccionado(self):
        sel = self._tree.selection() if self._tree else []
        if not sel:
            mostrar_error("Selecciona un pago."); return None
        return self._tree.item(sel[0])["values"]

    def _form_pago(self): FormPago(self, on_save=self.cargar)

    def _eliminar_pago(self):
        v = self._seleccionado()
        if not v: return
        if confirmar(f"¿ELIMINAR el pago #{v[0]} de {v[1]}?"):
            try:
                crud.delete_pago(v[0]); mostrar_info("Pago eliminado."); self.cargar()
            except Exception as e: mostrar_error(e)


class FormPago(ctk.CTkToplevel):
    """
    Formulario de registro de pago:
    - Busca al jugador por cédula
    - Si el concepto es Mensualidad, exige fecha de expiración
    - Para otros conceptos, la fecha de expiración es opcional
    """
    def __init__(self, master, on_save=None):
        super().__init__(master)
        self.on_save = on_save
        self.title("Registrar Pago")
        self.geometry("560x640")
        self.configure(fg_color=GRIS_FONDO)
        self.grab_set()
        self._id_jugador = None
        self._construir()

    def _construir(self):
        ctk.CTkLabel(self, text="Registrar Pago", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=(16, 8))

        # ── Búsqueda de jugador ──
        fbusq = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=8)
        fbusq.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(fbusq, text="Buscar jugador por cédula:",
                     font=FONT_NORMAL, text_color=TEXTO_SEC).pack(anchor="w", padx=10, pady=(8, 2))
        bf = ctk.CTkFrame(fbusq, fg_color="transparent")
        bf.pack(fill="x", padx=8, pady=4)
        self.e_busq = ctk.CTkEntry(bf, placeholder_text="Documento...",
                                    width=200, fg_color=GRIS_PANEL, border_color=VERDE)
        self.e_busq.pack(side="left")
        boton(bf, "Buscar", self._buscar, ancho=90).pack(side="left", padx=8)
        boton(bf, "Limpiar", self._limpiar_busqueda, color="#555577", ancho=80).pack(side="left")
        self._lbl_jugador = ctk.CTkLabel(fbusq, text="Ningún jugador seleccionado",
                                          font=FONT_SMALL, text_color=TEXTO_SEC)
        self._lbl_jugador.pack(padx=10, pady=(2, 8))

        # Resultados de búsqueda (ocultos hasta buscar)
        self._area_busq = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._tree_busq = None

        # ── Datos del pago ──
        form = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=8)
        form.pack(fill="x", padx=20, pady=8)

        try:
            conceptos = crud.get_conceptos(); self._conceptos = conceptos
            con_names = [r[1] for r in conceptos]
        except:
            self._conceptos = []; con_names = []

        ctk.CTkLabel(form, text="Concepto *", font=FONT_NORMAL, text_color=TEXTO_SEC
                     ).grid(row=0, column=0, sticky="e", padx=(10, 4), pady=4)
        self.cb_concepto = ctk.CTkComboBox(form, values=con_names, width=260,
                                            fg_color=GRIS_PANEL, border_color=VERDE,
                                            button_color=VERDE, dropdown_fg_color=GRIS_PANEL,
                                            command=self._on_concepto_change)
        self.cb_concepto.grid(row=0, column=1, sticky="w", padx=(0, 14), pady=4)

        self.e_fecha_pago = campo_form(form, "Fecha Pago *", 1, placeholder="AAAA-MM-DD", ancho=180)
        self.e_fecha_pago.insert(0, datetime.today().strftime("%Y-%m-%d"))

        ctk.CTkLabel(form, text="Fec. Expiración", font=FONT_NORMAL,
                     text_color=TEXTO_SEC).grid(row=2, column=0, sticky="e", padx=(10, 4), pady=4)
        self.e_fecha_exp = ctk.CTkEntry(form, width=200,
                                         placeholder_text="AAAA-MM-DD (requerido para Mensualidad)",
                                         fg_color=GRIS_PANEL, border_color=VERDE)
        self.e_fecha_exp.grid(row=2, column=1, sticky="w", padx=(0, 14), pady=4)

        self._lbl_exp_hint = ctk.CTkLabel(form, text="",
                                           font=FONT_SMALL, text_color=NARANJA)
        self._lbl_exp_hint.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 4))

        self.e_valor   = campo_form(form, "Valor *", 4, placeholder="Ej: 80000", ancho=180)
        self.cb_metodo = combo_form(form, "Método *", 5,
                                    ["Efectivo", "Transferencia", "Tarjeta", "Nequi", "Daviplata"], ancho=200)
        self.e_obs     = campo_form(form, "Observaciones", 6, ancho=280, placeholder="Opcional")

        bf2 = ctk.CTkFrame(self, fg_color="transparent")
        bf2.pack(pady=10)
        boton(bf2, "Guardar Pago", self._guardar).pack(side="left", padx=8)
        boton(bf2, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=8)

    def _on_concepto_change(self, val=None):
        con_txt = self.cb_concepto.get()
        es_mens = any("mensualidad" in r[1].lower() and r[1] == con_txt for r in self._conceptos)
        if es_mens:
            self._lbl_exp_hint.configure(text="⚠ Mensualidad requiere fecha de expiración.")
        else:
            self._lbl_exp_hint.configure(text="")

    def _buscar(self):
        doc = self.e_busq.get()
        if not doc:
            mostrar_error("Ingresa un documento para buscar."); return
        try:
            cols, rows = crud.buscar_jugador_para_pago(doc)
        except Exception as e:
            mostrar_error(e); return
        if not rows:
            self._area_busq.pack_forget()
            self._lbl_jugador.configure(text="Sin resultados para ese documento.", text_color=ROJO)
            return
        self._area_busq.pack(fill="x", padx=20, pady=(0, 4))
        limpiar_frame(self._area_busq)
        ft, self._tree_busq = hacer_tabla(self._area_busq,
            ["ID", "Nombre", "Documento", "Estado"], rows, altura=3)
        ft.pack(fill="x")
        self._tree_busq.bind("<<TreeviewSelect>>", self._on_select_jugador)
        self._lbl_jugador.configure(text="Selecciona un jugador de la lista.", text_color=TEXTO_SEC)

    def _limpiar_busqueda(self):
        self._area_busq.pack_forget()
        self._id_jugador = None
        self._lbl_jugador.configure(text="Ningún jugador seleccionado", text_color=TEXTO_SEC)
        self.e_busq.delete(0, "end")

    def _on_select_jugador(self, event):
        sel = self._tree_busq.selection()
        if not sel: return
        v = self._tree_busq.item(sel[0])["values"]
        self._id_jugador = v[0]
        self._lbl_jugador.configure(text=f"  {v[1]} — Doc: {v[2]}", text_color=VERDE)

    def _guardar(self):
        if not self._id_jugador:
            mostrar_error("Selecciona un jugador primero."); return
        con_txt = self.cb_concepto.get()
        id_con = next((r[0] for r in self._conceptos if r[1] == con_txt), None)
        if not id_con:
            mostrar_error("Selecciona un concepto válido."); return
        fecha_exp = self.e_fecha_exp.get().strip() or None
        try:
            crud.insert_pago(self._id_jugador, id_con,
                             self.e_fecha_pago.get(), fecha_exp,
                             self.e_valor.get(), self.cb_metodo.get(),
                             self.e_obs.get() or None)
            mostrar_info("Pago registrado exitosamente.")
            if self.on_save: self.on_save()
            self.destroy()
        except Exception as e:
            mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4 — MOROSIDAD
# ─────────────────────────────────────────────────────────────────────────────

class TabMorosidad(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=GRIS_FONDO)
        self._tree = None
        self._construir()

    def _construir(self):
        top = ctk.CTkFrame(self, fg_color=GRIS_PANEL, corner_radius=0, height=52)
        top.pack(fill="x")
        ctk.CTkLabel(top, text="  Morosidad", font=FONT_TITULO, text_color=BLANCO
                     ).pack(side="left", padx=18, pady=10)
        boton(top, "Actualizar morosos", self._actualizar_morosos, color="#555577", ancho=160
              ).pack(side="right", padx=8, pady=8)
        boton(top, "Cambiar Estado", self._cambiar_estado, color=AZUL).pack(side="right", padx=4, pady=8)
        boton(top, "Agregar Recargo", self._agregar_recargo, color=NARANJA).pack(side="right", padx=4, pady=8)

        leyenda = ctk.CTkFrame(self, fg_color=GRIS_CARD, height=32)
        leyenda.pack(fill="x", padx=14, pady=(6, 0))
        ctk.CTkLabel(leyenda, text="Estados:", font=FONT_SMALL, text_color=TEXTO_SEC
                     ).pack(side="left", padx=8, pady=6)
        ctk.CTkLabel(leyenda, text="en mora = deuda vencida",
                     font=FONT_SMALL, text_color=ROJO).pack(side="left", padx=6)
        ctk.CTkLabel(leyenda, text=" | ", font=FONT_SMALL, text_color=TEXTO_SEC).pack(side="left")
        ctk.CTkLabel(leyenda, text="pendiente = primer mes sin confirmar",
                     font=FONT_SMALL, text_color=NARANJA).pack(side="left", padx=6)

        self._area = ctk.CTkFrame(self, fg_color=GRIS_FONDO)
        self._area.pack(fill="both", expand=True, padx=14, pady=6)
        self.cargar()

    def cargar(self):
        limpiar_frame(self._area)
        try:
            cols, rows = crud.get_morosos()
        except Exception as e:
            ctk.CTkLabel(self._area, text=f"Error: {e}", text_color=ROJO).pack()
            return
        nombres = ["ID Mora", "Jugador", "Documento", "Fec. Vencimiento",
                   "Recargo", "Estado", "Observaciones"]
        anchos = {"ID Mora": 60, "Jugador": 200, "Documento": 110,
                  "Fec. Vencimiento": 120, "Recargo": 100, "Estado": 90, "Observaciones": 250}
        ft, self._tree = hacer_tabla(self._area, nombres, rows, altura=22, ancho_col=anchos)
        ft.pack(fill="both", expand=True)
        for item in self._tree.get_children():
            vals = self._tree.item(item)["values"]
            est = str(vals[5])
            if est == "en mora":
                self._tree.tag_configure("mora", foreground=ROJO)
                self._tree.item(item, tags=("mora",))
            elif est == "pendiente":
                self._tree.tag_configure("pendiente", foreground=NARANJA)
                self._tree.item(item, tags=("pendiente",))

    def _seleccionado(self):
        sel = self._tree.selection() if self._tree else []
        if not sel:
            mostrar_error("Selecciona un registro de mora."); return None
        return self._tree.item(sel[0])["values"]

    def _actualizar_morosos(self):
        try:
            crud.actualizar_morosos()
            mostrar_info("Lista de morosos actualizada correctamente.")
            self.cargar()
        except Exception as e:
            mostrar_error(e)

    def _agregar_recargo(self):
        v = self._seleccionado()
        if not v: return
        win = ctk.CTkToplevel(self)
        win.title(f"Agregar Recargo — {v[1]}")
        win.geometry("420x300"); win.configure(fg_color=GRIS_FONDO); win.grab_set()
        ctk.CTkLabel(win, text=f"Recargo para {v[1]}", font=FONT_SUBTIT,
                     text_color=VERDE).pack(pady=12)
        ctk.CTkLabel(win, text=f"Recargo actual: ${v[4] or 0}",
                     font=FONT_NORMAL, text_color=TEXTO_SEC).pack()
        form = ctk.CTkFrame(win, fg_color=GRIS_CARD, corner_radius=8)
        form.pack(fill="x", padx=20, pady=8)
        e_valor  = campo_form(form, "Valor Recargo *", 0, placeholder="Ej: 10000")
        e_motivo = campo_form(form, "Motivo *", 1, ancho=280)
        def _guardar():
            try:
                crud.agregar_recargo_mora(v[0], e_valor.get(), e_motivo.get())
                mostrar_info("Recargo aplicado correctamente.")
                win.destroy(); self.cargar()
            except Exception as e:
                mostrar_error(e)
        bf = ctk.CTkFrame(win, fg_color="transparent"); bf.pack(pady=8)
        boton(bf, "Aplicar", _guardar).pack(side="left", padx=8)
        boton(bf, "Cancelar", win.destroy, color=ROJO).pack(side="left", padx=8)

    def _cambiar_estado(self):
        v = self._seleccionado()
        if not v: return
        win = ctk.CTkToplevel(self)
        win.title("Cambiar estado de mora")
        win.geometry("400x260"); win.configure(fg_color=GRIS_FONDO); win.grab_set()
        ctk.CTkLabel(win, text=f"Estado de mora — {v[1]}", font=FONT_SUBTIT,
                     text_color=VERDE).pack(pady=12)
        ctk.CTkLabel(win, text=f"Estado actual: {v[5]}", font=FONT_NORMAL,
                     text_color=TEXTO_SEC).pack()
        form = ctk.CTkFrame(win, fg_color=GRIS_CARD, corner_radius=8)
        form.pack(fill="x", padx=20, pady=8)
        cb = combo_form(form, "Nuevo Estado *", 0, ["pendiente", "pagada", "en mora"])
        e_obs = campo_form(form, "Observaciones", 1, ancho=280)
        def _guardar():
            try:
                crud.update_morosidad(v[0], cb.get(), e_obs.get() or None)
                mostrar_info("Estado actualizado.")
                win.destroy(); self.cargar()
            except Exception as e:
                mostrar_error(e)
        bf = ctk.CTkFrame(win, fg_color="transparent"); bf.pack(pady=8)
        boton(bf, "Guardar", _guardar).pack(side="left", padx=8)
        boton(bf, "Cancelar", win.destroy, color=ROJO).pack(side="left", padx=8)


class FormPagarMora(ctk.CTkToplevel):
    def __init__(self, master, id_mora, jugador, on_save=None):
        super().__init__(master)
        self.id_mora = id_mora
        self.on_save = on_save
        self.title(f"Pagar Mora — {jugador}")
        self.geometry("520x440")
        self.configure(fg_color=GRIS_FONDO)
        self.grab_set()
        self._id_jugador = None
        self._construir(jugador)

    def _construir(self, jugador):
        ctk.CTkLabel(self, text="Registrar pago de mora", font=FONT_TITULO,
                     text_color=VERDE).pack(pady=(16, 4))
        ctk.CTkLabel(self, text=f"Jugador: {jugador}", font=FONT_NORMAL,
                     text_color=TEXTO_SEC).pack()

        # Obtener id_jugador buscando en la vista de morosos
        try:
            cols, rows = crud.get_morosos()
            for r in rows:
                if r[0] == self.id_mora:
                    doc = r[2]
                    cols2, rows2 = crud.buscar_jugador_para_pago(doc)
                    if rows2:
                        self._id_jugador = rows2[0][0]
                    break
        except:
            pass

        form = ctk.CTkFrame(self, fg_color=GRIS_CARD, corner_radius=10)
        form.pack(fill="x", padx=20, pady=12)

        try:
            conceptos = crud.get_conceptos(); self._conceptos = conceptos
            con_names = [r[1] for r in conceptos]
        except:
            self._conceptos = []; con_names = []

        ctk.CTkLabel(form, text="Concepto *", font=FONT_NORMAL, text_color=TEXTO_SEC
                     ).grid(row=0, column=0, sticky="e", padx=(10, 4), pady=8)
        self.cb_concepto = ctk.CTkComboBox(form, values=con_names, width=260,
                                            fg_color=GRIS_PANEL, border_color=VERDE,
                                            button_color=VERDE, dropdown_fg_color=GRIS_PANEL)
        self.cb_concepto.grid(row=0, column=1, sticky="w", padx=(0, 14), pady=8)
        for r in self._conceptos:
            if "mensualidad" in r[1].lower():
                self.cb_concepto.set(r[1]); break

        self.e_fecha  = campo_form(form, "Fecha Pago *", 1, placeholder="AAAA-MM-DD", ancho=180)
        self.e_fecha.insert(0, datetime.today().strftime("%Y-%m-%d"))
        self.e_valor  = campo_form(form, "Valor *", 2, placeholder="Ej: 80000", ancho=180)
        self.cb_metodo = combo_form(form, "Método *", 3,
                                    ["Efectivo", "Transferencia", "Tarjeta", "Nequi", "Daviplata"], ancho=200)
        self.e_obs = campo_form(form, "Observaciones", 4, ancho=280, placeholder="Opcional")

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=10)
        boton(bf, "Registrar Pago", self._guardar).pack(side="left", padx=8)
        boton(bf, "Cancelar", self.destroy, color=ROJO).pack(side="left", padx=8)

    def _guardar(self):
        if not self._id_jugador:
            mostrar_error("No se pudo identificar al jugador.\nUsa la Caja de Pagos directamente.")
            return
        con_txt = self.cb_concepto.get()
        id_con = next((r[0] for r in self._conceptos if r[1] == con_txt), None)
        if not id_con:
            mostrar_error("Selecciona un concepto válido."); return
        try:
            crud.insert_pago(self._id_jugador, id_con, self.e_fecha.get(),
                             None, self.e_valor.get(), self.cb_metodo.get(),
                             self.e_obs.get() or None, id_morosidad=self.id_mora)
            mostrar_info("Pago registrado. La mora fue marcada como pagada.")
            if self.on_save: self.on_save()
            self.destroy()
        except Exception as e:
            mostrar_error(e)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 5 — DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

class TabDashboard(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=GRIS_FONDO)
        self._construir()
        self.cargar()

    def _construir(self):
        top = ctk.CTkFrame(self, fg_color=GRIS_PANEL, corner_radius=0, height=52)
        top.pack(fill="x")
        ctk.CTkLabel(top, text="  Dashboard", font=FONT_TITULO, text_color=BLANCO
                     ).pack(side="left", padx=18, pady=10)
        boton(top, "Actualizar", self.cargar, color="#555577", ancho=120).pack(side="right", padx=8, pady=8)
        self._contenido = ctk.CTkScrollableFrame(self, fg_color=GRIS_FONDO)
        self._contenido.pack(fill="both", expand=True)

    def cargar(self):
        limpiar_frame(self._contenido)
        try:
            (kpi_cols, kpi_rows), (hist_cols, hist_rows) = crud.get_datos_dashboard()
        except Exception as e:
            ctk.CTkLabel(self._contenido, text=f"Error al cargar dashboard: {e}",
                         text_color=ROJO, font=FONT_NORMAL).pack(pady=20)
            return

        if not kpi_rows:
            ctk.CTkLabel(self._contenido, text="Sin datos disponibles.",
                         text_color=TEXTO_SEC).pack(pady=20)
            return

        kpi = kpi_rows[0]
        ctk.CTkLabel(self._contenido, text="Resumen del Mes", font=FONT_SUBTIT,
                     text_color=VERDE).pack(anchor="w", padx=20, pady=(16, 8))

        fkpi = ctk.CTkFrame(self._contenido, fg_color="transparent")
        fkpi.pack(fill="x", padx=20)
        kpi_data = [
            ("Ingresos del Mes", f"${kpi[0]:,.0f}" if kpi[0] else "$0", VERDE),
            ("Jugadores Activos", str(kpi[1]), AZUL),
            ("Profesores Activos", str(kpi[2]), AZUL),
            ("Sesiones del Mes", str(kpi[3]), NARANJA),
            ("Morosos", str(kpi[4]), ROJO),
        ]
        for i, (titulo, valor, color) in enumerate(kpi_data):
            card = tarjeta_kpi(fkpi, titulo, valor, color)
            card.grid(row=0, column=i, padx=8, pady=4, sticky="nsew")
            fkpi.columnconfigure(i, weight=1)

        ctk.CTkLabel(self._contenido, text="Histórico de Ingresos Mensuales",
                     font=FONT_SUBTIT, text_color=VERDE).pack(anchor="w", padx=20, pady=(20, 6))
        if hist_rows:
            self._dibujar_grafico_barras(hist_rows)

        ctk.CTkLabel(self._contenido, text="Top Morosos", font=FONT_SUBTIT,
                     text_color=ROJO).pack(anchor="w", padx=20, pady=(16, 6))
        try:
            cols_m, rows_m = crud.get_ranking_morosos()
            ft_m, _ = hacer_tabla(self._contenido,
                ["Jugador", "Documento", "Registros Mora", "Total Recargos", "Último Venc."],
                rows_m, altura=5,
                ancho_col={"Jugador": 200, "Documento": 110, "Total Recargos": 120})
            ft_m.pack(fill="x", padx=20, pady=4)
        except Exception as e:
            ctk.CTkLabel(self._contenido, text=f"Error morosos: {e}",
                         text_color=TEXTO_SEC, font=FONT_SMALL).pack()

        ctk.CTkLabel(self._contenido, text="Sesiones por Categoría",
                     font=FONT_SUBTIT, text_color=AZUL).pack(anchor="w", padx=20, pady=(16, 6))
        try:
            cols_s, rows_s = crud.get_resumen_sesiones_por_categoria()
            ft_s, _ = hacer_tabla(self._contenido,
                ["Categoría", "Tipo", "Total", "Realizadas", "Canceladas"],
                rows_s, altura=6,
                ancho_col={"Categoría": 160, "Tipo": 120, "Total": 70, "Realizadas": 90, "Canceladas": 90})
            ft_s.pack(fill="x", padx=20, pady=(4, 20))
        except Exception as e:
            ctk.CTkLabel(self._contenido, text=f"Error sesiones: {e}",
                         text_color=TEXTO_SEC, font=FONT_SMALL).pack()

    def _dibujar_grafico_barras(self, hist_rows):
        datos = list(reversed(hist_rows[:12]))
        if not datos: return
        MESES = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
                 "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        W, H = 860, 220
        canvas = tk.Canvas(self._contenido, width=W, height=H,
                           bg=GRIS_CARD, highlightthickness=0)
        canvas.pack(padx=20, pady=4)
        margin_l, margin_r, margin_b, margin_t = 70, 20, 40, 20
        chart_w = W - margin_l - margin_r; chart_h = H - margin_b - margin_t
        valores = [float(r[2]) for r in datos]
        max_val = max(valores) if valores else 1
        for i in range(5):
            y = margin_t + chart_h * i / 4; v = max_val * (1 - i / 4)
            canvas.create_line(margin_l, y, W - margin_r, y, fill="#3a3a5a", dash=(4, 4))
            canvas.create_text(margin_l - 6, y, text=f"${v/1000:.0f}k",
                               anchor="e", fill=TEXTO_SEC, font=("Segoe UI", 8))
        bar_w = max(8, chart_w // len(datos) - 8)
        for i, (anio, mes, total) in enumerate(datos):
            x_center = margin_l + (i + 0.5) * chart_w / len(datos)
            bar_h = (float(total) / max_val) * chart_h
            x0 = x_center - bar_w // 2; y0 = margin_t + chart_h - bar_h
            x1 = x_center + bar_w // 2; y1 = margin_t + chart_h
            canvas.create_rectangle(x0, y0, x1, y1, fill=VERDE, outline=VERDE_DARK)
            canvas.create_text(x_center, y0 - 6, text=f"${float(total)/1000:.1f}k",
                               fill=BLANCO, font=("Segoe UI", 7))
            canvas.create_text(x_center, H - margin_b + 10,
                               text=f"{MESES[int(mes)]}\n{str(anio)[2:]}",
                               fill=TEXTO_SEC, font=("Segoe UI", 8))


# ─────────────────────────────────────────────────────────────────────────────
# VENTANA PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class AppClubFutbol(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Club Fútbol DB — Sistema de Gestión")
        self.geometry("1300x780")
        self.minsize(1100, 650)
        self.configure(fg_color=GRIS_FONDO)
        self._construir()
        threading.Thread(target=self._init_morosos, daemon=True).start()

    def _init_morosos(self):
        try:
            crud.actualizar_morosos()
        except:
            pass

    def _construir(self):
        sidebar = ctk.CTkFrame(self, width=210, fg_color=GRIS_PANEL, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo_f = ctk.CTkFrame(sidebar, fg_color=VERDE, height=80, corner_radius=0)
        logo_f.pack(fill="x")
        ctk.CTkLabel(logo_f, text="Club Fútbol DB", font=("Segoe UI", 13, "bold"),
                     text_color=BLANCO).pack(expand=True)

        self._main = ctk.CTkFrame(self, fg_color=GRIS_FONDO, corner_radius=0)
        self._main.pack(side="left", fill="both", expand=True)

        self._tabs = {
            "dashboard":  TabDashboard,
            "jugadores":  TabJugadores,
            "tutores":    TabTutores,
            "profesores": TabProfesores,
            "plantillas": TabPlantillas,
            "categorias": TabCategorias,
            "canchas":    TabCanchas,
            "sesiones":   TabSesiones,
            "conceptos":  TabConceptos,
            "pagos":      TabPagos,
            "morosidad":  TabMorosidad,
        }
        self._tab_frames = {}
        self._tab_activa = None

        menu_items = [
            ("Dashboard",       "dashboard"),
            ("── Personas ──",   None),
            ("Jugadores",        "jugadores"),
            ("Tutores",          "tutores"),
            ("Profesores",       "profesores"),
            ("── Deporte ──",    None),
            ("Plantillas",       "plantillas"),
            ("Categorías",       "categorias"),
            ("Canchas",          "canchas"),
            ("Sesiones",         "sesiones"),
            ("── Finanzas ──",   None),
            ("Conceptos",        "conceptos"),
            ("Caja de Pagos",    "pagos"),
            ("Morosidad",        "morosidad"),
        ]

        for label, key in menu_items:
            if key is None:
                ctk.CTkLabel(sidebar, text=label, font=("Segoe UI", 9),
                             text_color="#666688").pack(pady=(12, 2), padx=10, anchor="w")
            else:
                btn = ctk.CTkButton(
                    sidebar, text=label, anchor="w",
                    fg_color="transparent", hover_color=GRIS_CARD,
                    text_color=TEXTO_SEC, font=("Segoe UI", 12),
                    corner_radius=8, height=36,
                    command=lambda k=key: self._mostrar_tab(k)
                )
                btn.pack(fill="x", padx=8, pady=2)

        self._mostrar_tab("dashboard")

    def _mostrar_tab(self, key):
        if self._tab_activa and self._tab_activa in self._tab_frames:
            self._tab_frames[self._tab_activa].pack_forget()
        if key not in self._tab_frames:
            cls = self._tabs[key]
            frame = cls(self._main)
            self._tab_frames[key] = frame
        self._tab_frames[key].pack(fill="both", expand=True)
        self._tab_activa = key


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = AppClubFutbol()
    app.mainloop()