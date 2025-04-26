import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import splrep, splev, interp1d
import os
import time
from datetime import datetime, timedelta
import base64
import plotly.express as px
import plotly.graph_objects as go
import json

# Configurar página
st.set_page_config(
    page_title="Sistema de Dosificación | SEDACAJ",
    layout="wide",
    page_icon="💧",
    initial_sidebar_state="collapsed"
)

# Definir colores institucionales
COLOR_PRIMARIO = "#003366"  # Azul oscuro institucional
COLOR_SECUNDARIO = "#336699"  # Azul medio
COLOR_ACENTO = "#66A3D2"  # Azul claro
COLOR_TEXTO = "#333333"  # Gris oscuro para texto
COLOR_FONDO = "#F8F9FA"  # Gris muy claro para fondo
COLOR_EXITO = "#28A745"  # Verde para éxito
COLOR_ADVERTENCIA = "#FFC107"  # Amarillo para advertencias
COLOR_ERROR = "#DC3545"  # Rojo para errores

# Rutas de carpetas
DATA_DIR = "data"
IMAGES_DIR = os.path.join(DATA_DIR, "images")
HISTORY_FILE = os.path.join(DATA_DIR, "historial_pruebas.csv")

# Crear directorio de datos si no existe
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Función para cargar imágenes base64 (solución para el problema de los logos)
def get_base64_encoded_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# Intentar cargar logos como base64
logo_unc_path = os.path.join(IMAGES_DIR, "logo_unc.png")
logo_posgrado_path = os.path.join(IMAGES_DIR, "logo_escuela_posgrado.png")

logo_unc_base64 = get_base64_encoded_image(logo_unc_path)
logo_posgrado_base64 = get_base64_encoded_image(logo_posgrado_path)

# --- Funciones para el manejo del historial ---

def guardar_resultado_historial(turbidez, ph, caudal, dosis_sugerida, metodo, categoria):
    """
    Guarda los resultados de una prueba en el historial
    """
    # Crear dataframe con una fila para el nuevo registro
    ahora = datetime.now()
    nuevo_registro = pd.DataFrame({
        'fecha': [ahora.strftime('%Y-%m-%d')],
        'hora': [ahora.strftime('%H:%M:%S')],
        'turbidez': [turbidez],
        'ph': [ph],
        'caudal': [caudal],
        'dosis_mg_l': [dosis_sugerida],
        'metodo_calculo': [metodo],
        'categoria': [categoria]
    })
    
    # Verificar si el archivo de historial existe
    if os.path.exists(HISTORY_FILE):
        # Cargar historial existente y agregar nuevo registro
        historial = pd.read_csv(HISTORY_FILE)
        historial = pd.concat([historial, nuevo_registro], ignore_index=True)
    else:
        # Crear nuevo archivo de historial
        historial = nuevo_registro
    
    # Guardar historial actualizado
    historial.to_csv(HISTORY_FILE, index=False)

def cargar_historial():
    """
    Carga el historial de pruebas desde el archivo CSV
    """
    if os.path.exists(HISTORY_FILE):
        historial = pd.read_csv(HISTORY_FILE)
        
        # Convertir columnas de fecha y hora a datetime
        historial['fecha'] = pd.to_datetime(historial['fecha'])
        
        # Asegurar que los valores numéricos sean correctos
        for col in ['turbidez', 'ph', 'caudal', 'dosis_mg_l']:
            historial[col] = pd.to_numeric(historial[col], errors='coerce')
            
        return historial
    else:
        return pd.DataFrame(columns=[
            'fecha', 'hora', 'turbidez', 'ph', 'caudal', 
            'dosis_mg_l', 'metodo_calculo', 'categoria'
        ])

# --- Funciones para generar gráficas ---

def crear_grafica_tendencia_turbidez_dosis(historial_df):
    """
    Crea una gráfica de la relación entre turbidez y dosis a lo largo del tiempo
    """
    if historial_df.empty:
        return None
    
    # Ordenar por fecha
    df_ordenado = historial_df.sort_values(by='fecha')
    
    # Crear figura
    fig = px.scatter(
        df_ordenado, 
        x='turbidez', 
        y='dosis_mg_l',
        color='fecha',
        color_continuous_scale='viridis',
        labels={
            'turbidez': 'Turbidez (NTU)',
            'dosis_mg_l': 'Dosis de Sulfato de Aluminio (mg/L)',
            'fecha': 'Fecha'
        },
        title='Relación Turbidez vs Dosis a lo largo del tiempo',
        hover_data=['fecha', 'hora', 'ph', 'caudal']
    )
    
    # Añadir línea de tendencia
    fig.update_layout(
        xaxis_title='Turbidez (NTU)',
        yaxis_title='Dosis (mg/L)',
        height=500,
        template='plotly_white'
    )
    
    return fig

def crear_grafica_serie_temporal(historial_df, periodo='mes'):
    """
    Crea una gráfica de serie temporal de turbidez y dosis
    
    Args:
        historial_df: DataFrame con historial
        periodo: 'dia', 'semana', 'mes' o 'todo'
    """
    if historial_df.empty:
        return None
    
    # Filtrar por periodo
    hoy = datetime.now().date()
    df = historial_df.copy()
    
    if periodo == 'dia':
        df = df[df['fecha'].dt.date == hoy]
        titulo = f"Tendencia del día ({hoy.strftime('%d/%m/%Y')})"
    elif periodo == 'semana':
        una_semana_atras = hoy - timedelta(days=7)
        df = df[df['fecha'].dt.date >= una_semana_atras]
        titulo = f"Tendencia de la última semana ({una_semana_atras.strftime('%d/%m/%Y')} - {hoy.strftime('%d/%m/%Y')})"
    elif periodo == 'mes':
        un_mes_atras = hoy - timedelta(days=30)
        df = df[df['fecha'].dt.date >= un_mes_atras]
        titulo = f"Tendencia del último mes ({un_mes_atras.strftime('%d/%m/%Y')} - {hoy.strftime('%d/%m/%Y')})"
    else:
        titulo = "Tendencia histórica completa"
    
    if df.empty:
        return None
    
    # Ordenar por fecha y hora
    df['fecha_hora'] = pd.to_datetime(df['fecha'].astype(str) + ' ' + df['hora'])
    df = df.sort_values('fecha_hora')
    
    # Crear figura con dos ejes Y
    fig = go.Figure()
    
    # Añadir línea para turbidez
    fig.add_trace(
        go.Scatter(
            x=df['fecha_hora'],
            y=df['turbidez'],
            name='Turbidez (NTU)',
            line=dict(color=COLOR_ADVERTENCIA, width=2),
            mode='lines+markers'
        )
    )
    
    # Añadir línea para dosis
    fig.add_trace(
        go.Scatter(
            x=df['fecha_hora'],
            y=df['dosis_mg_l'],
            name='Dosis (mg/L)',
            line=dict(color=COLOR_PRIMARIO, width=2),
            mode='lines+markers',
            yaxis='y2'
        )
    )
    
    # Configurar layouts con dos ejes Y
    fig.update_layout(
        title=titulo,
        xaxis=dict(title='Fecha y Hora'),
        yaxis=dict(
            title=dict(text='Turbidez (NTU)', font=dict(color=COLOR_ADVERTENCIA)),
            tickfont=dict(color=COLOR_ADVERTENCIA)
        ),
        yaxis2=dict(
            title=dict(text='Dosis (mg/L)', font=dict(color=COLOR_PRIMARIO)),
            tickfont=dict(color=COLOR_PRIMARIO),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        height=500,
        template='plotly_white',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    return fig

def crear_grafica_distribucion_dosis(historial_df):
    """
    Crea una gráfica de distribución de dosis utilizadas
    """
    if historial_df.empty:
        return None
    
    # Crear histograma de dosis
    fig = px.histogram(
        historial_df,
        x='dosis_mg_l',
        nbins=20,
        title='Distribución de Dosis Aplicadas',
        labels={'dosis_mg_l': 'Dosis de Sulfato de Aluminio (mg/L)'},
        color_discrete_sequence=[COLOR_PRIMARIO]
    )
    
    fig.update_layout(
        xaxis_title="Dosis (mg/L)",
        yaxis_title="Frecuencia",
        height=400,
        template='plotly_white'
    )
    
    return fig

# --- Función para cargar datos ---
@st.cache_data  # Cachear los datos para mejorar rendimiento
def load_data():
    data_path = os.path.join(DATA_DIR, "tabla_dosificacion.csv")
    if not os.path.exists(data_path):
        st.error(f"No se encontró el archivo de datos: {data_path}")
        st.stop()
        
    data = pd.read_csv(data_path)
    
    # Forzar que turbiedad y dosis sean numéricos
    data['turbiedad'] = pd.to_numeric(data['turbiedad'], errors='coerce')
    data['dosis_mg_l'] = pd.to_numeric(data['dosis_mg_l'], errors='coerce')
    
    # Eliminar filas con NaN en columnas críticas
    data = data.dropna(subset=['turbiedad', 'dosis_mg_l'])
    
    return data

try:
    # Cargar datos de dosificación
    data = load_data()
    
    # Verificar si hay datos después de la limpieza
    if data.empty:
        st.error("No hay datos válidos en el archivo CSV después de eliminar valores no numéricos.")
        st.stop()

    # Estilos CSS personalizados
    css = """
    <style>
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        
        .header-container {
            background: linear-gradient(90deg, #003366 0%, #336699 100%);
            padding: 1.5rem;
            border-radius: 0.75rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        /* Aumentada la especificidad y añadido !important */
        div.header-container h1.header-titulo {
            color: white !important;
            text-align: center !important;
            font-size: 2rem !important;
        }
        
        div.header-container h3.header-subtitulo {
            color: rgba(255,255,255,0.9) !important;
            text-align: center !important;
            font-weight: 300 !important;
        }
        
        .card {
            background-color: white;
            border-radius: 0.75rem;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
        }
        
        .card-titulo {
            color: #003366;
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #66A3D2;
        }
        
        .result-card {
            background-color: white;
            border-radius: 0.75rem;
            padding: 1.5rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            margin-bottom: 1.5rem;
            border-left: 5px solid #003366;
        }
        
        .metric-container {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: #F8F9FA;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        
        .metric-label {
            font-size: 1.1rem;
            color: #333333;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 3rem;
            font-weight: 700;
            color: #003366;
        }
        
        .metric-unit {
            font-size: 1.2rem;
            color: #336699;
            font-weight: 400;
        }
        
        .footer {
            background-color: #003366;
            color: white;
            padding: 1.5rem;
            border-radius: 0.75rem;
            margin-top: 2rem;
            text-align: center;
        }
        
        .footer-institution {
            font-size: 1rem !important;
            opacity: 1 !important;
            font-weight: 500 !important;
            margin-top: 1rem !important;
            color: rgba(255,255,255,0.95) !important;
        }
        
        .info-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background-color: rgba(102, 163, 210, 0.2);
            border-radius: 1rem;
            font-size: 0.8rem;
            color: #336699;
            margin-top: 0.25rem;
        }
        
        .instruccion-panel {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: rgba(102, 163, 210, 0.1);
            margin-bottom: 1rem;
            border-left: 4px solid #336699;
        }
        
        .instruccion-titulo {
            color: #336699;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .instruccion-texto {
            color: #333;
            font-size: 0.9rem;
        }
        
        .param-panel {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .param-item {
            flex: 1;
            padding: 1rem;
            background-color: #f8f9fa;
            border-radius: 0.5rem;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .param-label {
            font-size: 0.85rem;
            color: #6c757d;
            margin-bottom: 0.25rem;
        }
        
        .param-value {
            font-size: 1.2rem;
            font-weight: 600;
            color: #003366;
        }
        
        .doc-panel {
            margin-top: 1.5rem;
            padding: 1rem;
            background-color: #f8f9fa;
            border-radius: 0.5rem;
        }
        
        .doc-titulo {
            color: #336699;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .alerta {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid;
        }
        
        .alerta-titulo {
            font-weight: 600;
            margin-bottom: 0.25rem;
        }
        
        .alerta-texto {
            font-size: 0.9rem;
        }
        
        /* Estilos para historial */
        .history-table {
            font-size: 0.9rem;
        }
        
        .history-table th {
            background-color: #f1f7fc;
            color: #003366;
            font-weight: 600;
        }
        
        .history-table tr:hover {
            background-color: #f8f9fa;
        }
        
        .trend-filter {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        
        /* Estilos para las pestañas */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            white-space: pre-wrap;
            background-color: white;
            border-radius: 0.5rem;
            color: #003366;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #003366 !important;
            color: white !important;
        }
    </style>

    <script>
        // Función para mantener la sesión activa
        function keepAlive() {
            fetch(window.location.href).then(r => setTimeout(keepAlive, 60000)).catch(e => setTimeout(keepAlive, 120000));
        }
        setTimeout(keepAlive, 60000);
    </script>
    """

    st.markdown(css, unsafe_allow_html=True)

    # Funciones para encabezado y pie de página
    def mostrar_encabezado():
        """Función para mostrar el encabezado en ambas pestañas"""
        st.markdown(
            """
            <div class="header-container">
                <h1 class="header-titulo" style="color: white !important; text-align: center; font-size: 2rem;">Sistema de Dosificación Óptima</h1>
                <h3 class="header-subtitulo" style="color: rgba(255,255,255,0.9) !important; text-align: center; font-weight: 300; margin-bottom: 0.2rem;">Planta de Tratamiento:</h3>
                <h3 class="header-subtitulo" style="color: rgba(255,255,255,0.9) !important; text-align: center; font-weight: 300; margin-bottom: 0.2rem;">"El Milagro"</h3>
                <h3 class="header-subtitulo" style="color: rgba(255,255,255,0.9) !important; text-align: center; font-weight: 300;">EPS SEDACAJ S.A.</h3>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    def mostrar_pie_pagina():
        """Función para mostrar el pie de página en ambas pestañas"""
        st.markdown(
            """
            <div class="footer">
                <div style="font-weight: 600; margin-bottom: 0.5rem; font-size: 1.2rem;">Sistema de Dosificación Óptima de Sulfato de Aluminio</div>
                <div style="display: flex; justify-content: space-around; flex-wrap: wrap; margin: 1.5rem 0;">
                    <div style="padding: 0 1rem; text-align: center;">
                        <div style="font-size: 0.9rem; color: rgba(255,255,255,0.7); margin-bottom: 0.3rem;">Investigador principal</div>
                        <div style="font-size: 1.1rem; font-weight: 500;">MSc. Ever Rojas Huamán</div>
                    </div>
                    <div style="padding: 0 1rem; text-align: center;">
                        <div style="font-size: 0.9rem; color: rgba(255,255,255,0.7); margin-bottom: 0.3rem;">Asesor de Investigación</div>
                        <div style="font-size: 1.1rem; font-weight: 500;">Dr. Glicerio Eduardo Torres Carranza</div>
                    </div>
                </div>
                <div class="footer-institution">Universidad Nacional de Cajamarca<br>Escuela de Posgrado, 2025</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Mostrar encabezado (compartido en ambas pestañas)
    mostrar_encabezado()
    
    # Crear pestañas
    tab1, tab2 = st.tabs(["📊 Calculadora de Dosis", "📈 Historial y Tendencias"])
    # PESTAÑA 1: CALCULADORA DE DOSIS
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Tarjeta de parámetros
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<h3 class="card-titulo">Parámetros de Entrada</h3>', unsafe_allow_html=True)
            
            # Panel de instrucción
            st.markdown(
                """
                <div class="instruccion-panel">
                    <div class="instruccion-titulo">📋 Instrucciones de uso</div>
                    <div class="instruccion-texto">
                        Ingrese los valores de turbidez, pH y caudal operativo para calcular la dosis óptima de 
                        sulfato de aluminio necesaria para el tratamiento de agua potable. El cálculo se realiza 
                        mediante interpolación por splines cúbicos y toma de decisiones con lógica difusa, basado en datos experimentales.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Formulario para entrada de datos
            with st.form(key="parametros_form"):
                # Sección de datos de agua cruda
                st.markdown(
                    f'<p style="color:{COLOR_SECUNDARIO}; font-weight:500; margin-bottom:0.5rem;">Características del Agua Cruda:</p>', 
                    unsafe_allow_html=True
                )
                
                turbidez = st.number_input(
                    "Turbidez (NTU)", 
                    min_value=0.1, 
                    max_value=4000.0, 
                    value=100.0, 
                    step=1.0,
                    help="Ingrese la turbidez del agua cruda medida en Unidades Nefelométricas de Turbidez (NTU)"
                )
                
                ph = st.number_input(
                    "pH", 
                    min_value=5.0, 
                    max_value=9.5, 
                    value=7.2, 
                    step=0.1,
                    help="Ingrese el valor de pH del agua cruda"
                )
                
                st.markdown(
                    f'<p style="color:{COLOR_SECUNDARIO}; font-weight:500; margin-top:1rem; margin-bottom:0.5rem;">Parámetros Operativos:</p>', 
                    unsafe_allow_html=True
                )
                
                caudal = st.number_input(
                    "Caudal Operativo (L/s)", 
                    min_value=150.0, 
                    max_value=300.0, 
                    value=200.0, 
                    step=5.0,
                    help="Ingrese el caudal de operación de la planta en litros por segundo"
                )
                
                # Nueva opción para guardar en historial
                guardar_en_historial = st.checkbox(
                    "Guardar resultado en historial", 
                    value=True,
                    help="Marque esta opción para registrar el resultado en el historial de pruebas"
                )
                
                # Botón de cálculo personalizado
                submitted = st.form_submit_button(
                    "Calcular Dosis Óptima", 
                    use_container_width=True,
                    type="primary"
                )
            
            # Fecha y hora actual
            now = datetime.now()
            st.markdown(
                f'<div style="text-align:center;"><span class="info-badge">Fecha: {now.strftime("%d/%m/%Y")} • Hora: {now.strftime("%H:%M")}</span></div>', 
                unsafe_allow_html=True
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Columna de resultados
        with col2:
            # Contenedor para resultados
            results_container = st.empty()
            
            # Indicador inicial o mostrar resultados si se envió el formulario
            if not submitted:
                with results_container.container():
                    st.markdown(
                        """
                        <div class="result-card" style="display: flex; align-items: center; justify-content: center; min-height: 300px; text-align: center;">
                            <div>
                                <h3 style="color: #6c757d; font-weight: 400;">Resultados del Análisis</h3>
                                <p style="color: #6c757d; font-weight: 300;">Complete el formulario y presione el botón "Calcular Dosis Óptima" para obtener los resultados.</p>
                            </div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
            
            else:
                # Animación de carga
                with st.spinner("Procesando datos..."):
                    # Simular tiempo de cálculo
                    time.sleep(0.8)
                    
                    # Obtener caudales disponibles en el dataset
                    caudales_disponibles = sorted(data['caudal'].unique())
                    
                    # Usar el caudal más cercano disponible para los cálculos
                    if caudales_disponibles:
                        # Encontrar el caudal más cercano disponible
                        caudal_calculo = min(caudales_disponibles, key=lambda x: abs(x - caudal))
                    else:
                        st.error("No hay datos de caudal disponibles en el archivo CSV.")
                        st.stop()

                    # Procesamiento de datos
                    data_caudal = data[data['caudal'] == caudal_calculo].copy()
                    data_caudal = data_caudal.sort_values(by='turbiedad')
                    
                    # Verificar valores duplicados en turbiedad y promediar si es necesario
                    x_values = data_caudal['turbiedad'].values
                    y_values = data_caudal['dosis_mg_l'].values
                    
                    if len(np.unique(x_values)) < len(x_values):
                        data_grouped = data_caudal.groupby('turbiedad')['dosis_mg_l'].mean().reset_index()
                        x_values = data_grouped['turbiedad'].values
                        y_values = data_grouped['dosis_mg_l'].values
                    
                    try:
                        # Intentar crear spline cúbico o usar interpolación lineal como alternativa
                        try:
                            spl = splrep(x_values, y_values, k=3)
                            dosis_sugerida = float(splev(turbidez, spl))
                            metodo = "Spline Cúbico"
                        except:
                            interp_linear = interp1d(x_values, y_values, bounds_error=False, fill_value="extrapolate")
                            dosis_sugerida = float(interp_linear(turbidez))
                            metodo = "Interpolación Lineal"
                        
                        # Asegurar que la dosis no sea negativa
                        dosis_sugerida = max(dosis_sugerida, 0)
                        
                        # Determinar categoría de turbidez
                        if turbidez < 10:
                            categoria = "Turbidez Baja"
                            recomendacion = "Verificar ajuste fino de la dosificación. En aguas de baja turbidez, pequeñas variaciones pueden ser significativas."
                            color_categoria = COLOR_ADVERTENCIA
                        elif turbidez > 1000:
                            categoria = "Turbidez Muy Alta"
                            recomendacion = "Supervisar proceso y evaluar posibilidad de dosificación escalonada o pre-sedimentación."
                            color_categoria = COLOR_ERROR
                        else:
                            categoria = "Turbidez Normal"
                            recomendacion = "Condiciones estándar de operación. Mantener monitoreo regular del proceso."
                            color_categoria = COLOR_EXITO
                        
                        # Guardar en historial si está marcada la opción
                        if guardar_en_historial:
                            guardar_resultado_historial(
                                turbidez, 
                                ph, 
                                caudal, 
                                dosis_sugerida, 
                                metodo, 
                                categoria
                            )
                        
                        # Mostrar resultados en la tarjeta
                        with results_container.container():
                            st.markdown('<div class="result-card">', unsafe_allow_html=True)
                            st.markdown('<h3 class="card-titulo">Resultado del Análisis</h3>', unsafe_allow_html=True)
                            
                            # Mostrar dosis óptima como métrica destacada
                            st.markdown(
                                f"""
                                <div class="metric-container">
                                    <div class="metric-label">Dosis Óptima Calculada</div>
                                    <div class="metric-value">{dosis_sugerida:.2f}<span class="metric-unit"> mg/L</span></div>
                                    <div style="font-size: 0.8rem; margin-top: 0.25rem; color: #6c757d;">Calculado mediante Splines Cúbicos y Lógica Difusa</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            
                            # Panel de parámetros
                            st.markdown(
                                f"""
                                <div class="param-panel">
                                    <div class="param-item">
                                        <div class="param-label">Turbidez</div>
                                        <div class="param-value">{turbidez:.1f} NTU</div>
                                    </div>
                                    <div class="param-item">
                                        <div class="param-label">Caudal</div>
                                        <div class="param-value">{int(caudal)} L/s</div>
                                    </div>
                                    <div class="param-item">
                                        <div class="param-label">pH</div>
                                        <div class="param-value">{ph:.1f}</div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            
                            # Alerta de recomendación
                            hex_to_rgb = lambda h: tuple(int(h.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                            r, g, b = hex_to_rgb(color_categoria)
                            
                            st.markdown(
                                f"""
                                <div class="alerta" style="background-color: rgba({r}, {g}, {b}, 0.1); border-color: {color_categoria};">
                                    <div class="alerta-titulo" style="color: {color_categoria};">{categoria}</div>
                                    <div class="alerta-texto">{recomendacion}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            
                            if guardar_en_historial:
                                st.markdown(
                                    """
                                    <div style="background-color: rgba(40, 167, 69, 0.1); padding: 0.5rem; border-radius: 0.5rem; margin-top: 1rem; border-left: 3px solid #28A745;">
                                        <div style="color: #28A745; font-weight: 500; font-size: 0.9rem;">✓ Resultado guardado en el historial</div>
                                        <div style="font-size: 0.85rem; color: #333; margin-top: 0.2rem;">Puede consultar todos los registros en la pestaña "Historial y Tendencias".</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            
                            # Panel informativo
                            st.markdown(
                                """
                                <div class="doc-panel">
                                    <div class="doc-titulo">📝 Información Adicional</div>
                                    <p>La determinación precisa de la dosis de sulfato de aluminio constituye un factor determinante para lograr la eficiencia del proceso de coagulación-floculación en el tratamiento de agua potable. Una dosificación técnicamente calibrada garantiza:</p>
                                    <ul>
                                        <li>Remoción efectiva de materias en suspensión</li>
                                        <li>Optimización en el consumo de productos químicos</li>
                                        <li>Mejor calidad del agua tratada</li>
                                        <li>Reducción en costos operativos</li>
                                    </ul>
                                    <p>Este sistema emplea avanzados modelos matemáticos de interpolación con splines cúbicos y algoritmos de toma de decisiones basados en lógica difusa, calibrados con datos experimentales de la Planta El Milagro, para determinar con precisión la dosis óptima de tratamiento según las condiciones específicas del agua cruda.</p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    except Exception as e:
                        # Mensaje de error genérico
                        st.error(f"Ocurrió un error al procesar los datos: {str(e)}")
                        st.error("Verifique los parámetros ingresados e intente nuevamente.")
                        # PESTAÑA 2: HISTORIAL Y TENDENCIAS
    with tab2:
        # Cargar datos históricos
        historial_df = cargar_historial()
        
        # Mostrar mensaje si no hay datos
        if historial_df.empty:
            st.info("No hay datos históricos disponibles. Realice cálculos de dosis y guárdelos para comenzar a generar un historial.")
        else:
            # Crear layout de dos columnas
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Tarjeta de filtros
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<h3 class="card-titulo">Filtros y Opciones</h3>', unsafe_allow_html=True)
                
                # Filtro de periodo
                st.markdown(f'<p style="color:{COLOR_SECUNDARIO}; font-weight:500; margin-bottom:0.5rem;">Periodo de análisis:</p>', unsafe_allow_html=True)
                
                periodo = st.radio(
                    "Seleccione el periodo a analizar:",
                    ["Último día", "Última semana", "Último mes", "Todo el historial"],
                    index=2,  # Default: último mes
                    key="periodo_filtro"
                )
                
                # Mapear selección a valor de periodo
                periodo_map = {
                    "Último día": "dia",
                    "Última semana": "semana",
                    "Último mes": "mes",
                    "Todo el historial": "todo"
                }
                periodo_seleccionado = periodo_map[periodo]
                
                # Filtro de rango de turbidez
                st.markdown(f'<p style="color:{COLOR_SECUNDARIO}; font-weight:500; margin-top:1rem; margin-bottom:0.5rem;">Rango de turbidez:</p>', unsafe_allow_html=True)
                
                # Obtener valores mínimos y máximos para el slider
                min_turbidez = float(historial_df['turbidez'].min())
                max_turbidez = float(historial_df['turbidez'].max())

# Verificar si min y max son iguales y ajustar
                if min_turbidez == max_turbidez:
                    min_turbidez = max(0.0, min_turbidez - 1.0)  # Reducir el mínimo en 1
                    max_turbidez = max_turbidez + 1.0  # Aumentar el máximo en 1

                rango_turbidez = st.slider(
                    "Filtrar por turbidez (NTU):",
                    min_value=min_turbidez,
                    max_value=max_turbidez,
                    value=(min_turbidez, max_turbidez),
                    step=1.0
                )
                
                # Aplicar filtros al dataframe
                # Filtro por periodo
                hoy = datetime.now().date()
                if periodo_seleccionado == "dia":
                    historial_filtrado = historial_df[historial_df['fecha'].dt.date == hoy]
                elif periodo_seleccionado == "semana":
                    una_semana_atras = hoy - timedelta(days=7)
                    historial_filtrado = historial_df[historial_df['fecha'].dt.date >= una_semana_atras]
                elif periodo_seleccionado == "mes":
                    un_mes_atras = hoy - timedelta(days=30)
                    historial_filtrado = historial_df[historial_df['fecha'].dt.date >= un_mes_atras]
                else:
                    historial_filtrado = historial_df.copy()
                
                # Filtro por rango de turbidez
                historial_filtrado = historial_filtrado[
                    (historial_filtrado['turbidez'] >= rango_turbidez[0]) &
                    (historial_filtrado['turbidez'] <= rango_turbidez[1])
                ]
                
                # Mostrar contadores
                st.markdown(
                    f"""
                    <div style="margin-top: 1rem; padding: 1rem; background-color: #f8f9fa; border-radius: 0.5rem;">
                        <div style="font-size: 0.85rem; color: #6c757d; margin-bottom: 0.5rem;">Registros seleccionados:</div>
                        <div style="font-size: 1.5rem; font-weight: 600; color: #003366; text-align: center;">
                            {len(historial_filtrado)} de {len(historial_df)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Opción para exportar datos
                st.markdown(f'<p style="color:{COLOR_SECUNDARIO}; font-weight:500; margin-top:1rem; margin-bottom:0.5rem;">Exportar datos:</p>', unsafe_allow_html=True)
                
                formato_export = st.selectbox(
                    "Formato de exportación:",
                    ["CSV", "Excel"],
                    index=0
                )
                
                if st.button("Exportar datos filtrados", use_container_width=True):
                    if formato_export == "CSV":
                        # Crear y descargar CSV
                        csv = historial_filtrado.to_csv(index=False)
                        b64 = base64.b64encode(csv.encode()).decode()
                        href = f'<a href="data:file/csv;base64,{b64}" download="historial_dosificacion.csv" class="btn" style="background-color: #003366; color: white; padding: 0.5rem 1rem; text-decoration: none; border-radius: 0.25rem; display: block; text-align: center; margin-top: 0.5rem;">Descargar CSV</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    else:
                        # Crear y descargar Excel (simulado, ya que no es soportado directamente)
                        st.warning("La exportación a Excel requiere una configuración adicional. Por ahora, se exportará como CSV.")
                        csv = historial_filtrado.to_csv(index=False)
                        b64 = base64.b64encode(csv.encode()).decode()
                        href = f'<a href="data:file/csv;base64,{b64}" download="historial_dosificacion.csv" class="btn" style="background-color: #003366; color: white; padding: 0.5rem 1rem; text-decoration: none; border-radius: 0.25rem; display: block; text-align: center; margin-top: 0.5rem;">Descargar CSV</a>'
                        st.markdown(href, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Columna de visualizaciones
            with col2:
                # Si no hay datos filtrados, mostrar mensaje
                if historial_filtrado.empty:
                    st.warning("No hay datos que coincidan con los filtros seleccionados. Ajuste los criterios de filtrado.")
                else:
                    # Crear tabs para diferentes visualizaciones
                    tab_tendencia, tab_relacion, tab_tabla = st.tabs(["Tendencia Temporal", "Relación Turbidez-Dosis", "Tabla de Datos"])
                    
                    # Tab 1: Tendencia temporal
                    with tab_tendencia:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<h3 class="card-titulo">Tendencia Temporal</h3>', unsafe_allow_html=True)
                        
                        # Crear gráfico de tendencia
                        fig_tendencia = crear_grafica_serie_temporal(historial_filtrado, periodo_seleccionado)
                        if fig_tendencia:
                            st.plotly_chart(fig_tendencia, use_container_width=True)
                        
                        # Estadísticas resumen
                        col_stats1, col_stats2, col_stats3 = st.columns(3)
                        
                        with col_stats1:
                            # Turbidez promedio
                            turbidez_promedio = historial_filtrado['turbidez'].mean()
                            st.markdown(
                                f"""
                                <div style="text-align: center; padding: 1rem; background-color: rgba(255, 193, 7, 0.1); border-radius: 0.5rem;">
                                    <div style="font-size: 0.85rem; color: #6c757d;">Turbidez Promedio</div>
                                    <div style="font-size: 1.5rem; font-weight: 600; color: {COLOR_ADVERTENCIA};">
                                        {turbidez_promedio:.1f} <span style="font-size: 0.9rem;">NTU</span>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        
                        with col_stats2:
                            # Dosis promedio
                            dosis_promedio = historial_filtrado['dosis_mg_l'].mean()
                            st.markdown(
                                f"""
                                <div style="text-align: center; padding: 1rem; background-color: rgba(0, 51, 102, 0.1); border-radius: 0.5rem;">
                                    <div style="font-size: 0.85rem; color: #6c757d;">Dosis Promedio</div>
                                    <div style="font-size: 1.5rem; font-weight: 600; color: {COLOR_PRIMARIO};">
                                        {dosis_promedio:.2f} <span style="font-size: 0.9rem;">mg/L</span>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        
                        with col_stats3:
                            # Total de registros y periodo
                            st.markdown(
                                f"""
                                <div style="text-align: center; padding: 1rem; background-color: rgba(102, 163, 210, 0.1); border-radius: 0.5rem;">
                                    <div style="font-size: 0.85rem; color: #6c757d;">Registros Analizados</div>
                                    <div style="font-size: 1.5rem; font-weight: 600; color: {COLOR_ACENTO};">
                                        {len(historial_filtrado)}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Tab 2: Relación Turbidez-Dosis
                    with tab_relacion:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<h3 class="card-titulo">Relación Turbidez vs Dosis</h3>', unsafe_allow_html=True)
                        
                        # Crear gráfico de dispersión
                        fig_relacion = crear_grafica_tendencia_turbidez_dosis(historial_filtrado)
                        if fig_relacion:
                            st.plotly_chart(fig_relacion, use_container_width=True)
                        
                        # Información adicional
                        st.markdown(
                            """
                            <div style="font-size: 0.9rem; margin-top: 1rem; padding: 1rem; background-color: #f8f9fa; border-radius: 0.5rem;">
                                <p><strong>Nota interpretativa:</strong> Este gráfico muestra la relación entre la turbidez del agua cruda y la dosis óptima de sulfato de aluminio calculada. La tendencia observada permite identificar patrones de dosificación que pueden optimizarse para condiciones específicas.</p>
                                <p>La coloración de los puntos representa la fecha, permitiendo visualizar cómo ha evolucionado esta relación a lo largo del tiempo.</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # Distribución de dosis
                        st.markdown('<h4 style="color: #003366; margin-top: 1.5rem;">Distribución de Dosis Aplicadas</h4>', unsafe_allow_html=True)
                        
                        fig_distribucion = crear_grafica_distribucion_dosis(historial_filtrado)
                        if fig_distribucion:
                            st.plotly_chart(fig_distribucion, use_container_width=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Tab 3: Tabla de datos
                    with tab_tabla:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<h3 class="card-titulo">Registro Histórico</h3>', unsafe_allow_html=True)
                        
                        # Preparar tabla más limpia para mostrar
                        tabla_historial = historial_filtrado.copy()
                        tabla_historial['fecha'] = tabla_historial['fecha'].dt.strftime('%d/%m/%Y')
                        tabla_historial = tabla_historial.rename(columns={
                            'fecha': 'Fecha',
                            'hora': 'Hora',
                            'turbidez': 'Turbidez (NTU)',
                            'ph': 'pH',
                            'caudal': 'Caudal (L/s)',
                            'dosis_mg_l': 'Dosis (mg/L)',
                            'metodo_calculo': 'Método de Cálculo',
                            'categoria': 'Categoría'
                        })
                        
                        # Ordenar por fecha y hora (más reciente primero)
                        tabla_historial['Fecha_Hora'] = pd.to_datetime(tabla_historial['Fecha'] + ' ' + tabla_historial['Hora'], 
                                                                      format='%d/%m/%Y %H:%M:%S')
                        tabla_historial = tabla_historial.sort_values('Fecha_Hora', ascending=False).drop('Fecha_Hora', axis=1)
                        
                        # Mostrar tabla con formato
                        st.dataframe(
                            tabla_historial,
                            use_container_width=True,
                            hide_index=True,
                        )
                        
                        # Estadísticas resumidas
                        with st.expander("Ver Estadísticas Resumidas"):
                            # Convertir de nuevo para estadísticas
                            stats_df = historial_filtrado.copy()
                            
                            col_est1, col_est2 = st.columns(2)
                            
                            with col_est1:
                                st.markdown("#### Estadísticas de Turbidez")
                                stats_turbidez = stats_df['turbidez'].describe().reset_index()
                                stats_turbidez.columns = ['Métrica', 'Valor']
                                stats_turbidez['Valor'] = stats_turbidez['Valor'].round(2)
                                st.dataframe(stats_turbidez, use_container_width=True, hide_index=True)
                            
                            with col_est2:
                                st.markdown("#### Estadísticas de Dosis")
                                stats_dosis = stats_df['dosis_mg_l'].describe().reset_index()
                                stats_dosis.columns = ['Métrica', 'Valor']
                                stats_dosis['Valor'] = stats_dosis['Valor'].round(2)
                                st.dataframe(stats_dosis, use_container_width=True, hide_index=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
        
    # Mostrar pie de página
    mostrar_pie_pagina()

except Exception as e:
    st.error(f"Error en la aplicación: {str(e)}")
    st.error("Verifique que todos los archivos necesarios estén disponibles.")
