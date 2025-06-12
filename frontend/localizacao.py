import streamlit as st
import sqlite3
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

def kpi_box(title, value, gradient_css):
    return f"""
    <div style="
        background: {gradient_css};
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        font-family: Arial, sans-serif;
        margin-bottom: 10px;
    ">
        <div style="font-size: 18px; font-weight: 500; color: #333;">{title}</div>
        <p style='font-size: 24px; margin: 5px 0 0 0; font-weight: bold;'>{value}</p>
    </div>
    """
st.markdown(f"<h1 style='text-align: center;'>🌎 Análise por Localização </h1>", unsafe_allow_html=True)
  
st.subheader('', divider=True)

conn = sqlite3.connect("data/shopping.db")
cursor = conn.cursor()

df = pd.read_sql_query("SELECT * FROM shopping ", conn)

cursor.execute('SELECT DISTINCT location FROM shopping')

cidades = [row[0] for row in cursor.fetchall() if row[0] is not None]

cidades.sort()

natureza_escolhida = st.selectbox("**Selecione uma cidade:**", cidades)

df = pd.read_sql_query("SELECT * FROM shopping", conn)

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

df['state_code'] = df['location'].map(state_abbrev)

selected_state_abbrev = state_abbrev.get(natureza_escolhida)

revenue_by_state = (
    df.dropna(subset=['state_code'])
    .groupby('state_code', as_index=False)['purchase_amount_usd']
    .sum()
    .rename(columns={'purchase_amount_usd': 'total_revenue'})
)

revenue_by_state['highlight'] = revenue_by_state['state_code'] == selected_state_abbrev

fig_map = px.choropleth(
    revenue_by_state,
    locations='state_code',
    locationmode='USA-states',
    color='total_revenue',
    scope='usa',
    title=' ',
    labels={'total_revenue': 'Receita (USD)'},
    color_continuous_scale='Blues'
)

if selected_state_abbrev:
    fig_map.update_traces(
        marker_line_width=1,
        marker_line_color='gray',
        selector=dict(type='choropleth')
    )
    
    fig_map.add_trace(
        go.Choropleth(
            locations=[selected_state_abbrev],
            z=[1],  # Valor fictício para cor
            locationmode='USA-states',
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']], 
            marker_line_width=3,
            marker_line_color='red',
            showscale=False,
            hoverinfo='skip'
        )
    )

# Centralizar título


## Big Numbers

col1, col2 = st.columns(2)

## Total de Vendas
cursor.execute('SELECT SUM(purchase_amount_usd) FROM shopping WHERE location = ?', (natureza_escolhida,))
total_amount = cursor.fetchone()[0]

with col1:
    st.markdown(kpi_box("Faturamento Total", f"$USD {total_amount:.2f}", "linear-gradient(to top, #d0f0c0, #b0e57c)"), unsafe_allow_html=True)

# Ticket Médio
cursor.execute('SELECT AVG(purchase_amount_usd) FROM shopping WHERE location = ?', (natureza_escolhida,))
ticket_medio = cursor.fetchone()[0]

with col2:
    st.markdown(kpi_box("Ticket Médio", f"$USD {ticket_medio:.2f}", "linear-gradient(to top, #d0f0c0, #b0e57c)"), unsafe_allow_html=True)


col1, col2, col3, col4 = st.columns(4)

## Total de Clientes
cursor.execute('SELECT COUNT(*) FROM shopping WHERE location = ?', (natureza_escolhida,))
total_clientes = cursor.fetchone()[0]

with col1:
    st.markdown(kpi_box("Número de Clientes", f"{total_clientes}", "linear-gradient(to bottom, #4d94d4, #cceeff)"), unsafe_allow_html=True)

## Idade Média
cursor.execute('SELECT AVG(age) FROM shopping WHERE location = ?', (natureza_escolhida,))
idade_media = cursor.fetchone()[0]

with col2:
    st.markdown(kpi_box("Idade Média", f"{idade_media:.2f}", "linear-gradient(to bottom, #4d94d4, #cceeff)"), unsafe_allow_html=True)

## Satisfação Regional
cursor.execute('SELECT AVG(review_rating) FROM shopping WHERE location = ?', (natureza_escolhida,))
avg_rat = cursor.fetchone()[0]

with col3:
    st.markdown(kpi_box("Satisfação Média", f"{avg_rat:.2f}", "linear-gradient(to bottom, #4d94d4, #cceeff)"), unsafe_allow_html=True)

## Taxa de Assinantes
cursor.execute('SELECT COUNT(*) FROM shopping WHERE location = ? AND subscription_status = "Yes"', (natureza_escolhida,))
taxa_assinantes = (cursor.fetchone()[0] / total_clientes)

with col4:
    st.markdown(kpi_box("Taxa de Assinantes", f"{taxa_assinantes:.2f}", "linear-gradient(to bottom, #4d94d4, #cceeff)"), unsafe_allow_html=True)

st.subheader('', divider=True)

fig_map.update_layout(title_x=0.35)
st.markdown(f"<h3 style='text-align: center;'>🌍 Receita Total por Estado </h3>", unsafe_allow_html=True)

st.plotly_chart(fig_map, use_container_width=True)

col1, col2 = st.columns(2)

with col1.container(border=True):
    localizacao, pagamentos,  = st.tabs([
    'Análise Pelo Valor e Categoria', 
    'Análise Pelo Método de Pagamento'
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
        
        fig = px.bar(df,
                    x="category",
                    y='total_amount',
                    color='category',
                    title='Valor Total de Vendas por Categoria')
        fig.update_layout(title_x=0.35)
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
        
        fig = px.pie(df,
                    values='quantidade',
                    names='payment_method', 
                    title='Distribuição de Métodos de Pagamento')
        fig.update_layout(title_x=0.30) 
        st.plotly_chart(fig)


with col2.container(border=True):
    generos, descontos = st.tabs([
    'Análise por Gênero',
    'Descontos e Vendas'
    ])
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
        
        fig = px.bar(df,
                        x="quantidade",
                        y='gender',
                        color="gender",
                        title='Distribuição de Compras por Gênero')
        fig.update_layout(title_x=0.30) 
        st.plotly_chart(fig)

    with descontos:
        st.subheader("Impacto de Descontos nas Vendas", divider=True, anchor=False)
        
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
        
        fig1 = px.bar(df_discount,
                        x='Total Compras',
                        y='Desconto', 
                        title='Volume de Compras com e sem Desconto',
                        color='Desconto',
                        color_continuous_scale='Blues'
                    )
        fig1.update_layout(title_x=0.30)
            
        st.plotly_chart(fig1)

sazonalidade, preferencias = st.tabs([
    'Sazonalidade',
    'Preferências (Tamanho/Cor'])

with sazonalidade:
    st.subheader("Padrões de Compras Sazonais", divider=True, anchor=False)
    
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
    
    fig1 = px.bar(df_season,
                 x='Estação',
                 y='Vendas Totais', 
                 title='Vendas Totais por Estação',
                 color='Estação',
                 color_continuous_scale='Blues'
                 )
    fig1.update_layout(title_x=0.3)
    
    fig2 = px.line(df_season,
                    x='Estação',
                    y='Total Compras', 
                    title='Volume de Compras por Estação',
                    markers=True)
    fig2.update_layout(title_x=0.3)
    
    col1, col2 = st.columns(2)

    col1.container(border=True).plotly_chart(fig1)
    col2.container(border=True).plotly_chart(fig2)

with preferencias:
    st.subheader("Preferências de Tamanho e Cor", divider=True, anchor=False)
    
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
    
    fig_size = px.bar(df_size,
                        x='Tamanho',
                        y='Total', 
                        title='Preferência de Tamanhos',
                        color='Tamanho')
    fig_size.update_layout(title_x=0.38)
    
    fig_color = px.bar(df_color,
                        x='Cor',
                        y='Total', 
                        title='Preferência de Cores',
                        color='Cor',
                        color_continuous_scale='Blues'
                       )
    fig_color.update_layout(title_x=0.38)
    
    col1, col2 = st.columns(2)

    col1.container(border=True).plotly_chart(fig_size, use_container_width=True)
    col2.container(border=True).plotly_chart(fig_color, use_container_width=True)

conn.close()