import streamlit as st
import pandas as pd
import re
from urllib.parse import urlparse
from datetime import datetime
from google_play_scraper import Sort, reviews_all
from app_store_scraper import AppStore
import io
import altair as alt
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from textblob import TextBlob

st.set_page_config(page_title="Extrator de Comentários de Apps", layout="wide")
st.title("📃 Extrator de Comentários da Play Store e App Store")

st.markdown("""
Insira a URL de um aplicativo da **Play Store** ou da **App Store**, e selecione o intervalo de datas para extrair os comentários em formato de planilha.
""")

# Funções auxiliares
def extrair_info_appstore(url):
    match_id = re.search(r'id(\d+)', url)
    app_id = match_id.group(1) if match_id else None
    path_parts = urlparse(url).path.strip('/').split('/')
    try:
        app_name_index = path_parts.index('app') + 1
        app_name = path_parts[app_name_index].replace('-', ' ')
    except (ValueError, IndexError):
        app_name = None
    return app_id, app_name

def extrair_info_playstore(url):
    match_id = re.search(r'details\?id=([a-zA-Z0-9_.]+)', url)
    return match_id.group(1) if match_id else None

def comentarios_playstore(app_id, data_inicio, data_fim):
    comentarios = reviews_all(
        app_id,
        lang='pt',
        country='br',
        sort=Sort.NEWEST
    )
    df = pd.DataFrame(comentarios)
    df['at'] = pd.to_datetime(df['at'], errors='coerce')
    df_filtrado = df[(df['at'] >= data_inicio) & (df['at'] <= data_fim)]
    colunas = ['userName', 'score', 'content', 'at', 'replyContent', 'reviewCreatedVersion']
    return df_filtrado[[col for col in colunas if col in df_filtrado.columns]]

def comentarios_appstore(app_id, app_name, data_inicio, data_fim):
    app = AppStore(country="br", app_name=app_name, app_id=app_id)
    app.review(how_many=2000)
    df = pd.DataFrame(app.reviews)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df_filtrado = df[(df['date'] >= data_inicio) & (df['date'] <= data_fim)]
        colunas = ['userName', 'rating', 'title', 'review', 'date']
        return df_filtrado[[col for col in colunas if col in df_filtrado.columns]]
    return pd.DataFrame()

def gerar_nuvem(texto):
    stopwords = set(STOPWORDS)
    wc = WordCloud(background_color="white", max_words=100, stopwords=stopwords, width=800, height=400)
    wc.generate(texto)
    return wc

def analisar_sentimento(texto):
    blob = TextBlob(str(texto))
    polaridade = blob.sentiment.polarity
    if polaridade > 0.1:
        return 'Positivo'
    elif polaridade < -0.1:
        return 'Negativo'
    else:
        return 'Neutro'

# Interface
url = st.text_input("URL do aplicativo")
data_inicio = st.date_input("Data de início", value=datetime(datetime.now().year, 1, 1))
data_fim = st.date_input("Data de fim", value=datetime.now())
data_inicio = pd.to_datetime(data_inicio)
data_fim = pd.to_datetime(data_fim)

nota_minima = st.slider("Nota mínima", min_value=1, max_value=5, value=1)
palavra_chave = st.text_input("Filtrar por palavra-chave (opcional)")

if st.button("Extrair Comentários"):
    if data_inicio > data_fim:
        st.error("A data de início deve ser anterior à data de fim.")
    else:
        df = pd.DataFrame()
        nome_loja = ""

        if "play.google.com" in url:
            app_id = extrair_info_playstore(url)
            if app_id:
                df = comentarios_playstore(app_id, data_inicio, data_fim)
                df = df.rename(columns={"score": "rating", "content": "review", "at": "date", "reviewCreatedVersion": "version"})
                nome_loja = "Play Store"
            else:
                st.error("App ID não encontrado na URL da Play Store.")

        elif "apps.apple.com" in url:
            app_id, app_name = extrair_info_appstore(url)
            if app_id and app_name:
                df = comentarios_appstore(app_id, app_name, data_inicio, data_fim)
                df = df.rename(columns={"title": "title", "review": "review", "rating": "rating", "date": "date"})
                nome_loja = "App Store"
            else:
                st.error("App ID ou nome não encontrado na URL da App Store.")

        if not df.empty:
            df = df[df['rating'] >= nota_minima]
            if palavra_chave:
                df = df[df['review'].str.contains(palavra_chave, case=False, na=False)]

            versoes = df['version'].dropna().unique().tolist() if 'version' in df.columns else []
            if versoes:
                versao_selecionada = st.multiselect("Filtrar por versão do app (opcional)", options=versoes)
                if versao_selecionada:
                    df = df[df['version'].isin(versao_selecionada)]

            st.success(f"{len(df)} comentários encontrados na {nome_loja} entre {data_inicio.date()} e {data_fim.date()}.")

            # Gráfico por mês e nota
            st.subheader("Gráfico de comentários por mês e nota")
            df['mes'] = df['date'].dt.to_period('M').astype(str)
            grafico = df.groupby(['mes', 'rating']).size().reset_index(name='quantidade')

            chart = alt.Chart(grafico).mark_bar().encode(
                x=alt.X('mes:N', title='Mês'),
                y=alt.Y('quantidade:Q', title='Quantidade de Comentários'),
                color=alt.Color('rating:O', title='Nota'),
                tooltip=['mes', 'rating', 'quantidade']
            ).properties(width=700, height=400)

            st.altair_chart(chart, use_container_width=True)

            # Nuvem de Palavras
            st.subheader("🌪️ Nuvem de Palavras dos Comentários")
            texto = " ".join(df['review'].dropna().astype(str))
            wc = gerar_nuvem(texto)
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis("off")
            st.pyplot(fig)

            # Análise de Sentimento
            st.subheader("🙂 Análise de Sentimento dos Comentários")
            df['sentimento'] = df['review'].apply(analisar_sentimento)
            sentimento_contagem = df['sentimento'].value_counts().reset_index()
            sentimento_contagem.columns = ['sentimento', 'quantidade']

            chart_sentimento = alt.Chart(sentimento_contagem).mark_bar().encode(
                x=alt.X('sentimento:N', title='Sentimento'),
                y=alt.Y('quantidade:Q', title='Quantidade'),
                color=alt.Color('sentimento:N'),
                tooltip=['sentimento', 'quantidade']
            ).properties(width=600, height=300)
            st.altair_chart(chart_sentimento, use_container_width=True)

            # Downloads
            st.download_button("📂 Baixar CSV", df.to_csv(index=False), file_name=f"comentarios_{nome_loja.lower().replace(' ', '_')}.csv", mime="text/csv")
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Comentarios')
            st.download_button("📂 Baixar Excel", excel_buffer.getvalue(), file_name=f"comentarios_{nome_loja.lower().replace(' ', '_')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        elif df.empty:
            st.warning("Nenhum comentário encontrado com os filtros selecionados.")
