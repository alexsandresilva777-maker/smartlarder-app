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

# ── CSS: esconde navegação nativa, mantém interface limpa ──────────────────────
# ── CSS RADICAL: Remove restrições para garantir funcionalidade ──────────────
# ── BLOCO CSS CORRIGIDO: Visibilidade total de textos e inputs ──────────────
# ── BLOCO CSS FINAL: Correção de Contraste para Fundos Claros e Escuros ──────
st.markdown("""
<style>
    /* 1. Mantém o botão de abrir/fechar funcional */
    button[data-testid="stSidebarCollapseButton"] {
        background-color: #2d6a4f !important;
        color: white !important;
        display: flex !important;
        visibility: visible !important;
        z-index: 999999 !important;
    }

    /* 2. Inputs: Texto preto em fundo branco para digitação visível */
    input {
        color: #1a1a1a !important;
        background-color: #ffffff !important;
        -webkit-text-fill-color: #1a1a1a !important;
    }
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div {
        color: #1a1a1a !important;
        background-color: #ffffff !important;
    }

    /* 3. AQUI ESTÁ A MUDANÇA: Cor escura para aparecer no fundo branco */
    /* Isso resolve os títulos "sumidos" na imagem 4 */
    label, .stMarkdown p, h1, h2, h3, [data-testid="stWidgetLabel"] {
        color: #262730 !important;
    }

    /* 4. Limpeza de interface e ajustes de layout */
    [data-testid="stSidebarNav"] { display: none !important; }
    .stDeployButton { display: none !important; }
    footer { visibility: hidden !important; }
    [data-testid="stHeader"] { 
        background: rgba(0,0,0,0) !important; 
        pointer-events: none !important; 
    }
    [data-testid="stHeader"] button { 
        pointer-events: auto !important; 
    }
    .block-container { padding-top: 1rem !important; }
</style>
""", unsafe_allow_html=True)
# ── CSS externo ────────────────────────────────────────────────────────────────
_CSS = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(_CSS):
    with open(_CSS, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def main():
    from utils.database import init_db, check_alerts, verificar_login

    # Inicializa banco
    try:
        init_db()
    except Exception as e:
        import traceback
        st.error(f"❌ Erro ao inicializar banco de dados: {e}")
        st.code(traceback.format_exc())
        st.stop()

    # ── Estado de sessão padrão ────────────────────────────────────────────────
    defaults = {
        "logged_in":     False,
        "user_id":       None,
        "username":      "",
        "nome_completo": "",
        "role":          "",
        "current_page":  "Dashboard",
        "batch_list":    [],       # Modo Recepção de Carga
        "alerts":        {},       # Alertas pós-login
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Verificação de sessão: redireciona para login se user_id ausente ───────
    if not st.session_state.get("logged_in") or st.session_state.get("user_id") is None:
        from telas.login import show_login
        show_login()
        st.stop()

    # ── check_alerts logo após o login (executa uma vez por sessão) ───────────
    if not st.session_state.alerts:
        try:
            st.session_state.alerts = check_alerts(st.session_state.user_id)
        except Exception:
            st.session_state.alerts = {}

    # ── Navegação ──────────────────────────────────────────────────────────────
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
    elif page == "Recepção de Carga":from telas.recepcao      import show_recepcao;      _load(show_recepcao)
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
