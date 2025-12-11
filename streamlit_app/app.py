# streamlit_app/app.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# =====================================================================
# CONFIGURACIÓN DE LA PÁGINA
# =====================================================================
st.set_page_config(
    page_title="OperAI - Dashboard Casino",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# ESTILOS CSS PERSONALIZADOS (TEMA OSCURO)
# =====================================================================
st.markdown("""
<style>
    /* Fondo principal oscuro */
    .main {
        background-color: #1e1e2e;
        color: #ffffff;
    }
    
    /* Sidebar oscuro */
    [data-testid="stSidebar"] {
        background-color: #2b2b3c;
    }
    
    /* Métricas personalizadas */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #00d4ff;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #ffffff !important;
    }
    
    /* Botones */
    .stButton>button {
        background-color: #00d4ff;
        color: #1e1e2e;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 0.5rem 2rem;
    }
    
    .stButton>button:hover {
        background-color: #00b8e6;
        border: none;
    }
    
    /* TextArea */
    textarea {
        background-color: #3b3b4f !important;
        color: #ffffff !important;
        border: 1px solid #4a4a5e !important;
    }
    
    /* SelectBox */
    [data-baseweb="select"] {
        background-color: #3b3b4f !important;
    }
    
    /* DataFrames */
    [data-testid="stDataFrame"] {
        background-color: #2b2b3c;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# CONFIGURACIÓN DE API
# =====================================================================
API_BASE = "http://127.0.0.1:8000/api/tools"
CHAT_ENDPOINT = "http://127.0.0.1:8000/chat"

# =====================================================================
# FUNCIONES AUXILIARES DE FORMATO
# =====================================================================
def format_currency(value):
    """Formatea números como moneda colombiana (COP)"""
    if pd.isna(value) or value is None:
        return "$0"
    try:
        value = float(value)
        formatted = f"${value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except (ValueError, TypeError):
        return "$0"

def format_hover_currency(value):
    """Formatea valores para tooltips en formato colombiano"""
    if pd.isna(value) or value is None:
        return "$0"
    try:
        value = float(value)
        formatted = f"${value:,.0f}".replace(",", ".")
        return formatted
    except (ValueError, TypeError):
        return "$0"

def capitalize_text(text):
    """
    Capitaliza texto: Primera letra en MAYÚSCULA, resto en minúscula
    Ejemplo: "ASEO DE ALFOMBRA" -> "Aseo de alfombra"
    """
    if pd.isna(text) or text is None or not isinstance(text, str):
        return text
    return text.capitalize()

def capitalize_dataframe_values(df, columns_to_capitalize=None):
    """
    Capitaliza valores en columnas específicas del DataFrame
    Si no se especifican columnas, busca automáticamente las de texto
    """
    if df is None or df.empty:
        return df
    
    df_copy = df.copy()
    
    # Si no se especifican columnas, buscar las de tipo texto
    if columns_to_capitalize is None:
        columns_to_capitalize = []
        for col in df_copy.columns:
            # Buscar columnas que contengan categoría, nombre, producto, descripción
            if any(keyword in col.lower() for keyword in ['categoria', 'nombre', 'producto', 'descripcion']):
                columns_to_capitalize.append(col)
    
    # Aplicar capitalización
    for col in columns_to_capitalize:
        if col in df_copy.columns:
            df_copy[col] = df_copy[col].apply(capitalize_text)
    
    return df_copy

def capitalize_columns(df):
    """Capitaliza los nombres de las columnas: Primera letra mayúscula, resto minúscula"""
    if df is None or df.empty:
        return df
    
    df.columns = [col.capitalize() if isinstance(col, str) else col for col in df.columns]
    return df

def format_dataframe_currency(df, currency_columns=None):
    """Formatea columnas numéricas del DataFrame como moneda colombiana"""
    if df is None or df.empty:
        return df
    
    df_copy = df.copy()
    
    # Si no se especifican columnas, buscar las que contengan palabras clave
    if currency_columns is None:
        currency_columns = [col for col in df_copy.columns 
                          if any(keyword in col.lower() 
                                for keyword in ['valor', 'monto', 'total', 'precio', 'promedio', 'costo'])]
    
    # Aplicar formato de moneda
    for col in currency_columns:
        if col in df_copy.columns and pd.api.types.is_numeric_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].apply(format_currency)
    
    return df_copy

def add_custom_hover_data(df, value_col, label_col=None):
    """
    Agrega columnas formateadas para tooltips interactivos
    - valor_formatted: Valor en formato COP
    - label_info: Información adicional (producto, categoría, etc.)
    """
    df_copy = df.copy()
    
    # Agregar valor formateado
    if value_col in df_copy.columns:
        df_copy['valor_formatted'] = df_copy[value_col].apply(format_hover_currency)
    
    # Agregar etiqueta informativa si existe
    if label_col and label_col in df_copy.columns:
        df_copy['label_info'] = df_copy[label_col].apply(capitalize_text)
    
    return df_copy

# =====================================================================
# FUNCIÓN INTELIGENTE PARA SELECCIONAR GRÁFICOS
# =====================================================================
def select_best_chart(df):
    """
    Analiza el DataFrame y selecciona el mejor tipo de gráfico
    Retorna: (tipo_grafico, config)
    
    Lógica de selección:
    1. Series temporales (fecha + valor) → Línea
    2. Productos/Items individuales (nombre_producto) → Barras horizontales
    3. Pocas categorías (≤8) con totales → Pastel/Donut
    4. Muchas categorías (>8) → Barras verticales
    5. Distribución de valores → Histograma
    """
    if df is None or df.empty or len(df) == 0:
        return None, None
    
    # Identificar tipos de columnas
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    text_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Buscar columnas específicas (case-insensitive)
    date_col = None
    value_col = None
    producto_col = None
    categoria_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Detectar fechas
        if 'fecha' in col_lower and date_col is None:
            date_col = col
        
        # Detectar valores monetarios
        if any(kw in col_lower for kw in ['valor', 'monto', 'total', 'precio']) and value_col is None:
            if col in numeric_cols:
                value_col = col
        
        # Detectar productos
        if 'nombre_producto' in col_lower or 'producto' in col_lower:
            producto_col = col
        
        # Detectar categorías
        if 'categoria' in col_lower:
            categoria_col = col
    
    # Si no se encontró columna de valor, usar la primera numérica
    if value_col is None and len(numeric_cols) > 0:
        value_col = numeric_cols[0]
    
    # ============================================================
    # CASO 1: SERIES TEMPORALES (fecha + valor)
    # ============================================================
    if date_col and value_col:
        # Detectar si hay productos para mostrar en tooltip
        hover_info = producto_col if producto_col else categoria_col
        
        return 'line', {
            'x': date_col,
            'y': value_col,
            'label': hover_info,
            'title': f'📈 Evolución temporal de {value_col.lower()}'
        }
    
    # ============================================================
    # CASO 2: PRODUCTOS INDIVIDUALES (ranking de productos)
    # ============================================================
    if producto_col and value_col:
        return 'barh', {
            'y': producto_col,
            'x': value_col,
            'title': '🏆 Top productos por valor',
            'limit': 15
        }
    
    # ============================================================
    # CASO 3: CATEGORÍAS CON TOTALES
    # ============================================================
    if categoria_col and value_col:
        # Pocas categorías → Pastel/Donut
        if len(df) <= 8:
            return 'pie', {
                'labels': categoria_col,
                'values': value_col,
                'title': '🎯 Distribución por categoría'
            }
        # Muchas categorías → Barras verticales
        else:
            return 'bar', {
                'x': categoria_col,
                'y': value_col,
                'title': '📊 Comparación por categoría',
                'limit': 15
            }
    
    # ============================================================
    # CASO 4: DATOS CATEGÓRICOS GENÉRICOS
    # ============================================================
    if len(text_cols) > 0 and value_col:
        first_text_col = text_cols[0]
        
        # Si hay pocos elementos → Pastel
        if len(df) <= 8:
            return 'pie', {
                'labels': first_text_col,
                'values': value_col,
                'title': f'🎯 Distribución de {first_text_col.lower()}'
            }
        # Muchos elementos → Barras
        else:
            return 'bar', {
                'x': first_text_col,
                'y': value_col,
                'title': f'📊 Análisis de {first_text_col.lower()}',
                'limit': 15
            }
    
    # ============================================================
    # CASO 5: SOLO VALORES NUMÉRICOS (distribución)
    # ============================================================
    if len(numeric_cols) > 0:
        return 'histogram', {
            'x': numeric_cols[0],
            'title': f'📉 Distribución de {numeric_cols[0].lower()}'
        }
    
    return None, None

# =====================================================================
# FUNCIÓN PARA CREAR GRÁFICOS
# =====================================================================
def create_chart(df, chart_type, config):
    """Crea el gráfico según el tipo y configuración con formato colombiano"""
    if chart_type is None or config is None:
        return None
    
    try:
        # Preparar DataFrame
        df_clean = df.copy()
        
        # Capitalizar valores de texto en todas las columnas relevantes
        df_clean = capitalize_dataframe_values(df_clean)
        
        # Convertir fechas si es necesario
        if 'x' in config and config['x'] in df_clean.columns:
            if 'fecha' in config['x'].lower():
                df_clean[config['x']] = pd.to_datetime(df_clean[config['x']], errors='coerce')
                df_clean = df_clean.dropna(subset=[config['x']]).sort_values(config['x'])
        
        # ============================================================
        # GRÁFICO DE LÍNEA TEMPORAL
        # ============================================================
        if chart_type == 'line':
            # Agregar datos formateados para hover
            label_col = config.get('label')
            df_clean = add_custom_hover_data(df_clean, config['y'], label_col)
            
            fig = px.line(
                df_clean,
                x=config['x'],
                y=config['y'],
                title=config['title'],
                template="plotly_dark",
                markers=True,
                line_shape='spline'
            )
            
            # Construir hovertemplate dinámico
            if label_col and 'label_info' in df_clean.columns:
                # Mostrar: Fecha + Producto/Categoría + Valor
                hover_template = '<b>%{x|%Y-%m-%d}</b><br>%{customdata[1]}<br>%{customdata[0]}<extra></extra>'
                custom_data = ['valor_formatted', 'label_info']
            else:
                # Mostrar solo: Fecha + Valor
                hover_template = '<b>%{x|%Y-%m-%d}</b><br>%{customdata[0]}<extra></extra>'
                custom_data = ['valor_formatted']
            
            fig.update_traces(
                line_color='#00d4ff',
                line_width=3,
                marker=dict(size=8, color='#ff6b6b', line=dict(width=2, color='#ffffff')),
                customdata=df_clean[custom_data].values,
                hovertemplate=hover_template
            )
            
            fig.update_layout(
                height=500,
                hovermode='x unified',
                font=dict(size=12),
                xaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(255,255,255,0.1)',
                    title='Fecha'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(255,255,255,0.1)',
                    tickformat='$,.0f',
                    title=config['y'].capitalize()
                )
            )
        
        # ============================================================
        # BARRAS HORIZONTALES (Rankings, Top productos)
        # ============================================================
        elif chart_type == 'barh':
            limit = config.get('limit', 10)
            df_plot = df_clean.head(limit)
            df_plot = add_custom_hover_data(df_plot, config['x'])
            
            fig = px.bar(
                df_plot,
                y=config['y'],
                x=config['x'],
                orientation='h',
                title=config['title'],
                template="plotly_dark",
                color=config['x'],
                color_continuous_scale='Turbo'
            )
            
            fig.update_layout(
                height=500,
                font=dict(size=12),
                yaxis_title=None,
                xaxis=dict(
                    tickformat='$,.0f',
                    title=config['x'].capitalize()
                ),
                coloraxis_colorbar=dict(
                    tickformat='$,.0f',
                    title=None
                )
            )
            
            fig.update_traces(
                marker_line_color='#ffffff',
                marker_line_width=1.5,
                customdata=df_plot[['valor_formatted']].values,
                hovertemplate='<b>%{y}</b><br>%{customdata[0]}<extra></extra>'
            )
        
        # ============================================================
        # GRÁFICO DE PASTEL/DONUT
        # ============================================================
        elif chart_type == 'pie':
            df_clean = add_custom_hover_data(df_clean, config['values'])
            
            fig = go.Figure(data=[go.Pie(
                labels=df_clean[config['labels']],
                values=df_clean[config['values']],
                hole=.4,
                marker=dict(colors=px.colors.qualitative.Set3),
                textinfo='label+percent',
                textposition='outside'
            )])
            
            fig.update_traces(
                customdata=df_clean['valor_formatted'].tolist(),
                hovertemplate='<b>%{label}</b><br>%{customdata}<br>%{percent}<extra></extra>'
            )
            
            fig.update_layout(
                title=config['title'],
                template="plotly_dark",
                showlegend=True,
                height=500,
                font=dict(size=12)
            )
        
        # ============================================================
        # BARRAS VERTICALES
        # ============================================================
        elif chart_type == 'bar':
            limit = config.get('limit', 15)
            df_plot = df_clean.sort_values(config['y'], ascending=False).head(limit)
            df_plot = add_custom_hover_data(df_plot, config['y'])
            
            fig = px.bar(
                df_plot,
                x=config['x'],
                y=config['y'],
                title=config['title'],
                template="plotly_dark",
                color=config['y'],
                color_continuous_scale='Blues'
            )
            
            fig.update_layout(
                height=500,
                xaxis_tickangle=-45,
                font=dict(size=12),
                xaxis_title=config['x'].capitalize(),
                yaxis=dict(
                    tickformat='$,.0f',
                    title=config['y'].capitalize()
                ),
                coloraxis_colorbar=dict(
                    tickformat='$,.0f',
                    title=None
                )
            )
            
            fig.update_traces(
                marker_line_color='#ffffff',
                marker_line_width=1.5,
                customdata=df_plot[['valor_formatted']].values,
                hovertemplate='<b>%{x}</b><br>%{customdata[0]}<extra></extra>'
            )
        
        # ============================================================
        # HISTOGRAMA
        # ============================================================
        elif chart_type == 'histogram':
            fig = px.histogram(
                df_clean,
                x=config['x'],
                title=config['title'],
                template="plotly_dark",
                nbins=30,
                color_discrete_sequence=['#00d4ff']
            )
            
            fig.update_layout(
                height=500,
                font=dict(size=12),
                xaxis=dict(
                    tickformat='$,.0f',
                    title=config['x'].capitalize()
                ),
                yaxis_title='Frecuencia'
            )
        
        else:
            return None
        
        return fig
        
    except Exception as e:
        st.error(f"❌ Error al crear gráfico: {e}")
        return None

# =====================================================================
# FUNCIONES DE API
# =====================================================================
def call_api(endpoint, params=None):
    """Llama a la API y retorna JSON"""
    try:
        url = f"{API_BASE}/{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error en API: {e}")
        return None

def call_chat_api(mensaje):
    """Llama al endpoint de chat con IA"""
    try:
        response = requests.post(CHAT_ENDPOINT, json={"message": mensaje}, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error en Chat IA: {e}")
        return None

def get_fechas_disponibles():
    """Obtiene el rango de fechas disponibles en la BD"""
    data = call_api("fechas")
    if data:
        fecha_min = pd.to_datetime(data.get("fecha_minima", "2025-01-01"))
        fecha_max = pd.to_datetime(data.get("fecha_maxima", "2025-12-31"))
        return fecha_min, fecha_max
    return pd.to_datetime("2025-01-01"), pd.to_datetime("2025-12-31")

# =====================================================================
# SIDEBAR - FILTROS Y CONSULTAS
# =====================================================================
st.sidebar.title("🎛️ Panel de Control")

# --- Rango de Fechas ---
st.sidebar.subheader("📅 Rango de fechas")
fecha_min, fecha_max = get_fechas_disponibles()

fecha_inicio = st.sidebar.date_input(
    "Fecha inicio:",
    value=fecha_min,
    min_value=fecha_min,
    max_value=fecha_max
)

fecha_fin = st.sidebar.date_input(
    "Fecha fin:",
    value=fecha_max,
    min_value=fecha_min,
    max_value=fecha_max
)

st.sidebar.markdown("---")

# --- Consulta a la IA ---
st.sidebar.subheader("💬 Consulta a la IA")
mensaje_ia = st.sidebar.text_area(
    "Escribe tu consulta:",
    placeholder="Ej: Productos más caros de ASEO entre enero y octubre de 2025",
    height=120
)

if st.sidebar.button("🚀 Enviar a IA", use_container_width=True):
    if mensaje_ia.strip():
        with st.spinner("🤖 Consultando a la IA..."):
            respuesta = call_chat_api(mensaje_ia)
            if respuesta:
                st.session_state["respuesta_ia"] = respuesta
                st.session_state["mensaje_enviado"] = mensaje_ia
    else:
        st.sidebar.warning("⚠️ Escribe una consulta primero")

st.sidebar.markdown("---")

# --- Opciones Manuales ---
st.sidebar.subheader("🔧 Opciones manuales")

tipo_analisis = st.sidebar.selectbox(
    "Selecciona el análisis:",
    [
        "Promedio por categoría",
        "Buscar por categoría",
        "Productos más caros",
        "Total por categoría",
        "Gasto por categoría",
        "Estadísticas generales"
    ]
)

# Obtener categorías disponibles
categorias_data = call_api("categorias")
categorias = categorias_data.get("categorias", []) if categorias_data else []

# Capitalizar categorías para el selector
categorias_capitalizadas = [capitalize_text(cat) for cat in categorias] if categorias else ["Aseo"]

categoria_seleccionada = st.sidebar.selectbox(
    "Categoría:",
    options=categorias_capitalizadas
)

# Convertir de vuelta a mayúsculas para la API (si es necesario)
categoria_api = categoria_seleccionada.upper()

# =====================================================================
# ÁREA PRINCIPAL - TÍTULO Y MÉTRICAS
# =====================================================================
st.title("📊 Dashboard Dinámico - OperAI Casino")
st.markdown("*Análisis inteligente de gastos con IA*")

# Mostrar estadísticas generales
stats = call_api("estadisticas_generales", {
    "fecha_inicio": fecha_inicio.isoformat(),
    "fecha_fin": fecha_fin.isoformat()
})

if stats:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total Registros",
            value=f"{stats['total_registros']:,}"
        )
    
    with col2:
        st.metric(
            label="💰 Monto Total",
            value=format_currency(stats['monto_total'])
        )
    
    with col3:
        st.metric(
            label="📊 Promedio",
            value=format_currency(stats['promedio'])
        )
    
    with col4:
        st.metric(
            label="🏷️ Categorías",
            value=stats['total_categorias']
        )

st.markdown("---")

# =====================================================================
# MOSTRAR RESPUESTA DE LA IA
# =====================================================================
if "respuesta_ia" in st.session_state:
    st.subheader("🤖 Respuesta de la IA")
    
    respuesta = st.session_state["respuesta_ia"]
    mensaje_original = st.session_state.get("mensaje_enviado", "")
    
    # Mostrar consulta original
    st.info(f"**💬 Tu consulta:** {mensaje_original}")
    
    # Mostrar respuesta
    if "reply" in respuesta:
        st.success(f"**🎯 OperAI responde:** {respuesta['reply']}")
    
    # Mostrar datos si existen
    if "data" in respuesta and respuesta["data"]:
        data = respuesta["data"]
        df = None
        
        # Convertir a DataFrame
        if isinstance(data, dict):
            if "lista_registros" in data:
                df = pd.DataFrame(data["lista_registros"])
            elif "stats" in data:
                st.json(data["stats"])
        elif isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
        
        # Mostrar tabla y gráfico
        if df is not None and len(df) > 0:
            # Capitalizar columnas
            df = capitalize_columns(df)
            
            # Capitalizar valores de texto
            df = capitalize_dataframe_values(df)
            
            # Crear copia para mostrar con formato de moneda
            df_display = format_dataframe_currency(df.copy())
            
            st.dataframe(df_display.head(20), use_container_width=True)
            
            # SELECCIONAR Y CREAR GRÁFICO AUTOMÁTICAMENTE
            chart_type, config = select_best_chart(df)
            
            if chart_type and config:
                fig = create_chart(df, chart_type, config)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ℹ️ No se pudo generar un gráfico para estos datos")
    
    st.markdown("---")

# =====================================================================
# ANÁLISIS MANUAL SELECCIONADO
# =====================================================================
st.subheader(f"📈 {tipo_analisis}")

if tipo_analisis == "Promedio por categoría":
    data = call_api("promedio_categoria", {
        "categoria": categoria_api,
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat()
    })
    
    if data:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💵 Promedio", format_currency(data['monto_promedio']))
        with col2:
            st.metric("📊 Registros", f"{data['cantidad_registros']:,}")

elif tipo_analisis == "Buscar por categoría":
    data = call_api("buscar_por_categoria", {
        "categoria": categoria_api,
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat()
    })
    
    if data:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📦 Total registros", f"{data['cantidad_registros']:,}")
        with col2:
            st.metric("💰 Monto total", format_currency(data['monto_total']))
        
        if data.get("lista_registros"):
            df = pd.DataFrame(data["lista_registros"])
            df = capitalize_columns(df)
            df = capitalize_dataframe_values(df)
            
            # Mostrar tabla
            df_display = format_dataframe_currency(df.copy())
            st.dataframe(df_display, use_container_width=True)
            
            # Crear gráfico inteligente
            chart_type, config = select_best_chart(df)
            if chart_type and config:
                fig = create_chart(df, chart_type, config)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

elif tipo_analisis == "Productos más caros":
    data = call_api("productos_caros", {"limit": 15})
    
    if data:
        df = pd.DataFrame(data)
        df = capitalize_columns(df)
        df = capitalize_dataframe_values(df)
        
        # Mostrar tabla
        df_display = format_dataframe_currency(df.copy())
        st.dataframe(df_display, use_container_width=True)
        
        # Crear gráfico
        chart_type, config = select_best_chart(df)
        if chart_type and config:
            fig = create_chart(df, chart_type, config)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

elif tipo_analisis == "Total por categoría":
    data = call_api("total_categoria_valor", {
        "categoria": categoria_api,
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "limit": 20
    })
    
    if data:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total", format_currency(data['monto_total']))
        with col2:
            st.metric("📊 Promedio", format_currency(data['promedio']))
        with col3:
            st.metric("📦 Registros", f"{data['cantidad_registros']:,}")
        
        if data.get("lista_registros"):
            df = pd.DataFrame(data["lista_registros"])
            df = capitalize_columns(df)
            df = capitalize_dataframe_values(df)
            
            df_display = format_dataframe_currency(df.copy())
            st.dataframe(df_display, use_container_width=True)
            
            # Crear gráfico
            chart_type, config = select_best_chart(df)
            if chart_type and config:
                fig = create_chart(df, chart_type, config)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

elif tipo_analisis == "Gasto por categoría":
    data = call_api("gasto_por_categoria", {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat()
    })
    
    if data:
        df = pd.DataFrame(data)
        df = capitalize_columns(df)
        df = capitalize_dataframe_values(df)
        
        df_display = format_dataframe_currency(df.copy())
        st.dataframe(df_display, use_container_width=True)
        
        # Crear gráficos: pastel y barras
        chart_type, config = select_best_chart(df)
        if chart_type and config:
            fig = create_chart(df, chart_type, config)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de barras adicional si es pastel
        if chart_type == 'pie':
            total_col = [col for col in df.columns if 'total' in col.lower()]
            cat_col = [col for col in df.columns if 'categoria' in col.lower()]
            
            if total_col and cat_col:
                fig2 = create_chart(df, 'bar', {
                    'x': cat_col[0],
                    'y': total_col[0],
                    'title': '💰 Comparación de gastos por categoría'
                })
                if fig2:
                    st.plotly_chart(fig2, use_container_width=True)

elif tipo_analisis == "Estadísticas generales":
    data = call_api("estadisticas_generales", {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat()
    })
    
    if data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📦 Total Registros", f"{data['total_registros']:,}")
            st.metric("💰 Monto Total", format_currency(data['monto_total']))
        
        with col2:
            st.metric("📊 Promedio", format_currency(data['promedio']))
            st.metric("🏷️ Categorías", data['total_categorias'])

# =====================================================================
# FOOTER
# =====================================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        <p>🤖 <strong>OperAI</strong> - Dashboard de Gestión de Gastos Casino</p>
        <p>📊 Powered by Streamlit + FastAPI + Gemini AI</p>
        <p style='font-size: 0.85em;'>✨ Gráficos interactivos con formato colombiano (COP)</p>
    </div>
    """,
    unsafe_allow_html=True
)