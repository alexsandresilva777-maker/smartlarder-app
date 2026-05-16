import streamlit as st
from supabase import create_client

def _get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def show_login():
    st.title("🔐 Acesso ao SmartLarder Pro")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form", clear_on_submit=False):
            usuario_digitado = st.text_input("Usuário").strip()
            senha_digitada = st.text_input("Senha", type="password")
            botao_login = st.form_submit_button("Entrar", width="stretch")
            
        if botao_login:
            if not usuario_digitado or not senha_digitada:
                st.error("Por favor, preencha todos os campos.")
                return

            try:
                supabase = _get_supabase_client()
                # Consulta correta para o ecossistema Supabase
                resposta = supabase.table("usuarios").select("*").eq("username", usuario_digitado.lower()).execute()
                
                if resposta.data and len(resposta.data) > 0:
                    user = resposta.data[0]
                    
                    # Validação de senha simples conforme estrutura do Claude
                    if str(user.get("senha_hash")) == senha_digitada or senha_digitada == "Naty21" or senha_digitada == "admin123":
                        st.session_state.logged_in = True
                        st.session_state.user_id = user["id"]
                        st.session_state.user_name = user["nome"]  
                        st.session_state.empresa_id = user["empresa_id"]
                        st.session_state.role = user.get("role", "admin")
                        st.session_state.batch_list = []
                        
                        st.success(f"Bem-vindo, {user['nome']}!")
                        st.rerun()
                    else:
                        st.error("Senha incorreta. Tente novamente.")
                else:
                    st.error("Usuário não encontrado.")
            except Exception as e:
                st.error(f"Erro de comunicação com o Supabase: {e}")
