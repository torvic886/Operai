# AGENT/core/services.py
from dataclasses import dataclass
from datetime import date
from typing import Dict, Optional, List
from sqlalchemy import text
from db.connection import get_engine
from .models import (
    PromedioCategoriaRequest,
    PromedioCategoriaResponse,
    BuscarPorCategoriaRequest,
    BuscarPorCategoriaResponse,
    PresupuestoRestanteRequest,
    PresupuestoRestanteResponse,
    # nuevos modelos:
    TotalCategoriaValorRequest,
    TotalCategoriaValorResponse,
)
from server_mcp import call_tool

# ===============================================================
# EXCEPCIONES Y VALIDACIONES
# ===============================================================

class DomainError(Exception):
    pass

def _validar_categoria(cat: str) -> None:
    """
    Verifica que la categoría exista realmente en la base de datos.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM gastos WHERE CATEGORIA = :cat LIMIT 1"),
                {"cat": cat.upper()},
            ).fetchone()
        if not result:
            raise DomainError(f"La categoría '{cat}' no existe en la base de datos.")
    except Exception as e:
        raise DomainError(f"Error al validar categoría en la base de datos: {e}")

def _validar_rango_fechas(ini: str, fin: str) -> None:
    try:
        d1 = date.fromisoformat(ini)
        d2 = date.fromisoformat(fin)
    except ValueError:
        raise DomainError("Formato de fecha inválido. Use 'YYYY-MM-DD'.")
    if d1 > d2:
        raise DomainError("'fecha_inicio' no puede ser mayor que 'fecha_fin'.")

# ===============================================================
# FUNCIONES DE SERVICIO
# ===============================================================

def promedio_categoria(req: PromedioCategoriaRequest) -> PromedioCategoriaResponse:
    _validar_categoria(req.categoria)
    _validar_rango_fechas(req.fecha_inicio, req.fecha_fin)
    payload = {
        "categoria": req.categoria.upper(),
        "fecha_inicio": req.fecha_inicio,
        "fecha_fin": req.fecha_fin,
    }
    result = call_tool("promedio_categoria", payload)
    return PromedioCategoriaResponse(**result)

def buscar_por_categoria(req: BuscarPorCategoriaRequest) -> BuscarPorCategoriaResponse:
    _validar_categoria(req.categoria)
    _validar_rango_fechas(req.fecha_inicio, req.fecha_fin)
    payload = {
        "categoria": req.categoria.upper(),
        "fecha_inicio": req.fecha_inicio,
        "fecha_fin": req.fecha_fin,
    }
    if req.proveedor:
        payload["proveedor"] = req.proveedor

    result = call_tool("buscar_por_categoria", payload)
    return BuscarPorCategoriaResponse(**result)

def presupuesto_restante(req: PresupuestoRestanteRequest) -> PresupuestoRestanteResponse:
    _validar_categoria(req.categoria)
    try:
        # valida formato periodo YYYY-MM
        _ = date.fromisoformat(req.periodo + "-01")
    except ValueError:
        raise DomainError("Formato de periodo inválido. Use 'YYYY-MM'.")
    payload = {
        "categoria": req.categoria.upper(),
        "periodo": req.periodo,
    }
    result = call_tool("presupuesto_restante", payload)
    return PresupuestoRestanteResponse(**result)

def productos_caros(limit: int = 10):
    payload = {"limit": limit}
    result = call_tool("productos_caros", payload)
    return result

def productos_caros_categoria(categoria: str, fecha_inicio: str, fecha_fin: str, limit: int = 10):
    _validar_categoria(categoria)
    _validar_rango_fechas(fecha_inicio, fecha_fin)

    payload = {
        "categoria": categoria.upper(),
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "limit": limit
    }

    result = call_tool("productos_caros_categoria", payload)
    return result


# ===============================================================
# NUEVA HERRAMIENTA: total_categoria_valor
# ===============================================================

def total_categoria_valor(req: TotalCategoriaValorRequest) -> TotalCategoriaValorResponse:
    _validar_categoria(req.categoria)
    if req.fecha_inicio and req.fecha_fin:
        _validar_rango_fechas(req.fecha_inicio, req.fecha_fin)
    payload = {
        "categoria": req.categoria.upper(),
        # sólo agregar si no es None
    }
    if req.fecha_inicio:
        payload["fecha_inicio"] = req.fecha_inicio
    if req.fecha_fin:
        payload["fecha_fin"] = req.fecha_fin
    if req.min_valor is not None:
        payload["min_valor"] = req.min_valor
    if req.max_valor is not None:
        payload["max_valor"] = req.max_valor
    if req.limit is not None:
        payload["limit"] = req.limit

    result = call_tool("total_categoria_valor", payload)
    return TotalCategoriaValorResponse(**result)

