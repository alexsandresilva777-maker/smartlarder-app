import streamlit as st
from supabase import create_client
import hashlib

def _get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def _converter_para_sha256(texto):
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

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
                login_busca = usuario_digitado.lower()
                
                # Busca os dados brutos da tabela
                resposta = supabase.table("usuarios").select("*").execute()
                
                user = None
                if resposta.data:
                    for u in resposta.data:
                        if str(u.get("username", "")).lower() == login_busca:
                            user = u
                            break
                
                if user is not None:
                    # Gera o hash da senha digitada
                    senha_hash_digitada = _converter_para_sha256(senha_digitada)
                    
                    # FALLBACK TOTAL: Aceita se bater o hash SHA-256 OU se a senha digitada for igual ao texto salvo no banco
                    if user.get("senha_hash") == senha_hash_digitada or user.get("senha_hash") == senha_digitada:
                        
                        st.session_state.logged_in = True
                        st.session_state.user_id = user["id"]
                        st.session_state.user_name = user["nome"]  
                        st.session_state.empresa_id = user["empresa_id"] 
                        st.session_state.batch_list = []
                        st.session_state.deve_salvar_cookie = True
                        
                        st.success(f"Bem-vindo de volta, {user['nome']}!")
                        st.rerun()
                    else:
                        st.error("Senha incorreta. Tente novamente.")
                else:
                    st.error("Usuário não encontrado.")
                    
            except Exception as e:
                st.error(f"Erro na comunicação com o banco: {e}")
