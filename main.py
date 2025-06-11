import streamlit as st
# from data.CriacaoBD import criarTable
from streamlit import config as _config

_config.set_option("theme.base", "light")
_config.set_option("theme.primaryColor", "#ff4b4b")
_config.set_option("theme.backgroundColor", "#ffffff")
_config.set_option("theme.secondaryBackgroundColor", "#f0f2f6")
_config.set_option("theme.textColor", "#31333F")

def main():
    # criarTable()
    st.set_page_config(
        page_title="Customer Shopping",
        page_icon="💸",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    dashboard_page = st.Page("frontend/dashboard.py", title="Dashboard", icon="📊", url_path="/dashboard")
    localizacao = st.Page("frontend/localizacao.py", title="Análise por Localização", icon="🌎", url_path="/localizacao") 
    consumidor = st.Page("frontend/consumidor.py", title="Perfil do Consumidor", icon="👤", url_path="/consumidor") 
    promocoes = st.Page("frontend/promocoes.py", title="Análise de Promoções", icon="🏷️", url_path="/promocoes")

    pg = st.navigation([dashboard_page])

    pg = st.navigation([
            dashboard_page,
            localizacao,
            consumidor,
            promocoes
        ])
    
    pg.run()

if __name__ == "__main__":
    main()