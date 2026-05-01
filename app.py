"""
SmartLarder Pro v3.0
Ponto de entrada principal - Estrutura Consolidada.
"""
import streamlit as st
import os
# Ajuste na importação do banco de dados (agora dentro de utilitarios)
from utilitarios.database import init_db 

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS Global ────────────────────────────────────────────────────────────────
# O CSS continua na pasta assets, que você deve manter na raiz
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

# ── Roteamento (Ajustado para a pasta utilitarios) ───────────────────────────
if not st.session_state.logged_in:
    from utilitarios.login import show_login
    show_login()
    st.stop()

# Usuário autenticado — carrega sidebar e páginas (Tudo vindo de utilitarios)
from utilitarios.sidebar import show_sidebar
page = show_sidebar()

if page == "Dashboard":
    from utilitarios.dashboard import show_dashboard
    show_dashboard()

elif page == "Produtos":
    from utilitarios.produtos import show_produtos
    show_produtos()

elif page == "Cadastrar":
    from utilitarios.cadastro import show_cadastro
    show_cadastro()

elif page == "Lista de Compras":
    from utilitarios.lista_compras import show_lista_compras
    show_lista_compras()

elif page == "Relatórios":
    from utilitarios.relatorios import show_relatorios
    show_relatorios()

elif page == "Alertas":
    from utilitarios.alertas import show_alertas
    show_alertas()

elif page == "Usuários":
    if st.session_state.role == "admin":
        from utilitarios.usuarios import show_usuarios
        show_usuarios()
    else:
        st.error("Acesso restrito a administradores.")

elif page == "Ajuda":
    from utilitarios.Ajuda import show_ajuda
    show_ajuda()