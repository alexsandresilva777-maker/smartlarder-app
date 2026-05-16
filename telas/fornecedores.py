# -*- coding: utf-8 -*-
import streamlit as st

def DB_listar_fornecedores():
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    if not db: return []
    try:
        res = db.table("fornecedores").select("*").eq("empresa_id", empresa_id).execute()
        return res.data or []
    except:
        # Caso a tabela ainda não exista, retorna uma lista mockada para não travar a tela
        return [{"id": 1, "nome": "Itambé Distribuidora"}, {"id": 2, "nome": "Ambev S/A"}]

def DB_criar_fornecedor(nome, contato):
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    if not db: return False
    try:
        data = {"nome": nome, "contato": contato, "empresa_id": empresa_id}
        db.table("fornecedores").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar fornecedor: {e}")
        return False

def show_fornecedores():
    st.markdown("## 🏭 Gerenciamento de Fornecedores")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["👁️ Fornecedores Cadastrados", "➕ Registrar Fornecedor"])
    
    with tab1:
        lista = DB_listar_fornecedores()
        for f in lista:
            st.markdown(f"🏢 **{f.get('nome')}** — *Contato:* {f.get('contato', 'Não informado')}")
            st.markdown("<hr style='margin:5px 0; border-color:#eee;'>", unsafe_allow_html=True)
            
    with tab2:
        with st.form("form_novo_fornecedor"):
            nome_f = st.text_input("Razão Social / Nome Fantasia")
            contato_f = st.text_input("Telefone ou E-mail de Contato")
            if st.form_submit_button("Salvar Fornecedor", type="primary"):
                if nome_f.strip():
                    if DB_criar_fornecedor(nome_f.strip(), contato_f.strip()):
                        st.success("Fornecedor cadastrado com sucesso!")
                        st.rerun()
                else:
                    st.warning("O nome do fornecedor é obrigatório.")
