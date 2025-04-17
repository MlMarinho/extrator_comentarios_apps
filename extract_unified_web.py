import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from io import BytesIO
import re
from google_play_scraper import reviews as gp_reviews, Sort as GP_Sort
from app_store_scraper import AppStore

st.set_page_config(layout="wide")
st.title("Extrator de Comentários de Apps - Play Store e App Store")

# Função para detectar a loja com base na URL
def detectar_loja(url):
    if "play.google.com" in url:
        return "play_store"
    elif "apps.apple.com" in url:
        return "app_store"
    else:
        return None

# Função para extrair o ID do app da Play Store
def extrair_id_play_store(url):
    match = re.search(r"id=([a-zA-Z0-9._]+)", url)
    return match.group(1) if match else None

# Função para extrair o nome e país da App Store
def extrair_info_app_store(url):
    match = re.search(r"/([a-z]{2})/app/.+/id(\d+)", url)
    if match:
        pais, app_id = match.groups()
        return app_id, pais
    return None, None

# Entrada da URL do app
url = st.text_input("Insira a URL do aplicativo na Play Store ou App Store")
data_inicio = st.date_input("Data de início")
data_fim = st.date_input("Data de fim")

botao_buscar = st.button("Buscar comentários")

if url and botao_buscar:
    loja = detectar_loja(url)
    df_comentarios = pd.DataFrame()

    if loja == "play_store":
        app_id = extrair_id_play_store(url)
        if app_id:
            comentarios, _ = gp_reviews(
                app_id,
                lang='pt',
                country='br',
                sort=GP_Sort.NEWEST,
                count=1000
            )
            df_comentarios = pd.DataFrame(comentarios)
            df_comentarios['content'] = df_comentarios['content'].astype(str)
            df_comentarios['score'] = df_comentarios['score'].astype(int)
            df_comentarios['at'] = pd.to_datetime(df_comentarios['at'])

    elif loja == "app_store":
        app_id, pais = extrair_info_app_store(url)
        if app_id and pais:
            app = AppStore(country=pais, app_name='', app_id=app_id)
            app.review(how_many=1000)
            dados = app.reviews
            df_comentarios = pd.DataFrame(dados)
            if not df_comentarios.empty:
                df_comentarios['score'] = df_comentarios['rating']
                df_comentarios['content'] = df_comentarios['review']
                df_comentarios['at'] = pd.to_datetime(df_comentarios['date'])

    if not df_comentarios.empty:
        # Filtra pelos dados
        df_filtrado = df_comentarios[
            (df_comentarios['at'] >= pd.to_datetime(data_inicio)) &
            (df_comentarios['at'] <= pd.to_datetime(data_fim))
        ]

        st.success(f"Foram encontrados {len(df_filtrado)} comentários no período selecionado.")

        # Agrupa por mês e nota
        df_filtrado['mes'] = df_filtrado['at'].dt.to_period('M').astype(str)
        agrupado = df_filtrado.groupby(['mes', 'score']).size().reset_index(name='quantidade')

        # Gráfico
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=agrupado, x='mes', y='quantidade', hue='score', ax=ax)
        ax.set_title('Comentários por Mês e Nota')
        ax.set_xlabel('Mês')
        ax.set_ylabel('Quantidade')

        for c in ax.containers:
            ax.bar_label(c, fmt='%d', label_type='edge')

        st.pyplot(fig)

        # Tabela
        st.dataframe(df_filtrado[['at', 'score', 'content']])

        # Exporta para Excel
        buffer = BytesIO()
        df_filtrado.to_excel(buffer, index=False)
        st.download_button(
            label="Baixar Excel",
            data=buffer.getvalue(),
            file_name="comentarios_app.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("Não foi possível extrair os comentários. Verifique a URL e tente novamente.")
