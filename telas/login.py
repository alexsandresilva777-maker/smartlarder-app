import streamlit as st
from supabase import create_client
import hashlib

def _get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def _converter_para_sha256(texto):
    """Transforma a senha digitada no mesmo formato criptografado do Supabase"""
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def show_login():
    st.title("🔐 Acesso ao SmartLarder Pro")
    
    # Centraliza o formulário na tela
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Usuário", placeholder="Digite seu usuário (ex: alex)").strip()
            senha = st.text_input("Senha", type="password", placeholder="Sua senha secreta")
            botao_login = st.form_submit_button("Entrar", width="stretch")
            
        if botao_login:
            if not email or not senha:
                st.error("Por favor, preencha todos os campos.")
                return

            try:
                supabase = _get_supabase_client()
                
                # Busca o usuário na coluna 'username' (conforme a imagem)
                resposta = supabase.table("usuarios").select("*").eq("username", email).execute()
                
                if resposta.data and len(resposta.data) > 0:
                    user = resposta.data[0]
                    
                    # Converte a senha digitada para SHA-256 para comparar de igual para igual
                    senha_digitada_hash = _converter_para_sha256(senha)
                    
                    # Compara o hash gerado com o 'senha_hash' armazenado no banco
                    if user["senha_hash"] == senha_digitada_hash:
                        # Define os estados na sessão
                        st.session_state.logged_in = True
                        st.session_state.user_id = user["id"]
                        st.session_state.user_name = user["nome"]  
                        st.session_state.empresa_id = user["empresa_id"] 
                        st.session_state.batch_list = []
                        
                        # Ativa o gatilho para o app.py salvar os cookies
                        st.session_state.deve_salvar_cookie = True
                        
                        st.success(f"Bem-vindo de volta, {user['nome']}!")
                        st.rerun()
                    else:
                        st.error("Senha incorreta. Tente novamente.")
                else:
                    st.error("Usuário não encontrado.")
                    
            except Exception as e:
                st.error(f"Erro ao tentar autenticar: {e}")
