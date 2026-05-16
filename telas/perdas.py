# -*- coding: utf-8 -*-
import streamlit as st
import datetime

def DB_registrar_perda(produto_id, qtd, motivo):
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    if not db: return False
    try:
        data = {
            "produto_id": produto_id,
            "quantidade": qtd,
            "tipo": "perda",
            "motivo": motivo,
            "data": datetime.datetime.now().isoformat(),
            "empresa_id": empresa_id
        }
        db.table("movimentacoes").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao registrar perda: {e}")
        return False

def show_perdas():
    st.markdown("## 📉 Controle de Perdas e Avarias")
    st.markdown("---")
    
    with st.form("form_registrar_perda"):
        st.markdown("### 🚫 Registrar Novo Descarte / Avaria")
        p_id = st.number_input("ID do Produto", min_value=1, value=1)
        qtd_p = st.number_input("Quantidade Avariada", min_value=1, value=1)
        motivo_p = st.selectbox("Motivo da Perda", ["Validade Vencida", "Embalagem Danificada", "Produto Roubado/Extraviado", "Defeito de Fábrica"])
        
        if st.form_submit_button("Confirmar Registro de Perda", type="primary"):
            if DB_registrar_perda(p_id, qtd_p, motivo_p):
                st.success("📉 Perda registrada no sistema e estoque atualizado!")
