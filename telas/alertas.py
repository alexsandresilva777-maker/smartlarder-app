def show_alertas():
    """
    Interface com Modo Diagnóstico para desmascarar o retorno do Supabase.
    """
    st.markdown("## 🔔 Central de Alertas Ativos")
    st.markdown("---")
    
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    
    st.info("🔬 **Modo Diagnóstico Ativado:** Vamos verificar o que o banco de dados está respondendo.")
    
    # Botão de Teste Rápido
    if st.button("🔍 Inspecionar Resposta do Supabase", type="secondary"):
        if not db:
            st.error("❌ Conexão 'db' não foi encontrada na sessão!")
            return
            
        try:
            # Força a busca bruta exatamente como a função de e-mail faz
            res = db.table("produtos").select("*").execute()
            
            st.markdown("### 📊 Relatório Técnico do Banco:")
            st.write(f"**Tipo do retorno:** `{type(res)}`")
            
            if hasattr(res, 'data'):
                st.write(f"**Quantidade de itens retornados:** `{len(res.data)}` itens.")
                st.markdown("**Dados Brutos Recebidos (Primeiros 2 itens):**")
                # Mostra o formato real dos dados na tela para checarmos as chaves
                st.json(res.data[:2]) 
            else:
                st.warning("⚠️ O objeto retornado não possui o atributo '.data'.")
                st.write(res)
                
        except Exception as e:
            st.error(f"❌ Erro ao tentar ler a tabela 'produtos': {e}")
            
    st.markdown("---")
    
    # Campo de e-mail e botão original continuam aqui embaixo...
    email_destino = st.text_input("E-mail de Destino para Alertas:", value="alexsandresilva777@gmail.com")
    
    btn_verificar = st.button("🚀 Verificar Estoque e Enviar Relatório", type="primary", use_container_width=True)
    
    if btn_verificar:
        with st.spinner("Varrendo o Supabase..."):
            enviou = verificar_e_enviar_alertas(db, empresa_id, email_destino)
            if enviou:
                st.success("🎉 Enviado com sucesso!")
                st.balloons()
            else:
                st.info("🔍 O sistema rodou a varredura, mas nenhuma inconsistência foi detectada.")
