import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from datetime import datetime
from PIL import Image
import folium
from streamlit_folium import folium_static

# Configuração da página
st.set_page_config(page_title='Visão Empresa', layout='wide')

# ====================================================
# 1. Carregamento e Limpeza de Dados
# ====================================================
df = pd.read_csv('dataset/train.csv', low_memory=False)
df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

# Limpeza de NaNs e tipos
df = df.loc[df['Delivery_person_Age'] != 'NaN', :].copy()
df = df.loc[df['City'] != 'NaN', :]
df = df.loc[df['Road_traffic_density'] != 'NaN', :]
df['Order_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y')
df['Time_taken(min)'] = df['Time_taken(min)'].apply(lambda x: x.split('(min) ')[1]).astype(int)

# ====================================================
# 2. Barra Lateral (Sidebar)
# ====================================================
st.sidebar.markdown('# Curry Company')
st.sidebar.markdown('## Fastest Delivery in Town')
st.sidebar.markdown("""---""")

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

# Filtro dinâmico
linhas_selecionadas = (df['Order_Date'] <= date_slider) & (df['Road_traffic_density'].isin(traffic_options))
df = df.loc[linhas_selecionadas, :]

# ====================================================
# 3. Layout das Abas (Tabs)
# ====================================================
st.header('Marketplace - Visão Cliente')
tab1, tab2, tab3 = st.tabs(['Visão Gerencial', 'Visão Tática', 'Visão Geográfica'])

with tab1:
    with st.container():
        st.markdown('# Orders by Day')
        df_aux = df.loc[:, ['ID', 'Order_Date']].groupby('Order_Date').count().reset_index()
        fig = px.bar(df_aux, x='Order_Date', y='ID')
        st.plotly_chart(fig, use_container_width=True)

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('### Coluna 1')
            df_aux = df.loc[:, ['ID', 'Road_traffic_density']].groupby('Road_traffic_density').count().reset_index()
            fig = px.pie(df_aux, values='ID', names='Road_traffic_density')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.markdown('### Coluna 2')
            df_aux = df.loc[:, ['ID', 'City', 'Road_traffic_density']].groupby(['City', 'Road_traffic_density']).count().reset_index()
            fig = px.scatter(df_aux, x='City', y='Road_traffic_density', size='ID', color='City')
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    # --- Container 1: Quantidade de pedidos por semana ---
    with st.container():
        st.markdown("# Order by Week")
        df['week_of_year'] = df['Order_Date'].dt.strftime('%U')
        df_aux = df.loc[:, ['ID', 'week_of_year']].groupby('week_of_year').count().reset_index()
        
        fig = px.line(df_aux, x='week_of_year', y='ID')
        st.plotly_chart(fig, use_container_width=True)

    # --- Container 2: Média de pedidos por entregador por semana ---
    with st.container():
        st.markdown("# Order Share by Week")
        # Pedidos por semana
        df_aux01 = df.loc[:, ['ID', 'week_of_year']].groupby('week_of_year').count().reset_index()
        # Entregadores únicos por semana
        df_aux02 = df.loc[:, ['Delivery_person_ID', 'week_of_year']].groupby('week_of_year').nunique().reset_index()
        
        # Junção das tabelas
        df_aux = pd.merge(df_aux01, df_aux02, how='inner', on='week_of_year')
        df_aux['order_by_deliverer'] = df_aux['ID'] / df_aux['Delivery_person_ID']
        
        fig = px.line(df_aux, x='week_of_year', y='order_by_deliverer')
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("# Country Maps")
    df_aux = df.loc[:, ['City', 'Road_traffic_density', 'Delivery_location_latitude', 'Delivery_location_longitude']].groupby(['City', 'Road_traffic_density']).median().reset_index()
    
    map = folium.Map()
    for index, location_info in df_aux.iterrows():
        folium.Marker([location_info['Delivery_location_latitude'], 
                       location_info['Delivery_location_longitude']],
                      popup=location_info['City']).add_to(map)
    folium_static(map, width=1024, height=600)