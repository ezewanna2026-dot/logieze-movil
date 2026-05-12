"""
LOGIEZE Movil - v1.0
App Android para gestion de stock LOGIEZE via Cloudflare Tunnel.

Probar en desktop:
    pip install -r requirements.txt
    python main.py

Compilar APK (Linux/WSL):
    buildozer android debug
"""

__version__ = "1.0"

import json
import os
import threading
from functools import partial

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, TwoLineListItem, ThreeLineListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar

try:
    import requests
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except Exception:
        pass
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False


# ── API client ─────────────────────────────────────────────────────────────────

class API:
    def __init__(self):
        self.base_url = ""
        self.token = "logieze_movil_2024"
        self._session = None

    @property
    def session(self):
        if self._session is None and _REQUESTS_OK:
            self._session = requests.Session()
        return self._session

    def _headers(self):
        return {"X-Token": self.token, "Content-Type": "application/json"}

    def _call(self, method, path, callback, **kwargs):
        if not _REQUESTS_OK:
            Clock.schedule_once(lambda dt: callback(None, "requests no disponible — instalar con pip install requests"), 0)
            return
        if not self.base_url:
            Clock.schedule_once(lambda dt: callback(None, "Sin URL configurada"), 0)
            return

        def _run():
            try:
                url = self.base_url.rstrip("/") + path
                resp = self.session.request(
                    method, url,
                    headers=self._headers(),
                    timeout=12,
                    verify=False,
                    **kwargs,
                )
                data = resp.json()
                Clock.schedule_once(lambda dt: callback(data, None), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: callback(None, str(e)), 0)

        threading.Thread(target=_run, daemon=True).start()

    def get(self, path, callback, params=None):
        self._call("GET", path, callback, params=params)

    def post(self, path, callback, body=None):
        self._call("POST", path, callback, json=body)

    def patch(self, path, callback, body=None):
        self._call("PATCH", path, callback, json=body)

    def ping(self, callback):
        self.get("/ping", callback)

    def stock(self, callback, q="", page=1, per=50):
        self.get("/api/stock", callback, params={"q": q, "page": page, "per": per})

    def producto(self, cod_int, callback):
        self.get(f"/api/stock/{cod_int}", callback)

    def movimiento(self, data, callback):
        self.post("/api/movimiento", callback, body=data)

    def pedidos(self, callback, estado="pendiente", page=1):
        self.get("/api/pedidos", callback, params={"estado": estado, "page": page, "per": 50})

    def historial(self, callback, page=1):
        self.get("/api/historial", callback, params={"page": page, "per": 60})


api = API()


# ── Panel widget classes ───────────────────────────────────────────────────────

class StockPanel(BoxLayout):
    pass

class MoverPanel(BoxLayout):
    pass

class PedidosPanel(BoxLayout):
    pass

class HistorialPanel(BoxLayout):
    pass

class ConfigScreen(MDScreen):
    pass

class HomeScreen(MDScreen):
    pass


# ── KV layout ─────────────────────────────────────────────────────────────────

KV = """
<ConfigScreen>:
    name: "config"
    BoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "LOGIEZE Movil"
            elevation: 2
        ScrollView:
            BoxLayout:
                orientation: "vertical"
                adaptive_height: True
                padding: dp(24)
                spacing: dp(20)

                MDLabel:
                    text: "Configuracion del servidor"
                    font_style: "H5"
                    halign: "center"
                    adaptive_height: True

                MDLabel:
                    text: "Ingresa la URL del tunel Cloudflare del servidor LOGIEZE y el token de acceso."
                    halign: "center"
                    adaptive_height: True
                    theme_text_color: "Secondary"

                MDTextField:
                    id: txt_url
                    hint_text: "URL Tunel Cloudflare"
                    helper_text: "ej: https://algo.trycloudflare.com"
                    helper_text_mode: "persistent"
                    mode: "rectangle"

                MDTextField:
                    id: txt_token
                    hint_text: "Token de acceso"
                    mode: "rectangle"
                    text: "logieze_movil_2024"

                MDRaisedButton:
                    text: "GUARDAR Y CONECTAR"
                    size_hint_x: 1
                    on_release: app.guardar_config()

                MDFlatButton:
                    text: "Probar conexion sin guardar"
                    size_hint_x: 1
                    on_release: app.test_conexion_manual()

<HomeScreen>:
    name: "home"
    MDBottomNavigation:
        id: bottom_nav
        MDBottomNavigationItem:
            name: "stock"
            text: "Stock"
            icon: "magnify"
            StockPanel:
                id: stock_panel
        MDBottomNavigationItem:
            name: "mover"
            text: "Mover"
            icon: "swap-horizontal"
            MoverPanel:
                id: mover_panel
        MDBottomNavigationItem:
            name: "pedidos"
            text: "Pedidos"
            icon: "clipboard-list"
            PedidosPanel:
                id: pedidos_panel
        MDBottomNavigationItem:
            name: "historial"
            text: "Historial"
            icon: "history"
            HistorialPanel:
                id: historial_panel

<StockPanel>:
    orientation: "vertical"
    BoxLayout:
        size_hint_y: None
        height: dp(64)
        padding: [dp(8), dp(6)]
        spacing: dp(8)
        MDTextField:
            id: txt_buscar
            hint_text: "Buscar por nombre, codigo o barras..."
            mode: "rectangle"
            on_text_validate: app.buscar_stock(self.text)
        MDRaisedButton:
            text: "IR"
            size_hint_x: None
            width: dp(60)
            on_release: app.buscar_stock(root.ids.txt_buscar.text)
    BoxLayout:
        size_hint_y: None
        height: dp(36)
        padding: [dp(10), 0]
        MDLabel:
            id: lbl_stock_info
            text: "Escribi para buscar productos"
            theme_text_color: "Secondary"
            halign: "left"
        MDFlatButton:
            text: "Config"
            size_hint_x: None
            width: dp(72)
            on_release: app.ir_config()
    ScrollView:
        MDList:
            id: list_stock

<MoverPanel>:
    orientation: "vertical"
    padding: [dp(16), dp(8)]
    spacing: dp(8)
    MDLabel:
        text: "Registrar Movimiento"
        font_style: "H6"
        halign: "center"
        size_hint_y: None
        height: dp(36)
    BoxLayout:
        size_hint_y: None
        height: dp(56)
        spacing: dp(8)
        MDTextField:
            id: txt_cod
            hint_text: "Codigo de producto"
            mode: "rectangle"
            size_hint_x: 0.65
            on_text_validate: app.buscar_para_mover()
        MDRaisedButton:
            text: "Buscar"
            size_hint_x: 0.35
            on_release: app.buscar_para_mover()
    MDLabel:
        id: lbl_prod_nombre
        text: ""
        halign: "center"
        font_style: "Subtitle1"
        size_hint_y: None
        height: dp(28)
    MDLabel:
        id: lbl_prod_stock
        text: ""
        halign: "center"
        theme_text_color: "Secondary"
        size_hint_y: None
        height: dp(24)
    BoxLayout:
        size_hint_y: None
        height: dp(56)
        spacing: dp(8)
        MDRaisedButton:
            id: btn_tipo
            text: "ENTRADA"
            size_hint_x: 0.5
            on_release: app.abrir_menu_tipo(self)
        MDTextField:
            id: txt_cantidad
            hint_text: "Cantidad"
            mode: "rectangle"
            input_filter: "float"
            size_hint_x: 0.5
    MDTextField:
        id: txt_ubicacion
        hint_text: "Ubicacion (ej: Salon 3)"
        mode: "rectangle"
        size_hint_y: None
        height: dp(56)
    MDRaisedButton:
        text: "REGISTRAR MOVIMIENTO"
        size_hint_x: 1
        md_bg_color: 0.1, 0.55, 0.1, 1
        on_release: app.registrar_movimiento()
    Widget:

<PedidosPanel>:
    orientation: "vertical"
    BoxLayout:
        size_hint_y: None
        height: dp(46)
        padding: [dp(4), dp(4)]
        spacing: dp(4)
        MDRaisedButton:
            text: "Pendientes"
            on_release: app.cargar_pedidos("pendiente")
            size_hint_x: 1
        MDFlatButton:
            text: "Completados"
            on_release: app.cargar_pedidos("completado")
            size_hint_x: 1
        MDFlatButton:
            text: "Cancelados"
            on_release: app.cargar_pedidos("cancelado")
            size_hint_x: 1
    MDLabel:
        id: lbl_pedidos_info
        text: "Cargando..."
        halign: "center"
        theme_text_color: "Secondary"
        size_hint_y: None
        height: dp(32)
    ScrollView:
        MDList:
            id: list_pedidos

<HistorialPanel>:
    orientation: "vertical"
    BoxLayout:
        size_hint_y: None
        height: dp(46)
        padding: [dp(8), dp(4)]
        MDRaisedButton:
            text: "Actualizar historial"
            size_hint_x: 1
            on_release: app.cargar_historial()
    MDLabel:
        id: lbl_hist_info
        text: "Cargando..."
        halign: "center"
        theme_text_color: "Secondary"
        size_hint_y: None
        height: dp(32)
    ScrollView:
        MDList:
            id: list_historial
"""


# ── App ────────────────────────────────────────────────────────────────────────

class LOGIEZEApp(MDApp):
    _tipo_mov = "entrada"
    _producto_actual = None
    _pedidos_estado = "pendiente"
    _dialog = None
    _menu_tipo = None

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        Builder.load_string(KV)
        sm = MDScreenManager()
        sm.add_widget(ConfigScreen())
        sm.add_widget(HomeScreen())
        return sm

    def on_start(self):
        self._cargar_config()

    # ── Config ─────────────────────────────────────────────────────────────────

    def _config_path(self):
        try:
            return os.path.join(self.user_data_dir, "logieze_config.json")
        except Exception:
            return "logieze_config.json"

    def _cargar_config(self):
        try:
            with open(self._config_path()) as f:
                cfg = json.load(f)
            url = cfg.get("url", "")
            token = cfg.get("token", "logieze_movil_2024")
            if url:
                api.base_url = url
                api.token = token
                cs = self.root.get_screen("config")
                cs.ids.txt_url.text = url
                cs.ids.txt_token.text = token
                self.root.current = "home"
                Clock.schedule_once(lambda dt: self._datos_inicio(), 0.8)
        except Exception:
            pass  # Primera vez: mostrar pantalla config

    def guardar_config(self):
        cs = self.root.get_screen("config")
        url = cs.ids.txt_url.text.strip()
        token = cs.ids.txt_token.text.strip() or "logieze_movil_2024"
        if not url:
            self._snack("Ingresa la URL del tunel")
            return
        if not url.startswith("http"):
            url = "https://" + url
            cs.ids.txt_url.text = url
        api.base_url = url
        api.token = token
        try:
            os.makedirs(os.path.dirname(self._config_path()), exist_ok=True)
        except Exception:
            pass
        try:
            with open(self._config_path(), "w") as f:
                json.dump({"url": url, "token": token}, f)
        except Exception as e:
            self._snack(f"Error guardando: {e}")
            return
        self._snack("Guardado. Probando conexion...")
        api.ping(lambda data, err: self._on_ping(data, err, ir_home=True))

    def test_conexion_manual(self):
        cs = self.root.get_screen("config")
        url = cs.ids.txt_url.text.strip()
        token = cs.ids.txt_token.text.strip() or "logieze_movil_2024"
        if not url:
            self._snack("Ingresa la URL primero")
            return
        if not url.startswith("http"):
            url = "https://" + url
        api.base_url = url
        api.token = token
        self._snack("Probando...")
        api.ping(lambda data, err: self._on_ping(data, err, ir_home=False))

    def _on_ping(self, data, err, ir_home=False):
        if err:
            self._snack(f"Sin conexion: {err[:70]}")
        elif data and data.get("ok"):
            self._snack("Conexion exitosa")
            if ir_home:
                self.root.current = "home"
                Clock.schedule_once(lambda dt: self._datos_inicio(), 0.5)
        else:
            self._snack("Respuesta inesperada del servidor")

    def ir_config(self):
        self.root.current = "config"

    def _datos_inicio(self):
        self.buscar_stock("")
        self.cargar_pedidos()
        self.cargar_historial()

    # ── Stock ──────────────────────────────────────────────────────────────────

    def buscar_stock(self, q=""):
        home = self.root.get_screen("home")
        p = home.ids.stock_panel
        p.ids.lbl_stock_info.text = "Buscando..."
        p.ids.list_stock.clear_widgets()

        def _cb(data, err):
            if err:
                p.ids.lbl_stock_info.text = f"Error: {err[:60]}"
                return
            items = data.get("items", [])
            n = len(items)
            p.ids.lbl_stock_info.text = f"{n} resultado{'s' if n != 1 else ''}"
            for item in items:
                nom = item.get("nombre", "?")
                cod = item.get("cod_int", "")
                stock = item.get("cantidad_total", 0)
                precio = item.get("precio", "")
                row = TwoLineListItem(
                    text=f"{nom}  ({cod})",
                    secondary_text=f"Stock: {stock}  |  ${precio}",
                    on_release=partial(self._ver_producto, item),
                )
                p.ids.list_stock.add_widget(row)

        api.stock(_cb, q=q.strip())

    def _ver_producto(self, item, *args):
        cod = item.get("cod_int", "")
        api.producto(cod, self._mostrar_producto)

    def _mostrar_producto(self, data, err):
        if err:
            self._snack(f"Error: {err[:60]}")
            return
        if not data or "error" in data:
            self._snack("Producto no encontrado")
            return
        cod = data.get("cod_int", "")
        nombre = data.get("nombre", "?")
        stock = data.get("cantidad_total", 0)
        salon3 = data.get("stock_salon3", "")
        precio = data.get("precio", "")
        costo = data.get("costo", "")
        barras = data.get("barras", "")
        cat = data.get("categoria", "")

        lineas = [f"Codigo: {cod}", f"Stock total: {stock}"]
        if salon3 not in ("", None):
            lineas.append(f"Salon 3: {salon3}")
        if precio:
            lineas.append(f"Precio: ${precio}")
        if costo:
            lineas.append(f"Costo: ${costo}")
        if barras:
            lineas.append(f"Barras: {barras}")
        if cat:
            lineas.append(f"Categoria: {cat}")

        if self._dialog:
            self._dialog.dismiss()
        self._dialog = MDDialog(
            title=nombre,
            text="\n".join(lineas),
            buttons=[
                MDFlatButton(text="CERRAR",
                             on_release=lambda x: self._dialog.dismiss()),
                MDRaisedButton(text="IR A MOVER",
                               on_release=lambda x: self._ir_a_mover(cod)),
            ],
        )
        self._dialog.open()

    def _ir_a_mover(self, cod):
        if self._dialog:
            self._dialog.dismiss()
        home = self.root.get_screen("home")
        home.ids.mover_panel.ids.txt_cod.text = cod
        self._snack("Codigo cargado — usa la pestana Mover")

    # ── Movimiento ─────────────────────────────────────────────────────────────

    def buscar_para_mover(self):
        home = self.root.get_screen("home")
        p = home.ids.mover_panel
        cod = p.ids.txt_cod.text.strip()
        if not cod:
            return
        p.ids.lbl_prod_nombre.text = "Buscando..."
        p.ids.lbl_prod_stock.text = ""
        self._producto_actual = None

        def _cb(data, err):
            if err:
                p.ids.lbl_prod_nombre.text = f"Error: {err[:50]}"
                return
            if not data or "error" in data:
                p.ids.lbl_prod_nombre.text = "Producto no encontrado"
                return
            self._producto_actual = data
            p.ids.lbl_prod_nombre.text = data.get("nombre", "?")
            p.ids.lbl_prod_stock.text = f"Stock actual: {data.get('cantidad_total', 0)}"

        api.producto(cod, _cb)

    def abrir_menu_tipo(self, btn):
        self._menu_tipo = MDDropdownMenu(
            caller=btn,
            items=[
                {
                    "viewclass": "OneLineListItem",
                    "text": "Entrada (suma al stock)",
                    "height": dp(54),
                    "on_release": lambda: (
                        self._set_tipo("entrada", btn),
                        self._menu_tipo.dismiss(),
                    ),
                },
                {
                    "viewclass": "OneLineListItem",
                    "text": "Salida (resta al stock)",
                    "height": dp(54),
                    "on_release": lambda: (
                        self._set_tipo("salida", btn),
                        self._menu_tipo.dismiss(),
                    ),
                },
                {
                    "viewclass": "OneLineListItem",
                    "text": "Ajuste (fija el valor)",
                    "height": dp(54),
                    "on_release": lambda: (
                        self._set_tipo("ajuste", btn),
                        self._menu_tipo.dismiss(),
                    ),
                },
            ],
            width_mult=4,
        )
        self._menu_tipo.open()

    def _set_tipo(self, tipo, btn):
        self._tipo_mov = tipo
        btn.text = tipo.upper()

    def registrar_movimiento(self):
        if not self._producto_actual:
            self._snack("Primero busca un producto")
            return
        home = self.root.get_screen("home")
        p = home.ids.mover_panel
        cant_txt = p.ids.txt_cantidad.text.strip()
        if not cant_txt:
            self._snack("Ingresa la cantidad")
            return
        try:
            cantidad = float(cant_txt)
        except ValueError:
            self._snack("Cantidad invalida")
            return
        if cantidad < 0:
            self._snack("La cantidad no puede ser negativa")
            return

        body = {
            "cod_int": self._producto_actual.get("cod_int"),
            "nombre": self._producto_actual.get("nombre"),
            "tipo": self._tipo_mov,
            "cantidad": cantidad,
            "ubicacion": p.ids.txt_ubicacion.text.strip(),
            "usuario": "movil",
        }

        def _cb(data, err):
            if err:
                self._snack(f"Error: {err[:70]}")
                return
            if data and data.get("ok"):
                nuevo = data.get("stock_nuevo", "?")
                antes = data.get("stock_antes", "?")
                self._snack(f"OK — Stock: {antes} -> {nuevo}")
                p.ids.txt_cantidad.text = ""
                p.ids.txt_ubicacion.text = ""
                p.ids.lbl_prod_stock.text = f"Nuevo stock: {nuevo}"
                self._producto_actual = None
                p.ids.txt_cod.text = ""
                p.ids.lbl_prod_nombre.text = ""
                p.ids.btn_tipo.text = "ENTRADA"
                self._tipo_mov = "entrada"
            else:
                msg = data.get("error", "Error desconocido") if data else "Sin respuesta"
                self._snack(msg)

        api.movimiento(body, _cb)

    # ── Pedidos ────────────────────────────────────────────────────────────────

    def cargar_pedidos(self, estado=None):
        if estado:
            self._pedidos_estado = estado
        home = self.root.get_screen("home")
        p = home.ids.pedidos_panel
        p.ids.lbl_pedidos_info.text = f"Cargando {self._pedidos_estado}..."
        p.ids.list_pedidos.clear_widgets()

        def _cb(data, err):
            if err:
                p.ids.lbl_pedidos_info.text = f"Error: {err[:60]}"
                return
            pedidos = data.get("pedidos", [])
            n = len(pedidos)
            p.ids.lbl_pedidos_info.text = (
                f"{n} pedido{'s' if n != 1 else ''} — {self._pedidos_estado}"
            )
            for ped in pedidos:
                nombre = ped.get("nombre", "?")
                fecha = str(ped.get("fecha", ""))[:10]
                items = ped.get("items", [])
                n_items = len(items) if isinstance(items, list) else "?"
                estado_ped = ped.get("estado", "")
                row = ThreeLineListItem(
                    text=nombre,
                    secondary_text=f"Fecha: {fecha}  |  {n_items} items",
                    tertiary_text=f"Estado: {estado_ped}",
                    on_release=partial(self._ver_pedido, ped),
                )
                p.ids.list_pedidos.add_widget(row)

        api.pedidos(_cb, estado=self._pedidos_estado)

    def _ver_pedido(self, pedido, *args):
        nombre = pedido.get("nombre", "?")
        fecha = str(pedido.get("fecha", ""))[:10]
        estado = pedido.get("estado", "")
        items = pedido.get("items", [])
        pid = pedido.get("id")

        lineas = [f"Fecha: {fecha}", f"Estado: {estado}", ""]
        if isinstance(items, list):
            for it in items[:25]:
                if isinstance(it, dict):
                    cod = it.get("cod_int", it.get("codigo", ""))
                    nom = it.get("nombre", cod)
                    cant = it.get("cantidad", "")
                    lineas.append(f"- {nom}: {cant}")
            if len(items) > 25:
                lineas.append(f"  ... y {len(items) - 25} mas")

        if self._dialog:
            self._dialog.dismiss()

        btns = [MDFlatButton(text="CERRAR", on_release=lambda x: self._dialog.dismiss())]
        if estado == "pendiente":
            btns.append(MDRaisedButton(
                text="COMPLETAR",
                md_bg_color=(0.1, 0.55, 0.1, 1),
                on_release=lambda x: self._cambiar_estado_pedido(pid, "completado"),
            ))
            btns.append(MDFlatButton(
                text="CANCELAR",
                on_release=lambda x: self._cambiar_estado_pedido(pid, "cancelado"),
            ))

        self._dialog = MDDialog(title=nombre, text="\n".join(lineas), buttons=btns)
        self._dialog.open()

    def _cambiar_estado_pedido(self, pid, estado):
        if self._dialog:
            self._dialog.dismiss()

        def _cb(data, err):
            if err:
                self._snack(f"Error: {err[:60]}")
            elif data and data.get("ok"):
                self._snack(f"Pedido marcado como {estado}")
                self.cargar_pedidos()
            else:
                self._snack("No se pudo actualizar el estado")

        api.patch(f"/api/pedidos/{pid}/estado", _cb, body={"estado": estado})

    # ── Historial ──────────────────────────────────────────────────────────────

    def cargar_historial(self):
        home = self.root.get_screen("home")
        p = home.ids.historial_panel
        p.ids.lbl_hist_info.text = "Cargando..."
        p.ids.list_historial.clear_widgets()

        def _cb(data, err):
            if err:
                p.ids.lbl_hist_info.text = f"Error: {err[:60]}"
                return
            movs = data.get("movimientos", [])
            n = len(movs)
            p.ids.lbl_hist_info.text = f"Ultimos {n} movimientos"
            for m in movs:
                tipo = m.get("tipo", "?").upper()
                nombre = m.get("nombre", "?")
                cant = m.get("cantidad", 0)
                usuario = m.get("usuario", "")
                fecha = str(m.get("fecha_hora", ""))[:16]
                ubicacion = m.get("ubicacion", "")
                sec = fecha
                if usuario:
                    sec += f"  |  {usuario}"
                tert = f"Ubicacion: {ubicacion}" if ubicacion else " "
                row = ThreeLineListItem(
                    text=f"[{tipo}]  {nombre}",
                    secondary_text=f"Cantidad: {cant}  |  {sec}",
                    tertiary_text=tert,
                )
                p.ids.list_historial.add_widget(row)

        api.historial(_cb)

    # ── Helper ─────────────────────────────────────────────────────────────────

    def _snack(self, text):
        Snackbar(
            text=str(text),
            snackbar_x=dp(8),
            snackbar_y=dp(8),
            size_hint_x=0.95,
        ).open()


if __name__ == "__main__":
    LOGIEZEApp().run()
