# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client

# Configuração da página (Deve ser o primeiro comando do Streamlit)
st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização da Barra Lateral do Claude
st.markdown("""<style>
    [data-testid="stSidebarNav"] {display: none !important;}
    button[data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        display: flex !important;
        background-color: #2d6a4f !important;
        color: white !important;
        z-index: 999999 !important;
    }
    .block-container {padding-top: 1rem !important;}
</style>""", unsafe_allow_html=True)

def add_pwa_support():
    """Configura metatags para o PWA não reiniciar ao minimizar no celular"""
    pwa_html = (
        "<meta name='viewport' content='width=device-width, initial-scale=1, "
        "maximum-scale=1, user-scalable=no, viewport-fit=cover'>"
        "<meta name='apple-mobile-web-app-capable' content='yes'>"
        "<meta name='apple-mobile-web-app-status-bar-style' content='black-translucent'>"
        "<meta name='mobile-web-app-capable' content='yes'>"
        "<style>"
        "html { overflow: hidden; height: 100%; }"
        "body { height: 100%; overflow: auto; -webkit-overflow-scrolling: touch; }"
        "</style>"
    )
    st.markdown(pwa_html, unsafe_allow_html=True)

add_pwa_support()

def init_connection():
    """Conecta com o banco de dados Supabase de forma correta"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def main():
    # Inicializa os estados padrões da sessão do Claude
    defaults = {
        "logged_in":     False,
        "user_id":       None,
        "empresa_id":    None,
        "role":          "",
        "user_name":     "Alex",
        "current_page":  "Dashboard",
        "alerts":        {},
        "batch_list":    [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Bloco de segurança: Se não logado, chama a tela de login
    if not st.session_state.logged_in:
        from telas.login import show_login
        show_login()
        st.stop()

    # Usuário Logado -> Conecta ao Supabase
    supabase = init_connection()

    # ── BARRA LATERAL (SHOW SIDEBAR) ──
    from telas.sidebar import show_sidebar
    page = show_sidebar()

    # Função auxiliar do Claude para carregar as páginas com segurança
    def _load(fn):
        try:
            fn(supabase) # Passa o cliente do Supabase para as telas salvarem os dados
        except Exception as e:
            import traceback
            st.error(f"Erro na página {page}: {e}")
            st.code(traceback.format_exc())

    # Roteamento das abas e páginas originais do Claude
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
    elif page == "Relatórios":
        from telas.relatorios import show_relatorios; _load(show_relatorios)

if __name__ == "__main__":
    main()
