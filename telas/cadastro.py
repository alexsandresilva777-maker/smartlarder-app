if submitted:
        if not nome:
            st.error("O nome é obrigatório!")
        else:
            # CRIANDO O DICIONÁRIO COMPLETO PARA O DATABASE.PY
            novo_prod = {
                "codigo_barras": barcode,
                "nome": nome,
                "categoria": categoria,
                "quantidade": quantidade,
                "unidade": unidade,
                "validade": str(validade),
                "lote": "",            # Adicionado para evitar o erro de binding
                "fornecedor": "",      # Adicionado por segurança
                "localizacao": "",     # Adicionado por segurança
                "preco_custo": 0.0,    # Adicionado por segurança
                "estoque_minimo": 0.0, # Adicionado por segurança
                "observacoes": "",     # Adicionado por segurança
                "criado_por": st.session_state.get("username", "admin")
            }
            
            try:
                db.inserir_produto(novo_prod, user_id, novo_prod["criado_por"])
                st.success(f"✅ {nome} cadastrado com sucesso!")
                # Limpa para o próximo
                st.session_state.lk_codigo = ""
                st.session_state.dados_busca = {}
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar no banco: {e}")
