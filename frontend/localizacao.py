import streamlit as st
import sqlite3
import plotly.express as px
import pandas as pd
import pycountry
from fuzzywuzzy import process



# Análise Exclusivas:
#     Mapa de Calor Geográfico (heatmap)
# Diferenças Regionais:
#     Top 3 categorias por cidade
#     Preferência de método de pagamento por região
#     Média de uso de Cupons por localidade
# Análise de fronteira:
#     Cidades com maior ticket médio vs cidades com maior fidelidade
#         (frequência de compras)
  
st.subheader('', divider=True)

conn = sqlite3.connect("data/shopping.db")
cursor = conn.cursor()

cursor.execute('SELECT DISTINCT location FROM shopping')

cidades = [row[0] for row in cursor.fetchall() if row[0] is not None]

cidades.sort()

natureza_escolhida = st.selectbox("**Selecione uma cidade:**", cidades)

## Big Numbers

col1, col2, col3, col4 = st.columns(4)

# Ticket Médio
cursor.execute('SELECT AVG(purchase_amount_usd) FROM shopping WHERE location = ?', (natureza_escolhida,))
ticket_medio = cursor.fetchone()[0]

col1.container(border=True).metric('Ticked Médio', f'{ticket_medio:.2f}')

## Total de Vendas
cursor.execute('SELECT SUM(purchase_amount_usd) FROM shopping WHERE location = ?', (natureza_escolhida,))
total_amount = cursor.fetchone()[0]

col2.container(border=True).metric('Renda total', f'{total_amount:.2f} $USD')

## Total de Clientes
cursor.execute('SELECT COUNT(*) FROM shopping WHERE location = ?', (natureza_escolhida,))
total_clientes = cursor.fetchone()[0]

col3.container(border=True).metric('Número de Clientes', f'{total_clientes}')

## Idade Média
cursor.execute('SELECT AVG(age) FROM shopping WHERE location = ?', (natureza_escolhida,))
idade_media = cursor.fetchone()[0]

col4.container(border=True).metric('Idade Média', f'{idade_media:.2f}')

col1, col2, col3 = st.columns(3)

## Aderência de Cupons
cursor.execute('SELECT COUNT(*) FROM shopping WHERE location = ? AND promo_code_used = "Yes" ', (natureza_escolhida,))
ad_cupom =  (cursor.fetchone()[0] / total_clientes) * 100

col1.container(border=True).metric('Taxa de Aderência de Cupons', f'{ad_cupom:.2%}')

## Satisfação Regional
cursor.execute('SELECT AVG(review_rating) FROM shopping WHERE location = ?', (natureza_escolhida,))
avg_rat = cursor.fetchone()[0]

col2.container(border=True).metric('Satisfação Média', f'{avg_rat:.2f}')

## Taxa de Assinantes
cursor.execute('SELECT COUNT(*) FROM shopping WHERE location = ? AND subscription_status = "Yes"', (natureza_escolhida,))
taxa_assinantes = (cursor.fetchone()[0] / total_clientes) * 100

col3.container(border=True).metric('Taxa de Assinantes', f'{taxa_assinantes:.2%}')

localizacao, pagamentos, generos = st.tabs(['Análise Pelo Valor e Categoria', 'Análise Pelo Método de Pagamento', 'Analise por Gênero'])

with localizacao:

    cursor.execute("DROP VIEW IF EXISTS maps")

    cursor.execute('''
        CREATE VIEW IF NOT EXISTS maps AS
            SELECT 
                location,
                category,
                SUM(purchase_amount_usd) AS total_amount
            FROM
                shopping
            GROUP BY
                location, category
            ORDER BY
                location, total_amount DESC
    ''')

    df = pd.read_sql_query("SELECT * FROM maps WHERE location = ?", conn, params=(natureza_escolhida,))

    fig = px.histogram(df, x="location", y='total_amount', color="category")
    st.plotly_chart(fig)

with pagamentos:

    cursor.execute("DROP VIEW IF EXISTS maps")

    cursor.execute('''
        CREATE VIEW IF NOT EXISTS payments AS
                SELECT 
                        location,
                        payment_method,
                        COUNT(payment_method) as quantidade
                    FROM 
                        shopping
                    GROUP BY
                        location,
                        payment_method
                ORDER BY
                        location
    ''')

    df = pd.read_sql_query("SELECT * FROM payments WHERE location = ?", conn, params=(natureza_escolhida,))

    fig = px.pie(df, values='quantidade', names='payment_method')
    st.plotly_chart(fig)

with generos:

    cursor.execute("DROP VIEW IF EXISTS genders")

    cursor.execute('''
                CREATE VIEW IF NOT EXISTS genders AS
                    SELECT
                        location,
                        category,
                        COUNT(gender) AS quantidade,
                        gender
                    FROM
                        shopping
                    GROUP BY
                        location,
                        gender
                    ORDER BY
                        location 
                   ''')
    
    df = pd.read_sql_query("SELECT * FROM genders WHERE location = ?", conn, params=(natureza_escolhida,))

    fig = px.histogram(df, x="gender", y='quantidade', color="category")
    st.plotly_chart(fig)
