import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# Configuración página
st.set_page_config(
    page_title="🗺️ IA Sindical Dashboard - Análisis Completo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Token y configuración Airtable
AIRTABLE_TOKEN = "patwjlairfW69N772.47b49b5d6e0d169a150a4405398d9519d2eaf5be282233e87ec1332a3c73fa0f"
BASE_ID = "appcAG3ImhfeNL6UW"
TABLE_NAME = "Casos IA Sindical"

# Coordenadas países mejoradas
COORDS_PAISES = {
    'España': [40.4168, -3.7038],
    'Francia': [46.6034, 1.8883],
    'Brasil': [-14.2350, -51.9253],
    'Estados Unidos': [37.0902, -95.7129],
    'Reino Unido': [55.3781, -3.4360],
    'Alemania': [51.1657, 10.4515],
    'Italia': [41.8719, 12.5674],
    'Argentina': [-38.4161, -63.6167],
    'México': [23.6345, -102.5528],
    'Canadá': [56.1304, -106.3468]
}

# Colores por tipo de IA
COLORES_IA = {
    'Machine Learning': '#FF6B6B',
    'Procesamiento de Lenguaje Natural': '#4ECDC4',
    'Visión por Computadora': '#45B7D1',
    'Robótica': '#96CEB4',
    'IA Generativa': '#FFEAA7',
    'Automatización': '#DDA0DD',
    'Análisis Predictivo': '#98D8C8',
    'Chatbots': '#F7DC6F',
    'Reconocimiento de Voz': '#BB8FCE',
    'Sistemas Expertos': '#85C1E9'
}

@st.cache_data(ttl=300)  # Cache 5 minutos
def get_airtable_data():
    """Obtener datos completos de Airtable"""
    try:
        url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
        headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
        
        all_records = []
        offset = None
        
        # Obtener todos los registros (paginación)
        while True:
            params = {'pageSize': 100}
            if offset:
                params['offset'] = offset
                
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                all_records.extend(data.get('records', []))
                
                offset = data.get('offset')
                if not offset:
                    break
            else:
                st.error(f"❌ Error Airtable: {response.status_code}")
                return pd.DataFrame()
        
        if not all_records:
            st.warning("⚠️ No se encontraron registros")
            return pd.DataFrame()
        
        # Procesar registros con TODOS los campos
        casos_lista = []
        for record in all_records:
            fields = record.get('fields', {})
            
            caso = {
                'ID': record.get('id', ''),
                'Título': str(fields.get('Título', 'Sin título')),
                'País': str(fields.get('País', 'No especificado')),
                'Organización': str(fields.get('Organización Sindical', 'No especificado')),
                'Estado': str(fields.get('Estado del Caso', 'No especificado')),
                'Tipo_IA': str(fields.get('Tipo de IA', 'No especificado')),
                'Sector': str(fields.get('Sector Productivo', 'No especificado')),
                'Fecha_Inicio': str(fields.get('Fecha de Inicio', 'No especificado')),
                'Descripción': str(fields.get('Descripción', 'Sin descripción')),
                'Impacto': str(fields.get('Impacto Esperado', 'No especificado')),
                'Presupuesto': str(fields.get('Presupuesto', 'No especificado')),
                'Contacto': str(fields.get('Contacto Principal', 'No especificado')),
                'URL': str(fields.get('URL/Enlaces', 'No especificado')),
                'Notas': str(fields.get('Notas Adicionales', 'Sin notas')),
                'Última_Actualización': str(fields.get('Última Actualización', 'No especificado'))
            }
            casos_lista.append(caso)
        
        df = pd.DataFrame(casos_lista)
        st.success(f"✅ Datos cargados: {len(df)} casos de IA sindical")
        return df
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return pd.DataFrame()

def crear_filtros_avanzados(df):
    """Panel de filtros completo"""
    st.sidebar.header("🔍 Filtros Avanzados")
    
    # Filtro por país
    paises_disponibles = ['Todos'] + sorted([p for p in df['País'].unique() if p != 'No especificado'])
    pais_seleccionado = st.sidebar.selectbox("🌍 País", paises_disponibles)
    
    # Filtro por organización
    orgs_disponibles = ['Todas'] + sorted([o for o in df['Organización'].unique() if o != 'No especificado'])
    org_seleccionada = st.sidebar.selectbox("🏢 Organización", orgs_disponibles)
    
    # Filtro por tipo de IA
    tipos_ia = ['Todos'] + sorted([t for t in df['Tipo_IA'].unique() if t != 'No especificado'])
    tipo_ia_seleccionado = st.sidebar.selectbox("🤖 Tipo de IA", tipos_ia)
    
    # Filtro por estado
    estados = ['Todos'] + sorted([e for e in df['Estado'].unique() if e != 'No especificado'])
    estado_seleccionado = st.sidebar.selectbox("📊 Estado del Caso", estados)
    
    # Filtro por sector
    sectores = ['Todos'] + sorted([s for s in df['Sector'].unique() if s != 'No especificado'])
    sector_seleccionado = st.sidebar.selectbox("🏭 Sector", sectores)
    
    # Búsqueda por texto
    st.sidebar.markdown("---")
    busqueda_texto = st.sidebar.text_input("🔍 Búsqueda libre", placeholder="Buscar en título, descripción...")
    
    return {
        'pais': pais_seleccionado,
        'organizacion': org_seleccionada,
        'tipo_ia': tipo_ia_seleccionado,
        'estado': estado_seleccionado,
        'sector': sector_seleccionado,
        'busqueda': busqueda_texto
    }

def aplicar_filtros(df, filtros):
    """Aplicar todos los filtros al DataFrame"""
    df_filtrado = df.copy()
    
    # Filtro país
    if filtros['pais'] != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['País'] == filtros['pais']]
    
    # Filtro organización
    if filtros['organizacion'] != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Organización'] == filtros['organizacion']]
    
    # Filtro tipo IA
    if filtros['tipo_ia'] != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Tipo_IA'] == filtros['tipo_ia']]
    
    # Filtro estado
    if filtros['estado'] != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Estado'] == filtros['estado']]
    
    # Filtro sector
    if filtros['sector'] != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Sector'] == filtros['sector']]
    
    # Búsqueda por texto
    if filtros['busqueda']:
        texto_busqueda = filtros['busqueda'].lower()
        mask = (
            df_filtrado['Título'].str.lower().str.contains(texto_busqueda, na=False) |
            df_filtrado['Descripción'].str.lower().str.contains(texto_busqueda, na=False) |
            df_filtrado['Organización'].str.lower().str.contains(texto_busqueda, na=False)
        )
        df_filtrado = df_filtrado[mask]
    
    return df_filtrado

def crear_mapa_profesional(df):
    """Crear mapa interactivo profesional"""
    if df.empty:
        return None
    
    # Calcular centro del mapa basado en datos
    paises_con_datos = df['País'].value_counts()
    if len(paises_con_datos) == 1:
        pais_principal = paises_con_datos.index[0]
        if pais_principal in COORDS_PAISES:
            center_lat, center_lon = COORDS_PAISES[pais_principal]
            zoom_start = 6
        else:
            center_lat, center_lon = 20, 0
            zoom_start = 2
    else:
        center_lat, center_lon = 20, 0
        zoom_start = 2
    
    # Crear mapa
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles='OpenStreetMap'
    )
    
    # Agregar marcadores por país
    for pais, casos_pais in df.groupby('País'):
        if pais in COORDS_PAISES:
            lat, lon = COORDS_PAISES[pais]
            
            # Contar casos por tipo de IA
            tipos_ia_count = casos_pais['Tipo_IA'].value_counts()
            
            # Determinar color del marcador
            tipo_principal = tipos_ia_count.index[0] if len(tipos_ia_count) > 0 else 'No especificado'
            color = COLORES_IA.get(tipo_principal, '#gray')
            
            # Crear popup con información detallada
            popup_html = f"""
            <div style="width: 300px;">
                <h4>🌍 {pais}</h4>
                <p><strong>Total casos:</strong> {len(casos_pais)}</p>
                <p><strong>Tipo IA principal:</strong> {tipo_principal}</p>
                <hr>
                <h5>Casos:</h5>
                <ul>
            """
            
            for _, caso in casos_pais.head(5).iterrows():  # Mostrar máximo 5 casos
                popup_html += f"<li><strong>{caso['Título']}</strong><br>"
                popup_html += f"Org: {caso['Organización']}<br>"
                popup_html += f"Estado: {caso['Estado']}</li>"
            
            if len(casos_pais) > 5:
                popup_html += f"<li><em>... y {len(casos_pais) - 5} casos más</em></li>"
            
            popup_html += "</ul></div>"
            
            # Agregar marcador
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=f"{pais}: {len(casos_pais)} casos",
                icon=folium.Icon(color='red' if len(casos_pais) > 2 else 'blue', icon='info-sign')
            ).add_to(m)
    
    return m

def crear_estadisticas_avanzadas(df):
    """Crear panel de estadísticas y gráficos"""
    if df.empty:
        st.warning("No hay datos para mostrar estadísticas")
        return
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Casos", len(df))
    
    with col2:
        paises_unicos = len([p for p in df['País'].unique() if p != 'No especificado'])
        st.metric("🌍 Países", paises_unicos)
    
    with col3:
        orgs_unicas = len([o for o in df['Organización'].unique() if o != 'No especificado'])
        st.metric("🏢 Organizaciones", orgs_unicas)
    
    with col4:
        tipos_ia_unicos = len([t for t in df['Tipo_IA'].unique() if t != 'No especificado'])
        st.metric("🤖 Tipos de IA", tipos_ia_unicos)
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico por país
        paises_count = df['País'].value_counts().head(10)
        if not paises_count.empty:
            fig_paises = px.bar(
                x=paises_count.values,
                y=paises_count.index,
                orientation='h',
                title="📊 Casos por País",
                labels={'x': 'Número de Casos', 'y': 'País'}
            )
            fig_paises.update_layout(height=400)
            st.plotly_chart(fig_paises, use_container_width=True)
    
    with col2:
        # Gráfico por tipo de IA
        tipos_count = df['Tipo_IA'].value_counts().head(10)
        if not tipos_count.empty:
            fig_tipos = px.pie(
                values=tipos_count.values,
                names=tipos_count.index,
                title="🤖 Distribución por Tipo de IA"
            )
            fig_tipos.update_layout(height=400)
            st.plotly_chart(fig_tipos, use_container_width=True)

def main():
    # Header
    st.title("🗺️ IA Sindical Dashboard - Análisis Completo")
    st.markdown("**Dashboard interactivo con filtros avanzados y actualización automática**")
    
    # Obtener datos
    with st.spinner("Cargando datos de Airtable..."):
        df = get_airtable_data()
    
    if df.empty:
        st.error("❌ No se pudieron cargar los datos. Verifica la conexión con Airtable.")
        st.stop()
    
    # Crear filtros
    filtros = crear_filtros_avanzados(df)
    
    # Aplicar filtros
    df_filtrado = aplicar_filtros(df, filtros)
    
    # Mostrar estadísticas
    st.subheader("📊 Estadísticas Avanzadas")
    crear_estadisticas_avanzadas(df_filtrado)
    
    # Mostrar mapa
    st.subheader("🗺️ Mapa Interactivo Global")
    if not df_filtrado.empty:
        mapa = crear_mapa_profesional(df_filtrado)
        if mapa:
            st_folium(mapa, width=700, height=500)
        else:
            st.info("🗺️ Selecciona filtros para ver el mapa")
    else:
        st.warning("⚠️ No hay casos que coincidan con los filtros seleccionados")
    
    # Tabla completa expandible
    st.subheader("📋 Tabla Completa de Casos")
    
    if not df_filtrado.empty:
        # Selector de columnas a mostrar
        columnas_disponibles = [
            'Título', 'País', 'Organización', 'Estado', 'Tipo_IA', 
            'Sector', 'Fecha_Inicio', 'Descripción', 'Impacto', 
            'Presupuesto', 'Contacto', 'URL', 'Notas'
        ]
        
        columnas_seleccionadas = st.multiselect(
            "Selecciona columnas a mostrar:",
            columnas_disponibles,
            default=['Título', 'País', 'Organización', 'Estado', 'Tipo_IA', 'Sector']
        )
        
        if columnas_seleccionadas:
            # Mostrar tabla filtrada
            st.dataframe(
                df_filtrado[columnas_seleccionadas],
                use_container_width=True,
                height=400
            )
            
            # Botón de exportación
            csv = df_filtrado[columnas_seleccionadas].to_csv(index=False)
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"casos_ia_sindical_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ Selecciona al menos una columna para mostrar")
    else:
        st.info("🔍 No hay casos que coincidan con los filtros actuales")
    
    # Footer
    st.markdown("---")
    st.markdown("**💡 Dashboard creado con Streamlit | 🔄 Actualización automática desde Airtable**")

if __name__ == "__main__":
    main()
