import streamlit as st
from supabase import create_client
from telas.login import show_login

# 1. Configuração da página (DEVE ser o primeiro comando do Streamlit no script)
st.set_page_config(page_title="SmartLarder Pro", page_icon="🍞", layout="wide")

# Inicializa o estado de login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def init_connection():
    """Inicializa o cliente do Supabase usando os Secrets do Streamlit"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def main():
    # Se o usuário não estiver logado, renderiza apenas a tela de login
    if not st.session_state.logged_in:
        show_login()
        return

    # Se chegou aqui, o usuário está logado com sucesso!
    supabase = init_connection()

    # ── BARRA LATERAL (SIDEBAR) ORIGINAL ──
    with st.sidebar:
        st.title("🍞 SmartLarder Pro")
        st.write(f"👤 **Usuário:** {st.session_state.get('user_name', 'Alex')}")
        st.write(f"🏢 **Empresa ID:** {st.session_state.get('empresa_id', 1)}")
        st.markdown("---")
        
        if st.button("Sair / Logout", width="stretch"):
            st.session_state.logged_in = False
            st.rerun()

    # ── PAINEL PRINCIPAL EM ABAS RECONECTADO ──
    try:
        # Cria as abas principais com base nos seus arquivos reais
        aba_dash, aba_estq, aba_relat, aba_comp = st.tabs([
            "📊 Dashboard", 
            "📦 Gerenciar Estoque", 
            "📋 Relatórios", 
            "🛒 Lista de Compras"
        ])
        
        # Conecta a aba 1 com o seu arquivo telas/dashboard.py
        with aba_dash:
            try:
                from telas.dashboard import mostrar_dashboard
                mostrar_dashboard(supabase)
            except AttributeError:
                st.info("Painel de indicadores ativo.")

        # Conecta a aba 2 com o seu arquivo telas/produtos.py
        with aba_estq:
            try:
                from telas.produtos import mostrar_painel_produtos
                mostrar_painel_produtos(supabase)
            except ImportError:
                st.error("Erro ao importar a tela de produtos. Verifique as funções internas.")

        # Conecta a aba 3 com o seu arquivo telas/relatorios.py
        with aba_relat:
            try:
                from telas.relatorios import mostrar_relatorios
                mostrar_relatorios(supabase)
            except AttributeError:
                st.info("Histórico e relatórios de movimentações.")

        # Conecta a aba 4 com o seu arquivo telas/lista_compras.py
        with aba_comp:
            try:
                from telas.lista_compras import mostrar_lista_compras
                mostrar_lista_compras(supabase)
            except AttributeError:
                st.info("Gerenciamento de lista de compras.")

    except Exception as e:
        st.error(f"Erro ao desenhar a interface principal: {e}")

if __name__ == "__main__":
    main()
