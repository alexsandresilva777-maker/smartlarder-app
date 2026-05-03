# -*- coding: utf-8 -*-
import os
import streamlit as st
from utils.auth import tem_permissao

# ── Configuração da página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# ── CSS DE EMERGÊNCIA: Foco no botão e layout ──────────────────────────────────
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

# ── CSS Externo ────────────────────────────────────────────────────────────────
_CSS = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(_CSS):
    with open(_CSS, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    from utils.database import init_db, check_alerts

    # 1. Inicializa o banco de dados e executa migrações (empresa_id, role)
    try:
        init_db()
    except Exception as e:
        st.error(f"❌ Erro crítico no banco de dados: {e}")
        st.stop()

    # 2. Estado de sessão padrão (Ajustado para SaaS)
    defaults = {
        "logged_in":     False,
        "user_id":       None,
        "empresa_id":    None,
        "username":      "",
        "nome_completo": "",
        "role":          "",
        "current_page":  "Dashboard",
        "batch_list":    [],
        "alerts":        {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # 3. Verificação de sessão
    if not st.session_state.logged_in or st.session_state.user_id is None:
        from telas.login import show_login
        show_login()
        st.stop()

    # 4. Alertas automáticos (roda uma vez por login)
    if not st.session_state.alerts:
        try:
            st.session_state.alerts = check_alerts(st.session_state.user_id)
        except Exception:
            st.session_state.alerts = {}

    # 5. Navegação e Sidebar
    from telas.sidebar import show_sidebar
    page = show_sidebar()

    # 6. Roteamento de páginas com tratamento de erros
    def _load(fn):
        try:
            fn()
        except Exception as e:
            import traceback
            st.error(f"❌ Erro na página **{page}**: `{e}`")
            st.code(traceback.format_exc())

    # Mapeamento de Páginas
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

    # Páginas com Filtro de Permissão (Comercial/SaaS)
    elif page == "Fornecedores":
        if tem_permissao("ver_fornecedores"):
            from telas.fornecedores import show_fornecedores; _load(show_fornecedores)
        else:
            st.error("⛔ Acesso restrito ao plano Comercial.")

    elif page == "Relatórios":
        from telas.relatorios import show_relatorios; _load(show_relatorios)

    elif page == "Usuários":
        if st.session_state.role == "admin":
            from telas.usuarios import show_usuarios; _load(show_usuarios)
        else:
            st.error("⛔ Acesso restrito a administradores.")

if __name__ == "__main__":
    main()
