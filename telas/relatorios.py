# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

def show_relatorios():
    st.markdown("## 📊 Painel de Relatórios")
    st.markdown("---")
    
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    
    if not db:
        st.error("Banco de dados inacessível.")
        return

    try:
        # CORREÇÃO: Utilizando 'desc=True' em vez de 'descending=True' para a nova API do Supabase
        res = db.table("produtos").select("*").eq("empresa_id", empresa_id).order("nome", desc=False).execute()
        
        if not res.data:
            st.info("Nenhum dado encontrado para gerar relatórios.")
            return
            
        df = pd.DataFrame(res.data)
        
        # Exibição básica de métricas de exemplo
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Itens Cadastrados", len(df))
        if "quantidade" in df.columns:
            c2.metric("Volume Total em Estoque", int(df["quantidade"].sum()))
        
        st.markdown("### 📋 Visão Geral dos Dados")
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao conectar com as tabelas do Supabase: {e}")
