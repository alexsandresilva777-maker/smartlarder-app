# -*- coding: utf-8 -*-
import streamlit as st

def DB_buscar_produto_por_codigo(codigo):
    """Busca um produto direto no Supabase pelo código de barras de forma segura"""
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    if not db or not codigo:
        return None
    try:
        res = db.table("produtos").select("*").eq("empresa_id", empresa_id).eq("codigo_barras", str(codigo)).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.warning(f"Aviso na busca por código: {e}")
        return None

def DB_salvar_produto(data):
    """Insere ou atualiza um produto no banco de dados"""
    db = st.session_state.get("db")
    if not db:
        return False
    try:
        db.table("produtos").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar produto: {e}")
        return False

def show_cadastrar():
    st.markdown("## ➕ Cadastrar Produto")
    st.checkbox("📸 Acionar Scanner (Câmera)", key="scanner_camera")
    st.markdown("---")
    
    st.markdown("### 🔍 Busca Manual")
    c_codigo = st.text_input("Digite o código de barras", key="input_cod_barras")
    
    if st.button("Buscar", type="primary"):
        if c_codigo.strip():
            produto = DB_buscar_produto_por_codigo(c_codigo.strip())
            if produto:
                st.success(f"📦 Produto localizado: {produto.get('nome')}")
                st.json(produto)
            else:
                st.info("⚠️ Produto não encontrado no banco. Pronto para novo cadastro!")
        else:
            st.warning("Insira um código válido.")
