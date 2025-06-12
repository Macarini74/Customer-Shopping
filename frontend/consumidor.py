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

with st.container(border=True):
    st.subheader("🗺️ Faixa Etária vs. Categoria Preferida")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

df['genero'] = (
    df['gender']
    .str.lower()
    .map({'male': 'Masculino', 'female': 'Feminino'})
    .fillna(df['gender'].str.title())
)

color_df = (
    df
    .groupby(['genero', 'color'])
    .size()
    .reset_index(name='count')
)

fig1 = px.bar(
    color_df,
    x='color',
    y='count',
    color='genero',
    barmode='group',
    color_discrete_map={
        'Masculino': '#89CFF0',
        'Feminino': '#eb2188'
    },
    labels={
        'color': 'Cor',
        'count': 'Número de Compras',
        'genero': 'Gênero'
    },
    text='count'
)
fig1.update_traces(textposition='outside')
fig1.update_layout(
    xaxis_title='Cor',
    yaxis_title='Número de Compras',
    legend_title='Gênero',
    uniformtext_minsize=8,
    uniformtext_mode='hide'
)

with st.container(border=True):
    st.subheader("🎨 Preferência de Cores por Gênero")
    st.plotly_chart(fig1, use_container_width=True)

st.divider()

mapa_sub = {
    'Yes': 'Assinante',
    'No': 'Não Assinante',
    'Y': 'Assinante',
    'N': 'Não Assinante',
    'Active': 'Assinante',
    'Inactive': 'Não Assinante',
    'Subscribed': 'Assinante',
    'Not Subscribed': 'Não Assinante'
}
df['status_pt'] = (
    df['subscription_status']
    .map(mapa_sub)
    .fillna(df['subscription_status'].str.title())
)

sub_df = (
    df
    .groupby(['genero', 'status_pt'])
    .size()
    .reset_index(name='count')
)

totais_por_genero = sub_df.groupby('genero')['count'].transform('sum')
sub_df['pct'] = sub_df['count'] / totais_por_genero * 100


fig2 = px.bar(
    sub_df,
    x='genero',
    y='pct',
    color='status_pt',
    barmode='stack',
    text=sub_df['pct'].map(lambda x: f"{x:.1f}%"),
    labels={
        'genero': 'Gênero',
        'pct': '% de Clientes',
        'status_pt': 'Status de Assinatura'
    },
    color_discrete_map={
        'Assinante': '#2BAB4D',      
        'Não Assinante': '#B61E1B'   
    }
)
fig2.update_layout(
    yaxis=dict(ticksuffix='%'),
    legend_title_text='Status de Assinatura'
)
fig2.update_traces(textposition='inside')

with st.container(border=True):
    st.subheader("🔖 Adoção de Assinaturas por Gênero")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

mapa_desc = {
    'Yes': 'Com Desconto',
    'No': 'Sem Desconto',
    'Y': 'Com Desconto',
    'N': 'Sem Desconto',
    'True': 'Com Desconto',
    'False': 'Sem Desconto'
}
df['desconto_pt'] = (
    df['discount_applied']
      .map(mapa_desc)
      .fillna(df['discount_applied'])
)

freq_desc = (
    df
    .groupby(['frequency_of_purchases', 'desconto_pt'])
    .size()
    .reset_index(name='count')
)
totais_freq = freq_desc.groupby('frequency_of_purchases')['count'].transform('sum')
freq_desc['pct'] = freq_desc['count'] / totais_freq * 100

fig3 = px.bar(
    freq_desc,
    x='frequency_of_purchases',
    y='pct',
    color='desconto_pt',
    barmode='stack',
    text=freq_desc['pct'].map(lambda x: f"{x:.1f}%"),
    labels={
        'frequency_of_purchases': 'Frequência de Compras',
        'pct': '% de Compras',
        'desconto_pt': 'Desconto Aplicado'
    },
    color_discrete_map={
        'Com Desconto': '#4CAF50',
        'Sem Desconto': '#B0BEC5'
    }
)
fig3.update_layout(
    yaxis=dict(ticksuffix='%'),
    legend_title='Desconto'
)
fig3.update_traces(textposition='inside')

with st.container(border=True):
    st.subheader("🔄 Frequência de Compras vs. Uso de Descontos")
    st.plotly_chart(fig3, use_container_width=True)