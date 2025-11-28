# AGENT/db/repositories.py
from typing import Dict, Any
from datetime import date
from calendar import monthrange
from sqlalchemy import text
from .connection import get_engine

def get_promedio_categoria(categoria: str, fecha_inicio: str, fecha_fin: str) -> Dict[str, Any]:
    """
    Devuelve { monto_promedio: float, cantidad_registros: int } para la categoría y rango.
    """
    sql = text("""
        SELECT AVG(VALOR) AS monto_promedio, COUNT(*) AS cantidad_registros
        FROM gastos
        WHERE CATEGORIA = :categoria
          AND FECHA BETWEEN :fecha_inicio AND :fecha_fin
    """)

    eng = get_engine()
    with eng.connect() as conn:
        row = conn.execute(
            sql, {"categoria": categoria, "fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}
        ).mappings().one()

    avg_val = float(row["monto_promedio"]) if row["monto_promedio"] is not None else 0.0
    count = int(row["cantidad_registros"] or 0)
    return {"monto_promedio": avg_val, "cantidad_registros": count}


def buscar_por_categoria(categoria: str, fecha_inicio: str, fecha_fin: str, proveedor: str | None) -> Dict[str, Any]:
    """
    Retorna listado de registros y totales para la categoría y rango de fechas.
    NOTA: Tu tabla 'gastos' NO tiene proveedor ni nro_factura. Devolvemos None en esos campos.
    Convierte FECHA (date) a string ISO 'YYYY-MM-DD' para evitar errores de serialización/validación.
    """
    base_sql = text("""
        SELECT FECHA AS fecha,
               VALOR AS monto
        FROM gastos
        WHERE CATEGORIA = :categoria
          AND FECHA BETWEEN :fecha_inicio AND :fecha_fin
        ORDER BY FECHA ASC, id ASC
    """)

    total_sql = text("""
        SELECT SUM(VALOR) AS monto_total, COUNT(*) AS cantidad
        FROM gastos
        WHERE CATEGORIA = :categoria
          AND FECHA BETWEEN :fecha_inicio AND :fecha_fin
    """)

    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(
            base_sql, {"categoria": categoria, "fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}
        ).mappings().all()
        total = conn.execute(
            total_sql, {"categoria": categoria, "fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}
        ).mappings().one()

    lista = []
    for r in rows:
        f = r["fecha"]
        # date -> "YYYY-MM-DD"
        f_iso = f.isoformat() if hasattr(f, "isoformat") else (str(f) if f is not None else None)
        lista.append({
            "fecha": f_iso,
            "monto": float(r["monto"]) if r["monto"] is not None else 0.0,
            "proveedor": None,
            "nro_factura": None
        })

    monto_total = float(total["monto_total"]) if total["monto_total"] is not None else 0.0
    cantidad = int(total["cantidad"] or 0)
    return {"lista_registros": lista, "monto_total": monto_total, "cantidad_registros": cantidad}


def get_presupuesto_restante(categoria: str, periodo: str) -> Dict[str, Any]:
    """
    Calcula presupuesto anual para la categoría y ejecutado acumulado del año.
    Si NO existe fila en 'presupuestos', usa presupuesto_asignado=0.0.
    """
    # 1) Rango de fechas del mes
    y, m = map(int, periodo.split("-"))
    anio = y  # aquí nace el valor que se usa en :anio

    ini = date(anio, m, 1)
    fin = date(anio, m, monthrange(anio, m)[1])
    periodo_real = fin.isoformat()   # 2025-10 → 2025-10-31

    # 2) Presupuesto (último día del mes)
    q_ppto = text(""" 
        SELECT MONTO_ASIGNADO AS presupuesto_asignado
        FROM presupuestos
        WHERE UPPER(CATEGORIA) = UPPER(:categoria)
          AND PERIODO = :periodo_real
        LIMIT 1
    """)

    # 3) Ejecutado del AÑO
    q_exec = text("""
        SELECT COALESCE(SUM(VALOR), 0) AS ejecutado
        FROM gastos
        WHERE CATEGORIA = :categoria
          AND YEAR(FECHA) = :anio
    """)

    eng = get_engine()
    with eng.connect() as conn:
        p = conn.execute(
            q_ppto,
            {"categoria": categoria, "periodo_real": periodo_real}
        ).mappings().first()
        presupuesto_asignado = float(p["presupuesto_asignado"]) if p and p["presupuesto_asignado"] is not None else 0.0

        e = conn.execute(
            q_exec,
            {"categoria": categoria, "anio": anio}  # 👈 aquí se usa anio
        ).mappings().one()
        ejecutado = float(e["ejecutado"]) if e["ejecutado"] is not None else 0.0

    restante = presupuesto_asignado - ejecutado
    porcentaje = (ejecutado / presupuesto_asignado * 100) if presupuesto_asignado > 0 else 0.0

    return {
        "presupuesto_asignado": presupuesto_asignado,
        "monto_ejecutado": ejecutado,
        "restante": restante,
        "porcentaje_usado": porcentaje,
    }


def get_productos_caros(limit: int = 10) -> list[dict]:
    """
    Devuelve los productos más caros registrados en gastos.
    """
    from sqlalchemy import text
    sql = text("""
        SELECT NOMBRE_PRODUCTO, CATEGORIA, VALOR, FECHA
        FROM gastos
        ORDER BY VALOR DESC
        LIMIT :limit
    """)
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(sql, {"limit": limit}).mappings().all()
    return [dict(row) for row in rows]

def get_total_categoria_valor(
    categoria: str,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    min_valor: float | None = None,
    max_valor: float | None = None,
    limit: int | None = None,
) -> dict:
    engine = get_engine()
    # construye la consulta básica
    sql = """
    SELECT FECHA, VALOR, CANTIDAD, (VALOR * CANTIDAD) AS monto
    FROM gastos
    WHERE CATEGORIA = :categoria
    """
    params = {"categoria": categoria.upper()}
    if fecha_inicio:
        sql += " AND FECHA >= :fecha_inicio"
        params["fecha_inicio"] = fecha_inicio
    if fecha_fin:
        sql += " AND FECHA <= :fecha_fin"
        params["fecha_fin"] = fecha_fin
    if min_valor is not None:
        sql += " AND VALOR >= :min_valor"
        params["min_valor"] = min_valor
    if max_valor is not None:
        sql += " AND VALOR <= :max_valor"
        params["max_valor"] = max_valor

    # agregados
    agg_sql = f"""
    SELECT
      SUM(VALOR * CANTIDAD) AS monto_total,
      COUNT(*) AS cantidad_registros,
      AVG(VALOR * CANTIDAD) AS promedio,
      MIN(VALOR * CANTIDAD) AS minimo,
      MAX(VALOR * CANTIDAD) AS maximo
    FROM ({sql}) AS sub
    """

    with engine.connect() as conn:
        agg = conn.execute(text(agg_sql), params).mappings().one()
        monto_total = agg["monto_total"] or 0.0
        cantidad_registros = agg["cantidad_registros"] or 0
        promedio = agg["promedio"] or 0.0
        minimo = agg["minimo"] or 0.0
        maximo = agg["maximo"] or 0.0

        lista = []
        if limit:
            list_sql = sql + " ORDER BY FECHA DESC LIMIT :limit"
            params["limit"] = limit
            result = conn.execute(text(list_sql), params).mappings().all()
            for r in result:
                # Asegúrate de que FECHA exista
                lista.append({
                  "fecha": r["FECHA"].isoformat(),
                  "valor": float(r["VALOR"]),
                  "cantidad": float(r["CANTIDAD"]),
                  "monto": float(r["monto"])
                })

    return {
    "monto_total": float(monto_total),
    "cantidad_registros": int(cantidad_registros),
    "promedio": float(promedio),
    "minimo": float(minimo),
    "maximo": float(maximo),
    "lista_registros": lista
    }

def get_productos_caros_categoria(categoria: str, fecha_inicio: str, fecha_fin: str, limit: int = 10) -> list[dict]:
    sql = text("""
        SELECT NOMBRE_PRODUCTO, CATEGORIA, VALOR, FECHA
        FROM gastos
        WHERE UPPER(CATEGORIA) = UPPER(:categoria)
          AND FECHA BETWEEN :fecha_inicio AND :fecha_fin
        ORDER BY VALOR DESC
        LIMIT :limit
    """)
    
    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(sql, {
            "categoria": categoria,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "limit": limit
        }).mappings().all()

    return [dict(r) for r in rows]




