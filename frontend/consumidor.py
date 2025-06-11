import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px


conn = sqlite3.connect('data/shopping.db')

query_revenue = """
SELECT SUM(purchase_amount_usd) AS total_revenue
FROM shopping
"""
total_revenue = pd.read_sql_query(query_revenue, conn)['total_revenue'][0] or 0.0

query_avg_ticket = """
SELECT AVG(purchase_amount_usd) AS avg_ticket
FROM shopping
"""
avg_ticket = pd.read_sql_query(query_avg_ticket, conn)['avg_ticket'][0] or 0.0

query_top_decade = """
SELECT
  (age/10)*10 AS decade_floor,
  COUNT(*) AS cnt
FROM shopping
GROUP BY decade_floor
ORDER BY cnt DESC
LIMIT 1
"""
decade_df = pd.read_sql_query(query_top_decade, conn)
if not decade_df.empty:
    top_decade = int(decade_df['decade_floor'][0])
    faixa_etaria = f"{top_decade}-{top_decade+9} anos"
else:
    faixa_etaria = "N/A"

query_top_gender = """
SELECT gender, COUNT(*) AS cnt
FROM shopping
GROUP BY gender
ORDER BY cnt DESC
LIMIT 1
"""
gender_df = pd.read_sql_query(query_top_gender, conn)
if not gender_df.empty:
    genero_raw = gender_df['gender'][0].lower()
    mapa_genero = {
        'male': 'Masculino',
        'female': 'Feminino'
    }
    genero_predominante = mapa_genero.get(genero_raw, genero_raw.title())
else:
    genero_predominante = "N/A"

st.markdown("<h1 style='text-align: center;'>👤 Perfil do Consumidor</h1>", unsafe_allow_html=True)
st.divider()

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Receita Total (USD)", f"{total_revenue:,.2f}")
col2.metric("🛒 Ticket Médio (USD)", f"{avg_ticket:,.2f}")
col3.metric("👥 Faixa Etária Mais Numerosa", faixa_etaria)
col4.metric("🚻 Gênero Predominante", genero_predominante)

st.divider()

with st.expander("🛠️ Filtrar dados para as análises", expanded=True):
    min_age, max_age = st.slider(
        "Selecione a faixa de idade",
        int(pd.read_sql_query("SELECT MIN(age) FROM shopping", conn).iloc[0,0]),
        int(pd.read_sql_query("SELECT MAX(age) FROM shopping", conn).iloc[0,0]),
        (18, 65)
    )

    genders = [row[0] for row in conn.execute("SELECT DISTINCT gender FROM shopping").fetchall()]
    selected_genders = st.multiselect("Selecione gêneros", options=genders, default=genders)

df = pd.read_sql_query("SELECT * FROM shopping", conn)
df = df[
    df.age.between(min_age, max_age) &
    df.gender.isin(selected_genders)
]

df['age_decade'] = (df.age // 10) * 10

heatmap_df = (
    df
    .groupby(['age_decade', 'category'])
    .size()
    .reset_index(name='count')
    .pivot(index='age_decade', columns='category', values='count')
    .fillna(0)
)

y_labels = [f"{int(d)}-{int(d)+9}" for d in heatmap_df.index]

fig = px.imshow(
    heatmap_df.values,
    x=heatmap_df.columns,
    y=y_labels,
    labels=dict(x="Categoria", y="Década de Vida", color="Contagem"),
    text_auto=True,
    aspect="auto",
)

st.subheader("🗺️ Faixa Etária vs. Categoria Preferida")
st.plotly_chart(fig, use_container_width=True)

st.divider()

