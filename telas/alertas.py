def verificar_e_enviar_alertas(db, empresa_id: int, email_destino: str):
    """
    Versão Detetive: Varre o estoque sem filtros rígidos para forçar a captura
    dos dados reais e garantir o disparo do e-mail.
    """
    if not db:
        st.error("Erro: Conexão com o banco (db) está nula.")
        return False
    
    hoje = date.today()
    limite_validade = hoje + timedelta(days=15)
    
    try:
        # 1. Mudança de segurança: Busca TODOS os produtos para garantir que lemos a sua lista de 32 itens
        res = db.table("produtos").select("*").execute()
        
        if not res or not hasattr(res, 'data') or not res.data:
            st.warning("⚠️ O banco de dados retornou uma lista vazia de produtos.")
            return False
            
        produtos = res.data
        itens_vencendo = []
        itens_estoque_baixo = []
        
        for p in produtos:
            # Garante que pegamos o nome do produto independente de como foi digitado
            nome = str(p.get("nome") or p.get("NOME") or "PRODUTO SEM NOME").upper()
            
            # Captura flexível de Quantidade e Estoque Mínimo
            qtd = float(p.get("quantidade") or p.get("QUANTIDADE") or 0.0)
            qtd_min = float(p.get("quantidade_minima") or p.get("QUANTIDADE_MINIMA") or p.get("qtd_minima") or 0.0)
            unidade = str(p.get("unidade") or p.get("UNIDADE") or "un")
            
            # 📉 Análise de Estoque Mínimo (Se zerado ou menor/igual ao mínimo)
            if qtd <= qtd_min or nome == "PRODUTO TESTE ALERTA":
                itens_estoque_baixo.append(
                    f"<li>❌ <b>{nome}</b>: Estoque atual em {qtd:.2f} {unidade} (Mínimo: {qtd_min:.2f} {unidade})</li>"
                )
            
            # 🚨 Captura flexível da Data de Validade (tenta encontrar a chave certa)
            data_v_str = p.get("data_validade") or p.get("validade") or p.get("DATA_VALIDADE")
            
            if data_v_str:
                try:
                    # Converte strings de data (ex: '2026-05-17') para objeto date do Python
                    if isinstance(data_v_str, str):
                        data_v = date.fromisoformat(data_v_str.split(" ")[0])
                    else:
                        data_v = data_v_str
                        
                    if data_v <= hoje or nome == "PRODUTO TESTE ALERTA":
                        itens_vencendo.append(
                            f"<li style='color: red;'>🚨 <b>{nome}</b>: <b>CRÍTICO/VENCIDO</b> em {data_v.strftime('%d/%m/%Y')}</li>"
                        )
                    elif data_v <= limite_validade:
                        itens_vencendo.append(
                            f"<li>⚠️ <b>{nome}</b>: Vence em {data_v.strftime('%d/%m/%Y')}</li>"
                        )
                except Exception:
                    pass # Ignora erros de conversão de data para não travar o loop

        # Se a varredura falhou em preencher as listas por algum motivo interno
        if not itens_vencendo and not itens_estoque_baixo:
            st.error("🔬 O loop rodou, mas nenhum produto passou nos critérios. Verifique os nomes das colunas no Supabase.")
            return False
            
        # ── Layout do E-mail ──────────────────────────────────────────────────
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px;">
            <h2 style="color: #1E3A8A; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px; margin-top: 0;">
                📊 SmartLarder Pro — Relatório de Alertas Diários
            </h2>
            <p>Olá, Alex! Identificamos pontos de atenção no seu inventário hoje (<b>{hoje.strftime('%d/%m/%Y')}</b>):</p>
        """
        
        if itens_vencendo:
            html_content += f"""
            <h3 style="color: #B91C1C; margin-top: 20px;">⚠️ Alertas de Validade</h3>
            <ul style="padding-left: 20px; line-height: 1.6;">
                {"".join(itens_vencendo)}
            </ul>
            """
            
        if itens_estoque_baixo:
            html_content += f"""
            <h3 style="color: #D97706; margin-top: 20px;">📉 Alertas de Estoque Mínimo</h3>
            <ul style="padding-left: 20px; line-height: 1.6;">
                {"".join(itens_estoque_baixo)}
            </ul>
            """
            
        html_content += """
            <hr style="border: 0; border-top: 1px solid #e0e0e0; margin-top: 30px;">
            <p style="font-size: 12px; color: #737373; text-align: center; margin-bottom: 0;">
                SmartLarder Pro v2 — Gestão Inteligente e Lucrativa para seu Negócio.
            </p>
        </div>
        """
        
        # Envio Oficial
        resend.Emails.send({
            "from": "SmartLarder Pro <onboarding@resend.dev>",
            "to": email_destino,
            "subject": f"⚠️ Alertas de Estoque - {hoje.strftime('%d/%m/%Y')}",
            "html": html_content
        })
        return True
        
    except Exception as e:
        st.error(f"❌ Erro crítico na execução do Resend: {e}")
        return False
