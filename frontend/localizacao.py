import streamlit as st
import sqlite3
import plotly.express as px
import pandas as pd

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
ad_cupom =  (cursor.fetchone()[0] / total_clientes)

col1.container(border=True).metric('Taxa de Aderência de Cupons', f'{ad_cupom:.2%}')

## Satisfação Regional
cursor.execute('SELECT AVG(review_rating) FROM shopping WHERE location = ?', (natureza_escolhida,))
avg_rat = cursor.fetchone()[0]

col2.container(border=True).metric('Satisfação Média', f'{avg_rat:.2f}')

## Taxa de Assinantes
cursor.execute('SELECT COUNT(*) FROM shopping WHERE location = ? AND subscription_status = "Yes"', (natureza_escolhida,))
taxa_assinantes = (cursor.fetchone()[0] / total_clientes)

col3.container(border=True).metric('Taxa de Assinantes', f'{taxa_assinantes:.2%}')

localizacao, pagamentos, generos, descontos, sazonalidade, preferencias = st.tabs([
    'Análise Pelo Valor e Categoria', 
    'Análise Pelo Método de Pagamento', 
    'Analise por Gênero', 
    'Descontos e Vendas',
    'Sazonalidade',
    'Preferências (Tamanho/Cor)'
])

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

    fig = px.histogram(df, x="category", y='total_amount', color='category')
    st.container(border=True).plotly_chart(fig)

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
    st.container(border=True).plotly_chart(fig)

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
    st.container(border=True).plotly_chart(fig)

with descontos:
    st.subheader("Correlação entre Descontos e Volume de Vendas")
    
    # Consulta para correlacionar descontos e volume de vendas
    cursor.execute("""
        SELECT 
            discount_applied,
            AVG(purchase_amount_usd) AS avg_amount,
            COUNT(*) AS total_compras
        FROM 
            shopping 
        WHERE 
            location = ?
        GROUP BY 
            discount_applied
    """, (natureza_escolhida,))
    
    df_discount = pd.DataFrame(cursor.fetchall(), columns=['Desconto', 'Valor Médio', 'Total Compras'])
    
    # Criando gráfico duplo (barras e linha)
    fig = px.bar(df_discount, x='Desconto', y='Total Compras', 
                 title='Volume de Compras com e sem Desconto',
                 color='Desconto')
    
    fig2 = px.line(df_discount, x='Desconto', y='Valor Médio', 
                  title='Valor Médio por Transação',
                  markers=True)
    
    st.container(border=True).plotly_chart(fig)
    

with sazonalidade:
    st.subheader("Padrões de Compras por Estação")
    
    # Consulta para sazonalidade
    cursor.execute("""
        SELECT 
            season,
            SUM(purchase_amount_usd) AS total_vendas,
            COUNT(*) AS total_compras
        FROM 
            shopping 
        WHERE 
            location = ?
        GROUP BY 
            season
    """, (natureza_escolhida,))
    
    df_season = pd.DataFrame(cursor.fetchall(), columns=['Estação', 'Vendas Totais', 'Total Compras'])
    
    # Gráfico de vendas por estação
    fig = px.bar(df_season, x='Estação', y='Vendas Totais', 
                 title='Vendas Totais por Estação',
                 color='Estação')
    
    # Gráfico de volume de compras por estação
    fig2 = px.pie(df_season, values='Total Compras', names='Estação', 
                 title='Distribuição de Compras por Estação')
    
    col1, col2 = st.columns(2)
    col1.container(border=True).plotly_chart(fig, use_container_width=True)
    col2.container(border=True).plotly_chart(fig2, use_container_width=True)

with preferencias:
    st.subheader("Preferências de Tamanho e Cor")
    
    # Consulta para tamanhos
    cursor.execute("""
        SELECT 
            size,
            COUNT(*) AS total
        FROM 
            shopping 
        WHERE 
            location = ?
        GROUP BY 
            size
    """, (natureza_escolhida,))
    
    df_size = pd.DataFrame(cursor.fetchall(), columns=['Tamanho', 'Total'])
    
    # Consulta para cores
    cursor.execute("""
        SELECT 
            color,
            COUNT(*) AS total
        FROM 
            shopping 
        WHERE 
            location = ?
        GROUP BY 
            color
    """, (natureza_escolhida,))
    
    df_color = pd.DataFrame(cursor.fetchall(), columns=['Cor', 'Total'])
    
    # Gráficos combinados
    fig_size = px.bar(df_size, x='Tamanho', y='Total', 
                      title='Preferência de Tamanhos',
                      color='Tamanho')
    
    fig_color = px.bar(df_color, x='Cor', y='Total', 
                       title='Preferência de Cores',
                       color='Cor')
    
    fig_pie = px.pie(df_color, values='Total', names='Cor', 
                     title='Distribuição de Cores')
    
    st.container(border=True).plotly_chart(fig_size)
    
    col1, col2 = st.columns(2)
    col1.container(border=True).plotly_chart(fig_color, use_container_width=True)
    col2.container(border=True).plotly_chart(fig_pie, use_container_width=True)
    
