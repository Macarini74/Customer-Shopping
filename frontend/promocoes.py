# ====================================
# IMPORTAÇÕES
# ====================================
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ====================================
# CONEXÃO COM BANCO DE DADOS
# ====================================
conn = sqlite3.connect("data\\shopping.db")
cursor = conn.cursor()

# ====================================
# LEITURA DA BASE DE DADOS
# ====================================
df = pd.read_sql_query("SELECT * FROM shopping", conn)

# ====================================
# TÍTULO DA PÁGINA
# ====================================
st.title("Análise de Promoções")
st.subheader('', divider=True)

# ====================================
# COLUNAS PARA KPIs
# ====================================
cl1c, cl2c = st.columns(2)
cl1, cl2, cl3, cl4 = st.columns(4)

# ====================================
# GRÁFICO: Frequência de Compras por Status de Assinatura
# ====================================
st.subheader("Frequência de Compras por Status de Assinatura")

frequency_by_subscription = df.groupby(['subscription_status', 'frequency_of_purchases']).size().reset_index(name='count')
frequency_by_subscription['proportion'] = frequency_by_subscription.groupby('subscription_status')['count'].transform(lambda x: x / x.sum())
frequency_by_subscription['subscription_status'] = frequency_by_subscription['subscription_status'].map({'Yes': 'Com Assinatura', 'No': 'Sem Assinatura'})

frequency_order = ['Weekly', 'Bi-Weekly', 'Fortnightly', 'Monthly', 'Quarterly', 'Every 3 months', 'Annually']
frequency_by_subscription['frequency_of_purchases'] = pd.Categorical(frequency_by_subscription['frequency_of_purchases'], categories=frequency_order, ordered=True)
frequency_by_subscription = frequency_by_subscription.sort_values('frequency_of_purchases')

fig_frequency = px.bar(
    frequency_by_subscription,
    x='frequency_of_purchases',
    y='proportion',
    color='subscription_status',
    barmode='group',
    labels={
        'frequency_of_purchases': 'Frequência de Compras',
        'proportion': 'Proporção de Clientes',
        'subscription_status': 'Status de Assinatura'
    },
    text_auto='.1%'
)
fig_frequency.update_layout(yaxis_tickformat='.1%')
fig_frequency.update_traces(textposition='outside')
st.plotly_chart(fig_frequency)

# ====================================
# KPIs: Ticket Médio e Clientes
# ====================================
discount_applied_yes = df[df['discount_applied'] == 'Yes']
discount_applied_no = df[df['discount_applied'] == 'No']

ticket_medio_yes = discount_applied_yes['purchase_amount_usd'].mean().round(2)
ticket_mediono = discount_applied_no['purchase_amount_usd'].mean().round(2)

count_clientes_yes = discount_applied_yes['customer_id'].nunique()
count_clientes_no = discount_applied_no['customer_id'].nunique()
df['ticketmediono'] = ticket_mediono
df['ticketmedioyes'] = ticket_medio_yes

diferenca_percentual_ticket_medio = 0
if ticket_mediono != 0:
    diferenca_percentual_ticket_medio = ((ticket_medio_yes - ticket_mediono) / ticket_mediono) * 100


# ====================================
# GRÁFICO: Método de Pagamento por Grupo
# ====================================
pcol1, pcol2 = st.columns(2)

discount_applied_with_subscription = df[df['subscription_status'] == 'Yes']
discount_applied_without_subscription = df[df['subscription_status'] == 'No']

payment_with_subscription_discount = discount_applied_with_subscription['preferred_payment_method'].value_counts().rename('Com Desconto e Assinatura')
payment_without_subscription_no_discount = discount_applied_without_subscription['preferred_payment_method'].value_counts().rename('Sem Desconto e Sem Assinatura')

payment_df = pd.concat([payment_with_subscription_discount, payment_without_subscription_no_discount], axis=1).fillna(0)
payment_df.index.name = 'Metodo de Pagamento'
payment_df = payment_df.reset_index()

payment_melted = payment_df.melt(
    id_vars='Metodo de Pagamento',
    value_vars=['Com Desconto e Assinatura', 'Sem Desconto e Sem Assinatura'],
    var_name='Grupo',
    value_name='Quantidade'
)

payment_pct = payment_melted.copy()
payment_pct['Total'] = payment_pct.groupby('Metodo de Pagamento')['Quantidade'].transform('sum')
payment_pct['Proporcao'] = payment_pct['Quantidade'] / payment_pct['Total']

fig = px.bar(
    payment_pct,
    x='Metodo de Pagamento',
    y='Proporcao',
    color='Grupo',
    barmode='stack',
    title='Proporção de Grupos por Método de Pagamento',
    text_auto='.0%'
)
pcol2.plotly_chart(fig)

# Gráfico de pizza: distribuição geral
pagamento_geral = df['preferred_payment_method'].value_counts().reset_index()
pagamento_geral.columns = ['Metodo de Pagamento', 'Quantidade']

fig_pizza_pagamento = px.pie(
    pagamento_geral,
    names='Metodo de Pagamento',
    values='Quantidade',
    title='Distribuição Geral dos Métodos de Pagamento',
    hole=0,
    color_discrete_sequence=px.colors.qualitative.Pastel
)
pcol1.plotly_chart(fig_pizza_pagamento)



# ====================================
# GRÁFICO: Frequência e Proporção de Cupons por Temporada
# ====================================
cl1g, cl2g = st.columns(2)
st.subheader("Frequência e Proporção de Cupons por Temporada")

season_yes = discount_applied_yes.groupby('season').size().rename('com_desconto')
season_no = discount_applied_no.groupby('season').size().rename('sem_desconto')

season_data = pd.concat([season_yes, season_no], axis=1).fillna(0)
season_data['total'] = season_data['com_desconto'] + season_data['sem_desconto']
season_data['proporcao_com_desconto'] = season_data['com_desconto'] / season_data['total']

st.dataframe(season_data)

fig = px.pie(
    season_data.reset_index(),
    names='season',
    values='proporcao_com_desconto',
    title='Proporção de Uso de Cupons por Temporada',
    hole=0.4
)
cl1g.plotly_chart(fig)

# ====================================
# GRÁFICO: Porcentagem de Uso de Cupons
# ====================================
cupom_counts = df['discount_applied'].value_counts(normalize=True) * 100
cupom_counts.index = cupom_counts.index.map({'Yes': 'Com Cupom', 'No': 'Sem Cupom'})
cupom_df = cupom_counts.reset_index()
cupom_df.columns = ['Uso de Cupom', 'Porcentagem']

fig = px.bar(
    cupom_df,
    x='Uso de Cupom',
    y='Porcentagem',
    text='Porcentagem',
    color='Uso de Cupom',
    title='Porcentagem de Clientes que Usam Cupom vs. Não Usam'
)
fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
fig.update_layout(yaxis_tickformat='.1f%', showlegend=False)
cl2g.plotly_chart(fig)

# ====================================
# GRÁFICO: Satisfação por Categoria
# ====================================
media_aval_yes = discount_applied_yes['review_rating'].mean().round(2)
media_aval_no = discount_applied_no['review_rating'].mean().round(2)

aval_yes = discount_applied_yes.groupby('category')['review_rating'].mean().round(2)
aval_no = discount_applied_no.groupby('category')['review_rating'].mean().round(2)

categorias = sorted(set(aval_yes.index).union(set(aval_no.index)))
valores_yes = [aval_yes.get(cat, 0) for cat in categorias]
valores_no = [aval_no.get(cat, 0) for cat in categorias]

# ====================================
# KPIs: Compras Anteriores
# ====================================
compra_anter_yes = discount_applied_yes['previous_purchases'].mean().round(1)
compra_anter_no = discount_applied_no['previous_purchases'].mean().round(1)

# ====================================
# EXIBIÇÃO DOS KPIs
# ====================================
# Função auxiliar para centralizar KPIs
def kpi_centered(label, value, delta=None, help=None, border_color="#ccc", value_color="#0066cc"):
    # Determina a cor do delta: verde se positivo, vermelho se negativo, cinza se None ou vazio
    if delta is None or str(delta).strip() == '':
        delta_color = "#999999"  # cinza neutro para quando não houver delta
    else:
        # Assume que delta é uma string tipo "12.3%" ou "-5.2%"
        # Se começar com "-", vermelho, senão verde
        delta_color = "red" if str(delta).startswith("-") else "green"

    st.markdown(
        f"""
        <div style="
            border: 2px solid {border_color};
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.05);
            background-color: #f9f9f9;
            margin-bottom: 20px;  /* Espaçamento vertical adicionado */
        ">
            <div style="font-size: 16px; font-weight: 500; color: #333;">{label}</div>
            <div style="font-size: 28px; font-weight: bold; color: {value_color}; margin-top: 5px;">{value}</div>
            {f'<div style="font-size: 12px; color: gray; margin-top: 4px;">{help}</div>' if (help is not None and str(help).strip() != '') else ''}
        </div>
        """,
        unsafe_allow_html=True
    )

# KPIs principais
with cl1c:
    kpi_centered(
        "Ticket Médio com Desconto",
        f"US$ {ticket_medio_yes:.2f}",
        delta=f"{diferenca_percentual_ticket_medio:.1f}%",
        help=f"{count_clientes_yes} clientes únicos"
    )

with cl2c:
    kpi_centered(
        "Ticket Médio sem Desconto",
        f"US$ {ticket_mediono:.2f}",
        delta=None,
        help=f"{count_clientes_no} clientes únicos"
    )

# KPIs adicionais
with cl1:
    kpi_centered("Média de Avaliação (com desconto)", f"{float(media_aval_yes):.2f}")
with cl2:
    kpi_centered("Compras Anteriores (com desconto)", f"{float(compra_anter_yes):.1f}")
with cl3:
    kpi_centered("Média de Avaliação (sem desconto)", f"{float(media_aval_no):.2f}")
with cl4:
    kpi_centered("Compras Anteriores (sem desconto)", f"{float(compra_anter_no):.1f}")
