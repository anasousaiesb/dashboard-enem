import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import requests

# -------------------------
# CONFIGURAÇÃO
# -------------------------
st.set_page_config(page_title="Dashboard ENEM 2024", layout="wide")

# PALETA
cores = ["#C77DFF", "#9D4EDD", "#7B2CBF", "#FF99C8", "#E0AAFF", "#5A189A"]
scale_roxo = ["#f8f0ff", "#e0aaff", "#c77dff", "#9d4edd", "#7b2cbf", "#5a189a"]

# -------------------------
# MENU LATERAL
# -------------------------
pagina = st.sidebar.radio("📂 Navegação", [
    "Distribuição por Estado",
    "Tipo de Linguagem",
    "Distribuições por Nota",
    "Estatísticas Gerais"
])

# -------------------------
# GEOJSON (MAPA BRASIL)
# -------------------------
url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
geojson = requests.get(url).json()

# -------------------------
# CONEXÃO
# -------------------------
conn = psycopg2.connect(
    host="bigdata.dataiesb.com",
    database="iesb",
    user="data_iesb",
    password="iesb",
    port="5432"
)

# -------------------------
# QUERY
# -------------------------
query = """
SELECT 
    sg_uf_prova,
    nota_media_5_notas,
    nota_mt_matematica,
    nota_ch_ciencias_humanas,
    nota_cn_ciencias_da_natureza,
    nota_redacao,
    nota_lc_linguagens_e_codigos,
    tp_lingua
FROM ed_enem_2024_resultados_amos_per
"""

df = pd.read_sql(query, conn)

# -------------------------
# LIMPEZA
# -------------------------
df = df.dropna()
df["sg_uf_prova"] = df["sg_uf_prova"].str.strip().str.upper()

# -------------------------
# FILTROS
# -------------------------
st.sidebar.markdown("---")
st.sidebar.header("🎛️ Filtros")

ufs = st.sidebar.multiselect("Estados", sorted(df["sg_uf_prova"].unique()))

nota_min, nota_max = st.sidebar.slider(
    "Faixa da média",
    float(df["nota_media_5_notas"].min()),
    float(df["nota_media_5_notas"].max()),
    (200.0, 800.0)
)

if ufs:
    df = df[df["sg_uf_prova"].isin(ufs)]

df = df[
    (df["nota_media_5_notas"] >= nota_min) &
    (df["nota_media_5_notas"] <= nota_max)
]

# -------------------------
# FUNÇÃO DISTRIBUIÇÃO
# -------------------------
def plot_dist(coluna, nome):
    st.markdown(f"### {nome}")

    col1, col2 = st.columns(2)

    with col1:
        fig_hist = px.histogram(
            df,
            x=coluna,
            nbins=30,
            color_discrete_sequence=[cores[0]]
        )
        st.plotly_chart(fig_hist, width="stretch")

    with col2:
        fig_box = px.box(
            df,
            y=coluna,
            color_discrete_sequence=[cores[2]],
            points="outliers"
        )
        st.plotly_chart(fig_box, width="stretch")

    stats = df[coluna].describe()

    col3, col4, col5, col6 = st.columns(4)
    col3.metric("Média", round(stats["mean"], 2))
    col4.metric("Mediana", round(stats["50%"], 2))
    col5.metric("Desvio", round(stats["std"], 2))
    col6.metric("Min/Max", f"{round(stats['min'],1)} / {round(stats['max'],1)}")


# -------------------------
# PÁGINAS
# -------------------------

# 🗺️ ANÁLISE POR ESTADO (COM SUBPÁGINAS)
if pagina == "Distribuição por Estado":

    st.title("🗺️ Análise por Estado")

    subpagina = st.radio(
        "Selecione a visualização:",
        ["Mapa de Desempenho", "Boxplot por Estado"],
        horizontal=True
    )

    # MAPA
    if subpagina == "Mapa de Desempenho":

        mapa = df.groupby("sg_uf_prova")["nota_media_5_notas"].mean().reset_index()
        mapa.columns = ["sigla", "media"]

        fig = px.choropleth(
            mapa,
            geojson=geojson,
            locations="sigla",
            featureidkey="properties.sigla",
            color="media",
            color_continuous_scale=scale_roxo
        )

        fig.update_geos(fitbounds="locations", visible=False)

        st.plotly_chart(fig, width="stretch")

    # BOXPLOT
    elif subpagina == "Boxplot por Estado":

        fig = px.box(
            df,
            x="sg_uf_prova",
            y="nota_media_5_notas",
            color_discrete_sequence=[cores[1]]
        )

        st.plotly_chart(fig, width="stretch")


# 🌍 TIPO DE LINGUAGEM
elif pagina == "Tipo de Linguagem":

    st.title("🌍 Tipo de Linguagem")

    df_lingua = df.copy()
    df_lingua["tp_lingua"] = df_lingua["tp_lingua"].replace({0: "Espanhol", 1: "Inglês"})

    dist = df_lingua["tp_lingua"].value_counts().reset_index()
    dist.columns = ["Língua", "Quantidade"]

    total = dist["Quantidade"].sum()
    dist["Percentual"] = (dist["Quantidade"] / total * 100).round(1)
    dist = dist.sort_values(by="Quantidade", ascending=True)

    fig = px.bar(
        dist,
        x="Quantidade",
        y="Língua",
        orientation="h",
        color="Língua",
        color_discrete_sequence=[cores[3], cores[1]],
        text=dist["Percentual"].astype(str) + "%"
    )

    fig.update_layout(showlegend=False)
    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, width="stretch")


# 📈 DISTRIBUIÇÕES POR NOTA (COM SUBPÁGINAS)
elif pagina == "Distribuições por Nota":

    st.title("📈 Distribuições por Nota")

    subpagina_nota = st.radio(
        "Selecione a disciplina:",
        [
            "Matemática",
            "Linguagens",
            "Ciências Humanas",
            "Ciências da Natureza",
            "Redação"
        ],
        horizontal=True
    )

    if subpagina_nota == "Matemática":
        plot_dist("nota_mt_matematica", "Distribuição - Matemática")

    elif subpagina_nota == "Linguagens":
        plot_dist("nota_lc_linguagens_e_codigos", "Distribuição - Linguagens")

    elif subpagina_nota == "Ciências Humanas":
        plot_dist("nota_ch_ciencias_humanas", "Distribuição - Ciências Humanas")

    elif subpagina_nota == "Ciências da Natureza":
        plot_dist("nota_cn_ciencias_da_natureza", "Distribuição - Ciências da Natureza")

    elif subpagina_nota == "Redação":
        plot_dist("nota_redacao", "Distribuição - Redação")


# 📊 ESTATÍSTICAS
elif pagina == "Estatísticas Gerais":

    st.title("📊 Estatísticas Gerais")
    st.dataframe(df.describe())
