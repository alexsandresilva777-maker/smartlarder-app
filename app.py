# -*- coding: utf-8 -*-
import os
import streamlit as st

# ── Configuração da página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={},
)

# ── CSS: esconde navegação nativa e mantém interface limpa ─────────────────────
st.markdown("""
<style>
    [data-testid="stHeader"] { 
        background: transparent !important;
        color: transparent !important;
    }
    [data-testid="stSidebarNav"] { display: none !important; }
    .stDeployButton { display: none !important; }
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }
    [data-testid="stDecoration"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── CSS personalizado do arquivo externo ───────────────────────────────────────
_CSS = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(_CSS):
    with open(_CSS, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def main():
    from utils.database import init_db

    # Inicializa banco de dados
    try:
        init_db()
    except Exception as e:
        import traceback
        st.error(f"❌ Erro ao inicializar banco de dados: {e}")
        st.code(traceback.format_exc())
        st.stop()

    # Estado de sessão padrão
    defaults = {
        "logged_in":     False,
        "username":      "",
        "nome_completo": "",
        "role":          "",
        "current_page":  "Dashboard",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Tela de login ──────────────────────────────────────────────────────────
    if not st.session_state.logged_in:
        from telas.login import show_login
        show_login()
        st.stop()

    # ── Navegação lateral ──────────────────────────────────────────────────────
    from telas.sidebar import show_sidebar
    page = show_sidebar()

    # ── Roteamento de páginas ──────────────────────────────────────────────────
    def _load(fn):
        try:
            fn()
        except Exception as e:
            import traceback
            st.error(f"❌ Erro na página **{page}**: `{e}`")
            st.code(traceback.format_exc())

    if   page == "Dashboard":        from telas.dashboard     import show_dashboard;     _load(show_dashboard)
    elif page == "Produtos":         from telas.produtos      import show_produtos;      _load(show_produtos)
    elif page == "Cadastrar":        from telas.cadastro      import show_cadastro;      _load(show_cadastro)
    elif page == "Lista de Compras": from telas.lista_compras import show_lista_compras; _load(show_lista_compras)
    elif page == "Relatórios":       from telas.relatorios    import show_relatorios;    _load(show_relatorios)
    elif page == "Alertas":          from telas.alertas       import show_alertas;       _load(show_alertas)
    elif page == "Usuários":
        if st.session_state.role == "admin":
            from telas.usuarios import show_usuarios; _load(show_usuarios)
        else:
            st.error("⛔ Acesso restrito a administradores.")


if __name__ == "__main__":
    main()
