import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from google_play_scraper import reviews, Sort, app as gp_app
from app_store_scraper import AppStore
import re
import tempfile
import os
import itertools

st.set_page_config(page_title="Extrator de Comentários", layout="wide")

st.title("📱 Extrator de Comentários da Play Store e App Store")

def identificar_loja(url):
    if "play.google.com" in url:
        return "playstore"
    elif "apps.apple.com" in url:
        return "appstore"
    else:
        return None

def extrair_id_playstore(url):
    match = re.search(r"id=([a-zA-Z0-9_.]+)", url)
    return match.group(1) if match else None

def extrair_id_appstore(url):
    match = re.search(r"id(\d+)", url)
    return match.group(1) if match else None

def coletar_playstore(app_id, data_inicio, data_fim):
    all_reviews = []
    cont_token = None

    while True:
        result, cont_token = reviews(
            app_id,
            lang='pt',
            country='br',
            sort=Sort.NEWEST,
            count=200,
            continuation_token=cont_token
        )
        if not result:
            break
        all_reviews.extend(result)
        if cont_token is None:
            break

    df = pd.DataFrame(all_reviews)
    df['date'] = pd.to_datetime(df['at']).dt.date
    df = df[(df['date'] >= data_inicio) & (df['date'] <= data_fim)]
    df = df.rename(columns={"userName": "nome", "score": "nota", "content": "comentario"})
    return df[['nome', 'nota', 'comentario', 'date']]

def coletar_appstore(app_id, data_inicio, data_fim):
    app = AppStore(country="br", app_name="app", app_id=app_id)
    app.review(how_many=1000)
    df = pd.DataFrame(app.reviews)
    df['date'] = pd.to_datetime(df['date']).dt.date
    df = df[(df['date'] >= data_inicio) & (df['date'] <= data_fim)]
    df = df.rename(columns={"userName": "nome", "rating": "nota", "review": "comentario"})
    return df[['nome', 'nota', 'comentario', 'date']]

# Inputs do usuário
url = st.text_input("Insira a URL do aplicativo")
data_inicio = st.date_input("Data início", value=datetime(2024, 1, 1))
data_fim = st.date_input("Data fim", value=datetime.now().date())

buscar = st.button("🔍 Buscar Comentários")

if buscar and url:
    loja = identificar_loja(url)
    if loja == "playstore":
        app_id = extrair_id_playstore(url)
        df = coletar_playstore(app_id, data_inicio, data_fim)
    elif loja == "appstore":
        app_id = extrair_id_appstore(url)
        df = coletar_appstore(app_id, data_inicio, data_fim)
    else:
        st.error("URL inválida.")
        df = None

    if df is not None and not df.empty:
        st.success(f"{len(df)} comentários extraídos com sucesso!")

        # Exibir DataFrame
        st.dataframe(df)

        # Exportar para Excel
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            caminho_excel = tmp.name
            df.to_excel(caminho_excel, index=False)
        with open(caminho_excel, "rb") as f:
            st.download_button(
                label="📥 Baixar Excel",
                data=f,
                file_name="comentarios_app.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        os.remove(caminho_excel)

    elif df is not None and df.empty:
        st.warning("Nenhum comentário encontrado no período selecionado.")
