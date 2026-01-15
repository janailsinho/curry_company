import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from PIL import Image
from haversine import haversine

# ====================================================
# Funções de Processamento (Lógica)
# ====================================================

def clean_code(df):
    """ Faz a limpeza, conversão de tipos e cálculo de distância """
    # Removendo espaços
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Filtros de NaNs
    df = df.loc[df['City'] != 'NaN', :]
    df = df.loc[df['Festival'] != 'NaN', :]
    df = df.loc[df['Road_traffic_density'] != 'NaN', :]

    # Conversão de tipos
    df['Order_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y')
    df['Time_taken(min)'] = df['Time_taken(min)'].str.extract(r'(\d+)').astype(int)

    # Cálculo de distância usando Haversine
    df['distance'] = df.apply(lambda x: haversine(
        (x['Restaurant_latitude'], x['Restaurant_longitude']), 
        (x['Delivery_location_latitude'], x['Delivery_location_longitude'])), axis=1)
    
    return df

def avg_std_time_delivery(df, festival, op):
    """ 
    Calcula o tempo médio ou desvio padrão durante ou fora de festivais 
    festival: 'Yes' ou 'No'
    op: 'avg_time' ou 'std_time'
    """
    df_aux = df.loc[df['Festival'] == festival, 'Time_taken(min)'].agg(['mean', 'std'])
    df_aux.columns = ['avg_time', 'std_time']
    
    if op == 'avg_time':
        return df_aux['mean']
    elif op == 'std_time':
        return df_aux['std']

# ====================================================
# Configuração da Página
# ====================================================
st.set_page_config(page_title='Visão Restaurantes', layout='wide', initial_sidebar_state='expanded')

# Carregamento e Limpeza
df_raw = pd.read_csv('dataset/train.csv', low_memory=False)
df = clean_code(df_raw)

# ====================================================
# Barra Lateral (Sidebar)
# ====================================================

try:
    image = Image.open('image.png') 
    st.sidebar.image(image, width=120)
except:
    st.sidebar.markdown('### Logo')

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

# Aplicando Filtros
df = df.loc[(df['Order_Date'] <= date_slider) & (df['Road_traffic_density'].isin(traffic_options)), :]

# ====================================================
# Layout Principal
# ====================================================
st.title('Marketplace - Visão Restaurantes')

# --- CONTAINER 1: Overall Metrics ---
st.markdown("## Overal Metrics")
with st.container():
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric('Entregadores', df['Delivery_person_ID'].nunique())
    with col2:
        st.metric('A distancia media', f"{df['distance'].mean():.2f}")
    with col3:
        res = avg_std_time_delivery(df, 'Yes', 'avg_time')
        st.metric('Tempo Médio', f"{res:.2f}")
    with col4:
        res = avg_std_time_delivery(df, 'Yes', 'std_time')
        st.metric('STD Entrega', f"{res:.2f}")
    with col5:
        res = avg_std_time_delivery(df, 'No', 'avg_time')
        st.metric('Tempo Médio', f"{res:.2f}")
    with col6:
        res = avg_std_time_delivery(df, 'No', 'std_time')
        st.metric('STD Entrega', f"{res:.1f}")

st.markdown("""---""")

# --- CONTAINER 2: Performance por Cidade e Tipo ---
with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Tempo Medio de entrega por cidade")
        df_aux = df.loc[:, ['City', 'Time_taken(min)']].groupby('City').agg({'Time_taken(min)': ['mean', 'std']})
        df_aux.columns = ['avg_time', 'std_time']
        df_aux = df_aux.reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Control', x=df_aux['City'], y=df_aux['avg_time'], 
                             error_y=dict(type='data', array=df_aux['std_time'])))
        fig.update_layout(template='plotly_dark', margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.markdown("### Tempo médio por tipo de entrega")
        df_aux = (df.loc[:, ['City', 'Type_of_order', 'Time_taken(min)']]
                    .groupby(['City', 'Type_of_order'])
                    .agg({'Time_taken(min)': ['mean', 'std']}))
        df_aux.columns = ['avg_time', 'std_time']
        st.dataframe(df_aux.reset_index(), use_container_width=True)

st.markdown("""---""")

# --- CONTAINER 3: Distribuição (Pizza e Sunburst) ---
st.markdown("## Distribuição do Tempo")
with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        df_aux = df.loc[:, ['City', 'distance']].groupby('City').mean().reset_index()
        fig = px.pie(df_aux, values='distance', names='City')
        fig.update_layout(template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        df_aux = (df.loc[:, ['City', 'Road_traffic_density', 'Time_taken(min)']]
                    .groupby(['City', 'Road_traffic_density'])
                    .agg({'Time_taken(min)': ['mean', 'std']})
                    .reset_index())
        df_aux.columns = ['City', 'Road_traffic_density', 'avg_time', 'std_time']
        
        fig = px.sunburst(df_aux, path=['City', 'Road_traffic_density'], values='avg_time',
                          color='std_time', color_continuous_scale='RdBu')
        fig.update_layout(template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)