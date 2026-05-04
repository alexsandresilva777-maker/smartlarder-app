# -*- coding: utf-8 -*-
import os
import streamlit as st
from utils.auth import tem_permissao

# -- Configuração da página --
st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -- CSS Interno --
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none !important;}
    button[data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        display: flex !important;
        background-color: #2d6a4f !important;
        color: white !important;
        z-index: 999999 !important;
    }
    .block-container {padding-top: 1rem !important;}
</style>
""", unsafe_allow_html=True)

def main():
    from utils.database import init_db, check_alerts

    try:
        init_db()
    except Exception as e:
        st.error(f"Erro no banco: {e}")
        st.stop()

 # -- Estado de sessão --
    defaults = {
        "logged_in": False,
        "user_id": None,
        "empresa_id": None,  # Essencial para o isolamento de dados SaaS
        "role": "",
        "current_page": "Dashboard",
        "alerts": {}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # BLOQUEIO DE SEGURANÇA (Ajustado)
    # Verificamos se está logado E se possui os IDs necessários para as consultas
    if not st.session_state.logged_in or st.session_state.user_id is None or st.session_state.empresa_id is None:
        from telas.login import show_login
        show_login()
        st.stop()  # Impede que o app tente carregar o sidebar ou páginas sem os IDs

    # -- Carregamento da Interface --
    # Só chega aqui se passar pelo bloqueio acima
    from telas.sidebar import show_sidebar
    page = show_sidebar()

    def _load(fn):
        try:
            fn()
        except Exception as e:
            st.error(f"Erro na página {page}: {e}")

    # Roteamento Estrito (Mantendo sua estrutura original)
    if page == "Dashboard":
        from telas.dashboard import show_dashboard; _load(show_dashboard)

    # Roteamento Estrito (Alinhado com 4 espaços)
    # Bloco de Roteamento Limpo
    if page == "Dashboard":
        from telas.dashboard import show_dashboard; _load(show_dashboard)
    elif page == "Produtos":
        from telas.produtos import show_produtos; _load(show_produtos)
    elif page == "Cadastrar":
        from telas.cadastro import show_cadastro; _load(show_cadastro)
    elif page == "Recepção de Carga":
        from telas.recepcao import show_recepcao; _load(show_recepcao)
    elif page == "Lista de Compras":
        from telas.lista_compras import show_lista_compras; _load(show_lista_compras)
    elif page == "Alertas":
        from telas.alertas import show_alertas; _load(show_alertas)
    elif page == "Fornecedores":
        if tem_permissao("ver_fornecedores"):
            from telas.fornecedores import show_fornecedores; _load(show_fornecedores)
        else:
            st.error("Acesso restrito.")
    elif page == "Relatórios":
        from telas.relatorios import show_relatorios; _load(show_relatorios)
    elif page == "Usuários":
        if st.session_state.role == "admin":
            from telas.usuarios import show_usuarios; _load(show_usuarios)
        else:
            st.error("Acesso restrito.")
if __name__ == "__main__":
    main()
