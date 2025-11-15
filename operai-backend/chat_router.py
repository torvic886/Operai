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
Dispones de estas herramientas REST (JSON):
- promedio_categoria(categoria, fecha_inicio, fecha_fin) -> /api/tools/promedio_categoria
- buscar_por_categoria(categoria, fecha_inicio, fecha_fin, proveedor?) -> /api/tools/buscar_por_categoria
- presupuesto_restante(categoria, periodo) -> /api/tools/presupuesto_restante
- total_categoria_valor(categoria, fecha_inicio?, fecha_fin?, min_valor?, max_valor?, limit?) -> /api/tools/total_categoria_valor

Instrucciones:
1) Decide si la pregunta del usuario requiere usar alguna herramienta.
2) Si sí, responde en JSON con: { "tool": nombre, "params": {...} }
3) Si no, responde en JSON con: { "tool": "none", "reply": "texto al usuario" }
4) Cuando uses herramienta, llama la API, obtén resultado, y devuelve una respuesta clara y breve al usuario.
"""

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
        if tool == "promedio_categoria":
            data = call_api("/api/tools/promedio_categoria", params)
            return {
                "reply": f"Promedio: {round(data['monto_promedio'], 2)} sobre {data['cantidad_registros']} registros.",
                "data": data
            }
        elif tool == "buscar_por_categoria":
            data = call_api("/api/tools/buscar_por_categoria", params)
            return {
                "reply": f"{data['cantidad_registros']} registros. Total: {round(data['monto_total'],2)}. Muestro una muestra.",
                "data": {"lista_registros": data["lista_registros"][:5], "monto_total": data["monto_total"]}
            }
        elif tool == "presupuesto_restante":
            data = call_api("/api/tools/presupuesto_restante", params)
            return {
                "reply": f"Asignado: {round(data['presupuesto_asignado'],2)}; Ejecutado: {round(data['monto_ejecutado'],2)}; Restante: {round(data['restante'],2)}; Uso: {round(data['porcentaje_usado'],2)}%.",
                "data": data
            }
        elif tool == "total_categoria_valor":
            logger.debug(f"Llamando herramienta total_categoria_valor con params: {params}")
            data = call_api("/api/tools/total_categoria_valor", params)
            return {
                "reply": f"Total: {round(data['monto_total'],2)} en {data['cantidad_registros']} registros. Promedio: {round(data['promedio'],2)}.",
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
