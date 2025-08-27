import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import numpy as np

# 🎨 CONFIGURACIÓN PÁGINA
st.set_page_config(
    page_title="🗺️ IA Sindical Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔑 CONFIGURACIÓN API AIRTABLE
AIRTABLE_TOKEN = "patwjlairfW69N772.582cebb38958f780cd2d438f68a94409ffad6b4d6cab862573c88dcd66c8a420"
BASE_ID = "appcAG3ImhfeNL6UW"
TABLE_NAME = "Casos IA Sindical"
# 🌍 COORDENADAS MUNDIALES COMPLETAS
COORDENADAS_PAISES = {
    'España': [40.4168, -3.7038],
    'Francia': [46.6034, 1.8883],
    'Alemania': [51.1657, 10.4515],
    'Reino Unido': [55.3781, -3.4360],
    'Italia': [41.8719, 12.5674],
    'Brasil': [-14.2350, -51.9253],
    'Estados Unidos': [37.0902, -95.7129],
    'Canadá': [56.1304, -106.3468],
    'Australia': [-25.2744, 133.7751],
    'Japón': [36.2048, 138.2529],
    'China': [35.8617, 104.1954],
    'India': [20.5937, 78.9629],
    'México': [23.6345, -102.5528],
    'Argentina': [-38.4161, -63.6167],
    'Chile': [-35.6751, -71.5430],
    'Colombia': [4.5709, -74.2973],
    'Perú': [-9.1900, -75.0152],
    'Suecia': [60.1282, 18.6435],
    'Noruega': [60.4720, 8.4689],
    'Dinamarca': [56.2639, 9.5018],
    'Países Bajos': [52.1326, 5.2913],
    'Portugal': [39.3999, -8.2245],
    'Grecia': [39.0742, 21.8243],
    'Polonia': [51.9194, 19.1451],
    'Turquía': [38.9637, 35.2433],
    'Rusia': [61.5240, 105.3188],
    'Sudáfrica': [-30.5595, 22.9375],
    'Nigeria': [9.0820, 8.6753],
    'Kenia': [-0.0236, 37.9062],
    'Egipto': [26.0975, 30.0444],
    'Marruecos': [31.7917, -7.0926],
    'Corea del Sur': [35.9078, 127.7669],
    'Tailandia': [15.8700, 100.9925],
    'Vietnam': [14.0583, 108.2772],
    'Indonesia': [-0.7893, 113.9213],
    'Filipinas': [12.8797, 121.7740],
    'Nueva Zelanda': [-40.9006, 174.8860],
    'Irlanda': [53.4129, -8.2439],
    'Bélgica': [50.5039, 4.4699],
    'Suiza': [46.8182, 8.2275],
    'Austria': [47.5162, 14.5501],
    'Finlandia': [61.9241, 25.7482],
    'Islandia': [64.9631, -19.0208],
    'Luxemburgo': [49.8153, 6.1296],
    'Malta': [35.9375, 14.3754],
    'Chipre': [35.1264, 33.4299],
    'Estonia': [58.5953, 25.0136],
    'Letonia': [56.8796, 24.6032],
    'Lituania': [55.1694, 23.8813],
    'República Checa': [49.8175, 15.4730],
    'Eslovaquia': [48.6690, 19.6990],
    'Hungría': [47.1625, 19.5033],
    'Eslovenia': [46.1512, 14.9955],
    'Croacia': [45.1000, 15.2000],
    'Serbia': [44.0165, 21.0059],
    'Bosnia y Herzegovina': [43.9159, 17.6791],
    'Montenegro': [42.7087, 19.3744],
    'Macedonia del Norte': [41.6086, 21.7453],
    'Albania': [41.1533, 20.1683],
    'Bulgaria': [42.7339, 25.4858],
    'Rumania': [45.9432, 24.9668],
    'Moldavia': [47.4116, 28.3699],
    'Ucrania': [48.3794, 31.1656],
    'Bielorrusia': [53.7098, 27.9534]
}

# 🛡️ FUNCIÓN LIMPIAR DATOS
def clean_data_value(value):
    """Limpia valores problemáticos para pandas"""
    if value is None:
        return 'No especificado'
    elif isinstance(value, (list, dict)):
        return str(value)
    elif isinstance(value, str):
        return value.strip() if value.strip() else 'No especificado'
    else:
        return str(value)

# 🛡️ FUNCIÓN OBTENER VALORES ÚNICOS SEGUROS
def get_safe_unique_values(series):
    """Obtiene valores únicos de forma segura, manejando errores"""
    try:
        # Limpiar la serie primero
        cleaned_series = series.apply(clean_data_value)
        # Eliminar valores nulos
        cleaned_series = cleaned_series.dropna()
        # Obtener valores únicos
        unique_values = cleaned_series.unique()
        # Convertir a lista y ordenar
        return sorted([str(val) for val in unique_values if val != 'No especificado'])
    except Exception as e:
        st.warning(f"⚠️ Error procesando valores únicos: {str(e)}")
        return ['No especificado']

# 🎯 FUNCIÓN OBTENER DATOS AIRTABLE (CORREGIDA CON MANEJO DE ERRORES)
@st.cache_data(ttl=300)
def get_airtable_data():
    """Obtiene datos de Airtable con manejo completo de errores y limpieza de datos"""
    try:
        url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
        headers = {
            "Authorization": f"Bearer {AIRTABLE_TOKEN}",
            "Content-Type": "application/json"
        }
        
        all_records = []
        offset = None
        
        # Paginación automática
        while True:
            params = {}
            if offset:
                params['offset'] = offset
                
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                st.error(f"❌ Error conexión Airtable: {response.status_code}")
                st.error(f"Detalle: {response.text}")
                return pd.DataFrame()
            
            data = response.json()
            all_records.extend(data['records'])
            
            # Verificar si hay más páginas
            if 'offset' in data:
                offset = data['offset']
            else:
                break
        
        if not all_records:
            st.warning("⚠️ No se encontraron registros en Airtable")
            return pd.DataFrame()
        
        # Procesar datos con limpieza
        casos_procesados = []
        for record in all_records:
            fields = record['fields']
            pais = clean_data_value(fields.get('País', 'No especificado'))
            
            # Obtener coordenadas
            if pais in COORDENADAS_PAISES:
                lat, lon = COORDENADAS_PAISES[pais]
            else:
                lat, lon = 0, 0
            
            caso = {
                'ID': record['id'],
                'Título': clean_data_value(fields.get('Título', 'Sin título')),
                'País': pais,
                'Organización': clean_data_value(fields.get('Organización Sindical', 'No especificada')),
                'Actores Involucrados': clean_data_value(fields.get('Actores Involucrados', 'No especificados')),
                'Sector Productivo': clean_data_value(fields.get('Sector Productivo', 'No especificado')),
                'Tipo de IA': clean_data_value(fields.get('Tipo de IA', 'No especificado')),
                'Aplicación Específica': clean_data_value(fields.get('Aplicación Específica', 'No especificada')),
                'Fecha': clean_data_value(fields.get('Fecha', 'No especificada')),
                'Estado': clean_data_value(fields.get('Estado del Caso', 'No especificado')),
                'Impacto': clean_data_value(fields.get('Impacto/Resultado', 'No especificado')),
                'Retos y Limitaciones': clean_data_value(fields.get('Retos y Limitaciones', 'No especificados')),
                'Fuente': clean_data_value(fields.get('Fuente', 'No especificada')),
                'URL': clean_data_value(fields.get('URL', 'No disponible')),
                'Contacto': clean_data_value(fields.get('Contacto', 'No disponible')),
                'Notas': clean_data_value(fields.get('Notas', 'Sin notas')),
                'Temática': clean_data_value(fields.get('Temática', 'No especificada')),
                'Latitud': lat,
                'Longitud': lon,
                'Fecha_Creación': record.get('createdTime', 'No disponible')
            }
            casos_procesados.append(caso)
        
        df = pd.DataFrame(casos_procesados)
        
        # Verificar que el DataFrame no esté vacío
        if df.empty:
            st.warning("⚠️ DataFrame vacío después del procesamiento")
            return pd.DataFrame()
        
        # Limpiar datos adicionales
        for col in df.columns:
            if col not in ['Latitud', 'Longitud']:
                df[col] = df[col].apply(clean_data_value)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        return pd.DataFrame()

# 🎯 FUNCIÓN CREAR GRÁFICOS (CORREGIDA)
def crear_graficos(df):
    """Crear gráficos estadísticos con manejo de errores"""
    if df.empty:
        return None, None, None
    
    try:
        # Gráfico por país
        pais_counts = df['País'].value_counts().head(10)
        fig_pais = px.bar(
            x=pais_counts.values,
            y=pais_counts.index,
            orientation='h',
            title="📊 Casos por País (Top 10)",
            labels={'x': 'Número de Casos', 'y': 'País'},
            color=pais_counts.values,
            color_continuous_scale='Blues'
        )
        fig_pais.update_layout(height=400)
        
        # Gráfico por tipo de IA
        tipo_counts = df['Tipo de IA'].value_counts()
        fig_tipo = px.pie(
            values=tipo_counts.values,
            names=tipo_counts.index,
            title="🤖 Distribución por Tipo de IA",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        # Gráfico por estado
        estado_counts = df['Estado'].value_counts()
        fig_estado = px.bar(
            x=estado_counts.index,
            y=estado_counts.values,
            title="📈 Estados de los Casos",
            labels={'y': 'Número de Casos', 'x': 'Estado'},
            color=estado_counts.values,
            color_continuous_scale='Greens'
        )
        fig_estado.update_xaxes(tickangle=45)
        
        return fig_pais, fig_tipo, fig_estado
        
    except Exception as e:
        st.error(f"❌ Error creando gráficos: {str(e)}")
        return None, None, None

# 🎯 APLICACIÓN PRINCIPAL
def main():
    # HEADER CON MÉTRICAS
    st.title("🗺️ IA Sindical Dashboard - Análisis Completo")
    st.markdown("**Dashboard interactivo con filtros avanzados y actualización automática**")
    
    # Obtener datos
    with st.spinner("🔄 Cargando datos desde Airtable..."):
        df = get_airtable_data()
    
    if df.empty:
        st.error("❌ No se pudieron cargar los datos. Verifica la conexión con Airtable.")
        st.stop()
    
    # MÉTRICAS PRINCIPALES
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Casos", len(df))
    with col2:
        st.metric("🌍 Países", df['País'].nunique())
    with col3:
        st.metric("🏢 Organizaciones", df['Organización'].nunique())
    with col4:
        casos_activos = len(df[df['Estado'].str.contains('Activo|En curso|Implementado', case=False, na=False)])
        st.metric("🚀 Casos Activos", casos_activos)
    
    # SIDEBAR FILTROS AVANZADOS CON MANEJO DE ERRORES
    st.sidebar.header("🔍 Filtros Avanzados")
    
    try:
        # Filtro por país
        paises_disponibles = ['Todos'] + get_safe_unique_values(df['País'])
        paises_seleccionados = st.sidebar.multiselect(
            "🌍 País", 
            paises_disponibles,
            default=['Todos']
        )
        
        # Filtro por aplicación
        aplicaciones = ['Todos'] + get_safe_unique_values(df['Aplicación Específica'])
        aplicaciones_seleccionadas = st.sidebar.multiselect(
            "🎯 Aplicación Específica",
            aplicaciones,
            default=['Todos']
        )
        
        # Filtro por estado
        estados = ['Todos'] + get_safe_unique_values(df['Estado'])
        estados_seleccionados = st.sidebar.multiselect(
            "📊 Estado del Caso",
            estados,
            default=['Todos']
        )
        
        # Filtro por tipo de IA
        tipos_ia = ['Todos'] + get_safe_unique_values(df['Tipo de IA'])
        tipos_seleccionados = st.sidebar.multiselect(
            "🤖 Tipo de IA",
            tipos_ia,
            default=['Todos']
        )
        
        # Filtro por sector
        sectores = ['Todos'] + get_safe_unique_values(df['Sector Productivo'])
        sectores_seleccionados = st.sidebar.multiselect(
            "🏭 Sector Productivo",
            sectores,
            default=['Todos']
        )
        
    except Exception as e:
        st.sidebar.error(f"❌ Error en filtros: {str(e)}")
        st.stop()
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    try:
        if 'Todos' not in paises_seleccionados:
            df_filtrado = df_filtrado[df_filtrado['País'].isin(paises_seleccionados)]
        
        if 'Todos' not in aplicaciones_seleccionadas:
            df_filtrado = df_filtrado[df_filtrado['Aplicación Específica'].isin(aplicaciones_seleccionadas)]
        
        if 'Todos' not in estados_seleccionados:
            df_filtrado = df_filtrado[df_filtrado['Estado'].isin(estados_seleccionados)]
        
        if 'Todos' not in tipos_seleccionados:
            df_filtrado = df_filtrado[df_filtrado['Tipo de IA'].isin(tipos_seleccionados)]
        
        if 'Todos' not in sectores_seleccionados:
            df_filtrado = df_filtrado[df_filtrado['Sector Productivo'].isin(sectores_seleccionados)]
            
    except Exception as e:
        st.error(f"❌ Error aplicando filtros: {str(e)}")
        df_filtrado = df.copy()
    
    # ESTADÍSTICAS SIDEBAR
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Resumen Filtrado")
    st.sidebar.metric("🎯 Mostrando", f"{len(df_filtrado)}/{len(df)}")
    
    if not df_filtrado.empty:
        st.sidebar.metric("🌍 Países Filtrados", df_filtrado['País'].nunique())
        
        try:
            st.sidebar.markdown("**📊 Top Estados:**")
            estados_count = df_filtrado['Estado'].value_counts()
            for estado, count in estados_count.head(3).items():
                porcentaje = (count / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
                st.sidebar.text(f"• {estado}: {count} ({porcentaje:.0f}%)")
            
            st.sidebar.markdown("**🎯 Top Aplicaciones:**")
            apps_count = df_filtrado['Aplicación Específica'].value_counts()
            for app, count in apps_count.head(2).items():
                porcentaje = (count / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
                st.sidebar.text(f"• {app[:20]}...: {porcentaje:.0f}%")
        except Exception as e:
            st.sidebar.warning(f"⚠️ Error en estadísticas: {str(e)}")
    
    # BOTÓN LIMPIAR FILTROS
    if st.sidebar.button("🔄 Limpiar Todos los Filtros"):
        st.experimental_rerun()
    
    # LAYOUT PRINCIPAL
    tab1, tab2, tab3 = st.tabs(["🗺️ Mapa Interactivo", "📊 Análisis Estadístico", "📋 Datos Detallados"])
    
    # TAB 1: MAPA INTERACTIVO
    with tab1:
        st.subheader("🗺️ Mapa Mundial Interactivo")
        
        if not df_filtrado.empty:
            try:
                # Crear mapa
                m = folium.Map(location=[20, 0], zoom_start=2)
                
                # Colores por tipo de IA
                colores = {
                    'Machine Learning': 'blue',
                    'Inteligencia Artificial': 'red',
                    'Automatización': 'green',
                    'Análisis de Datos': 'orange',
                    'Deep Learning': 'purple',
                    'NLP': 'pink',
                    'Computer Vision': 'gray',
                    'Robótica': 'darkgreen',
                    'No especificado': 'black'
                }
                
                # Agregar marcadores
                for _, caso in df_filtrado.iterrows():
                    if caso['Latitud'] != 0 and caso['Longitud'] != 0:
                        color = colores.get(caso['Tipo de IA'], 'black')
                        
                        popup_html = f"""
                        <div style="width: 350px; font-family: Arial; font-size: 12px;">
                            <h4 style="color: #2E86AB; margin-bottom: 8px; font-size: 14px;">{caso['Título']}</h4>
                            <p><strong>🌍 País:</strong> {caso['País']}</p>
                            <p><strong>🏢 Organización:</strong> {caso['Organización']}</p>
                            <p><strong>🤖 Tipo IA:</strong> {caso['Tipo de IA']}</p>
                            <p><strong>⚙️ Aplicación:</strong> {caso['Aplicación Específica']}</p>
                            <p><strong>🏭 Sector:</strong> {caso['Sector Productivo']}</p>
                            <p><strong>📊 Estado:</strong> {caso['Estado']}</p>
                            <p><strong>📅 Fecha:</strong> {caso['Fecha']}</p>
                            <p><strong>👥 Actores:</strong> {caso['Actores Involucrados'][:100]}...</p>
                            <p><strong>💡 Impacto:</strong> {caso['Impacto'][:100]}...</p>
                            <p><strong>⚠️ Retos:</strong> {caso['Retos y Limitaciones'][:100]}...</p>
                            <p><strong>📞 Contacto:</strong> {caso['Contacto']}</p>
                            <p><strong>📚 Fuente:</strong> {caso['Fuente']}</p>
                            <p><strong>🏷️ Temática:</strong> {caso['Temática']}</p>
                            {f'<p><strong>🔗 URL:</strong> <a href="{caso["URL"]}" target="_blank">Ver más</a></p>' if caso['URL'] != 'No disponible' else ''}
                        </div>
                        """
                        
                        folium.Marker(
                            location=[caso['Latitud'], caso['Longitud']],
                            popup=folium.Popup(popup_html, max_width=400),
                            tooltip=f"{caso['Título']} - {caso['País']}",
                            icon=folium.Icon(color=color, icon='info-sign')
                        ).add_to(m)
                
                # Mostrar mapa
                map_data = st_folium(m, width=700, height=500)
                
                # Información del mapa
                st.info(f"🗺️ Mostrando {len(df_filtrado)} casos en el mapa")
                
            except Exception as e:
                st.error(f"❌ Error creando mapa: {str(e)}")
                
        else:
            st.info("🗺️ Selecciona filtros para ver casos en el mapa")
    
    # TAB 2: ANÁLISIS ESTADÍSTICO
    with tab2:
        st.subheader("📊 Análisis Estadístico Completo")
        
        if not df_filtrado.empty:
            try:
                # Crear gráficos
                fig_pais, fig_tipo, fig_estado = crear_graficos(df_filtrado)
                
                # Mostrar gráficos en columnas
                col1, col2 = st.columns(2)
                
                with col1:
                    if fig_pais:
                        st.plotly_chart(fig_pais, use_container_width=True)
                    if fig_estado:
                        st.plotly_chart(fig_estado, use_container_width=True)
                
                with col2:
                    if fig_tipo:
                        st.plotly_chart(fig_tipo, use_container_width=True)
                    
                    # Métricas adicionales
                    st.subheader("📈 Métricas Clave")
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.metric("📊 Casos Filtrados", len(df_filtrado))
                        st.metric("🌍 Países Únicos", df_filtrado['País'].nunique())
                    with col_m2:
                        st.metric("🏢 Organizaciones", df_filtrado['Organización'].nunique())
                        st.metric("🎯 Aplicaciones", df_filtrado['Aplicación Específica'].nunique())
                
                # Tabla de frecuencias
                st.subheader("📋 Análisis de Frecuencias")
                col_freq1, col_freq2 = st.columns(2)
                
                with col_freq1:
                    st.write("**🌍 Top 5 Países:**")
                    paises_freq = df_filtrado['País'].value_counts().head(5)
                    st.dataframe(paises_freq.to_frame('Casos'))
                    
                    st.write("**🤖 Tipos de IA:**")
                    tipos_freq = df_filtrado['Tipo de IA'].value_counts()
                    st.dataframe(tipos_freq.to_frame('Casos'))
                
                with col_freq2:
                    st.write("**📊 Estados:**")
                    estados_freq = df_filtrado['Estado'].value_counts()
                    st.dataframe(estados_freq.to_frame('Casos'))
                    
                    st.write("**🏭 Sectores:**")
                    sectores_freq = df_filtrado['Sector Productivo'].value_counts().head(5)
                    st.dataframe(sectores_freq.to_frame('Casos'))
                    
            except Exception as e:
                st.error(f"❌ Error en análisis estadístico: {str(e)}")
        
        else:
            st.info("📊 Selecciona filtros para ver análisis estadístico")
    
    # TAB 3: DATOS DETALLADOS
    with tab3:
        st.subheader("📋 Tabla de Datos Completa")
        
        if not df_filtrado.empty:
            try:
                # Selector de columnas
                todas_columnas = df_filtrado.columns.tolist()
                columnas_por_defecto = ['Título', 'País', 'Organización', 'Tipo de IA', 'Estado', 'Fecha']
                columnas_seleccionadas = st.multiselect(
                    "📋 Seleccionar columnas a mostrar:",
                    todas_columnas,
                    default=columnas_por_defecto
                )
                
                if columnas_seleccionadas:
                    df_display = df_filtrado[columnas_seleccionadas].copy()
                    st.dataframe(df_display, use_container_width=True, height=400)
                    
                    # Botones de exportación
                    col_exp1, col_exp2, col_exp3 = st.columns(3)
                    
                    with col_exp1:
                        csv = df_filtrado.to_csv(index=False)
                        st.download_button(
                            label="📤 Exportar CSV Completo",
                            data=csv,
                            file_name=f"casos_ia_sindical_completo_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv"
                        )
                    
                    with col_exp2:
                        csv_filtrado = df_display.to_csv(index=False)
                        st.download_button(
                            label="📤 Exportar CSV Filtrado",
                            data=csv_filtrado,
                            file_name=f"casos_ia_sindical_filtrado_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv"
                        )
                    
                    with col_exp3:
                        json_data = df_filtrado.to_json(orient='records', indent=2)
                        st.download_button(
                            label="📤 Exportar JSON",
                            data=json_data,
                            file_name=f"casos_ia_sindical_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                            mime="application/json"
                        )
                    
                    # Búsqueda en texto
                    st.subheader("🔍 Búsqueda en Contenido")
                    busqueda = st.text_input("Buscar en títulos, organizaciones, notas...")
                    
                    if busqueda:
                        mask = (
                            df_filtrado['Título'].str.contains(busqueda, case=False, na=False) |
                            df_filtrado['Organización'].str.contains(busqueda, case=False, na=False) |
                            df_filtrado['Notas'].str.contains(busqueda, case=False, na=False) |
                            df_filtrado['Impacto'].str.contains(bus
