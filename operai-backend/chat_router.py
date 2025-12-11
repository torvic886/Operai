# AGENT/chat_router.py
import os
import json
import logging
import requests
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from typing import Tuple
import locale
import logging

# ---------------------------
# CONFIGURAR FORMATO COLOMBIANO
# ---------------------------
try:
    locale.setlocale(locale.LC_ALL, "es_CO.UTF-8")
except:
    locale.setlocale(locale.LC_ALL, "")

def money(value: float) -> str:
    try:
        return locale.format_string("%.2f", value, grouping=True)
    except:
        val = f"{value:,.2f}"
        partes = val.split(".")
        entero = partes[0].replace(",", ".")
        decimales = partes[1]
        return f"{entero},{decimales}"

# ---------------------------
# CARGA API KEY
# ---------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Falta la clave GEMINI_API_KEY en el entorno")

client = genai.Client(api_key=GEMINI_API_KEY)

API_BASE = "http://localhost:8000"

# ==================== IMPORTANTE: DEFINIR ROUTER ====================
router = APIRouter()
# ====================================================================

logger = logging.getLogger("uvicorn.error")

class ChatIn(BaseModel):
    message: str

# =====================================================================
# PALABRAS CLAVE DEL DOMINIO DE NEGOCIO
# =====================================================================
BUSINESS_KEYWORDS = {
    'campos': [
        'categoria', 'categoría', 'producto', 'valor', 'monto', 'precio', 
        'cantidad', 'fecha', 'gasto', 'compra', 'proveedor', 'presupuesto',
        'nomina', 'nómina', 'pago', 'bono', 'bonificacion', 'canon'
    ],
    
    'categorias': [
        'administrativos', 'aseo', 'bono cliente', 'cafeteria', 'cafetería',
        'coljuegos', 'gold club', 'inversiones', 'nomina', 'nómina',
        'papeleria', 'papelería', 'servicios publicos', 'públicos', 'transporte'
    ],
    
    'productos': [
        'varios', 'mantenimiento', 'maqui', 'datafono', 'parking', 'parqueo',
        'salud', 'leche', 'natilla', 'transp', 'cumpleaños', 'refrigerios',
        'energia', 'energía', 'pulpas', 'cerveza', 'supermercado', 'materiales',
        'caneca', 'azucar', 'azúcar', 'novomatic', 'efectivo', 'viaticos',
        'gas', 'envios', 'envíos', 'desechables', 'bretaña', 'agua', 
        'seguridad', 'atlas', 'internet', 'aires', 'repuestos', 'arrendamiento',
        'resma', 'examenes', 'exámenes', 'ruleta', 'dotacion', 'dotación',
        'café', 'fumigacion', 'fumigación', 'carne', 'limpido', 'decoracion',
        'decoración', 'termos', 'alfombra', 'rollos', 'boletas', 'retencion',
        'retención', 'arriendo', 'gaseosa', 'bill', 'prem', 'jack', 'telefonia',
        'telefonía', 'poliza', 'póliza', 'bonificaciones', 'ahorro', 'anchetas',
        'bingo', 'limpieza', 'equipos'
    ],
    
    'acciones': [
        'cuanto', 'cuánto', 'mostrar', 'muestra', 'dame', 'lista', 
        'buscar', 'encuentra', 'comparar', 'total', 'promedio', 
        'suma', 'estadisticas', 'estadísticas', 'caro', 'barato',
        'mayor', 'menor', 'top', 'ranking', 'distribucion', 
        'distribución', 'evolucion', 'evolución', 'tendencia',
        'analisis', 'análisis', 'compra', 'compras', 'gasto', 'gastos',
        'pago', 'pagos'
    ],
    
    'temporal': [
        'mes', 'dia', 'día', 'año', 'fecha', 'enero', 'febrero', 'marzo', 
        'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 
        'octubre', 'noviembre', 'diciembre', 'hoy', 'ayer', 'semana', 
        'trimestre', 'entre', 'desde', 'hasta', 'anterior'
    ]
}

# =====================================================================
# VALIDADOR DE RELEVANCIA
# =====================================================================
def es_consulta_relevante(mensaje: str) -> Tuple[bool, str]:
    """Valida si la consulta es relevante para el dominio de negocio"""
    mensaje_lower = mensaje.lower().strip()
    
    if len(mensaje_lower) < 3:
        return False, "La consulta es demasiado corta"
    
    # LISTA NEGRA
    patrones_invalidos = [
        (r'\b(quien|quién)\s+(es|fue|era|será)\b', 'historia/biografías'),
        (r'\b(cleopatra|cesar|julio|marco\s+antonio)\b', 'historia antigua'),
        (r'\bcapital\s+de\b', 'geografía'),
        (r'\b(pais|país|ciudad|continente)\b.*\b(donde|dónde|cual|cuál)\b', 'geografía'),
        (r'\b(receta|cocinar|preparar|ingredientes)\b', 'cocina'),
        (r'\b(cancion|canción|musica|música|banda|artista)\b', 'música'),
        (r'\b(pelicula|película|actor|actriz|director|serie|netflix)\b', 'cine/TV'),
        (r'\b(deporte|futbol|fútbol|basketball|tenis|olimpiadas)\b', 'deportes'),
    ]
    
    for patron, categoria in patrones_invalidos:
        if re.search(patron, mensaje_lower, re.IGNORECASE):
            return False, f"La consulta parece relacionada con {categoria}, no con gestión de gastos"
    
    # LISTA BLANCA
    palabras_mensaje = set(re.findall(r'\w+', mensaje_lower))
    
    coincidencias = 0
    for categoria, palabras in BUSINESS_KEYWORDS.items():
        if any(palabra in palabras_mensaje for palabra in palabras):
            coincidencias += 1
    
    if coincidencias >= 1:
        return True, "Consulta válida - contiene palabras del dominio de negocio"
    
    if re.search(r'\$|peso|cop|dinero|\d+[\.,]?\d*', mensaje_lower):
        return True, "Consulta válida - menciona valores monetarios"
    
    if re.search(r'\d{4}|\d{1,2}', mensaje_lower) and any(mes in mensaje_lower for mes in BUSINESS_KEYWORDS['temporal']):
        return True, "Consulta válida - menciona fechas/períodos"
    
    return False, "La consulta no parece relacionada con gastos, productos o análisis financiero del casino"

def generar_mensaje_rechazo(razon: str) -> dict:
    """Genera mensaje de rechazo con sugerencias"""
    return {
        "reply": (
            "🚫 **Lo siento, solo puedo ayudarte con consultas sobre gestión de gastos del casino.**\n\n"
            f"❌ {razon}\n\n"
            "**📊 Puedo responder preguntas como:**\n"
            "✅ ¿Cuánto gastamos en ASEO el mes pasado?\n"
            "✅ Muéstrame los productos más caros de CAFETERIA\n"
            "✅ Dame el total de NOMINA en octubre\n"
            "✅ Total gastado en COLJUEGOS\n\n"
            "💡 **Categorías disponibles:**\n"
            "• ADMINISTRATIVOS, ASEO, CAFETERIA, COLJUEGOS\n"
            "• GOLD CLUB, INVERSIONES, NOMINA, PAPELERIA\n"
            "• SERVICIOS PUBLICOS, TRANSPORTE"
        ),
        "data": None,
        "error": "consulta_fuera_de_contexto"
    }

# =====================================================================
# SYSTEM PROMPT
# =====================================================================
# Reemplaza SYSTEM_PROMPT en chat_router.py - VERSIÓN MEJORADA

SYSTEM_PROMPT = """Eres OperAI, asistente EXCLUSIVO de análisis de gastos del casino.

⚠️ CONTEXTO CRÍTICO:
- Tu ÚNICA función es analizar gastos, productos, categorías y presupuestos
- NUNCA respondas preguntas sobre temas generales

📅 INFORMACIÓN DE DATOS DISPONIBLES:
- HOY es 11 de diciembre de 2025
- La base de datos contiene registros desde 2025-01-05 hasta 2025-11-11
- Si el usuario menciona un mes SIN año, asume 2025
- SIEMPRE usa formato ISO: YYYY-MM-DD
- Ejemplos de inferencia correcta:
  * "enero" → 2025-01-01 a 2025-01-31
  * "gastos de marzo" → 2025-03-01 a 2025-03-31
  * "este mes" (diciembre 2025) → 2025-12-01 a 2025-12-11
  * "mes pasado" → 2025-11-01 a 2025-11-30

📋 CATEGORÍAS DISPONIBLES (SIEMPRE usar MAYÚSCULAS):
ADMINISTRATIVOS, ASEO, BONO CLIENTE, CAFETERIA, COLJUEGOS, 
GOLD CLUB, INVERSIONES, NOMINA, PAPELERIA, SERVICIOS PUBLICOS, TRANSPORTE

🔧 HERRAMIENTAS DISPONIBLES:

1️⃣ promedio_categoria(categoria, fecha_inicio, fecha_fin)
   Endpoint: /api/tools/promedio_categoria
   Uso: Calcula el promedio de gastos en un rango de fechas
   Retorna: { monto_promedio: float, cantidad_registros: int }
   Ejemplo: promedio_categoria("ASEO", "2025-01-01", "2025-01-31")

2️⃣ buscar_por_categoria(categoria, fecha_inicio, fecha_fin, proveedor?)
   Endpoint: /api/tools/buscar_por_categoria
   Uso: Lista detallada de gastos con productos
   Retorna: { lista_registros: [], monto_total: float, cantidad_registros: int }
   Ejemplo: buscar_por_categoria("CAFETERIA", "2025-03-01", "2025-03-31")

3️⃣ presupuesto_restante(categoria, periodo)
   Endpoint: /api/tools/presupuesto_restante
   Uso: Consulta presupuesto vs ejecutado (periodo formato YYYY-MM)
   Retorna: { presupuesto_asignado, monto_ejecutado, restante, porcentaje_usado }
   Ejemplo: presupuesto_restante("NOMINA", "2025-10")

4️⃣ total_categoria_valor(categoria, fecha_inicio?, fecha_fin?, min_valor?, max_valor?, limit?)
   Endpoint: /api/tools/total_categoria_valor
   Uso: Totales y estadísticas con filtros opcionales
   Retorna: { monto_total, cantidad_registros, promedio, minimo, maximo, lista_registros }
   Ejemplo: total_categoria_valor("ASEO", "2025-01-01", "2025-12-31", null, null, 50)

5️⃣ productos_caros(limit?)
   Endpoint: /api/tools/productos_caros
   Uso: Top productos más caros de todas las categorías
   Retorna: [ { NOMBRE_PRODUCTO, CATEGORIA, VALOR, FECHA } ]
   Ejemplo: productos_caros(10)

6️⃣ productos_caros_categoria(categoria, fecha_inicio, fecha_fin, limit?)
   Endpoint: /api/tools/productos_caros_categoria
   Uso: Top productos más caros de una categoría específica
   Retorna: [ { NOMBRE_PRODUCTO, CATEGORIA, VALOR, FECHA } ]
   Ejemplo: productos_caros_categoria("ASEO", "2025-01-01", "2025-12-31", 10)

⚙️ REGLAS DE RESPUESTA:
1. Responde SIEMPRE en JSON válido
2. Si requiere herramienta: { "tool": "nombre_herramienta", "params": { ... } }
3. Si NO requiere herramienta: { "tool": "none", "reply": "mensaje_directo" }
4. NORMALIZA la categoría a MAYÚSCULAS en los params
5. Para búsquedas, SIEMPRE incluye fecha_inicio y fecha_fin
6. Si el usuario no especifica límite, usa limit=50 para consultas de lista

📝 EJEMPLOS DE USO CORRECTO:

Pregunta: "Buscar productos de aseo en enero"
✅ Respuesta correcta:
{
  "tool": "buscar_por_categoria",
  "params": {
    "categoria": "ASEO",
    "fecha_inicio": "2025-01-01",
    "fecha_fin": "2025-01-31"
  }
}

Pregunta: "¿Cuánto gastamos en CAFETERIA en marzo?"
✅ Respuesta correcta:
{
  "tool": "total_categoria_valor",
  "params": {
    "categoria": "CAFETERIA",
    "fecha_inicio": "2025-03-01",
    "fecha_fin": "2025-03-31"
  }
}

Pregunta: "Productos más caros de NOMINA este año"
✅ Respuesta correcta:
{
  "tool": "productos_caros_categoria",
  "params": {
    "categoria": "NOMINA",
    "fecha_inicio": "2025-01-01",
    "fecha_fin": "2025-12-31",
    "limit": 10
  }
}

Pregunta: "¿Qué tal el clima?"
✅ Respuesta correcta:
{
  "tool": "none",
  "reply": "Lo siento, solo puedo ayudarte con consultas sobre gastos del casino."
}

🎯 IMPORTANTE:
- Siempre infiere las fechas correctamente usando el año 2025
- Si hay ambigüedad, pregunta al usuario antes de ejecutar
- Los nombres de categorías deben estar EXACTAMENTE como aparecen en la lista
- Para herramientas de búsqueda, siempre proporciona ambas fechas (inicio y fin)
"""

def call_api(path: str, params: dict):
    logger.debug(f"LLAMANDO API {path} con params: {params}")
    r = requests.get(f"{API_BASE}{path}", params=params, timeout=30)
    if r.status_code != 200:
        logger.error(f"Error API {path}: {r.status_code}")
        raise HTTPException(status_code=500, detail=f"Error API {path}")
    return r.json()

# =====================================================================
# ENDPOINT DE CHAT CON VALIDACIÓN
# =====================================================================
@router.post("/chat")
def chat_endpoint(payload: ChatIn):
    user_msg = payload.message.strip()
    logger.info(f"📨 Mensaje: {user_msg}")
    
    # VALIDAR RELEVANCIA
    es_valida, razon = es_consulta_relevante(user_msg)
    
    if not es_valida:
        logger.warning(f"❌ Rechazada: {razon}")
        return generar_mensaje_rechazo(razon)
    
    logger.info(f"✅ Válida: {razon}")
    
    # PROCESAR CON GEMINI
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{SYSTEM_PROMPT}\n\nUsuario: {user_msg}\n\nResponde en JSON:"
    )
    raw = response.text or "{}"
    
    # Limpiar Markdown
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.lstrip("```").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].lstrip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

    try:
        plan = json.loads(cleaned)
    except Exception as e:
        logger.error(f"❌ Error JSON: {e}")
        return {"reply": raw, "data": None}

    tool = plan.get("tool", "none")
    params = plan.get("params", {}) or {}

    logger.info(f"🔧 Tool: {tool}")

    try:
        if tool == "promedio_categoria":
            data = call_api("/api/tools/promedio_categoria", params)
            return {
                "reply": f"📊 Promedio: ${money(data['monto_promedio'])} en {data['cantidad_registros']} registros.",
                "data": {"stats": data, "lista_registros": []}
            }
        
# Reemplaza la sección elif tool == "buscar_por_categoria" en chat_router.py
# Aproximadamente línea 170-190

        elif tool == "buscar_por_categoria":
            data = call_api("/api/tools/buscar_por_categoria", params)
            registros = data.get("lista_registros", [])
            
            logger.info(f"✅ Recibidos {len(registros)} registros de la API")
            
            # ✅ Ya vienen con el formato correcto desde repositories.py
            # Solo necesitamos mapear a la estructura que necesita el frontend
            registros_graficables = []
            
            for r in registros:
                registro = {
                    "fecha": r.get("fecha"),
                    "monto": r.get("monto", 0),
                    "categoria": r.get("Categoria", params.get('categoria', 'N/A')),
                    "producto": r.get("nombre_producto", "Sin especificar"),  # ✅ AQUÍ ESTÁ
                    "cantidad": r.get("cantidad", 1.0)
                }
                registros_graficables.append(registro)
            
            # 🔍 DEBUG
            if registros_graficables:
                logger.info(f"📦 Ejemplo de registro procesado: {registros_graficables[0]}")
            
            return {
                "reply": f"📦 {data['cantidad_registros']} registros encontrados. Total: ${money(data['monto_total'])}",
                "data": registros_graficables[:50]
            }
        
        elif tool == "presupuesto_restante":
            data = call_api("/api/tools/presupuesto_restante", params)
            return {
                "reply": (
                    f"💼 Asignado: ${money(data['presupuesto_asignado'])}, "
                    f"Ejecutado: ${money(data['monto_ejecutado'])}, "
                    f"Restante: ${money(data['restante'])} ({round(data['porcentaje_usado'],2)}%)"
                ),
                "data": data
            }
        
        elif tool == "productos_caros":
            data = call_api("/api/tools/productos_caros", params)
            registros = data if isinstance(data, list) else data.get("registros", [])
            if not registros:
                return {"reply": "❌ No hay productos.", "data": []}
            mensaje = f"🏆 Top {len(registros)} productos más caros:\n\n"
            for i, reg in enumerate(registros[:5], 1):
                mensaje += f"{i}. {reg.get('NOMBRE_PRODUCTO', 'N/A')} - ${money(reg.get('VALOR', 0))}\n"
            return {"reply": mensaje.strip(), "data": registros}
        
        elif tool == "productos_caros_categoria":
            data = call_api("/api/tools/productos_caros_categoria", params)
            registros = data if isinstance(data, list) else data.get("registros", [])
            if not registros:
                return {"reply": f"❌ Sin productos en {params.get('categoria', '')}", "data": []}
            total = sum(reg.get('VALOR', 0) for reg in registros)
            mensaje = f"🏆 Top productos de {params.get('categoria', '')}:\n\n"
            for i, reg in enumerate(registros[:10], 1):
                mensaje += f"{i}. {reg.get('NOMBRE_PRODUCTO', 'N/A')} — ${money(reg.get('VALOR', 0))}\n"
            mensaje += f"\n💰 Total: ${money(total)}"
            return {"reply": mensaje.strip(), "data": registros}

        elif tool == "total_categoria_valor":
            data = call_api("/api/tools/total_categoria_valor", params)
            return {
                "reply": (
                    f"📊 Total: ${money(data['monto_total'])} "
                    f"en {data['cantidad_registros']} registros. "
                    f"Promedio: ${money(data['promedio'])}"
                ),
                "data": data.get("lista_registros", [])
            }

        else:
            return {
                "reply": plan.get("reply", "❓ No entendí tu consulta"),
                "data": None
            }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("❌ Error en herramienta")
        raise HTTPException(status_code=500, detail=f"Error: {e}")