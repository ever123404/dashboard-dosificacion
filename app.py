import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import splrep, splev, interp1d
import os
import time
from datetime import datetime
import base64

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

# Función para cargar imágenes base64 (solución para el problema de los logos)
def get_base64_encoded_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# Intentar cargar logos como base64
logo_unc_path = os.path.join("data/images", "logo_unc.png")
logo_posgrado_path = os.path.join("data/images", "logo_escuela_posgrado.png")

logo_unc_base64 = get_base64_encoded_image(logo_unc_path)
logo_posgrado_base64 = get_base64_encoded_image(logo_posgrado_path)

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
    
    .header-titulo {
        color: white;
        text-align: center;
        font-size: 2rem;
    }
    
    .header-subtitulo {
        color: rgba(255,255,255,0.9);
        text-align: center;
        font-weight: 300;
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

# Rutas de carpetas
DATA_DIR = "data"
IMAGES_DIR = "images"

try:
    # Cargar datos
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
    
    data = load_data()
    
    # Verificar si hay datos después de la limpieza
    if data.empty:
        st.error("No hay datos válidos en el archivo CSV después de eliminar valores no numéricos.")
        st.stop()

    # Encabezado sin logos
    st.markdown(
        """
        <div class="header-container">
            <h1 class="header-titulo">Sistema de Dosificación Óptima</h1>
            <h3 class="header-subtitulo">Universidad Nacional de Cajamarca • Planta de Tratamiento El Milagro • EPS SEDACAJ S.A.</h3>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Contenedor principal
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
                    mediante interpolación por splines cúbicos basado en datos experimentales.
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
                                <div style="font-size: 0.8rem; margin-top: 0.25rem; color: #6c757d;">Calculado mediante {metodo}</div>
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
                        
                        # Panel informativo
                        st.markdown(
                            """
                            <div class="doc-panel">
                                <div class="doc-titulo">📝 Información Adicional</div>
                                <p>La dosificación óptima de sulfato de aluminio es crucial para lograr una efectiva coagulación-floculación en el tratamiento de agua potable. Una dosificación adecuada garantiza:</p>
                                <ul>
                                    <li>Remoción efectiva de materias en suspensión</li>
                                    <li>Optimización en el consumo de productos químicos</li>
                                    <li>Mejor calidad del agua tratada</li>
                                    <li>Reducción en costos operativos</li>
                                </ul>
                                <p>Este sistema utiliza modelos matemáticos de interpolación basados en datos experimentales de la Planta El Milagro para determinar la dosis óptima según las condiciones específicas del agua cruda.</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                
                except Exception as e:
                    # Mensaje de error genérico
                    st.error("Ocurrió un error al procesar los datos. Verifique los parámetros ingresados e intente nuevamente.")
    
    # Pie de página profesional
    st.markdown(
        """
        <div class="footer">
            <div style="font-weight: 600; margin-bottom: 0.5rem; font-size: 1.2rem;">Sistema de Dosificación Óptima de Sulfato de Aluminio</div>
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap; margin: 1.5rem 0;">
                <div style="padding: 0 1rem; text-align: center;">
                    <div style="font-size: 0.9rem; color: rgba(255,255,255,0.7); margin-bottom: 0.3rem;">Autor</div>
                    <div style="font-size: 1.1rem; font-weight: 500;">Ever Rojas Huamán</div>
                </div>
                <div style="padding: 0 1rem; text-align: center;">
                    <div style="font-size: 0.9rem; color: rgba(255,255,255,0.7); margin-bottom: 0.3rem;">Asesor</div>
                    <div style="font-size: 1.1rem; font-weight: 500;">Dr. Glicerio Eduardo Torres Carranza</div>
                </div>
            </div>
            <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 1rem;">Universidad Nacional de Cajamarca - Escuela de Posgrado, 2025</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
except Exception as e:
    st.error(f"Error general en la aplicación: {str(e)}")
    st.error("Verifique que todos los archivos necesarios estén disponibles.")