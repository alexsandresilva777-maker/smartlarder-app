import streamlit as st
from supabase import create_client

# Função auxiliar para conectar localmente ao Supabase se necessário
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
            email = st.text_input("E-mail ou Usuário", placeholder="exemplo@email.com").strip()
            senha = st.text_input("Senha", type="password", placeholder="Sua senha secreta")
            botao_login = st.form_submit_button("Entrar", width="stretch") # Atualizado para o novo padrão Streamlit
            
        if botao_login:
            if not email or not senha:
                st.error("Por favor, preencha todos os campos.")
                return

            try:
                supabase = _get_supabase_client()
                
                # Busca o usuário na tabela 'usuarios' pelo email
                resposta = supabase.table("usuarios").select("*").eq("email", email).execute()
                
                if resposta.data and len(resposta.data) > 0:
                    user = resposta.data[0]
                    
                    # Verificação simples de senha (substitua pela sua lógica de hash se houver)
                    if user["senha"] == senha:
                        # 1. Define os estados na sessão
                        st.session_state.logged_in = True
                        st.session_state.user_id = user["id"]
                        st.session_state.user_name = user["nome"]
                        st.session_state.empresa_id = user["empresa_id"]
                        st.session_state.batch_list = []
                        
                        # Indica para o app.py que o login acabou de ser efetuado com sucesso
                        st.session_state.deve_salvar_cookie = True
                        
                        st.success(f"Bem-vindo de volta, {user['nome']}!")
                        st.rerun()
                    else:
                        st.error("Senha incorreta. Tente novamente.")
                else:
                    st.error("Usuário ou e-mail não encontrado.")
                    
            except Exception as e:
                st.error(f"Erro ao tentar autenticar: {e}")
