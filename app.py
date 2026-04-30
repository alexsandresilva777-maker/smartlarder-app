"""
SmartLarder Pro v3.0
Ponto de entrada principal.
"""
import streamlit as st
import os
from utils.database import init_db

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}   # remove menu hambúrguer
)

# ── CSS Global ────────────────────────────────────────────────────────────────
_CSS = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(_CSS):
    with open(_CSS, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Inicializa banco ──────────────────────────────────────────────────────────
init_db()

# ── Estado de sessão padrão ───────────────────────────────────────────────────
_defaults = {"logged_in": False, "username": "", "nome_completo": "", "role": ""}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Roteamento ────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    from pages.login import show_login
    show_login()
    st.stop()

# Usuário autenticado — carrega sidebar e páginas
from pages.sidebar import show_sidebar
page = show_sidebar()

if page == "Dashboard":
    from pages.dashboard import show_dashboard
    show_dashboard()

elif page == "Produtos":
    from pages.produtos import show_produtos
    show_produtos()

elif page == "Cadastrar":
    from pages.cadastro import show_cadastro
    show_cadastro()

elif page == "Lista de Compras":
    from pages.lista_compras import show_lista_compras
    show_lista_compras()

elif page == "Relatórios":
    from pages.relatorios import show_relatorios
    show_relatorios()

elif page == "Alertas":
    from pages.alertas import show_alertas
    show_alertas()

elif page == "Usuários":
    if st.session_state.role == "admin":
        from pages.usuarios import show_usuarios
        show_usuarios()
    else:
        st.error("Acesso restrito a administradores.")

elif page == "Ajuda":
    from pages.Ajuda import show_ajuda
    show_ajuda()

