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
# CSS (CORES MAIS CLARAS)
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
    font-size: 14px;
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
# TEXTO HEADER (NOVO)
# -------------------------
st.markdown("""
<div style="background: linear-gradient(90deg, #E0AAFF, #C77DFF);
padding: 25px;
border-radius: 15px;
text-align: center;
color: #4B0082;">

<h1>📊 Análise do ENEM 2024</h1>

<p>
Este painel interativo tem como objetivo analisar os dados do ENEM 2024,
explorando distribuições de notas, diferenças entre estados e padrões de desempenho.
A aplicação permite visualizar informações por meio de gráficos estatísticos,
como histogramas, boxplots e distribuições de frequência, auxiliando na interpretação
dos dados e na geração de insights educacionais.
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

df = df[(df["nota_media_5_notas"] >= nota_min) & (df["nota_media_5_notas"] <= nota_max)]

# -------------------------
# FUNÇÃO DISTRIBUIÇÃO (SEM ALTERAR)
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
                         color_discrete_sequence=[cores[1]],
                         points="outliers")
        st.plotly_chart(fig_box, width='stretch')

    stats = df[coluna].describe()
    col3, col4, col5, col6 = st.columns(4)
    col3.metric("Média", round(stats["mean"], 2))
    col4.metric("Mediana", round(stats["50%"], 2))
    col5.metric("Desvio", round(stats["std"], 2))
    col6.metric("Min/Max", f"{round(stats['min'],1)} / {round(stats['max'],1)}")

# -------------------------
# PÁGINAS (NÃO ALTEREI SUA LÓGICA)
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


elif pagina == "Distribuições por Nota":
    st.title("📈 Distribuições por Nota")

    plot_dist("nota_mt_matematica", "Matemática")
    plot_dist("nota_lc_linguagens_e_codigos", "Linguagens")
    plot_dist("nota_ch_ciencias_humanas", "Ciências Humanas")
    plot_dist("nota_cn_ciencias_da_natureza", "Natureza")
    plot_dist("nota_redacao", "Redação")


elif pagina == "Boxplot por Estado":
    st.title("📦 Boxplot por Estado")

    fig = px.box(df, x="sg_uf_prova", y="nota_media_5_notas",
                 color_discrete_sequence=[cores[0]])

    st.plotly_chart(fig, width='stretch')


elif pagina == "Estatísticas Gerais":
    st.title("📊 Estatísticas Gerais")
    st.dataframe(df.describe())


# -------------------------
# RODAPÉ (NOVO)
# -------------------------
st.markdown("""
<footer>
Desenvolvido por <b>Ana Sophia Sousa</b> 💜
</footer>
""", unsafe_allow_html=True)
