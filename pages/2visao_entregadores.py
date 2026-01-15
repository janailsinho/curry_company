import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image

# ====================================================
# Funções de Processamento (Lógica)
# ====================================================

def clean_code(df):
    """ Faz a limpeza do dataframe e conversão de tipos """
    # Removendo espaços
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Limpeza de tipos e NaNs
    df = df.loc[df['Delivery_person_Age'] != 'NaN', :].copy()
    df['Delivery_person_Age'] = df['Delivery_person_Age'].astype(int)
    df['Delivery_person_Ratings'] = df['Delivery_person_Ratings'].astype(float)
    df['Order_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y')
    
    # Limpeza do tempo de entrega
    df['Time_taken(min)'] = df['Time_taken(min)'].apply(lambda x: x.split('(min) ')[1]).astype(int)
    
    return df

def top_delivers(df, top_asc):
    """ Calcula os entregadores mais rápidos ou lentos por cidade """
    df_result = ( df.loc[:, ['Delivery_person_ID', 'City', 'Time_taken(min)']]
                    .groupby(['City', 'Delivery_person_ID'])
                    .mean()
                    .sort_values(['City', 'Time_taken(min)'], ascending=top_asc)
                    .reset_index() )
    return df_result.head(10)

# ====================================================
# Configuração da Página
# ====================================================
st.set_page_config(page_title='Visão Entregadores', layout='wide')

# Carregamento e Limpeza Inicial
df_raw = pd.read_csv('dataset/train.csv', low_memory=False)
df = clean_code(df_raw)

# ====================================================
# Barra Lateral (Sidebar)
# ====================================================

try:
    image = Image.open('image.png')
    st.sidebar.image(image, width=120)
except:
    st.sidebar.markdown('### [Logo J]')

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
# Layout no Streamlit - Visão Entregadores
# ====================================================
st.header('Marketplace - Visão Entregadores')

# --- Container 1: Métricas Gerais ---
with st.container():
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric('Maior idade', df['Delivery_person_Age'].max())
    with col2:
        st.metric('Menor idade', df['Delivery_person_Age'].min())
    with col3:
        st.metric('Melhor condição de veículo', df['Vehicle_condition'].max())
    with col4:
        st.metric('Pior condição de veículo', df['Vehicle_condition'].min())

st.markdown("""---""")

# --- Container 2: Avaliações Médias ---
with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('### Avaliações médias por entregador')
        df_avg_ratings_per_deliverer = ( df.loc[:, ['Delivery_person_ID', 'Delivery_person_Ratings']]
                                         .groupby('Delivery_person_ID')
                                         .mean()
                                         .reset_index() )
        st.dataframe(df_avg_ratings_per_deliverer)
        
    with col2:
        st.markdown('### Avaliações médias por trânsito')
        df_avg_std_traffic = ( df.loc[:, ['Delivery_person_Ratings', 'Road_traffic_density']]
                                 .groupby('Road_traffic_density')
                                 .agg({'Delivery_person_Ratings': ['mean', 'std']}) )
        df_avg_std_traffic.columns = ['delivery_mean', 'delivery_std']
        st.dataframe(df_avg_std_traffic.reset_index())
        
        st.markdown('### Avaliações médias por clima')
        df_avg_std_weather = ( df.loc[:, ['Delivery_person_Ratings', 'Weatherconditions']]
                                 .groupby('Weatherconditions')
                                 .agg({'Delivery_person_Ratings': ['mean', 'std']}) )
        df_avg_std_weather.columns = ['delivery_mean', 'delivery_std']
        st.dataframe(df_avg_std_weather.reset_index())

st.markdown("""---""")

# --- Container 3: Velocidade de Entrega ---
with st.container():
    st.title('Velocidade de Entrega')
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('### Top entregadores mais rápidos')
        df_fastest = top_delivers(df, top_asc=True)
        st.dataframe(df_fastest)
        
    with col2:
        st.markdown('### Top entregadores mais lentos')
        df_slowest = top_delivers(df, top_asc=False)
        st.dataframe(df_slowest)