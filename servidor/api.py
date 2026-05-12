"""
LOGIEZE Mobile API
==================
Flask REST API que expone los datos de PostgreSQL al app Android.
Corre en el servidor LOGIEZE, expuesto via Cloudflare Tunnel.

Iniciar: python api.py
Puerto:  5050
"""

from flask import Flask, request, jsonify
from functools import wraps
import psycopg2, psycopg2.extras, json, os
from datetime import datetime

app = Flask(__name__)

# ── Configuración ─────────────────────────────────────────────────────────────
API_TOKEN = "logieze_movil_2024"   # Cambiar por uno seguro

PG = dict(
    host     = "localhost",
    port     = 5432,
    dbname   = "logieze",
    user     = "logieze_user",
    password = "Logieze2024",
    connect_timeout = 5
)

# ── Auth simple por token ──────────────────────────────────────────────────────
def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Token") or request.args.get("token")
        if token != API_TOKEN:
            return jsonify({"error": "No autorizado"}), 401
        return f(*args, **kwargs)
    return decorated

def pg():
    conn = psycopg2.connect(**PG)
    conn.autocommit = False
    return conn

def rows_to_dicts(cur):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/ping")
def ping():
    return jsonify({"ok": True, "ts": datetime.now().isoformat()})

# ══════════════════════════════════════════════════════════════════════════════
# STOCK — buscar productos
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/stock")
@require_token
def get_stock():
    q    = request.args.get("q", "").strip()
    page = int(request.args.get("page", 1))
    per  = int(request.args.get("per", 50))
    offset = (page - 1) * per

    conn = pg(); cur = conn.cursor()
    if q:
        like = f"%{q}%"
        cur.execute("""
            SELECT cod_int, nombre, cantidad_total, stock_salon3, precio, barras
            FROM maestra
            WHERE nombre ILIKE %s OR cod_int ILIKE %s OR barras ILIKE %s
            ORDER BY nombre
            LIMIT %s OFFSET %s
        """, (like, like, like, per, offset))
    else:
        cur.execute("""
            SELECT cod_int, nombre, cantidad_total, stock_salon3, precio, barras
            FROM maestra
            ORDER BY nombre
            LIMIT %s OFFSET %s
        """, (per, offset))
    rows = rows_to_dicts(cur)
    conn.close()
    return jsonify({"items": rows, "page": page})

@app.route("/api/stock/<cod_int>")
@require_token
def get_producto(cod_int):
    conn = pg(); cur = conn.cursor()
    cur.execute("""
        SELECT cod_int, nombre, cantidad_total, stock_salon3, precio, costo, barras, categoria
        FROM maestra WHERE cod_int = %s
    """, (cod_int,))
    row = rows_to_dicts(cur)
    conn.close()
    if not row:
        return jsonify({"error": "No encontrado"}), 404
    return jsonify(row[0])

# ══════════════════════════════════════════════════════════════════════════════
# MOVIMIENTOS — registrar entrada / salida
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/movimiento", methods=["POST"])
@require_token
def registrar_movimiento():
    data     = request.get_json()
    cod_int  = data.get("cod_int", "").strip()
    tipo     = data.get("tipo", "").strip()      # entrada / salida / ajuste
    cantidad = float(data.get("cantidad", 0))
    ubicacion = data.get("ubicacion", "")
    usuario  = data.get("usuario", "movil")
    nombre   = data.get("nombre", "")

    if not cod_int or not tipo or cantidad == 0:
        return jsonify({"error": "cod_int, tipo y cantidad son requeridos"}), 400
    if tipo not in ("entrada", "salida", "ajuste"):
        return jsonify({"error": "tipo debe ser entrada, salida o ajuste"}), 400

    conn = pg()
    cur  = conn.cursor()

    # Verificar que el producto exista
    cur.execute("SELECT nombre, cantidad_total FROM maestra WHERE cod_int = %s", (cod_int,))
    prod = cur.fetchone()
    if not prod:
        conn.close()
        return jsonify({"error": f"Producto {cod_int} no encontrado"}), 404

    nombre_prod = nombre or prod[0]
    stock_antes = float(prod[1] or 0)

    # Registrar en historial
    cur.execute("""
        INSERT INTO historial (fecha_hora, usuario, tipo, cod_int, nombre, cantidad, ubicacion)
        VALUES (now(), %s, %s, %s, %s, %s, %s)
    """, (usuario, tipo, cod_int, nombre_prod, cantidad, ubicacion))

    # Actualizar stock (salida resta, entrada suma, ajuste fija)
    if tipo == "entrada":
        cur.execute("UPDATE maestra SET cantidad_total = cantidad_total + %s WHERE cod_int = %s",
                    (cantidad, cod_int))
    elif tipo == "salida":
        cur.execute("UPDATE maestra SET cantidad_total = cantidad_total - %s WHERE cod_int = %s",
                    (cantidad, cod_int))
    elif tipo == "ajuste":
        cur.execute("UPDATE maestra SET cantidad_total = %s WHERE cod_int = %s",
                    (cantidad, cod_int))

    conn.commit()

    cur.execute("SELECT cantidad_total FROM maestra WHERE cod_int = %s", (cod_int,))
    stock_nuevo = float(cur.fetchone()[0] or 0)
    conn.close()

    return jsonify({
        "ok": True,
        "cod_int": cod_int,
        "nombre": nombre_prod,
        "tipo": tipo,
        "cantidad": cantidad,
        "stock_antes": stock_antes,
        "stock_nuevo": stock_nuevo
    })

# ══════════════════════════════════════════════════════════════════════════════
# PEDIDOS — ver presupuestos, carros y reposiciones
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/pedidos")
@require_token
def get_pedidos():
    estado  = request.args.get("estado", "pendiente")
    prefijo = request.args.get("tipo", "")    # PRESUP, CARRO, REPOSICION, o vacío para todos
    page    = int(request.args.get("page", 1))
    per     = int(request.args.get("per", 30))
    offset  = (page - 1) * per

    conn = pg(); cur = conn.cursor()
    if prefijo:
        cur.execute("""
            SELECT id, nombre, fecha, items, estado, created_at
            FROM pedidos
            WHERE estado = %s AND nombre LIKE %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (estado, f"%[{prefijo}]%", per, offset))
    else:
        cur.execute("""
            SELECT id, nombre, fecha, items, estado, created_at
            FROM pedidos
            WHERE estado = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (estado, per, offset))
    rows = rows_to_dicts(cur)
    conn.close()

    # Parsear items JSON
    for r in rows:
        if isinstance(r.get("items"), str):
            try: r["items"] = json.loads(r["items"])
            except: r["items"] = []
        if r.get("created_at"):
            r["created_at"] = str(r["created_at"])

    return jsonify({"pedidos": rows, "page": page})

@app.route("/api/pedidos/<int:pedido_id>")
@require_token
def get_pedido(pedido_id):
    conn = pg(); cur = conn.cursor()
    cur.execute("SELECT id, nombre, fecha, items, estado, created_at FROM pedidos WHERE id = %s",
                (pedido_id,))
    row = rows_to_dicts(cur)
    conn.close()
    if not row:
        return jsonify({"error": "No encontrado"}), 404
    r = row[0]
    if isinstance(r.get("items"), str):
        try: r["items"] = json.loads(r["items"])
        except: r["items"] = []
    r["created_at"] = str(r.get("created_at", ""))
    return jsonify(r)

@app.route("/api/pedidos/<int:pedido_id>/estado", methods=["PATCH"])
@require_token
def actualizar_estado_pedido(pedido_id):
    data   = request.get_json()
    estado = data.get("estado", "").strip()
    if estado not in ("pendiente", "completado", "cancelado"):
        return jsonify({"error": "estado inválido"}), 400
    conn = pg(); cur = conn.cursor()
    cur.execute("UPDATE pedidos SET estado = %s WHERE id = %s", (estado, pedido_id))
    conn.commit(); conn.close()
    return jsonify({"ok": True, "id": pedido_id, "estado": estado})

# ══════════════════════════════════════════════════════════════════════════════
# HISTORIAL — últimos movimientos
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/historial")
@require_token
def get_historial():
    page   = int(request.args.get("page", 1))
    per    = int(request.args.get("per", 50))
    offset = (page - 1) * per
    conn = pg(); cur = conn.cursor()
    cur.execute("""
        SELECT id, fecha_hora, usuario, tipo, cod_int, nombre, cantidad, ubicacion
        FROM historial
        ORDER BY fecha_hora DESC
        LIMIT %s OFFSET %s
    """, (per, offset))
    rows = rows_to_dicts(cur)
    conn.close()
    for r in rows:
        r["fecha_hora"] = str(r.get("fecha_hora", ""))
    return jsonify({"movimientos": rows, "page": page})

if __name__ == "__main__":
    print("LOGIEZE Mobile API corriendo en http://0.0.0.0:5050")
    app.run(host="0.0.0.0", port=5050, debug=False)
