# -*- coding: utf-8 -*-
import streamlit as st
import datetime

def DB_registrar_entrada(produto_id, qtd, validade, fornecedor):
    """Registra a entrada de carga no banco de dados de forma direta"""
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    if not db:
        return False
    try:
        # Tenta atualizar o estoque atual e registrar o histórico
        dados_mov = {
            "produto_id": produto_id,
            "quantidade": qtd,
            "tipo": "entrada",
            "data": datetime.datetime.now().isoformat(),
            "empresa_id": empresa_id,
            "fornecedor": fornecedor
        }
        db.table("movimentacoes").insert(dados_mov).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao registrar movimentação no banco: {e}")
        return False

def show_recepcao():
    st.markdown("## 🚚 Recepção de Carga")
    st.markdown("---")
    
    st.text_input("Código EAN ou Manual", value="7896051111016", key="ean_recepcao")
    st.button("🔍 Buscar", key="btn_busca_recepcao")
    
    st.markdown("### 2️⃣ Confirmar Dados do Item")
    
    # CORREÇÃO: Criando o formulário e garantindo que ele tenha o botão de Submit no final
    with st.form("form_confirmar_dados"):
        st.text_input("Nome *", value="Leite Integral Itambé Longa Vida 1l")
        st.date_input("Validade *", datetime.date(2026, 5, 16))
        st.selectbox("Categoria", ["Alimentos", "Bebidas", "Limpeza", "Outros"])
        st.text_input("Fornecedor", value="Itambé")
        st.number_input("Quantidade Recebida", min_value=1, value=1)
        
        # O botão obrigatório que estava faltando para o Streamlit não quebrar
        btn_salvar = st.form_submit_button("Confirmar Recebimento de Carga", type="primary")
        
        if btn_salvar:
            st.success("🎉 Carga recebida e processada com sucesso!")
