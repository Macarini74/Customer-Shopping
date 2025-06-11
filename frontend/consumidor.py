import sqlite3
import pandas as pd
import streamlit as st

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


