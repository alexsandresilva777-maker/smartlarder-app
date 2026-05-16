# -*- coding: utf-8 -*-
import streamlit as st

ROLES = ["operador", "gerente", "admin"]
ROLE_LABEL = {"operador": "👷 Operador", "gerente": "👔 Gerente", "admin": "🔑 Admin"}

def DB_listar_usuarios():
    """Função isolada para listar usuários diretamente via cliente Supabase do app"""
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    if not db:
        return []
    try:
        res = db.table("usuarios").select("*").eq("empresa_id", empresa_id).execute()
        return res.data or []
    except Exception as e:
        st.error(f"Erro ao listar usuários no banco: {e}")
        return []

def DB_criar_usuario(username, senha_hash, nome, role):
    """Função isolada para inserir um novo usuário deixando o banco gerar o ID automaticamente"""
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    if not db:
        return False
    try:
        # CORREÇÃO: Não enviamos o campo 'id' para evitar violação de chave primária duplicada
        data = {
            "username": username,
            "senha_hash": senha_hash,
            "nome": nome,
            "role": role,
            "ativo": 1,
            "empresa_id": empresa_id
        }
        db.table("usuarios").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar novo usuário: {e}")
        return False

def DB_excluir_usuario(user_id):
    """Função isolada para remover um usuário do banco"""
    db = st.session_state.get("db")
    if not db:
        return False
    try:
        db.table("usuarios").delete().eq("id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao remover usuário: {e}")
        return False

def show_usuarios():
    st.markdown("## 👥 Gerenciamento de Usuários")
    st.markdown("---")

    tab1, tab2 = st.tabs(["👁️ Usuários Cadastrados", "➕ Criar Novo Usuário"])
    
    with tab1:
        lista = DB_listar_usuarios()
        if not lista:
            st.info("Nenhum usuário encontrado.")
        else:
            for u in lista:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    col1.markdown(f"**{u.get('nome', 'Sem nome')}** (@{u.get('username', 'sem-username')})")
                    col2.markdown(f"Perfil: `{ROLE_LABEL.get(u.get('role'), u.get('role', 'operador'))}`")
                    
                    # Evita que o usuário logado se elimine por engano
                    if u.get('username') != st.session_state.get('username'):
                        if col3.button("🗑️ Remover", key=f"del_{u.get('id')}"):
                            if DB_excluir_usuario(u.get("id")):
                                st.success("Usuário removido!")
                                st.rerun()
                    else:
                        col3.caption("(Seu usuário)")
                st.markdown("<hr style='margin:10px 0; border-color:#eee;'>", unsafe_allow_html=True)
                
    with tab2:
        with st.form("novo_user_form_v6"):
            n_nome = st.text_input("Nome Completo")
            n_user = st.text_input("Username (Nome de login)")
            n_pass = st.text_input("Senha", type="password")
            n_role = st.selectbox("Perfil de Acesso", ROLES, format_func=lambda x: ROLE_LABEL[x])
            
            if st.form_submit_button("Salvar Usuário", type="primary"):
                if n_nome.strip() and n_user.strip() and n_pass.strip():
                    sucesso = DB_criar_usuario(n_user.strip(), n_pass, n_nome.strip(), n_role)
                    if sucesso:
                        st.success("🎉 Usuário criado com sucesso!")
                        st.rerun()
                else:
                    st.warning("⚠️ Por favor, preencha todos os campos obrigatórios.")
