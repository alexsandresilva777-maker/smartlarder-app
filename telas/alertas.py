# -*- coding: utf-8 -*-
import streamlit as st
import datetime

def show_alertas():
    st.markdown("## 🔔 Central de Alertas e Validades")
    st.markdown("---")
    
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    
    if not db:
        st.error("Banco de dados inacessível.")
        return

    try:
        # Puxa os dados gerais para checar as colunas sem forçar uma ordenação por coluna inexistente
        res = db.table("produtos").select("*").eq("empresa_id", empresa_id).execute()
        
        if not res.data:
            st.success("🎉 Nenhum produto cadastrado no momento!")
            return
            
        hoje = datetime.date.today()
        vencidos = 0
        criticos = 0
        
        # Mapeia dinamicamente qual nome de coluna o banco está usando para a data
        primeiro_registro = res.data[0]
        coluna_data = None
        for possivel_nome in ["validade", "data_validade", "vencimento", "data_vencimento"]:
            if possivel_nome in primeiro_registro:
                coluna_data = possivel_nome
                break
        
        if not coluna_data:
            st.warning("⚠️ Nota: Nenhuma coluna de data de validade foi encontrada na tabela do banco.")
            st.dataframe(res.data, use_container_width=True)
            return

        for p in res.data:
            if p.get(coluna_data):
                try:
                    dt_val = datetime.datetime.strptime(str(p[coluna_data])[:10], "%Y-%m-%d").date()
                    if dt_val < hoje:
                        vencidos += 1
                    elif (dt_val - hoje).days <= 7:
                        criticos += 1
                except:
                    pass
                    
        c1, c2 = st.columns(2)
        c1.metric("Produtos Vencidos", vencidos)
        c2.metric("Produtos em Alerta (≤ 7 dias)", criticos)
        
        st.markdown("### 📋 Listagem de Itens")
        st.dataframe(res.data, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao processar alertas: {e}")
