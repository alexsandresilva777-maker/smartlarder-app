# ── Persistência Inteligente, Recursiva e Adaptativa ──────────────────────────
def _salvar_produto(db, empresa_id, user_id, dados: dict):
    if not db:
        st.error("❌ Sem conexão com o banco de dados.")
        return

    # Payload inicial completo com o que tentamos enviar
    payload = {
        "nome": dados["nome"].upper(),
        "categoria": dados["categoria"],
        "quantidade": float(dados["quantidade"]),
        "unidade": dados["unidade"],
        "preco_custo": float(dados["preco_custo"]),
        "empresa_id": int(empresa_id),
        "user_id": int(user_id),
        "lote": dados["lote"],
        "fornecedor": dados["fornecedor"],
        "localizacao": dados["localizacao"],
        "observacoes": dados["observacoes"],
        "barcode": dados.get("codigo_input", "").strip() or None,
        
        # Colunas com alta chance de terem nomes diferentes ou não existirem
        "estoque_minimo": float(dados["estoque_min"]),
        "quantidade_minima": float(dados["estoque_min"]),
        "data_validade": dados["validade"],
        "validade": dados["validade"]
    }

    # Executa o loop de inserção inteligente
    _executar_persistencia_defensiva(db, payload)

def _executar_persistencia_defensiva(db, payload: dict):
    """
    Tenta salvar no Supabase. Se o banco rejeitar por coluna inexistente,
    o código identifica o campo (mesmo se o erro vier como dicionário),
    remove do payload e tenta novamente de forma automática.
    """
    try:
        if st.session_state["produto_existente"] and st.session_state["produto_id"]:
            res = db.table("produtos").update(payload).eq("id", st.session_state["produto_id"]).execute()
        else:
            res = db.table("produtos").insert(payload).execute()

        if res and hasattr(res, 'data') and res.data:
            st.success(f"🎉 **{payload.get('nome')}** salvo com sucesso!")
            st.balloons()
            time.sleep(1)
            
            # Reset completo pós salvamento bem-sucedido
            st.session_state[_K_CODIGO] = ""
            st.session_state[_K_BUSCADO] = ""
            st.session_state["status_busca"] = {}
            st.session_state["produto_existente"] = False
            st.session_state["produto_id"] = None
            
            for k in FORM_KEYS:
                if k in st.session_state: del st.session_state[k]
            st.session_state[_K_FORM_ID] += 1
            st.rerun()
            return

    except Exception as e:
        # Extrai a mensagem de erro de forma segura, seja ela string ou dicionário
        msg_erro = ""
        if hasattr(e, 'message'):
            msg_erro = str(e.message).lower()
        elif isinstance(e, dict) and "message" in e:
            msg_erro = str(e["message"]).lower()
        elif isinstance(getattr(e, 'args', None), tuple) and len(e.args) > 0 and isinstance(e.args[0], dict):
            msg_erro = str(e.args[0].get("message", "")).lower()
        else:
            msg_erro = str(e).lower()
        
        # Se o erro indicar explicitamente falta de coluna (PGRST204 ou texto 'column')
        if "column" in msg_erro or "not find" in msg_erro or "schema cache" in msg_erro:
            import re
            # Procura o nome da coluna problemática dentro de aspas simples na mensagem
            match = re.search(r"'(.*?)'", msg_erro)
            if match:
                coluna_errada = match.group(1)
                if coluna_errada in payload:
                    st.warning(f"⚠️ Removendo coluna ausente no banco: '{coluna_errada}'")
                    del payload[coluna_errada]
                    _executar_persistencia_defensiva(db, payload)
                    return
            
            # Força bruta inteligente: se não achou pelo Regex, remove a primeira da lista que existir no payload
            colunas_instaveis = ["fornecedor", "lote", "localizacao", "estoque_minimo", "quantidade_minima", "data_validade", "validade"]
            for col in colunas_instaveis:
                if col in payload:
                    st.warning(f"⚠️ Forçando remoção da coluna sob suspeita: '{col}'")
                    del payload[col]
                    _executar_persistencia_defensiva(db, payload)
                    return

        # Outros tratamentos de erro padrão
        if "duplicate" in msg_erro or "unique" in msg_erro:
            st.warning("⚠️ Um produto com este código de barras já se encontra registrado.")
        else:
            st.error(f"❌ Erro crítico no Supabase: {e}")
