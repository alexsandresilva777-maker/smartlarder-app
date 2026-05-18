# -*- coding: utf-8 -*-
"""
app.py — SmartLarder Pro v2 (Arquivo Principal)
- Gerenciamento de navegação, estado global e conexão Supabase.
- Gatilho automático de varredura matinal de alertas via Resend.
"""
import streamlit as st
from supabase import create_client, Client

# ── Importações das Telas do Sistema ──────────────────────────────────────────
from telas.cadastro import show_cadastro
from telas.alertas import show_alertas, verificar_e_enviar_alertas
# Importe suas outras telas aqui caso necessário, ex:
# from telas.dashboard import show_dashboard
# from telas.ajuda import show_ajuda

# ── Configuração da Página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="SmartLarder Pro v2",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Conexão com o Banco de Dados (Supabase) ───────────────────────────────────
@st.cache_resource
def init_supabase() -> Client:
    """
    Inicializa e cacheia a conexão com o Supabase utilizando st.secrets.
    """
    try:
        url = st.secrets["supabase_url"]
        key = st.secrets["supabase_key"]
        return create_client(url, key)
    except Exception as e:
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
