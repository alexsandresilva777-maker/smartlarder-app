# -*- coding: utf-8 -*-
import streamlit as st
from utils.auth import tem_permissao
import os
import hashlib
from streamlit_cookies_manager import EncryptedCookieManager

# -- Configuração da página --
# (DEVE ser o primeiro comando Streamlit executado)
st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -- CSS Interno --
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

import streamlit.components.v1 as components

# ── Persistência de sessão via cookie (INSERIDO AQUI) ─────────────────────────
_COOKIE_PREFIX  = "smartlarder/"
_COOKIE_PASSWORD = os.environ.get("COOKIES_PASSWORD", "smartlarder-secret-key-mude-isso")

# Instanciado no nível do módulo, fora de main()
cookies = EncryptedCookieManager(
    prefix=_COOKIE_PREFIX,
    password=_COOKIE_PASSWORD,
)

if not cookies.ready():
    # Aguarda o componente carregar os cookies do navegador
    st.stop()
# ─────────────────────────────────────────────────────────────────────────────

# Configuração para transformar em PWA (App)
def add_pwa_support():
    pwa_code = """
    <link rel="manifest" href="https://raw.githubusercontent.com/seu-usuario/seu-repo/main/manifest.json">
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
          navigator.serviceWorker.register('https://raw.githubusercontent.com/seu-usuario/seu-repo/main/sw.js');
        });
      }
    </script>
    """
    # Truque para injetar metatags de tela cheia no Streamlit
    st.markdown(
        f"""
        <style>
        @media all {{
            .stApp {{
                padding-bottom: 50px;
            }}
        }}
        </style>
        <script>
            var meta = document.createElement('meta');
            meta.name = "viewport";
            meta.content = "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover";
            document.getElementsByTagName('head')[0].appendChild(meta);
            
            var metaApple = document.createElement('meta');
            metaApple.name = "apple-mobile-web-app-capable";
            metaApple.content = "yes";
            document.getElementsByTagName('head')[0].appendChild(metaApple);
            
            var metaStatus = document.createElement('meta');
            metaStatus.name = "apple-mobile-web-app-status-bar-style";
            metaStatus.content = "black-translucent";
            document.getElementsByTagName('head')[0].appendChild(metaStatus);
        </script>
        """,
        unsafe_allow_html=True
    )

# Ativa o suporte ao App
add_pwa_support()
# ── Funções de persistência de sessão ─────────────────────────────────────────

def _salvar_sessao_no_cookie(user: dict):
    """
    Salva dados mínimos no cookie após login bem-sucedido.
    NUNCA salva a senha — apenas um token derivado do hash da senha.
    """
    try:
        cookies["sl_user_id"]    = str(user.get("id", ""))
        cookies["sl_username"]   = str(user.get("username", ""))
        cookies["sl_nome"]       = str(user.get("nome", ""))
        cookies["sl_role"]       = str(user.get("role", "domestico"))
        cookies["sl_empresa_id"] = str(user.get("empresa_id", "1"))
        # Token de verificação: hash do senha_hash — não é a senha, é o hash do hash
        cookies["sl_token"]      = hashlib.sha256(
            user.get("senha_hash", "").encode()
        ).hexdigest()[:16]
        cookies.save()
    except Exception as e:
        pass  # Cookie falhou — sessão ainda funciona normalmente


def _restaurar_sessao_do_cookie():
    """
    Tenta restaurar a sessão a partir do cookie salvo no navegador.
    Valida o token contra o banco antes de aceitar.
    """
    try:
        user_id    = cookies.get("sl_user_id", "")
        username   = cookies.get("sl_username", "")
        token      = cookies.get("sl_token", "")
        empresa_id = cookies.get("sl_empresa_id", "1")
        role       = cookies.get("sl_role", "domestico")
        nome       = cookies.get("sl_nome", "")

        if not user_id or not username or not token:
            return  # Sem cookie — vai para login normal

        # Valida token contra o banco (sem re-digitar senha)
        from utils.database import get_conn
        conn = get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM usuarios WHERE id=? AND username=? AND ativo=1",
                (int(user_id), username)
            ).fetchone()
        finally:
            conn.close()

        if not row:
            _limpar_cookie()
            return

        # Verifica se o token bate com o hash da senha armazenada
        token_esperado = hashlib.sha256(
            row["senha_hash"].encode()
        ).hexdigest()[:16]

        if token != token_esperado:
            _limpar_cookie()  # Token inválido — senha foi trocada
            return

        # ✅ Cookie válido — restaura sessão sem pedir login
        st.session_state.logged_in     = True
        st.session_state.user_id       = int(user_id)
        st.session_state.username      = username
        st.session_state.nome_completo = nome
        st.session_state.role          = role
        st.session_state.empresa_id    = int(empresa_id)
        st.session_state.alerts        = {}
        st.session_state.batch_list    = []

    except Exception:
        _limpar_cookie()


def _limpar_cookie():
    """Remove todos os cookies de sessão."""
    try:
        for key in ["sl_user_id","sl_username","sl_nome",
                    "sl_role","sl_empresa_id","sl_token"]:
            if key in cookies:
                cookies[key] = ""
        cookies.save()
    except Exception:
        pass
def main():
    from utils.database import init_db, check_alerts

    # Inicializa o Banco
    try:
        init_db()
    except Exception as e:
        st.error(f"Erro no banco: {e}")
        st.stop()

    # -- Estado de sessão --
    defaults = {
        "logged_in": False,
        "user_id": None,
        "empresa_id": None,
        "role": "",
        "current_page": "Dashboard",
        "alerts": {}
    }
    
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

   # ── Restaura sessão do cookie se session_state foi limpo ──────────────────
    if not st.session_state.get("logged_in"):
        _restaurar_sessao_do_cookie()

    # ── Bloco de segurança ────────────────────────────────────────────────────
    if not st.session_state.get("logged_in") \
       or st.session_state.get("user_id") is None \
       or st.session_state.get("empresa_id") is None:
        from telas.login import show_login
        show_login()
        st.stop()

    # -- Interface e Navegação --
    from telas.sidebar import show_sidebar
    page = show_sidebar()

    def _load(fn):
        try:
            fn()
        except Exception as e:
            st.error(f"Erro na página {page}: {e}")

    # Roteamento Centralizado
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
    elif page == "Fornecedores":
        if tem_permissao("ver_fornecedores"):
            from telas.fornecedores import show_fornecedores; _load(show_fornecedores)
        else:
            st.error("Acesso restrito.")
    elif page == "Usuários":
        if st.session_state.role == "admin":
            from telas.usuarios import show_usuarios; _load(show_usuarios)
        else:
            st.error("Acesso restrito.")

if __name__ == "__main__":
    main()
