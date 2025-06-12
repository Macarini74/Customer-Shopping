import streamlit as st
import sqlite3
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

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

df = pd.read_sql_query("SELECT * FROM shopping ", conn)

cursor.execute('SELECT DISTINCT location FROM shopping')

cidades = [row[0] for row in cursor.fetchall() if row[0] is not None]

cidades.sort()

natureza_escolhida = st.selectbox("**Selecione uma cidade:**", cidades)

# Carregar todos os dados
df = pd.read_sql_query("SELECT * FROM shopping", conn)

# 1. Dicionário de mapeamento: estado completo → sigla USPS
state_abbrev = {
    'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA',
    'Colorado':'CO','Connecticut':'CT','Delaware':'DE','Florida':'FL','Georgia':'GA',
    'Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA',
    'Kansas':'KS','Kentucky':'KY','Louisiana':'LA','Maine':'ME','Maryland':'MD',
    'Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS',
    'Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV',
    'New Hampshire':'NH','New Jersey':'NJ','New Mexico':'NM','New York':'NY',
    'North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK',
    'Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC',
    'South Dakota':'SD','Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT',
    'Virginia':'VA','Washington':'WA','West Virginia':'WV','Wisconsin':'WI',
    'Wyoming':'WY'
}

# 2. Criar coluna com sigla
df['state_code'] = df['location'].map(state_abbrev)

# 3. Obter sigla do estado selecionado
selected_state_abbrev = state_abbrev.get(natureza_escolhida)

# 4. Agregar receita por estado
revenue_by_state = (
    df.dropna(subset=['state_code'])
    .groupby('state_code', as_index=False)['purchase_amount_usd']
    .sum()
    .rename(columns={'purchase_amount_usd': 'total_revenue'})
)

# 5. Criar coluna para destacar o estado selecionado
revenue_by_state['highlight'] = revenue_by_state['state_code'] == selected_state_abbrev

# 6. Plotar choropleth dos EUA com destaque
fig_map = px.choropleth(
    revenue_by_state,
    locations='state_code',
    locationmode='USA-states',
    color='total_revenue',
    scope='usa',
    title='💰 Receita Total por Estado (EUA)',
    labels={'total_revenue': 'Receita (USD)'},
    color_continuous_scale='Blues'
)

# Destacar o estado selecionado com borda
if selected_state_abbrev:
    fig_map.update_traces(
        marker_line_width=1,
        marker_line_color='gray',
        selector=dict(type='choropleth')
    )
    
    # Adicionar borda destacada para o estado selecionado
    fig_map.add_trace(
        go.Choropleth(
            locations=[selected_state_abbrev],
            z=[1],  # Valor fictício para cor
            locationmode='USA-states',
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],  # Preenchimento transparente
            marker_line_width=3,
            marker_line_color='red',
            showscale=False,
            hoverinfo='skip'
        )
    )

# Centralizar título
fig_map.update_layout(title_x=0.5)

st.subheader("🌍 Receita Total por Estado")
st.plotly_chart(fig_map, use_container_width=True)

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

# Adicionando novas abas
localizacao, pagamentos, generos, descontos, sazonalidade, preferencias = st.tabs([
    'Análise Pelo Valor e Categoria', 
    'Análise Pelo Método de Pagamento', 
    'Analise por Gênero',
    'Descontos e Vendas',
    'Sazonalidade',
    'Preferências (Tamanho/Cor)'
])

with localizacao:
    st.subheader("Vendas por Categoria", divider=True, anchor=False)
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
    
    fig = px.bar(df, x="category", y='total_amount', color='category',
                 title='Valor Total de Vendas por Categoria')
    fig.update_layout(title_x=0.4)  # Centraliza o título
    st.plotly_chart(fig)

with pagamentos:
    st.subheader("Métodos de Pagamento", divider=True, anchor=False)
    cursor.execute("DROP VIEW IF EXISTS payments")
    
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
    
    fig = px.pie(df, values='quantidade', names='payment_method', 
                 title='Distribuição de Métodos de Pagamento')
    fig.update_layout(title_x=0.5)  # Centraliza o título
    st.plotly_chart(fig)

with generos:
    st.subheader("Distribuição por Gênero", divider=True, anchor=False)
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
    
    fig = px.bar(df, x="gender", y='quantidade', color="gender",
                 title='Distribuição de Compras por Gênero')
    fig.update_layout(title_x=0.5)  # Centraliza o título
    st.plotly_chart(fig)

# NOVOS GRÁFICOS ADICIONADOS
with descontos:
    st.subheader("Impacto de Descontos nas Vendas", divider=True, anchor=False)
    
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
    
    # Criando gráficos
    fig1 = px.bar(df_discount, x='Desconto', y='Total Compras', 
                 title='Volume de Compras com e sem Desconto',
                 color='Desconto')
    fig1.update_layout(title_x=0.5)
    
    fig2 = px.bar(df_discount, x='Desconto', y='Valor Médio', 
                 title='Valor Médio por Transação',
                 color='Desconto')
    fig2.update_layout(title_x=0.5)
    
    st.plotly_chart(fig1)
    st.plotly_chart(fig2)

with sazonalidade:
    st.subheader("Padrões de Compras Sazonais", divider=True, anchor=False)
    
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
    
    # Gráficos
    fig1 = px.bar(df_season, x='Estação', y='Vendas Totais', 
                 title='Vendas Totais por Estação',
                 color='Estação')
    fig1.update_layout(title_x=0.5)
    
    fig2 = px.line(df_season, x='Estação', y='Total Compras', 
                 title='Volume de Compras por Estação',
                 markers=True)
    fig2.update_layout(title_x=0.5)
    
    st.plotly_chart(fig1)
    st.plotly_chart(fig2)

with preferencias:
    st.subheader("Preferências de Tamanho e Cor", divider=True, anchor=False)
    
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
    
    # Gráficos
    fig_size = px.bar(df_size, x='Tamanho', y='Total', 
                      title='Preferência de Tamanhos',
                      color='Tamanho')
    fig_size.update_layout(title_x=0.5)
    
    fig_color = px.bar(df_color, x='Cor', y='Total', 
                       title='Preferência de Cores',
                       color='Cor')
    fig_color.update_layout(title_x=0.5)
    
    fig_pie = px.pie(df_color, values='Total', names='Cor', 
                     title='Distribuição Percentual de Cores')
    fig_pie.update_layout(title_x=0.5)
    
    st.plotly_chart(fig_size)
    st.plotly_chart(fig_color)
    st.plotly_chart(fig_pie)

# Fechar conexão com o banco de dados
conn.close()