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

# Coordenadas países EXPANDIDAS (incluye Perú)
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
    'Canadá': [56.1304, -106.3468],
    'Perú': [-9.1900, -75.0152],  # ← AGREGADO PERÚ
    'Chile': [-35.6751, -71.5430],
    'Colombia': [4.5709, -74.2973],
    'Venezuela': [6.4238, -66.5897],
    'Uruguay': [-32.5228, -55.7658],
    'Ecuador': [-1.8312, -78.1834],
    'Bolivia': [-16.2902, -63.5887],
    'Paraguay': [-23.4425, -58.4438],
    'India': [20.5937, 77.9629],
    'China': [35.8617, 104.1954],
    'Japón': [36.2048, 138.2529],
    'Australia': [-25.2744, 133.7751],
    'Sudáfrica': [-30.5595, 22.9375],
    'Nigeria': [9.0820, 8.6753],
    'Kenia': [-0.0236, 37.9062],
    'Marruecos': [31.7917, -7.0926]
}

# Colores por tipo de IA EXPANDIDOS
COLORES_IA = {
    'Machine Learning': '#FF6B6B',
    'Procesamiento de Lenguaje Natural': '#4ECDC4',
    'Procesamiento de Datos': '#45B7D1',  # ← AGREGADO
    'Visión por Computadora': '#45B7D1',
    'Robótica': '#96CEB4',
    'IA Generativa': '#FFEAA7',
    'Automatización': '#DDA0DD',
    'Análisis Predictivo': '#98D8C8',
    'Chatbots': '#F7DC6F',
    'Reconocimiento de Voz': '#BB8FCE',
    'Sistemas Expertos': '#85C1E9',
    'Otros': '#FFA07A'  # ← AGREGADO PARA "OTROS"
}

@st.cache_data(ttl=300)  # Cache 5 minutos
def get_airtable_data():
    """Obtener datos completos de Airtable con TODOS los campos"""
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
                st.error(f"❌ Error Airtable: {response.status_code} - {response.text}")
                return pd.DataFrame()
        
        if not all_records:
            st.warning("⚠️ No se encontraron registros")
            return pd.DataFrame()
        
        # Procesar registros con TODOS los campos CORREGIDOS
        casos_lista = []
        for record in all_records:
            fields = record.get('fields', {})
            
            # CORRECCIÓN: Usar nombres exactos de Airtable
            caso = {
                'ID': record.get('id', ''),
                'Título': str(fields.get('Título', fields.get('Title', 'Sin título'))),  # ← CORREGIDO
                'País': str(fields.get('País', fields.get('Country', 'No especificado'))),
                'Organización': str(fields.get('Organización Sindical', fields.get('Organization', 'No especificado'))),
                'Estado': str(fields.get('Estado del Caso', fields.get('Status', 'No especificado'))),
                'Tipo_IA': str(fields.get('Tipo de IA', fields.get('AI Type', 'No especificado'))),
                'Sector': str(fields.get('Sector Productivo', fields.get('Sector', 'No especificado'))),
                'Fecha_Inicio': str(fields.get('Fecha de Inicio', fields.get('Start Date', 'No especificado'))),
                'Descripción': str(fields.get('Descripción', fields.get('Description', 'Sin descripción'))),
                'Impacto': str(fields.get('Impacto Esperado', fields.get('Expected Impact', 'No especificado'))),
                'Presupuesto': str(fields.get('Presupuesto', fields.get('Budget', 'No especificado'))),
                'Contacto': str(fields.get('Contacto Principal', fields.get('Main Contact', 'No especificado'))),
                'URL': str(fields.get('URL/Enlaces', fields.get('Links', 'No especificado'))),
                'Notas': str(fields.get('Notas Adicionales', fields.get('Additional Notes', 'Sin notas'))),
                'Última_Actualización': str(fields.get('Última Actualización', fields.get('Last Update', 'No especificado'))),
                # Campos adicionales
                'Actores_Involucrados': str(fields.get('Actores Involucrados', 'No especificado')),
                'Aplicación_Específica': str(fields.get('Aplicación Específica', 'No especificado')),
                'Riesgos_Identificados': str(fields.get('Riesgos Identificados', 'No especificado')),
                'Beneficios_Esperados': str(fields.get('Beneficios Esperados', 'No especificado')),
                'Metodología': str(fields.get('Metodología', 'No especificado'))
            }
            casos_lista.append(caso)
        
        df = pd.DataFrame(casos_lista)
        st.success(f"✅ Datos cargados: {len(df)} casos de IA sindical")
        
        # DEBUG: Mostrar información de depuración
        st.sidebar.markdown("### 🔍 Debug Info")
        st.sidebar.write(f"**Registros totales**: {len(df)}")
        st.sidebar.write(f"**Países únicos**: {df['País'].nunique()}")
        st.sidebar.write(f"**Países**: {list(df['País'].unique())}")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return pd.DataFrame()

def crear_filtros_avanzados(df):
    """Panel de filtros completo"""
    st.sidebar.header("🔍 Filtros Avanzados")
    
    # Filtro por país
    paises_disponibles = ['Todos'] + sorted([p for p in df['País'].unique() if p and p != 'No especificado'])
    pais_seleccionado = st.sidebar.selectbox("🌍 País", paises_disponibles)
    
    # Filtro por organización
    orgs_disponibles = ['Todas'] + sorted([o for o in df['Organización'].unique() if o and o != 'No especificado'])
    org_seleccionada = st.sidebar.selectbox("🏢 Organización", orgs_disponibles)
    
    # Filtro por tipo de IA
    tipos_ia = ['Todos'] + sorted([t for t in df['Tipo_IA'].unique() if t and t != 'No especificado'])
    tipo_ia_seleccionado = st.sidebar.selectbox("🤖 Tipo de IA", tipos_ia)
    
    # Filtro por estado
    estados = ['Todos'] + sorted([e for e in df['Estado'].unique() if e and e != 'No especificado'])
    estado_seleccionado = st.sidebar.selectbox("📊 Estado del Caso", estados)
    
    # Filtro por sector
    sectores = ['Todos'] + sorted([s for s in df['Sector'].unique() if s and s != 'No especificado'])
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
    """Crear mapa interactivo profesional CORREGIDO"""
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
    
    # Contador de marcadores para debug
    marcadores_agregados = 0
    
    # Agregar marcadores por país
    for pais, casos_pais in df.groupby('País'):
        if pais in COORDS_PAISES:
            lat, lon = COORDS_PAISES[pais]
            
            # Contar casos por tipo de IA
            tipos_ia_count = casos_pais['Tipo_IA'].value_counts()
            
            # Determinar color del marcador
            tipo_principal = tipos_ia_count.index[0] if len(tipos_ia_count) > 0 else 'Otros'
            color_hex = COLORES_IA.get(tipo_principal, '#FFA07A')
            
            # Crear popup con información detallada CORREGIDA
            popup_html = f"""
            <div style="width: 350px; font-family: Arial;">
                <h3 style="color: {color_hex}; margin-bottom: 10px;">🌍 {pais}</h3>
                <p><strong>📊 Total casos:</strong> {len(casos_pais)}</p>
                <p><strong>🤖 Tipo IA principal:</strong> {tipo_principal}</p>
                <hr style="margin: 10px 0;">
                <h4 style="margin-bottom: 8px;">📋 Casos:</h4>
                <ul style="margin: 0; padding-left: 20px;">
            """
            
            for _, caso in casos_pais.head(5).iterrows():  # Mostrar máximo 5 casos
                titulo = caso['Título'] if caso['Título'] and caso['Título'] != 'Sin título' else 'Caso sin título'
                organizacion = caso['Organización'] if caso['Organización'] != 'No especificado' else 'Org. no especificada'
                estado = caso['Estado'] if caso['Estado'] != 'No especificado' else 'Estado no especificado'
                
                popup_html += f"""
                <li style="margin-bottom: 8px;">
                    <strong style="color: #2E86AB;">{titulo}</strong><br>
                    <span style="font-size: 12px;">🏢 {organizacion}</span><br>
                    <span style="font-size: 12px;">📊 {estado}</span>
                </li>
                """
            
            if len(casos_pais) > 5:
                popup_html += f"<li style='color: #666; font-style: italic;'>... y {len(casos_pais) - 5} casos más</li>"
            
            popup_html += "</ul></div>"
            
            # Determinar color de marcador para Folium
            if len(casos_pais) > 3:
                folium_color = 'red'
            elif len(casos_pais) > 1:
                folium_color = 'orange'
            else:
                folium_color = 'blue'
            
            # Agregar marcador
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=400),
                tooltip=f"{pais}: {len(casos_pais)} casos ({tipo_principal})",
                icon=folium.Icon(color=folium_color, icon='info-sign')
            ).add_to(m)
            
            marcadores_agregados += 1
        else:
            st.sidebar.warning(f"⚠️ País sin coordenadas: {pais}")
    
    # Debug info
    st.sidebar.write(f"**Marcadores en mapa**: {marcadores_agregados}")
    
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
        paises_unicos = len([p for p in df['País'].unique() if p and p != 'No especificado'])
        st.metric("🌍 Países", paises_unicos)
    
    with col3:
        orgs_unicas = len([o for o in df['Organización'].unique() if o and o != 'No especificado'])
        st.metric("🏢 Organizaciones", orgs_unicas)
    
    with col4:
        tipos_ia_unicos = len([t for t in df['Tipo_IA'].unique() if t and t != 'No especificado'])
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
                labels={'x': 'Número de Casos', 'y': 'País'},
                color=paises_count.values,
                color_continuous_scale='Blues'
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
                title="🤖 Distribución por Tipo de IA",
                color_discrete_sequence=px.colors.qualitative.Set3
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
    
    # Tabla completa expandible CORREGIDA
    st.subheader("📋 Tabla Completa de Casos")
    
    if not df_filtrado.empty:
        # Selector de columnas a mostrar - TODOS LOS CAMPOS
        columnas_disponibles = [
            'Título', 'País', 'Organización', 'Estado', 'Tipo_IA', 
            'Sector', 'Fecha_Inicio', 'Descripción', 'Impacto', 
            'Presupuesto', 'Contacto', 'URL', 'Notas', 'Última_Actualización',
            'Actores_Involucrados', 'Aplicación_Específica', 'Riesgos_Identificados',
            'Beneficios_Esperados', 'Metodología'
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
    st.markdown(f"**🕒 Última actualización**: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

if __name__ == "__main__":
    main()
