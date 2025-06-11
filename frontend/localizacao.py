import streamlit as st
import sqlite3


# Análise Exclusivas:
#     Mapa de Calor Geográfico (heatmap)
# Diferenças Regionais:
#     Top 3 categorias por cidade
#     Preferência de método de pagamento por região
#     Média de uso de Cupons por localidade
# Análise de fronteira:
#     Cidades com maior ticket médio vs cidades com maior fidelidade
#         (frequência de compras)

st.markdown("<h1 style='text-align: center;'>🌎 Análise por Localização </h1>", unsafe_allow_html=True)

st.subheader('', divider=True)

conn = sqlite3.connect("data/shopping.db")
cursor = conn.cursor()

cursor.execute('SELECT DISTINCT location FROM shopping')

cidades = [row[0] for row in cursor.fetchall() if row[0] is not None]

cidades.insert(0, "Todas")

natureza_escolhida = st.selectbox("**Selecione uma cidade:**", cidades)

## Big Numbers

# Ticket Médio
cursor.execute('SELECT AVG(purchase_amount_usd) FROM shopping WHERE location = ?', (natureza_escolhida,))
ticket_medio = cursor.fetchone()[0]

## Total de Vendas
cursor.execute('SELECT SUM(purchase_amount_usd) FROM shopping WHERE location = ?', (natureza_escolhida,))
total_amount = cursor.fetchone()[0]

## Total de Clientes
cursor.execute('SELECT COUNT(*) FROM shopping WHERE location = ?', (natureza_escolhida,))
total_clientes = cursor.fetchone()[0]

## Aderência de Cupons
cursor.execute('SELECT COUNT(*) FROM shopping WHERE location = ? AND promo_code_used = "Yes" ', (natureza_escolhida,))
ad_cupom =  (cursor.fetchone()[0] / total_clientes) * 100

## Satisfação Regional
cursor.execute('SELECT AVG(review_rating) FROM shopping WHERE location = ?', (natureza_escolhida,))
avg_rat = cursor.fetchone()[0]

## Taxa de Assinantes
cursor.execute('SELECT COUNT(*) FROM shopping WHERE location = ? AND subscription_status = "YES"', (natureza_escolhida,))
taxa_assinantes = cursor.fetchall() 
st.write(ad_cupom)
st.write(taxa_assinantes)