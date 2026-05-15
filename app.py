import streamlit as st
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
from telas.login import show_login

# Configuração da página (Deve ser o primeiro comando Streamlit do script)
st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 1. Inicialização do Cookie Manager (Sem cache_resource para eliminar o Warning) ──
# Pegamos a senha do secrets
COOKIE_PASS = st.secrets.get("COOKIE_PASSWORD", "chave_mestra_secreta_smartlarder_32char_min")

# Instancia diretamente no escopo do app para o Streamlit gerenciar corretamente o widget
cookies = EncryptedCookieManager(password=COOKIE_PASS)

if not cookies.ready():
    # Aguarda o componente sincronizar com o navegador sem travar a tela
    st.stop()

# ── 2. Inicialização do Banco de Dados Supabase ────────────────────────
@st.cache_resource
def init_supabase() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro crítico nas credenciais do Supabase: {e}")
        st.stop()

supabase = init_supabase()

# ── 3. Funções de Gerenciamento de Sessão via Cookies ──────────────────
def _salvar_sessao_no_cookie():
    try:
        cookies["logged_in"] = "true"
        cookies["user_id"] = str(st.session_state.get("user_id", ""))
        cookies["user_name"] = str(st.session_state.get("user_name", ""))
        cookies["empresa_id"] = str(st.session_state.get("empresa_id", ""))
        cookies.save()
    except Exception as e:
        st.warning(f"Não foi possível salvar os cookies de sessão: {e}")

def _restaurar_sessao_do_cookie():
    if cookies.get("logged_in") == "true":
        st.session_state.logged_in = True
        st.session_state.user_id = cookies.get("user_id")
        st.session_state.user_name = cookies.get("user_name")
        st.session_state.empresa_id = cookies.get("empresa_id")
        if "batch_list" not in st.session_state:
            st.session_state.batch_list = []

def _limpar_cookie():
    try:
        cookies["logged_in"] = "false"
        cookies["user_id"] = ""
        cookies["user_name"] = ""
        cookies["empresa_id"] = ""
        cookies.save()
    except Exception as e:
        pass

# ── 4. Fluxo de Execução Principal (Main) ──────────────────────────────
def main():
    # Tenta restaurar a sessão automaticamente se o usuário tiver o cookie ativo
    if not st.session_state.get("logged_in"):
        _restaurar_sessao_do_cookie()

    # Se continuar deslogado, exibe a tela de login
    if not st.session_state.get("logged_in"):
        show_login()
        
        # Se a tela de login autenticou o usuário com sucesso, ela ativa esta flag
        if st.session_state.get("deve_salvar_cookie"):
            _salvar_sessao_no_cookie()
            del st.session_state["deve_salvar_cookie"] # Limpa a flag temporária
            st.rerun()
        return

    # ── Bloco de Segurança e Logout ─────────────────────────────────────
    if st.session_state.get("user_id") is None or st.session_state.get("empresa_id") is None:
        _limpar_cookie()
        st.session_state.clear()
        st.rerun()

    # Sidebar com informações do usuário e botão de sair
    with st.sidebar:
        st.write(f"👤 **Usuário:** {st.session_state.get('user_name', 'Indefinido')}")
        st.write(f"🏢 **Empresa ID:** {st.session_state.get('empresa_id')}")
        
        if st.button("Sair / Logout", width="stretch"):
            _limpar_cookie()
            st.session_state.clear()
            st.rerun()

    # ── Renderização do Painel Principal ────────────────────────────────
    st.title("🍞 SmartLarder Pro — Painel Principal")
    st.success("Logado com sucesso!")
    st.info("Conexão com Supabase estabelecida.")
    
    # Daqui para baixo entra o miolo do seu painel administrativo/estoque

if __name__ == "__main__":
    main()
