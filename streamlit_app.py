
import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
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

# 🛡️ FUNCIÓN LIMPIAR DATOS SIMPLE
def clean_value(value):
    """Limpia un valor de forma simple y segura"""
    if pd.isna(value) or value is None:
        return 'No especificado'
    if isinstance(value, (list, dict)):
        return 'No especificado'
    return str(value).strip() if str(value).strip() else 'No especificado'

# 🎯 FUNCIÓN OBTENER DATOS AIRTABLE (SIMPLIFICADA)
@st.cache_data(ttl=300)
def get_airtable_data():
    """Obtiene datos de Airtable con manejo robusto de errores"""
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
                return pd.DataFrame()
            
            data = response.json()
            all_records.extend(data['records'])
            
            if 'offset' in data:
                offset = data['offset']
            else:
                break
        
        if not all_records:
            st.warning("⚠️ No se encontraron registros en Airtable")
            return pd.DataFrame()
        
        # Procesar datos de forma simple
        casos_procesados = []
        for record in all_records:
            fields = record.get('fields', {})
            
            # Limpiar país y obtener coordenadas
            pais = clean_value(fields.get('País'))
            if pais in COORDENADAS_PAISES:
                lat, lon = COORDENADAS_PAISES[pais]
            else:
                lat, lon = 0, 0
            
            # Crear registro limpio
            caso = {
                'ID': record.get('id', 'Sin ID'),
                'Título': clean_value(fields.get('Título')),
                'País': pais,
                'Organización': clean_value(fields.get('Organización Sindical')),
                'Actores Involucrados': clean_value(fields.get('Actores Involucrados')),
                'Sector Productivo': clean_value(fields.get('Sector Productivo')),
                'Tipo de IA': clean_value(fields.get('Tipo de IA')),
                'Aplicación Específica': clean_value(fields.get('Aplicación Específica')),
                'Fecha': clean_value(fields.get('Fecha')),
                'Estado': clean_value(fields.get('Estado del Caso')),
                'Impacto': clean_value(fields.get('Impacto/Resultado')),
                'Retos y Limitaciones': clean_value(fields.get('Retos y Limitaciones')),
                'Fuente': clean_value(fields.get('Fuente')),
                'URL': clean_value(fields.get('URL')),
                'Contacto': clean_value(fields.get('Contacto')),
                'Notas': clean_value(fields.get('Notas')),
                'Temática': clean_value(fields.get('Temática')),
                'Latitud': lat,
                'Longitud': lon,
                'Fecha_Creación': record.get('createdTime', 'No disponible')
            }
            casos_procesados.append(caso)
        
        df = pd.DataFrame(casos_procesados)
        
        # Verificación final
        if df.empty:
            st.warning("⚠️ DataFrame vacío después del procesamiento")
            return pd.DataFrame()
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        return pd.DataFrame()

# 🛡️ FUNCIÓN OBTENER VALORES ÚNICOS SEGUROS (SIMPLIFICADA)
def get_unique_values_safe(df, column):
    """Obtiene valores únicos de forma completamente segura"""
    try:
        if column not in df.columns:
            return ['No especificado']
        
        # Filtrar valores válidos
        valid_values = []
        for value in df[column]:
            cleaned = clean_value(value)
            if cleaned != 'No especificado':
                valid_values.append(cleaned)
        
        # Obtener únicos y ordenar
        unique_values = list(set(valid_values))
        return sorted(unique_values) if unique_values else ['No especificado']
        
    except Exception as e:
        st.warning(f"⚠️ Error procesando columna {column}: {str(e)}")
        return ['No especificado']

# 🎯 APLICACIÓN PRINCIPAL
def main():
    # HEADER
    st.title("🗺️ IA Sindical Dashboard - Análisis Completo")
    st.markdown("**Dashboard interactivo con filtros avanzados y actualización automática**")
    
    # Obtener datos
    with st.spinner("🔄 Cargando datos desde Airtable..."):
        df = get_airtable_data()
    
    if df.empty:
        st.error("❌ No se pudieron cargar los datos. Verifica la conexión con Airtable.")
        st.stop()
    
    # MÉTRICAS PRINCIPALES (LÍNEA 278 CORREGIDA)
    try:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Casos", len(df))
        with col2:
            st.metric("🌍 Países", len(get_unique_values_safe(df, 'País')))
        with col3:
            st.metric("🏢 Organizaciones", len(get_unique_values_safe(df, 'Organización')))
        with col4:
            # Contar casos activos de forma segura
            casos_activos = 0
            for estado in df['Estado']:
                estado_clean = clean_value(estado).lower()
                if any(word in estado_clean for word in ['activo', 'en curso', 'implementado', 'vigente']):
                    casos_activos += 1
            st.metric("🚀 Casos Activos", casos_activos)
    except Exception as e:
        st.error(f"❌ Error en métricas: {str(e)}")
    
    # SIDEBAR FILTROS SIMPLIFICADOS
    st.sidebar.header("🔍 Filtros Avanzados")
    
    try:
        # Filtro por país
        paises_disponibles = ['Todos'] + get_unique_values_safe(df, 'País')
        paises_seleccionados = st.sidebar.multiselect(
            "🌍 País", 
            paises_disponibles,
            default=['Todos']
        )
        
        # Filtro por tipo de IA
        tipos_ia = ['Todos'] + get_unique_values_safe(df, 'Tipo de IA')
        tipos_seleccionados = st.sidebar.multiselect(
            "🤖 Tipo de IA",
            tipos_ia,
            default=['Todos']
        )
        
        # Filtro por estado
        estados = ['Todos'] + get_unique_values_safe(df, 'Estado')
        estados_seleccionados = st.sidebar.multiselect(
            "📊 Estado del Caso",
            estados,
            default=['Todos']
        )
        
        # Filtro por sector
        sectores = ['Todos'] + get_unique_values_safe(df, 'Sector Productivo')
        sectores_seleccionados = st.sidebar.multiselect(
            "🏭 Sector Productivo",
            sectores,
            default=['Todos']
        )
        
    except Exception as e:
        st.sidebar.error(f"❌ Error en filtros: {str(e)}")
        # Valores por defecto en caso de error
        paises_seleccionados = ['Todos']
        tipos_seleccionados = ['Todos']
        estados_seleccionados = ['Todos']
        sectores_seleccionados = ['Todos']
    
    # Aplicar filtros de forma segura
    df_filtrado = df.copy()
    
    try:
        if 'Todos' not in paises_seleccionados and paises_seleccionados:
            df_filtrado = df_filtrado[df_filtrado['País'].isin(paises_seleccionados)]
        
        if 'Todos' not in tipos_seleccionados and tipos_seleccionados:
            df_filtrado = df_filtrado[df_filtrado['Tipo de IA'].isin(tipos_seleccionados)]
        
        if 'Todos' not in estados_seleccionados and estados_seleccionados:
            df_filtrado = df_filtrado[df_filtrado['Estado'].isin(estados_seleccionados)]
        
        if 'Todos' not in sectores_seleccionados and sectores_seleccionados:
            df_filtrado = df_filtrado[df_filtrado['Sector Productivo'].isin(sectores_seleccionados)]
            
    except Exception as e:
        st.error(f"❌ Error aplicando filtros: {str(e)}")
        df_filtrado = df.copy()
    
    # ESTADÍSTICAS SIDEBAR
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Resumen Filtrado")
    st.sidebar.metric("🎯 Mostrando", f"{len(df_filtrado)}/{len(df)}")
    
    # LAYOUT PRINCIPAL
    tab1, tab2, tab3 = st.tabs(["🗺️ Mapa Interactivo", "📊 Análisis Estadístico", "📋 Datos Detallados"])
    
    # TAB 1: MAPA INTERACTIVO
    with tab1:
        st.subheader("🗺️ Mapa Mundial Interactivo")
        
        if not df_filtrado.empty:
            try:
                # Crear mapa centrado automáticamente
                if len(df_filtrado) > 0:
                    # Calcular centro basado en datos válidos
                    valid_coords = df_filtrado[(df_filtrado['Latitud'] != 0) & (df_filtrado['Longitud'] != 0)]
                    if not valid_coords.empty:
                        center_lat = valid_coords['Latitud'].mean()
                        center_lon = valid_coords['Longitud'].mean()
                    else:
                        center_lat, center_lon = 20, 0
                else:
                    center_lat, center_lon = 20, 0
                
                m = folium.Map(location=[center_lat, center_lon], zoom_start=2)
                
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
                        <div style="width: 300px; font-family: Arial; font-size: 11px;">
                            <h4 style="color: #2E86AB; margin-bottom: 8px;">{caso['Título'][:50]}...</h4>
                            <p><strong>🌍 País:</strong> {caso['País']}</p>
                            <p><strong>🏢 Organización:</strong> {caso['Organización'][:30]}...</p>
                            <p><strong>🤖 Tipo IA:</strong> {caso['Tipo de IA']}</p>
                            <p><strong>📊 Estado:</strong> {caso['Estado']}</p>
                            <p><strong>🏭 Sector:</strong> {caso['Sector Productivo']}</p>
                        </div>
                        """
                        
                        folium.Marker(
                            location=[caso['Latitud'], caso['Longitud']],
                            popup=folium.Popup(popup_html, max_width=350),
                            tooltip=f"{caso['Título'][:30]}... - {caso['País']}",
                            icon=folium.Icon(color=color, icon='info-sign')
                        ).add_to(m)
                
                # Mostrar mapa
                st_folium(m, width=700, height=500)
                
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
                # Gráfico por país
                col1, col2 = st.columns(2)
                
                with col1:
                    pais_counts = df_filtrado['País'].value_counts().head(10)
                    if not pais_counts.empty:
                        fig_pais = px.bar(
                            x=pais_counts.values,
                            y=pais_counts.index,
                            orientation='h',
                            title="📊 Casos por País (Top 10)",
                            labels={'x': 'Número de Casos', 'y': 'País'}
                        )
                        st.plotly_chart(fig_pais, use_container_width=True)
                
                with col2:
                    tipo_counts = df_filtrado['Tipo de IA'].value_counts()
                    if not tipo_counts.empty:
                        fig_tipo = px.pie(
                            values=tipo_counts.values,
                            names=tipo_counts.index,
                            title="🤖 Distribución por Tipo de IA"
                        )
                        st.plotly_chart(fig_tipo, use_container_width=True)
                
                # Tabla de frecuencias
                st.subheader("📋 Análisis de Frecuencias")
                col_freq1, col_freq2 = st.columns(2)
                
                with col_freq1:
                    st.write("**🌍 Top 5 Países:**")
                    paises_freq = df_filtrado['País'].value_counts().head(5)
                    st.dataframe(paises_freq.to_frame('Casos'))
                
                with col_freq2:
                    st.write("**📊 Estados:**")
                    estados_freq = df_filtrado['Estado'].value_counts()
                    st.dataframe(estados_freq.to_frame('Casos'))
                    
            except Exception as e:
                st.error(f"❌ Error en análisis estadístico: {str(e)}")
        
        else:
            st.info("📊 Selecciona filtros para ver análisis estadístico")
    
    # TAB 3: DATOS DETALLADOS
    with tab3:
        st.subheader("📋 Tabla de Datos Completa")
        
        if not df_filtrado.empty:
            try:
                # Mostrar datos
                columnas_mostrar = ['Título', 'País', 'Organización', 'Tipo de IA', 'Estado', 'Fecha']
                df_display = df_filtrado[columnas_mostrar].copy()
                st.dataframe(df_display, use_container_width=True, height=400)
                
                # Botón de exportación
                csv = df_filtrado.to_csv(index=False)
                st.download_button(
                    label="📤 Exportar CSV",
                    data=csv,
                    file_name=f"casos_ia_sindical_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"❌ Error mostrando datos: {str(e)}")
        
        else:
            st.info("📋 Selecciona filtros para ver datos detallados")

if __name__ == "__main__":
    main()
