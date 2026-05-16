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
        # CORREÇÃO: Atualizado para 'desc=False' para evitar quebras na API
        res = db.table("produtos").select("*").eq("empresa_id", empresa_id).order("validade", desc=False).execute()
        
        if not res.data:
            st.success("🎉 Nenhum produto com inconformidade ou validade próxima!")
            return
            
        hoje = datetime.date.today()
        vencidos = 0
        criticos = 0
        
        for p in res.data:
            if p.get("validade"):
                dt_val = datetime.datetime.strptime(p["validade"], "%Y-%m-%d").date()
                if dt_val < hoje:
                    vencidos += 1
                elif (dt_val - hoje).days <= 7:
                    criticos += 1
                    
        st.metric("Produtos Vencidos", vencidos)
        st.metric("Produtos em Alerta (≤ 7 dias)", criticos)
        
    except Exception as e:
        st.error(f"Erro ao processar alertas: {e}")
