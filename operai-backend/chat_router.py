# AGENT/chat_router.py
import os
import json
import logging
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
import locale

# ---------------------------
# CONFIGURAR FORMATO COLOMBIANO
# ---------------------------
try:
    locale.setlocale(locale.LC_ALL, "es_CO.UTF-8")
except:
    # Fallback si el servidor no tiene el locale
    locale.setlocale(locale.LC_ALL, "")

# def money(value: float) -> str:
#     """
#     Formatea números como dinero colombiano:
#     1234567.89 → 1.234.568
#     -6937500 → -6.937.500
#     """
#     try:
#         return locale.format_string("%d", value, grouping=True)
#     except:
#         # Fallback manual
#         return f"{int(value):,}".replace(",", ".")

def money(value: float) -> str:
    try:
        # Formato colombiano correcto: 26.706,48
        return locale.format_string("%.2f", value, grouping=True)
    except:
        # Fallback manual
        val = f"{value:,.2f}"
        partes = val.split(".")
        entero = partes[0].replace(",", ".")  # miles → punto
        decimales = partes[1]                # decimales → coma
        return f"{entero},{decimales}"

# ---------------------------
# CARGA API KEY
# ---------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Falta la clave GEMINI_API_KEY en el entorno")

client = genai.Client(api_key=GEMINI_API_KEY)

API_BASE = "http://localhost:8000"  # ajusta si cambia

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

class ChatIn(BaseModel):
    message: str

SYSTEM_PROMPT = """Eres OperAI, asistente de gastos del casino.

Tienes acceso a las siguientes herramientas REST (JSON):

- promedio_categoria(categoria, fecha_inicio, fecha_fin)
    -> /api/tools/promedio_categoria

- buscar_por_categoria(categoria, fecha_inicio, fecha_fin, proveedor?)
    -> /api/tools/buscar_por_categoria

- presupuesto_restante(categoria, periodo)
    -> /api/tools/presupuesto_restante

- total_categoria_valor(categoria, fecha_inicio?, fecha_fin?, min_valor?, max_valor?, limit?)
    -> /api/tools/total_categoria_valor

- productos_caros(limit?)
    -> /api/tools/productos_caros
    Devuelve los registros más costosos (mayor VALOR) en TODA la base.

- productos_caros_categoria(categoria, fecha_inicio, fecha_fin, limit?)
    -> /api/tools/productos_caros_categoria
    Devuelve los registros más caros de UNA categoría dentro de un rango de fechas.
    Esta herramienta DEBE usarse siempre que el usuario pida:
        - "más caros"
        - + una categoría
        - + un rango de fechas
        Ejemplo: “más caros de ASEO entre fecha X y fecha Y”.

REGLAS OBLIGATORIAS:
1. Debes responder SIEMPRE en JSON válido. Prohibido responder texto libre.
2. Si el usuario nombra fechas como:
        “entre X e Y”
        “desde X hasta Y”
   entonces usa X como fecha_inicio y Y como fecha_fin (ISO YYYY-MM-DD).
3. Si el usuario pide “los más caros” + categoría + fechas:
        ⇒ Usa productos_caros_categoria.
4. Si el usuario pide "más caros" sin rango:
        ⇒ Usa productos_caros.
5. Si la pregunta requiere herramienta, responde SOLO:
        { "tool": "nombre", "params": { ... } }
6. Si NO requiere herramienta, responde:
        { "tool": "none", "reply": "mensaje" }
7. NO escribas explicaciones fuera del JSON.
"""

logger.error("*********** PROMPT QUE SE ESTÁ USANDO ***********")
logger.error(SYSTEM_PROMPT)
logger.error("***************************************************")


def call_api(path: str, params: dict):
    logger.debug(f"LLAMANDO API {path} con params: {params}")
    r = requests.get(f"{API_BASE}{path}", params=params, timeout=30)
    if r.status_code != 200:
        logger.error(f"Error API {path}: {r.status_code} / {r.text}")
        raise HTTPException(status_code=500, detail=f"Error API {path}: {r.text}")
    return r.json()

@router.post("/chat")
def chat_endpoint(payload: ChatIn):
    user_msg = payload.message.strip()
    logger.debug(f"Mensaje de usuario: {user_msg}")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{SYSTEM_PROMPT}\n\nUsuario: {user_msg}\n\nResponde en JSON:"
    )
    raw = response.text or "{}"
    logger.debug(f"Respuesta del modelo (cruda): {raw}")

    # Limpiar posibles bloques Markdown ```json ... ```
    cleaned = raw
    if cleaned.startswith("```"):
        # Remueve las tres backticks al inicio
        cleaned = cleaned.lstrip("```").strip()
        # Si empieza con "json", remuévelo
        if cleaned.lower().startswith("json"):
            # Elimina "json" al inicio
            cleaned = cleaned[4:].lstrip()
        # Remueve las backticks al final
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

    logger.debug(f"Texto limpiado para JSON: {cleaned}")

    try:
        plan = json.loads(cleaned)
        logger.debug(f"Plan parseado: {plan}")
    except Exception as e:
        logger.error(f"No JSON en plan después de limpieza: {e}")
        return {"reply": raw}

    tool = plan.get("tool", "none")
    params = plan.get("params", {}) or {}


    logger.debug(f"Plan recibido: tool={tool}, params={params}")

    try:
        # -----------------------------------------
        # PROMEDIO CATEGORÍA
        # -----------------------------------------
        if tool == "promedio_categoria":
            data = call_api("/api/tools/promedio_categoria", params)
            return {
                "reply": (
                    f"Promedio: ${money(data['monto_promedio'])} "
                    f"en {data['cantidad_registros']} registros."
                ),
                "data": data
            }
        # -----------------------------------------
        # BUSCAR POR CATEGORÍA
        # -----------------------------------------
        elif tool == "buscar_por_categoria":
            data = call_api("/api/tools/buscar_por_categoria", params)
            return {
                "reply": (
                    f"{data['cantidad_registros']} registros. "
                    f"Total: ${money(data['monto_total'])}. Muestro una muestra."
                ),
                "data": {
                    "lista_registros": data["lista_registros"][:5],
                    "monto_total": data["monto_total"]
                }
            }
        # -----------------------------------------
        # PRESUPUESTO RESTANTE
        # -----------------------------------------
        elif tool == "presupuesto_restante":
            data = call_api("/api/tools/presupuesto_restante", params)
            return {
                "reply": (
                    f"Asignado: ${money(data['presupuesto_asignado'])}; "
                    f"Ejecutado: ${money(data['monto_ejecutado'])}; "
                    f"Restante: ${money(data['restante'])}; "
                    f"Uso: {round(data['porcentaje_usado'],2)}%."
                ),
                "data": data
            }
        
        # -----------------------------------------
        # PRODUCTOS CAROS (GENERAL)
        # -----------------------------------------
        elif tool == "productos_caros":
            data = call_api("/api/tools/productos_caros", params)
            
            # El endpoint devuelve una lista directamente
            registros = data if isinstance(data, list) else data.get("registros", [])
            
            if not registros:
                return {"reply": "No se encontraron productos caros.", "data": []}
            
            # Construir mensaje con los top productos
            mensaje = f"Los {len(registros)} productos más caros son:\n\n"
            for i, reg in enumerate(registros[:5], 1):  # Mostrar top 5 en el mensaje
                mensaje += (
                    f"{i}. {reg.get('NOMBRE_PRODUCTO', 'N/A')} - "
                    f"${money(reg.get('VALOR', 0))} "
                    f"({reg.get('CATEGORIA', 'N/A')} - {reg.get('FECHA', 'N/A')})\n"
                )
            
            return {
                "reply": mensaje.strip(),
                "data": registros
            }
        
        # -----------------------------------------
        # PRODUCTOS CAROS POR CATEGORÍA
        # -----------------------------------------
        elif tool == "productos_caros_categoria":
            data = call_api("/api/tools/productos_caros_categoria", params)
            registros = data if isinstance(data, list) else data.get("registros", [])
            categoria = params.get("categoria", "")
            
            if not registros:
                return {"reply": f"No se encontraron productos en {categoria}.", "data": []}
            
            total = sum(reg.get('VALOR', 0) for reg in registros)
            
            mensaje = f"Los {len(registros)} más caros de {categoria}\n\n"
            
            for i, reg in enumerate(registros[:10], 1):
                nombre = reg.get('NOMBRE_PRODUCTO', 'N/A')
                valor = money(reg.get('VALOR', 0))
                fecha = reg.get('FECHA', 'N/A')
                
                mensaje += f"{i}. {nombre} — ${valor} ({fecha})\n"
            
            mensaje += f"\n Total: ${money(total)}"
            
            return {
                "reply": mensaje.strip(),
                "data": registros
            }

        # -----------------------------------------
        # TOTAL CATEGORÍA VALOR
        # -----------------------------------------
        elif tool == "total_categoria_valor":
            data = call_api("/api/tools/total_categoria_valor", params)
            return {
                "reply": (
                    f"Total: ${money(data['monto_total'])} "
                    f"en {data['cantidad_registros']} registros. "
                    f"Promedio: ${money(data['promedio'])}."
                ),
                "data": {
                    "stats": {
                        "monto_total": data["monto_total"],
                        "cantidad_registros": data["cantidad_registros"],
                        "promedio": data["promedio"],
                        "minimo": data["minimo"],
                        "maximo": data["maximo"]
                    },
                    "muestra": data.get("lista_registros", [])[:5]
                }
            }

        else:
            return {"reply": plan.get("reply", "No entendí, ¿puedes reformular?")}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error en ejecución de herramienta")
        raise HTTPException(status_code=500, detail=f"Error interno al ejecutar herramienta: {e}")
