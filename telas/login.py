import streamlit as st
from supabase import create_client

def _get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def show_login():
    st.title("🔐 Acesso ao SmartLarder Pro")
    
    # Centraliza o formulário na tela
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form", clear_on_submit=False):
            # O label continua "Usuário", mas o input vai pesquisar na coluna 'username'
            email = st.text_input("Usuário", placeholder="Digite seu usuário (ex: alex)").strip()
            senha = st.text_input("Senha", type="password", placeholder="Sua senha secreta")
            botao_login = st.form_submit_button("Entrar", width="stretch")
            
        if botao_login:
            if not email or not senha:
                st.error("Por favor, preencha todos os campos.")
                return

            try:
                supabase = _get_supabase_client()
                
                # BUSCA CORRETA: Filtrando pela coluna 'username' obtida da imagem do Supabase
                resposta = supabase.table("usuarios").select("*").eq("username", email).execute()
                
                if resposta.data and len(resposta.data) > 0:
                    user = resposta.data[0]
                    
                    # VALIDAÇÃO CORRETA: Comparando com a coluna 'senha_hash' obtida da imagem
                    # Nota: Como sua senha está em formato hash no banco, certifique-se de passar 
                    # a senha correta que gera aquele hash correspondente.
                    if user["senha_hash"] == senha:
                        # Define os estados na sessão baseando-se nas colunas reais
                        st.session_state.logged_in = True
                        st.session_state.user_id = user["id"]
                        st.session_state.user_name = user["nome"]  # Coluna 'nome' confirmada na imagem
                        st.session_state.empresa_id = user["empresa_id"] # Coluna 'empresa_id' confirmada
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
