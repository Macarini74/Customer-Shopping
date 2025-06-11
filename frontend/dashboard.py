import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.markdown(f"<h1 style='text-align: center;'>📊 Dashboard Geral<br> </h1>", unsafe_allow_html=True)

conn = sqlite3.connect("data/shopping.db")
cursor = conn.cursor()

#------------------------------------KPI TICKET----------------------------------------
cursor.execute("""
SELECT AVG(purchase_amount_usd) AS ticket_medio
FROM shopping
""")
ticket_medio = cursor.fetchone()[0]
#------------------------------------KPI FATURAMENTO----------------------------------------
cursor.execute("""
SELECT SUM(purchase_amount_usd) AS faturamento_total
FROM shopping
""")
faturamento_total = cursor.fetchone()[0]
#------------------------------------KPI REVIEW----------------------------------------
cursor.execute("""
SELECT AVG(review_rating) AS media_review
FROM shopping
""")
media_review = cursor.fetchone()[0]
percent_satisfacao = (media_review / 5)
#------------------------------------KPI ASSINATURAS----------------------------------------
cursor.execute("""
SELECT 
  COUNT(*) AS total,
  SUM(CASE WHEN subscription_status = 'Yes' THEN 1 ELSE 0 END) AS ativos
FROM shopping
""")
total, ativos = cursor.fetchone()
percentual_ativos = ativos / total if total > 0 else 0
#------------------------------------KPI FREQUENCIA----------------------------------------
cursor.execute("""
SELECT 
  AVG(
    CASE 
      WHEN frequency_of_purchases = 'Weekly' THEN 52
      WHEN frequency_of_purchases = 'Bi-Weekly' THEN 26
      WHEN frequency_of_purchases = 'Fortnightly' THEN 26
      WHEN frequency_of_purchases = 'Monthly' THEN 12
      WHEN frequency_of_purchases = 'Quarterly' THEN 4
      WHEN frequency_of_purchases = 'Every 3 Months' THEN 4
      WHEN frequency_of_purchases = 'Annually' THEN 1
      ELSE NULL
    END
  ) AS freq_media_anual
FROM shopping
""")
freq_media_anual = cursor.fetchone()[0]
#----------------------------------------------------------------------------
col1, col2= st.columns(2)
col3, col4, col = st.columns(3)

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
        <h3 style='margin:0'>{title}</h3>
        <p style='font-size: 24px; margin: 5px 0 0 0; font-weight: bold;'>{value}</p>
    </div>
    """


with col1:
    st.markdown(kpi_box("Faturamento Total", f"R$ {faturamento_total:.2f}", "linear-gradient(to top, #d0f0c0, #b0e57c)"), unsafe_allow_html=True)


with col2:
    st.markdown(kpi_box("Ticket Médio", f"R$ {ticket_medio:.2f}", "linear-gradient(to top, #d0f0c0, #b0e57c)"), unsafe_allow_html=True)

with col3:
    st.markdown(kpi_box("Satisfação Média", f"{percent_satisfacao:.2%}", "linear-gradient(to bottom, #4d94d4, #cceeff)"), unsafe_allow_html=True)

with col4:
    st.markdown(kpi_box("Adoção de Assinaturas", f"{percentual_ativos:.2%}", "linear-gradient(to bottom, #4d94d4, #cceeff)"), unsafe_allow_html=True)

with col:
    st.markdown(kpi_box("Freq. Média de Compra Anual", f"{freq_media_anual:.1f}", "linear-gradient(to bottom, #4d94d4, #cceeff)"), unsafe_allow_html=True)
st.subheader("",  divider = True)

#---------------------------------RADAR CHART-------------------------------------------
query_radar = """
SELECT season,
       AVG(purchase_amount_usd) AS avg_purchase,
       AVG(review_rating) AS avg_review
FROM shopping
GROUP BY season
"""
df_radar = pd.read_sql_query(query_radar, conn)

ordem_temporadas = ['Winter', 'Spring', 'Summer', 'Fall']
df_radar['season'] = pd.Categorical(df_radar['season'], categories=ordem_temporadas, ordered=True)
df_radar = df_radar.sort_values('season')

fig_radar = go.Figure()

fig_radar.add_trace(go.Scatterpolar(
    r=df_radar['avg_purchase'],
    theta=df_radar['season'],
    fill='toself',
    name='Média Compras (USD)'
))

fig_radar.add_trace(go.Scatterpolar(
    r=df_radar['avg_review'],
    theta=df_radar['season'],
    fill='toself',
    name='Média Avaliações',
    fillcolor='rgba(0, 128, 0, 0.3)',
    line_color='green'
))

fig_radar.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, max(df_radar[['avg_purchase', 'avg_review']].max()) * 1.1]
        )
    ),
    showlegend=True
)
#-------------------------------------TREEMAP-----------------------------------------
query = """
SELECT category, gender, SUM(purchase_amount_usd) AS total
FROM shopping
GROUP BY category, gender
"""
df = pd.read_sql_query(query, conn)

fig = px.treemap(
    df,
    path=['category', 'gender'],
    values='total',
    color='total',
    color_discrete_map={
        'Male': 'blue',
        'Female': 'pink',
    }
)

col5, col6 =st.columns(2)
with col5.container(border = True):
    st.markdown(f"<h3 style='text-align: center;'>Treemap: Compras por Categoria e Gênero<br>  </h3>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
with col6.container(border = True):
    st.markdown(f"<h3 style='text-align: center;'>Radar Chart: Vendas e Avaliações por Temporada<br></h3>", unsafe_allow_html=True)
    st.plotly_chart(fig_radar, use_container_width=True)



conn.close()