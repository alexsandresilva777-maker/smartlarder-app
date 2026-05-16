# -*- coding: utf-8 -*-
import streamlit as st

def show_ajuda():
    st.markdown("## ❓ Central de Ajuda e Suporte")
    st.markdown("---")
    
    st.markdown("""
    ### 📦 Sobre o SmartLarder Pro
    O **SmartLarder Pro** é um sistema inteligente de gestão de inventário e controlo de validades, 
    desenvolvido para automatizar processos de entrada, saída e monitorização de perecíveis.
    """)
    
    with st.expander("💡 Dicas de Utilização"):
        st.markdown("""
        - **Controlo de Validades:** Aceda à página de *Alertas* para verificar os produtos vencidos ou próximos do vencimento.
        - **Relatórios:** Exporte dados consolidados e verifique o histórico de movimentações na aba *Relatórios*.
        - **Configuração de E-mail:** Configure os parâmetros SMTP no menu de *Alertas* para receber notificações diárias automáticas.
        """)
        
    with st.expander("🔐 Perfis de Acesso"):
        st.markdown("""
        - **Administrador:** Acesso total ao sistema, gestão de fornecedores, relatórios financeiros/perdas e controlo de utilizadores.
        - **Comercial:** Gestão de stock, registo de produtos, fornecedores e movimentações.
        - **Doméstico / Operador:** Consulta de stock, lista de compras e registo básico de entradas e saídas.
        """)

    st.info("✉️ **Suporte Técnico:** Se precisar de assistência adicional, contacte o administrador do sistema.")
