import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium

# Configuración página
st.set_page_config(
    page_title="🗺️ IA Sindical Dashboard",
    page_icon="🤖",
    layout="wide"
)

# Configuración Airtable
AIRTABLE_TOKEN = "patwjlairfW69N772.47b49b5d6e0d169a150a4405398d9519d2eaf5be282233e87ec1332a3c73fa0f"
BASE_ID = "appcAG3ImhfeNL6UW"
TABLE_NAME = "Casos IA Sindical"

# Coordenadas básicas
COORDS = {
    'España': [40.4168, -3.7038],
    'Francia': [46.6034, 1.8883],
    'Brasil': [-14.2350, -51.9253],
    'Estados Unidos': [37.0902, -95.7129],
    'Reino Unido': [55.3781, -3.4360]
}

def get_data():
    """Función simple obtener datos"""
    try:
        url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
        headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            
            casos = []
            for record in records:
                fields = record.get('fields', {})
                
                # Limpiar datos básico
                pais = str(fields.get('País', 'No especificado')).strip()
                if not pais or pais == 'nan':
                    pais = 'No especificado'
                
                titulo = str(fields.get('Título', 'Sin título')).strip()
                if not titulo or titulo == 'nan':
                    titulo = 'Sin título'
                
                # Coordenadas
                lat, lon = COORDS.get(pais, [0, 0])
                
                caso = {
                    'Título': titulo,
                    'País': pais,
                    'Organización': str(fields.get('Organización Sindical', 'No especificado')),
                    'Estado': str(fields.get('Estado del Caso', 'No especificado')),
                    'Tipo_IA': str(fields.get('Tipo de IA', 'No especificado')),
                    'Latitud': lat,
                    'Longitud': lon
                }
                casos.append(caso)
            
            return pd.DataFrame(casos)
        
        else:
            st.error(f"Error API: {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("🗺️ IA Sindical Dashboard")
    
    # Obtener datos
    df = get_data()
    
    if df.empty:
        st.error("No se pudieron cargar datos")
        return
    
    # Métricas básicas (SIN UNIQUE PROBLEMÁTICO)
    st.subheader("📊 Estadísticas Básicas")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Casos", len(df))
    
    with col2:
        # Contar países manualmente (SIN .unique())
        paises_set = set()
        for pais in df['País']:
            if pais and pais != 'No especificado':
                paises_set.add(pais)
        st.metric("Países", len(paises_set))
    
    with col3:
        # Contar organizaciones manualmente
        orgs_set = set()
        for org in df['Organización']:
            if org and org != 'No especificado':
                orgs_set.add(org)
        st.metric("Organizaciones", len(orgs_set))
    
    # Filtros básicos SIN MULTISELECT PROBLEMÁTICO
    st.sidebar.header("🔍 Filtros")
    
    # Lista países manualmente
    paises_lista = ['Todos']
    for pais in df['País']:
        if pais not in paises_lista and pais != 'No especificado':
            paises_lista.append(pais)
    
    pais_seleccionado = st.sidebar.selectbox("Seleccionar País", paises_lista)
    
    # Filtrar datos
    if pais_seleccionado != 'Todos':
        df_filtrado = df[df['País'] == pais_seleccionado]
    else:
        df_filtrado = df.copy()
    
    # Mapa básico
    st.subheader("🗺️ Mapa Interactivo")
    
    if not df_filtrado.empty:
        # Centro del mapa
        center_lat = 20
        center_lon = 0
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=2)
        
        # Agregar marcadores
        for _, caso in df_filtrado.iterrows():
            if caso['Latitud'] != 0 and caso['Longitud'] != 0:
                folium.Marker(
                    location=[caso['Latitud'], caso['Longitud']],
                    popup=f"{caso['Título']} - {caso['País']}",
                    tooltip=caso['País']
                ).add_to(m)
        
        st_folium(m, width=700, height=400)
    
    # Tabla básica
    st.subheader("📋 Datos")
    st.dataframe(df_filtrado[['Título', 'País', 'Organización', 'Estado']])

if __name__ == "__main__":
    main()
