import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import requests

# -------------------------
# CONFIGURAÇÃO
# -------------------------
st.set_page_config(page_title="Dashboard ENEM 2024", layout="wide")

# -------------------------
# CSS
# -------------------------
st.markdown("""
<style>
body {
    background-color: #f8f0ff;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #E0AAFF, #C77DFF);
}

h1, h2, h3 {
    color: #7B2CBF;
}

footer {
    text-align: center;
    color: #7B2CBF;
    margin-top: 50px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# PALETA
# -------------------------
cores = ["#C77DFF", "#E0AAFF", "#D8B4FE", "#F3E8FF"]
scale_roxo = ["#f8f0ff", "#E0AAFF", "#C77DFF", "#9D4EDD"]

# -------------------------
# HEADER
# -------------------------
st.markdown("""
<div style="background: linear-gradient(90deg, #E0AAFF, #C77DFF);
padding: 25px;
border-radius: 15px;
text-align: center;
color: #4B0082;">

<h1>📊 Análise do ENEM 2024</h1>

<p>
Este painel interativo analisa os dados do ENEM 2024, explorando distribuições de notas,
diferenças entre estados e padrões de desempenho.
</p>

</div>
""", unsafe_allow_html=True)

# -------------------------
# MENU
# -------------------------
pagina = st.sidebar.radio("📂 Navegação", [
    "Distribuição por Estado",
    "Tipo de Linguagem",
    "Distribuições por Nota",
    "Boxplot por Estado",
    "Estatísticas Gerais"
])

# -------------------------
# GEOJSON (MAPA)
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

df = df.dropna()
df["sg_uf_prova"] = df["sg_uf_prova"].str.strip().str.upper()

# -------------------------
# FILTROS
# -------------------------
st.sidebar.markdown("---")
ufs = st.sidebar.multiselect("Estados", sorted(df["sg_uf_prova"].unique()))

if ufs:
    df = df[df["sg_uf_prova"].isin(ufs)]

# -------------------------
# FUNÇÃO DISTRIBUIÇÃO
# -------------------------
def plot_dist(coluna, nome):
    st.markdown(f"### {nome}")
    col1, col2 = st.columns(2)

    with col1:
        fig_hist = px.histogram(df, x=coluna, nbins=30,
                                color_discrete_sequence=[cores[0]])
        st.plotly_chart(fig_hist, width='stretch')

    with col2:
        fig_box = px.box(df, y=coluna,
                         color_discrete_sequence=[cores[1]])
        st.plotly_chart(fig_box, width='stretch')

# -------------------------
# PÁGINAS
# -------------------------

if pagina == "Distribuição por Estado":
    st.title("📍 Distribuição por Estado")

    dist = df["sg_uf_prova"].value_counts().reset_index()
    dist.columns = ["UF", "Quantidade"]

    fig = px.bar(dist, x="UF", y="Quantidade",
                 color="Quantidade",
                 color_continuous_scale=scale_roxo)

    st.plotly_chart(fig, width='stretch')


elif pagina == "Tipo de Linguagem":
    st.title("🌍 Tipo de Linguagem")

    df_lingua = df.copy()
    df_lingua["tp_lingua"] = df_lingua["tp_lingua"].replace({0: "Espanhol", 1: "Inglês"})

    dist = df_lingua["tp_lingua"].value_counts().reset_index()
    dist.columns = ["Língua", "Quantidade"]

    fig = px.bar(dist, x="Língua", y="Quantidade",
                 color="Língua",
                 color_discrete_sequence=cores)

    st.plotly_chart(fig, width='stretch')


# 🔥 SUBPÁGINAS VOLTARAM
elif pagina == "Distribuições por Nota":
    st.title("📈 Distribuições por Nota")

    subpagina = st.radio("Escolha a nota:", [
        "Matemática",
        "Linguagens",
        "Humanas",
        "Natureza",
        "Redação"
    ])

    if subpagina == "Matemática":
        plot_dist("nota_mt_matematica", "Matemática")

    elif subpagina == "Linguagens":
        plot_dist("nota_lc_linguagens_e_codigos", "Linguagens")

    elif subpagina == "Humanas":
        plot_dist("nota_ch_ciencias_humanas", "Humanas")

    elif subpagina == "Natureza":
        plot_dist("nota_cn_ciencias_da_natureza", "Natureza")

    elif subpagina == "Redação":
        plot_dist("nota_redacao", "Redação")


# 🔥 AQUI É A PARTE PRINCIPAL QUE VOCÊ PEDIU
elif pagina == "Boxplot por Estado":
    st.title("📦 Boxplot + Mapa por Estado")

    col1, col2 = st.columns(2)

    # MAPA
    with col1:
        mapa = df.groupby("sg_uf_prova")["nota_media_5_notas"].mean().reset_index()
        mapa.columns = ["sigla", "media"]

        fig_mapa = px.choropleth(
            mapa,
            geojson=geojson,
            locations="sigla",
            featureidkey="properties.sigla",
            color="media",
            color_continuous_scale=scale_roxo
        )

        fig_mapa.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_mapa, width='stretch')

    # BOXPLOT
    with col2:
        fig_box = px.box(
            df,
            x="sg_uf_prova",
            y="nota_media_5_notas",
            color_discrete_sequence=[cores[0]]
        )

        st.plotly_chart(fig_box, width='stretch')


elif pagina == "Estatísticas Gerais":
    st.title("📊 Estatísticas Gerais")
    st.dataframe(df.describe())


# -------------------------
# RODAPÉ
# -------------------------
st.markdown("""
<footer>
Desenvolvido por <b>Ana Sophia Sousa</b> 💜
</footer>
""", unsafe_allow_html=True)
