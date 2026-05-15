# -*- coding: utf-8 -*-
import streamlit as st
import hashlib

def show_login():
    # Centraliza o container de login na tela
    st.write("")
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            "<h2 style='text-align: center; color: #2d6a4f;'>📦 SmartLarder Pro</h2>", 
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align: center; color: #666;'>Gestão Inteligente de Estoque Despensa</p>", 
            unsafe_allow_html=True
        )
        
        with st.form(key="login_form", clear_on_submit=False):
            username = st.text_input("Usuário", key="login_username").strip().lower()
            password = st.text_input("Senha", type="password", key="login_password")
            submit_button = st.form_submit_button(label="Entrar", use_container_width=True)
            
            if submit_button:
                if not username or not password:
                    st.error("Por favor, preencha todos os campos.")
                    return
                
                try:
                    # Conecta dinamicamente ao Supabase
                    from utils.database import get_conn
                    supabase = get_conn()
                    
                    # Busca o usuário no banco de dados da nuvem
                    res = (
                        supabase.table("usuarios")
                        .select("*")
                        .eq("username", username)
                        .eq("ativo", 1)
                        .execute()
                    )
                    
                    user = res.data[0] if res.data else None
                    
                    if user:
                        # Gera o hash SHA-256 da senha digitada para comparar com o banco
                        senha_digitada_hash = hashlib.sha256(password.encode()).hexdigest()
                        
                        if user["senha_hash"] == senha_digitada_hash:
                            # 1. Alimenta o estado da sessão do Streamlit imediatamente
                            st.session_state.logged_in     = True
                            st.session_state.user_id       = int(user["id"])
                            st.session_state.username      = user["username"]
                            st.session_state.nome_completo = user["nome"]
                            st.session_state.role          = user["role"]
                            st.session_state.empresa_id    = int(user["empresa_id"])
                            st.session_state.alerts        = {}
                            st.session_state.batch_list    = []
                            
                            # 2. Salva nos cookies usando o gerenciador seguro do app.py (sem reimportar o arquivo inteiro)
                            try:
                                from app import _get_cookie_manager
                                current_cookies = _get_cookie_manager()
                                current_cookies["sl_user_id"]    = str(user["id"])
                                current_cookies["sl_username"]   = str(user["username"])
                                current_cookies["sl_nome"]       = str(user["nome"])
                                current_cookies["sl_role"]       = str(user["role"])
                                current_cookies["sl_empresa_id"] = str(user["empresa_id"])
                                current_cookies["sl_token"]      = hashlib.sha256(
                                    user["senha_hash"].encode()
                                ).hexdigest()[:16]
                                current_cookies.save()
                            except Exception:
                                pass # Se os cookies falharem, o app ainda loga pela sessão atual
                            
                            st.success("Login realizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Usuário ou senha incorretos.")
                    else:
                        st.error("Usuário ou senha incorretos.")
                        
                except Exception as e:
                    st.error(f"Erro ao autenticar no servidor: {e}")
