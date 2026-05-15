import streamlit as st
from supabase import create_client
from telas.login import show_login

# Configuração da página (Deve ser a primeira linha do Streamlit)
st.set_page_config(page_title="SmartLarder Pro", page_icon="🍞", layout="wide")

# Inicializa o estado da sessão se não existir
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def init_connection():
    """Conecta com o banco de dados Supabase"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def main():
    # Se o usuário não estiver logado, exibe a tela de login
    if not st.session_state.logged_in:
        show_login()
        return

    # Se chegou aqui, o usuário está logado!
    supabase = init_connection()

    # ── MENU LATERAL AMBIENTADO ──
    with st.sidebar:
        st.write(f"👤 **Usuário:** {st.session_state.get('user_name', 'Alex')}")
        st.write(f"🏢 **Empresa ID:** {st.session_state.get('empresa_id', 1)}")
        
        st.markdown("---")
        if st.button("Sair / Logout", width="stretch"):
            st.session_state.logged_in = False
            st.rerun()

    # ── CARREGAMENTO DAS SUAS TELAS ORIGINAIS ──
    # Alex, aqui embaixo o app vai tentar chamar os seus arquivos de estoque.
    # Certifique-se de que os nomes abaixo batem com os seus arquivos da pasta 'telas'
    
    try:
        # Criando as abas originais do seu sistema (ajuste os nomes se necessário)
        aba1, aba2, aba3 = st.tabs(["📋 Painel Geral", "📦 Gerenciar Estoque", "📊 Movimentações"])
        
        with aba1:
            st.title("🍞 SmartLarder Pro — Painel Principal")
            st.success(f"Bem-vindo de volta ao seu gerenciamento, {st.session_state.get('user_name')}!")
            
            # Se você tiver uma função de resumo/dashboard, chame-a aqui:
            # exemplo: dashboard.show(supabase)
            
        with aba2:
            st.header("Gerenciamento de Itens e Produtos")
            # Tenta importar e rodar a sua tela original de produtos/estoque
            try:
                from telas.produtos import mostrar_painel_produtos
                mostrar_painel_produtos(supabase)
            except ImportError:
                try:
                    from telas.estoque import renderizar_estoque
                    renderizar_estoque(supabase)
                except ImportError:
                    st.warning("Pronto para reconectar a sua tela de estoque padrão. Verifique o nome do arquivo na pasta telas.")

        with aba3:
            st.header("Histórico de Entradas e Saídas")
            # Tenta importar as movimentações se você tiver esse arquivo
            try:
                from telas.movimentacoes import mostrar_movimentacoes
                mostrar_movimentacoes(supabase)
            except ImportError:
                st.info("Área de relatórios e movimentações.")

    except Exception as e:
        st.error(f"Erro ao renderizar os componentes do painel: {e}")

if __name__ == "__main__":
    main()
