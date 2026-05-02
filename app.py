import os, sys

# ── Resolução de módulos — OBRIGATÓRIO ser o primeiro import ──────────────────
import imports  # noqa — registra utils.* e utilitarios.* no sys.modules

import streamlit as st
from utils.database import init_db

st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={},
)

_CSS = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(_CSS):
    with open(_CSS) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

try:
    init_db()
except Exception as e:
    st.error(f"❌ Erro ao inicializar banco: {e}")
    import traceback; st.code(traceback.format_exc())
    st.stop()

for k, v in {"logged_in":False,"username":"","nome_completo":"","role":""}.items():
    if k not in st.session_state:
        st.session_state[k] = v

if not st.session_state.logged_in:
    from pages.login import show_login
    show_login()
    st.stop()

from pages.sidebar import show_sidebar
page = show_sidebar()

def _load(fn):
    try:
        fn()
    except Exception as e:
        import traceback
        st.error(f"❌ Erro na página **{page}**: `{e}`")
        st.code(traceback.format_exc())

if   page == "Dashboard":        from pages.dashboard     import show_dashboard;     _load(show_dashboard)
elif page == "Produtos":         from pages.produtos      import show_produtos;      _load(show_produtos)
elif page == "Cadastrar":        from pages.cadastro      import show_cadastro;      _load(show_cadastro)
elif page == "Lista de Compras": from pages.lista_compras import show_lista_compras; _load(show_lista_compras)
elif page == "Relatórios":       from pages.relatorios    import show_relatorios;    _load(show_relatorios)
elif page == "Alertas":          from pages.alertas       import show_alertas;       _load(show_alertas)
elif page == "Ajuda":            from pages.ajuda         import show_ajuda;         _load(show_ajuda)
elif page == "Usuários":
    if st.session_state.role == "admin":
        from pages.usuarios import show_usuarios; _load(show_usuarios)
    else:
        st.error("Acesso restrito a administradores.")
