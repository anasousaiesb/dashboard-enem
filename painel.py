import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import requests

# -------------------------
# CONFIGURAÇÃO
# -------------------------
st.set_page_config(page_title="Análise do ENEM 2024", layout="wide")

# PALETA MAIS CLARA
cores = ["#E0AAFF", "#C77DFF", "#9D4EDD", "#7B2CBF"]
scale_roxo = ["#f8f0ff", "#e0aaff", "#c77dff", "#9d4edd"]

# -------------------------
# TÍTULO + TEXTO
# -------------------------
st.markdown("""
<div style='background: linear-gradient(90deg, #E0AAFF, #C77DFF);
padding:25px;border-radius:12px'>
<h1 style='color:white;'>📊 Análise do ENEM 2024</h1>
<p style='color:white;font-size:16px'>
Este painel interativo tem como objetivo apresentar uma análise exploratória dos dados do ENEM 2024, permitindo a visualização e interpretação de padrões relevantes no desempenho dos participantes. Por meio de técnicas de estatística descritiva e visualização de dados, são exploradas distribuições de notas, variações regionais e características dos candidatos, como a escolha de idioma na prova.
A plataforma foi desenvolvida com o intuito de facilitar a compreensão dos dados de forma intuitiva, utilizando gráficos interativos que possibilitam uma análise dinâmica e comparativa. Dessa forma, o usuário pode identificar tendências, dispersões e diferenças significativas entre grupos, contribuindo para uma visão mais ampla e fundamentada dos resultados do exame.

</p>
</div>
""", unsafe_allow_html=True)

# -------------------------
# GEOJSON
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

# LIMPEZA
df = df.dropna()
df["sg_uf_prova"] = df["sg_uf_prova"].str.strip().str.upper()

# -------------------------
# FILTROS
# -------------------------
st.sidebar.header(" Filtros")

ufs = st.sidebar.multiselect("Estados", sorted(df["sg_uf_prova"].unique()))

nota_min, nota_max = st.sidebar.slider(
    "Faixa da média",
    float(df["nota_media_5_notas"].min()),
    float(df["nota_media_5_notas"].max()),
    (200.0, 800.0)
)

if ufs:
    df = df[df["sg_uf_prova"].isin(ufs)]

df = df[(df["nota_media_5_notas"] >= nota_min) & (df["nota_media_5_notas"] <= nota_max)]

# -------------------------
# MENU PRINCIPAL (ABAS)
# -------------------------
abas = st.tabs([
    " Distribuição Geográfica",
    " Idioma",
    " Notas",
    " Desempenho Geral",
    " Estatísticas"
])

# -------------------------
# 📍 ESTADOS
# -------------------------
with abas[0]:
    st.subheader("Distribuição por Estado")

    dist = df["sg_uf_prova"].value_counts().reset_index()
    dist.columns = ["Estado", "Quantidade"]

    fig = px.bar(
        dist,
        x="Estado",
        y="Quantidade",
        color="Quantidade",
        color_continuous_scale=scale_roxo
    )

    st.plotly_chart(fig, width='stretch')

# -------------------------
# 🌍 LINGUAGEM
# -------------------------
with abas[1]:
    st.subheader("Tipo de Linguagem")

    df_lingua = df.copy()
    df_lingua["tp_lingua"] = df_lingua["tp_lingua"].replace({0: "Espanhol", 1: "Inglês"})

    dist = df_lingua["tp_lingua"].value_counts().reset_index()
    dist.columns = ["Língua", "Quantidade"]

    fig = px.bar(
        dist,
        x="Língua",
        y="Quantidade",
        color="Língua",
        color_discrete_sequence=cores
    )

    st.plotly_chart(fig, width='stretch')

# -------------------------
# 📊 NOTAS (SUBABAS)
# -------------------------
with abas[2]:
    st.subheader("Distribuições por Nota")

    subabas = st.tabs([
        "Matemática",
        "Linguagens",
        "Humanas",
        "Natureza",
        "Redação"
    ])

    def plot_nota(coluna):
        col1, col2 = st.columns(2)

        with col1:
            fig = px.histogram(df, x=coluna, nbins=30,
                               color_discrete_sequence=[cores[1]])
            st.plotly_chart(fig, width='stretch')

        with col2:
            fig = px.box(df, y=coluna,
                         color_discrete_sequence=[cores[2]])
            st.plotly_chart(fig, width='stretch')

    with subabas[0]:
        plot_nota("nota_mt_matematica")

    with subabas[1]:
        plot_nota("nota_lc_linguagens_e_codigos")

    with subabas[2]:
        plot_nota("nota_ch_ciencias_humanas")

    with subabas[3]:
        plot_nota("nota_cn_ciencias_da_natureza")

    with subabas[4]:
        plot_nota("nota_redacao")

# -------------------------
# 📦 ESTADO (MAPA + BOXPLOT)
# -------------------------
with abas[3]:
    st.subheader("Análises por Estado")

    subabas2 = st.tabs(["Mapa", "Boxplot"])

    # MAPA
    with subabas2[0]:
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
        st.plotly_chart(fig, width='stretch')

    # BOXPLOT
    with subabas2[1]:
        fig = px.box(
            df,
            x="sg_uf_prova",
            y="nota_media_5_notas",
            color_discrete_sequence=[cores[1]]
        )

        st.plotly_chart(fig, width='stretch')

# -------------------------
# 📈 ESTATÍSTICAS
# -------------------------
with abas[4]:
    st.subheader("Estatísticas Gerais")
    st.dataframe(df.describe())

# -------------------------
# RODAPÉ
# -------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:gray'>Desenvolvido por Ana Sophia Sousa</p>",
    unsafe_allow_html=True
)
