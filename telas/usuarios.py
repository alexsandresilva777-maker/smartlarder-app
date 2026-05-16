# -*- coding: utf-8 -*-
import streamlit as st
import utils.database as db_utils

ROLES = ["operador", "gerente", "admin"]
ROLE_LABEL = {"operador": "👷 Operador", "gerente": "👔 Gerente", "admin": "🔑 Admin"}

def show_usuarios():
    st.markdown("## 👥 Gerenciamento de Usuários")
    st.markdown("---")

    # Tratamento defensivo para validar se as funções originais do Claude existem
    funcoes_necessarias = ["listar_usuarios", "criar_usuario", "toggle_usuario", "excluir_usuario"]
    for func in funcoes_necessarias:
        if not hasattr(db_utils, func):
            st.error(f"⚠️ A função `{func}` não foi localizada no arquivo `utils/database.py`. Verifique a nomenclatura.")
            return

    tab1, tab2 = st.tabs(["👁️ Usuários Cadastrados", "➕ Criar Novo Usuário"])
    
    with tab1:
        lista = db_utils.listar_usuarios()
        if not lista:
            st.info("Nenhum usuário encontrado.")
        else:
            for u in lista:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    col1.markdown(f"**{u.get('nome')}** (@{u.get('username')})")
                    col2.markdown(f"Perfil: `{ROLE_LABEL.get(u.get('role'), u.get('role'))}`")
                    if u.get('username') != st.session_state.get('username'):
                        if col3.button("🗑️ Remover", key=f"del_{u.get('id')}"):
                            db_utils.excluir_usuario(u.get("id"))
                            st.rerun()
                    else:
                        col3.caption("(Seu usuário)")
                st.markdown("---")
                
    with tab2:
        with st.form("novo_user_form"):
            n_nome = st.text_input("Nome Completo")
            n_user = st.text_input("Username")
            n_pass = st.text_input("Senha", type="password")
            n_role = st.selectbox("Perfil de Acesso", ROLES, format_func=lambda x: ROLE_LABEL[x])
            
            if st.form_submit_button("Salvar Usuário"):
                if n_nome and n_user and n_pass:
                    # Envia para a função estrutural do Claude
                    sucesso = db_utils.criar_usuario(n_user, n_pass, n_nome, n_role)
                    if sucesso:
                        st.success("Usuário criado com sucesso!")
                        st.rerun()
                else:
                    st.warning("Preencha todos os campos obrigatórios.")
