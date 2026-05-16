# -*- coding: utf-8 -*-
import streamlit as st
import os
import hashlib
from streamlit_cookies_manager import EncryptedCookieManager
from supabase import create_client, Client

st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS — aspas simples no HTML para evitar SyntaxError
_CSS = (
    "<style>"
    "[data-testid='stSidebarNav']{display:none !important;}"
    "button[data-testid='stSidebarCollapseButton']{"
    "visibility:visible !important;display:flex !important;"
    "background-color:#2d6a4f !important;color:white !important;"
    "z-index:999999 !important;}"
    ".block-container{padding-top:1rem !important;}"
    "</style>"
)
st.markdown(_CSS, unsafe_allow_html=True)

# PWA — aspas simples no HTML para evitar SyntaxError
_PWA = (
    "<meta name='viewport' content='width=device-width,initial-scale=1,"
    "maximum-scale=1,user-scalable=no,viewport-fit=cover'>"
    "<meta name='apple-mobile-web-app-capable' content='yes'>"
    "<meta name='apple-mobile-web-app-status-bar-style' content='black-translucent'>"
    "<meta name='mobile-web-app-capable' content='yes'>"
    "<style>"
    "html{overflow:hidden;height:100%;}"
    "body{height:100%;overflow:auto;-webkit-overflow-scrolling:touch;}"
    "</style>"
)
st.markdown(_PWA, unsafe_allow_html=True)

# ── Cookie Manager ────────────────────────────────────────────────────────────
_COOKIE_PASSWORD = st.secrets.get("COOKIES_PASSWORD", "smartlarder-fallback-32chars!!")
cookies = EncryptedCookieManager(prefix="smartlarder/", password=_COOKIE_PASSWORD)
if not cookies.ready():
    st.stop()


# ── Funções de cookie ─────────────────────────────────────────────────────────

def _salvar_cookie(user: dict):
    try:
        cookies["sl_user_id"]    = str(user.get("id", ""))
        cookies["sl_username"]   = str(user.get("username", ""))
        cookies["sl_nome"]       = str(user.get("nome", "") or user.get("name", ""))
        cookies["sl_role"]       = str(user.get("role", "domestico"))
        cookies["sl_empresa_id"] = str(user.get("empresa_id", "1"))
        cookies["sl_token"]      = hashlib.sha256(
            str(user.get("senha_hash", "")).encode()
        ).hexdigest()[:16]
        cookies.save()
    except Exception:
        pass


def _limpar_cookie():
    try:
        for k in ["sl_user_id","sl_username","sl_nome",
                  "sl_role","sl_empresa_id","sl_token"]:
            if k in cookies:
                cookies[k] = ""
        cookies.save()
    except Exception:
        pass


def _restaurar_cookie():
    """
    Lê o cookie do navegador e valida contra o Supabase.
    Se válido, preenche o session_state sem pedir login.
    """
    try:
        user_id    = cookies.get("sl_user_id", "")
        username   = cookies.get("sl_username", "")
        token      = cookies.get("sl_token", "")
        empresa_id = cookies.get("sl_empresa_id", "1")
        role       = cookies.get("sl_role", "domestico")
        nome       = cookies.get("sl_nome", "")

        if not user_id or not username or not token:
            return

        db  = st.session_state.get("db")
        if db is None:
            return

        res = (db.table("usuarios")
                 .select("id,senha_hash,ativo")
                 .eq("id", int(user_id))
                 .eq("username", username)
                 .eq("ativo", 1)
                 .execute())

        row = res.data[0] if res.data else None
        if not row:
            _limpar_cookie(); return

        token_esperado = hashlib.sha256(
            str(row["senha_hash"]).encode()
        ).hexdigest()[:16]

        if token != token_esperado:
            _limpar_cookie(); return

        # Sessão restaurada com sucesso
        st.session_state["logged_in"]     = True
        st.session_state["user_id"]       = int(user_id)
        st.session_state["username"]      = username
        st.session_state["nome_completo"] = nome
        st.session_state["role"]          = role
        st.session_state["empresa_id"]    = int(empresa_id)
        st.session_state["alerts"]        = {}
        st.session_state["batch_list"]    = []

    except Exception:
        _limpar_cookie()


# ── App principal ─────────────────────────────────────────────────────────────

def main():
    # 1. Inicializa o cliente Supabase diretamente e guarda no session_state
    if "db" not in st.session_state:
        try:
            # Resgata as chaves diretamente do segredo do Streamlit Cloud
            url: str = st.secrets["SUPABASE_URL"]
            key: str = st.secrets["SUPABASE_KEY"]
            st.session_state["db"] = create_client(url, key)
        except Exception as e:
            st.error(f"Erro ao conectar diretamente ao Supabase: {e}")
            st.stop()

    # 2. Defaults de sessão
    _defaults = {
        "logged_in":     False,
        "user_id":       None,
        "empresa_id":    None,
        "role":          "",
        "username":      "",
        "nome_completo": "",
        "current_page":  "Dashboard",
        "alerts":        {},
        "batch_list":    [],
    }
    for k, v in _defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # 3. Tenta restaurar sessão do cookie (quando servidor reiniciou)
    if not st.session_state.get("logged_in"):
        _restaurar_cookie()

    # 4. Bloco de segurança — redireciona para login se não autenticado
    if (not st.session_state.get("logged_in")
            or st.session_state.get("user_id") is None
            or st.session_state.get("empresa_id") is None):
        from telas.login import show_login
        show_login(cookies, _salvar_cookie)
        st.stop()

   # 5. Sidebar e roteamento
    from telas.sidebar import show_sidebar
    page = show_sidebar(_limpar_cookie)

    def _load(fn):
        try:
            fn()
        except Exception as e:
            import traceback
            st.error(f"Erro na página {page}: {e}")
            st.code(traceback.format_exc())

    # Padroniza a string de role para evitar problemas com maiúsculas/espaços
    user_role = str(st.session_state.get("role", "")).lower().strip()

    # 6. Roteamento — as funções agora buscam a conexão na gaveta global
    if   page == "Dashboard":
        from telas.dashboard   import show_dashboard;    _load(show_dashboard)
    elif page == "Produtos":
        from telas.produtos    import show_produtos;     _load(show_produtos)
    elif page == "Cadastrar":
        from telas.cadastro    import show_cadastro;     _load(show_cadastro)
    elif page == "Recepção de Carga":
        from telas.recepcao    import show_recepcao;     _load(show_recepcao)
    elif page == "Lista de Compras":
        from telas.lista_compras import show_lista_compras; _load(show_lista_compras)
    elif page == "Alertas":
        from telas.alertas       import show_alertas;       _load(show_alertas)
    elif page == "Relatórios":
        from telas.relatorios    import show_relatorios;    _load(show_relatorios)
    elif page == "Fornecedores":
        from telas.fornecedores  import show_fornecedores;  _load(show_fornecedores)
    elif page == "Perdas":
        from telas.perdas        import show_perdas;        _load(show_perdas)
    elif page == "Usuários":
        # Validação flexível: aceita 'admin', 'administrador', etc.
        if "admin" in user_role:
            from telas.usuarios  import show_usuarios;      _load(show_usuarios)
        else:
            st.error("🔒 Acesso restrito a administradores.")
    elif page == "Ajuda":
        from telas.ajuda         import show_ajuda;         _load(show_ajuda)


if __name__ == "__main__":
    main()
