# AGENT/server_mcp.py
"""
Registro y dispatch de herramientas MCP.
"""
from typing import Any, Callable, Dict
from db import repositories

class MCPError(Exception):
    pass

# Registro en memoria
TOOLS: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

def tool(name: str):
    def deco(fn: Callable[[Dict[str, Any]], Any]):
        TOOLS[name] = fn
        return fn
    return deco

@tool("promedio_categoria")
def _promedio_categoria(params: Dict[str, Any]) -> Dict[str, Any]:
    return repositories.get_promedio_categoria(
        params["categoria"],
        params["fecha_inicio"],
        params["fecha_fin"]
    )

@tool("buscar_por_categoria")
def _buscar_por_categoria(params: Dict[str, Any]) -> Dict[str, Any]:
    return repositories.buscar_por_categoria(
        params["categoria"],
        params["fecha_inicio"],
        params["fecha_fin"],
        params.get("proveedor")
    )

@tool("presupuesto_restante")
def _presupuesto_restante(params: Dict[str, Any]) -> Dict[str, Any]:
    return repositories.get_presupuesto_restante(
        params["categoria"],
        params["periodo"]
    )

@tool("productos_caros")
def _productos_caros(params: Dict[str, Any]) -> list[Dict[str, Any]]:
    limit = params.get("limit", 10)
    return repositories.get_productos_caros(limit)

# -------------------------
# NUEVA HERRAMIENTA: total_categoria_valor
# -------------------------
@tool("total_categoria_valor")
def _total_categoria_valor(params: Dict[str, Any]) -> Dict[str, Any]:
    return repositories.get_total_categoria_valor(
        categoria=params["categoria"],
        fecha_inicio=params.get("fecha_inicio"),
        fecha_fin=params.get("fecha_fin"),
        min_valor=params.get("min_valor"),
        max_valor=params.get("max_valor"),
        limit=params.get("limit")
    )

def call_tool(name: str, params: Dict[str, Any]) -> Any:
    if name not in TOOLS:
        raise MCPError(f"Herramienta no registrada: {name}")
    return TOOLS[name](params)
