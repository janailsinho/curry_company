import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
import folium
from datetime import datetime
from PIL import Image
from streamlit_folium import folium_static

# ====================================================
# Funções de Processamento (Lógica)
# ====================================================

def clean_code(df):
    """ 
    Limpa o dataframe: remove espaços, filtra NaNs, 
    converte datas e tipos numéricos. 
    """
    # Removendo espaços vazios
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Filtros de NaNs
    df = df.loc[df['Delivery_person_Age'] != 'NaN', :].copy()
    df = df.loc[df['City'] != 'NaN', :]
    df = df.loc[df['Road_traffic_density'] != 'NaN', :]

    # Conversão de tipos
    df['Order_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y')
    df['Time_taken(min)'] = df['Time_taken(min)'].apply(lambda x: x.split('(min) ')[1]).astype(int)
    
    # Criando coluna de semana para a Visão Tática
    df['week_of_year'] = df['Order_Date'].dt.strftime('%U')
    
    return df

def country_maps(df):
    """ Cria o mapa com as localizações medianas por cidade e tráfego """
    df_aux = (df.loc[:, ['City', 'Road_traffic_density', 'Delivery_location_latitude', 'Delivery_location_longitude']]
                .groupby(['City', 'Road_traffic_density'])
                .median()
                .reset_index())
    
    map = folium.Map()
    for index, location_info in df_aux.iterrows():
        folium.Marker([location_info['Delivery_location_latitude'], 
                       location_info['Delivery_location_longitude']],
                       popup=location_info['City']).add_to(map)
    
    folium_static(map, width=1024, height=600)

# ====================================================
# Configuração da Página
# ====================================================
st.set_page_config(page_title='Visão Empresa', layout='wide')

# Carregamento dos dados
df_raw = pd.read_csv('dataset/train.csv', low_memory=False)
df = clean_code(df_raw)

# ====================================================
# Barra Lateral (Sidebar)
# ====================================================

try:
    image = Image.open('image.png') # Certifique-se do nome do arquivo
    st.sidebar.image(image, width=120)
except:
    st.sidebar.markdown('### [Logo J]')

st.sidebar.markdown('# Curry Company')
st.sidebar.markdown('## Fastest Delivery in Town')
st.sidebar.markdown("""---""")

# Filtros na Sidebar
date_slider = st.sidebar.slider(
    'Até qual data?',
    value=datetime(2022, 4, 13),
    min_value=datetime(2022, 2, 11),
    max_value=datetime(2022, 4, 13),
    format='DD-MM-YYYY'
)

traffic_options = st.sidebar.multiselect(
    'Condições do trânsito',
    ['Low', 'Medium', 'High', 'Jam'],
    default=['Low', 'Medium', 'High', 'Jam'] 
)

# Aplicando Filtros
linhas_selecionadas = (df['Order_Date'] <= date_slider) & (df['Road_traffic_density'].isin(traffic_options))
df = df.loc[linhas_selecionadas, :]

# ====================================================
# Layout das Abas (Visualização)
# ====================================================
st.header('Marketplace - Visão Empresa')
tab1, tab2, tab3 = st.tabs(['Visão Gerencial', 'Visão Tática', 'Visão Geográfica'])

with tab1:
    with st.container():
        st.markdown('### Orders by Day')
        df_aux = df.loc[:, ['ID', 'Order_Date']].groupby('Order_Date').count().reset_index()
        fig = px.bar(df_aux, x='Order_Date', y='ID')
        st.plotly_chart(fig, use_container_width=True)

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('### Pedidos por Tráfego')
            df_aux = df.loc[:, ['ID', 'Road_traffic_density']].groupby('Road_traffic_density').count().reset_index()
            fig = px.pie(df_aux, values='ID', names='Road_traffic_density')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.markdown('### Tráfego por Cidade')
            df_aux = df.loc[:, ['ID', 'City', 'Road_traffic_density']].groupby(['City', 'Road_traffic_density']).count().reset_index()
            fig = px.scatter(df_aux, x='City', y='Road_traffic_density', size='ID', color='City')
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    with st.container():
        st.markdown("### Order by Week")
        df_aux = df.loc[:, ['ID', 'week_of_year']].groupby('week_of_year').count().reset_index()
        fig = px.line(df_aux, x='week_of_year', y='ID')
        st.plotly_chart(fig, use_container_width=True)

    with st.container():
        st.markdown("### Order Share by Week")
        df_aux01 = df.loc[:, ['ID', 'week_of_year']].groupby('week_of_year').count().reset_index()
        df_aux02 = df.loc[:, ['Delivery_person_ID', 'week_of_year']].groupby('week_of_year').nunique().reset_index()
        
        df_aux = pd.merge(df_aux01, df_aux02, how='inner', on='week_of_year')
        df_aux['order_by_deliverer'] = df_aux['ID'] / df_aux['Delivery_person_ID']
        
        fig = px.line(df_aux, x='week_of_year', y='order_by_deliverer')
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("### Country Maps")
    country_maps(df)