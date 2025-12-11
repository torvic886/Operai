# app.py
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import json

# -----------------------------------------------------
# 1. Configurar la página
# -----------------------------------------------------
st.set_page_config(
    page_title="OperAI Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard dinámico impulsado por IA (Streamlit + FastAPI)")

# -----------------------------------------------------
# 2. URL del backend
# -----------------------------------------------------
API_BASE = "http://127.0.0.1:8000/api/tools"
IA_ENDPOINT = "http://127.0.0.1:8000/api/ia/instruccion"

# -----------------------------------------------------
# 3. Obtener rango de fechas válido desde FastAPI
# -----------------------------------------------------
def get_rango_fechas():
    try:
        r = requests.get("http://127.0.0.1:8000/api/tools/fechas")
        r.raise_for_status()
        return r.json()
    except:
        return {"fecha_minima": None, "fecha_maxima": None}

rango = get_rango_fechas()
fecha_minima = pd.to_datetime(rango["fecha_minima"]) if rango["fecha_minima"] else pd.to_datetime("2025-01-01")
fecha_maxima = pd.to_datetime(rango["fecha_maxima"]) if rango["fecha_maxima"] else pd.to_datetime("2025-12-31")

# -----------------------------------------------------
# 4. Sidebar dinámico de fechas
# -----------------------------------------------------
st.sidebar.subheader("Rango de fechas disponible en BD")

fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Selecciona el rango de fechas:",
    value=[fecha_minima, fecha_maxima],
    min_value=fecha_minima,
    max_value=fecha_maxima
)

# ======================================================
# 5. CONSULTA IA - PANEL INTELIGENTE
# ======================================================
st.sidebar.subheader("💬 Consulta a la IA")

mensaje_ia = st.sidebar.text_area("Escribe tu consulta para la IA:", "")

if st.sidebar.button("Enviar a IA"):
    r = requests.post(IA_ENDPOINT, json={"mensaje": mensaje_ia})
    respuesta_ia = r.json()

    if respuesta_ia.get("ok"):
        st.session_state["instruccion_ia"] = respuesta_ia["instruccion"]
    else:
        st.error(f"Error IA: {respuesta_ia.get('error')}")

# ======================================================
# 6. Procesar instrucción IA
# ======================================================
tool = None
params = {}
chart_cfg = None

if "instruccion_ia" in st.session_state:
    st.write("### Instrucción generada por la IA:")
    st.code(st.session_state["instruccion_ia"], language="json")

    try:
        instr = json.loads(st.session_state["instruccion_ia"])
        tool = instr.get("tool")
        params = instr.get("params", {})
        chart_cfg = instr.get("chart")
    except:
        st.error("JSON inválido recibido de la IA.")
        tool = None

# ======================================================
# 7. Llamada API
# ======================================================
def call_api(endpoint, params):
    try:
        r = requests.get(f"{API_BASE}/{endpoint}", params=params)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error API: {e}")
        return None

# ======================================================
# 8. EJECUCIÓN AUTOMÁTICA DE LA IA
# ======================================================
if tool and tool != "none":
    st.write(f"### Ejecutando herramienta: `{tool}`")

    datos = call_api(tool, params)

    if datos:
        st.write("### 📊 Datos devueltos por la API (IA):")

        df = None
        if isinstance(datos, dict) and "lista_registros" in datos:
            df = pd.DataFrame(datos["lista_registros"])
        elif isinstance(datos, dict) and "resultados" in datos:
            df = pd.DataFrame(datos["resultados"])
        elif isinstance(datos, dict) and "muestra" in datos:
            df = pd.DataFrame(datos["muestra"])
        elif isinstance(datos, list):
            df = pd.DataFrame(datos)

        if df is not None:
            st.dataframe(df)

        # ======================================================
        # 8.1 Soporte especial — gasto_por_categoria
        # ======================================================
        if tool == "gasto_por_categoria" and df is not None:

            df_sorted = df.sort_values(by="total", ascending=False)

            st.write("### Resumen de gasto por categoría")
            st.write(f"Categorías: {df.shape[0]}")
            st.write(f"Gasto total: ${df['total'].sum():,.0f} COP")

            fig, ax = plt.subplots(figsize=(9, 6))
            bars = ax.bar(df_sorted["categoria"], df_sorted["total"], color="#1f77b4")

            for bar in bars:
                h = bar.get_height()
                ax.text(
                    bar.get_x()+bar.get_width()/2,
                    h,
                    f"${h:,.0f}",
                    ha="center", va="bottom", fontsize=9, rotation=45
                )

            ax.set_title("Gasto Total por Categoría", fontsize=14, fontweight="bold")
            ax.tick_params(axis="x", rotation=45)
            plt.tight_layout()
            st.pyplot(fig)

        # ======================================================
        # 8.2 RENDERIZAR GRÁFICO SOLICITADO POR LA IA
        # ======================================================
        if chart_cfg and df is not None:

            tipo = chart_cfg.get("type")
            eje_x = chart_cfg.get("x")
            eje_y = chart_cfg.get("y")
            titulo = chart_cfg.get("title", "")

            # Validación de columnas
            if eje_x not in df.columns or eje_y not in df.columns:
                st.warning("⚠ Columnas inválidas para graficar.")
            else:

                # -----------------------------
                #  PIE / DONUT — moderno
                # -----------------------------
                if tipo == "pie":

                    df_sorted = df.sort_values(by=eje_y, ascending=False)
                    labels = df_sorted[eje_x].values
                    values = df_sorted[eje_y].values

                    fig, ax = plt.subplots(figsize=(10, 6))
                    colors = plt.cm.tab20.colors[:len(values)]

                    wedges, _ = ax.pie(
                        values,
                        labels=None,
                        colors=colors,
                        startangle=90,
                        wedgeprops={"width": 0.45}
                    )

                    # Centro blanco
                    centre = plt.Circle((0, 0), 0.30, fc="white")
                    ax.add_artist(centre)

                    legend_labels = [
                        f"{labels[i]} — ${values[i]:,.0f} COP ({values[i]/values.sum()*100:.1f}%)"
                        for i in range(len(values))
                    ]

                    ax.legend(
                        wedges,
                        legend_labels,
                        title="Categorías",
                        loc="center left",
                        bbox_to_anchor=(1, 0.5),
                        fontsize=10,
                        title_fontsize=12,
                        frameon=False
                    )

                    ax.set_title(titulo, fontsize=16, fontweight="bold")
                    plt.tight_layout()
                    st.pyplot(fig)

                # -----------------------------
                #  OTROS TIPOS DE GRÁFICO
                # -----------------------------
                else:
                    fig, ax = plt.subplots(figsize=(10, 5))

                    if tipo == "bar":
                        bars = ax.bar(df[eje_x], df[eje_y], color="#4A90E2")
                        for bar in bars:
                            h = bar.get_height()
                            ax.text(bar.get_x()+bar.get_width()/2, h, f"{h:,.0f}", ha="center", fontsize=9)

                    elif tipo == "line":
                        ax.plot(df[eje_x], df[eje_y], marker="o")

                    elif tipo == "hist":
                        ax.hist(df[eje_y], bins=10)

                    elif tipo == "area":
                        ax.fill_between(df[eje_x], df[eje_y], alpha=0.3)

                    elif tipo == "scatter":
                        ax.scatter(df[eje_x], df[eje_y], s=60)

                    ax.set_title(titulo, fontsize=14)
                    ax.tick_params(axis="x", rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig)

# ======================================================
# 9. Opciones manuales
# ======================================================
st.sidebar.subheader("Opciones manuales")

opcion = st.sidebar.selectbox(
    "Selecciona el análisis",
    ["Promedio por categoría", "Buscar por categoría", "Productos más caros", "Total por categoría"]
)

categoria = st.sidebar.text_input("Categoría:", "ASEO")

# ======================================================
# 10. Render manual
# ======================================================
if opcion == "Promedio por categoría":
    data = call_api("promedio_categoria",
                    {"categoria": categoria, "fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin})
    if data:
        st.write(f"Promedio: **{data['monto_promedio']}** COP")
        st.write(f"Registros analizados: **{data['cantidad_registros']}**")

elif opcion == "Buscar por categoría":
    data = call_api("buscar_por_categoria",
                    {"categoria": categoria, "fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin})
    if data:
        df = pd.DataFrame(data["lista_registros"])
        st.dataframe(df)

elif opcion == "Productos más caros":
    data = call_api("productos_caros", {"limit": 10})
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df)

elif opcion == "Total por categoría":
    data = call_api("total_categoria_valor",
                    {"categoria": categoria, "fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin})
    if data:
        df = pd.DataFrame(data["muestra"])
        st.dataframe(df)
