@@ -1,128 +1,107 @@
# -*- coding: utf-8 -*-
"""
app.py — SmartLarder Pro v2 (Arquivo Principal)
- Gerenciamento de navegação, estado global e conexão Supabase.
- Gatilho automático de varredura matinal de alertas via Resend.
"""
import streamlit as st
import hashlib
from streamlit_cookies_manager import EncryptedCookieManager
from supabase import create_client
from supabase import create_client, Client

# ── Importações das Telas do Sistema ──────────────────────────────────────────
from telas.cadastro import show_cadastro
from telas.alertas import show_alertas, verificar_e_enviar_alertas
# Importe suas outras telas aqui caso necessário, ex:
# from telas.dashboard import show_dashboard
# from telas.ajuda import show_ajuda

# ── Configuração da Página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    page_title="SmartLarder Pro v2",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ocultar navegação padrão do Streamlit
st.markdown(
    "<style>[data-testid='stSidebarNav']{display:none !important;} "
    ".block-container{padding-top:1rem !important;}</style>", 
    unsafe_allow_html=True
)

# Inicializar Gerenciador de Cookies
_COOKIE_PASSWORD = st.secrets.get("COOKIES_PASSWORD", "smartlarder-fallback-32chars!!")
cookies = EncryptedCookieManager(prefix="smartlarder/", password=_COOKIE_PASSWORD)
if not cookies.ready():
    st.stop()

def _salvar_cookie(user: dict):
    try:
        cookies["sl_user_id"]    = str(user.get("id", ""))
        cookies["sl_username"]   = str(user.get("username", ""))
        cookies["sl_nome"]       = str(user.get("nome", ""))
        cookies["sl_role"]       = str(user.get("role", "domestico"))
        cookies["sl_empresa_id"] = str(user.get("empresa_id", "1"))
        cookies["sl_token"]      = hashlib.sha256(str(user.get("senha_hash", "")).encode()).hexdigest()[:16]
        cookies.save()
    except: pass

def _limpar_cookie():
# ── Conexão com o Banco de Dados (Supabase) ───────────────────────────────────
@st.cache_resource
def init_supabase() -> Client:
    """
    Inicializa e cacheia a conexão com o Supabase utilizando st.secrets.
    """
    try:
        for k in ["sl_user_id","sl_username","sl_nome","sl_role","sl_empresa_id","sl_token"]:
            if k in cookies: cookies[k] = ""
        cookies.save()
    except: pass

def _restaurar_cookie():
    try:
        user_id = cookies.get("sl_user_id", "")
        username = cookies.get("sl_username", "")
        token = cookies.get("sl_token", "")
        if not user_id or not username or not token: return

        db = st.session_state.get("db")
        if not db: return

        res = db.table("usuarios").select("id,senha_hash,ativo").eq("id", int(user_id)).eq("username", username).eq("ativo", 1).execute()
        if not res.data:
            _limpar_cookie(); return

        row = res.data[0]
        if hashlib.sha256(str(row["senha_hash"]).encode()).hexdigest()[:16] != token:
            _limpar_cookie(); return

        st.session_state["logged_in"] = True
        st.session_state["user_id"] = int(user_id)
        st.session_state["username"] = username
        st.session_state["nome_completo"] = cookies.get("sl_nome", "Usuário")
        st.session_state["role"] = cookies.get("sl_role", "domestico")
        st.session_state["empresa_id"] = int(cookies.get("sl_empresa_id", "1"))
    except: _limpar_cookie()

# Conexão Supabase
if "db" not in st.session_state:
    try:
        st.session_state["db"] = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        url = st.secrets["supabase_url"]
        key = st.secrets["supabase_key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro de conexão com o banco: {e}")
        st.stop()

if not st.session_state.get("logged_in"):
    _restaurar_cookie()

if not st.session_state.get("logged_in") or st.session_state.get("user_id") is None:
    from telas.login import show_login
    show_login(cookies, _salvar_cookie)
    st.stop()

# Carregar Sidebar
from telas.sidebar import show_sidebar
page = show_sidebar(_limpar_cookie)

def _load(fn):
    try: fn()
    except Exception as e:
        st.error(f"Erro ao carregar a página {page}: {e}")

# Roteador de Páginas
user_role = str(st.session_state.get("role", "")).lower().strip()
session_user = str(st.session_state.get("username", "")).lower().strip()

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
    try:
        from telas.fornecedores import show_fornecedores; _load(show_fornecedores)
    except: st.info("Módulo de Fornecedores em desenvolvimento.")
elif page == "Perdas":
    try:
        from telas.perdas import show_perdas; _load(show_perdas)
    except: st.info("Módulo de Perdas em desenvolvimento.")
elif page == "Usuários":
    if "admin" in user_role or "alex" in session_user:
        from telas.usuarios import show_usuarios; _load(show_usuarios)
    else:
        st.error("🔒 Acesso restrito a administradores.")
elif page == "Ajuda":
    from telas.ajuda import show_ajuda; _load(show_ajuda)
        st.error(f"❌ Erro ao ler credenciais do st.secrets: {e}")
        return None

# ── Inicialização do Estado da Sessão ─────────────────────────────────────────
def init_global_state():
    if "db" not in st.session_state:
        st.session_state["db"] = init_supabase()
    
    # Simulação de Empresa ID padrão (Mudar dinamicamente se houver sistema de login)
    if "empresa_id" not in st.session_state:
        st.session_state["empresa_id"] = 1
        
    # Trava de segurança para enviar apenas um e-mail de alerta por sessão
    if "alerta_disparado_hoje" not in st.session_state:
        st.session_state["alerta_disparado_hoje"] = False

# ── Corpo Principal do Aplicativo ─────────────────────────────────────────────
def main():
    init_global_state()
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)

    if not db:
        st.warning("⚠️ Aguardando conexão com a base de dados Supabase...")
        return

    # ── 🚨 Gatilho de Alertas Automáticos (Segundo Plano) ─────────────────────
    # Executa a varredura silenciosa assim que o app abre.
    if not st.session_state["alerta_disparado_hoje"]:
        # 📝 IMPORTANTE: Substitua pelo e-mail cadastrado na sua conta do Resend
        email_destino = "seu_email_da_conta_resend@gmail.com"
        
        # Dispara a função que você colou em telas/alertas.py
        enviou = verificar_e_enviar_alertas(db, empresa_id, email_destino)
        
        if enviou:
            st.toast("📨 Relatório de alertas matinais enviado para o seu e-mail!", icon="📩")
        
        # Trava o gatilho para não disparar de novo a cada clique no menu lateral
        st.session_state["alerta_disparado_hoje"] = True

    # ── 🧭 Menu Lateral de Navegação ──────────────────────────────────────────
    st.sidebar.markdown("# 📊 SmartLarder Pro")
    st.sidebar.markdown(f"**ID Empresa:** `{empresa_id}`")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio(
        "Navegação",
        ["➕ Cadastrar Produto", "🔔 Central de Alertas", "📈 Painel de Controle", "ℹ️ Ajuda"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("SmartLarder Pro v2.0\nGestão Inteligente de Estoques")

    # ── 📐 Roteamento de Telas ────────────────────────────────────────────────
    if menu == "➕ Cadastrar Produto":
        show_cadastro()
        
    elif menu == "🔔 Central de Alertas":
        show_alertas()
        
    elif menu == "📈 Painel de Controle":
        st.markdown("## 📈 Painel de Controle (Dashboard)")
        st.info("Espaço reservado para os gráficos financeiros, relatórios de consumo a granel e estatísticas.")
        # Aqui você chamará a função do seu arquivo de dashboard quando quiser, ex: show_dashboard()
        
    elif menu == "ℹ️ Ajuda":
        st.markdown("## ℹ️ Ajuda & Suporte")
        st.markdown("Precisa de apoio com o leitor de código de barras ou com a precificação de itens? Contate o suporte técnico.")

if __name__ == "__main__":
    main()
