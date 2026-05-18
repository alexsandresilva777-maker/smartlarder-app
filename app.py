from datetime import date, timedelta
import resend
import streamlit as st

# Configure sua chave do Resend aqui (ou puxe do st.secrets no futuro)
resend.api_key = "re_WAGXgUKp_FqFwvS7zBAB5Q2o8NbYwrfFR"

def verificar_e_enviar_alertas(db, empresa_id: int, email_destino: str):
    """
    Varre o Supabase procurando produtos críticos (vencendo ou estoque baixo)
    e dispara um e-mail consolidado para o cliente.
    """
    if not db:
        return
    
    hoje = date.today()
    limite_validade = hoje + timedelta(days=15) # Alerta para produtos que vencem em 15 dias
    
    try:
        # 1. Puxa todos os produtos da empresa do banco
        res = db.table("produtos").select("*").eq("empresa_id", empresa_id).execute()
        if not res or not hasattr(res, 'data') or not res.data:
            return # Sem produtos cadastrados
            
        produtos = res.data
        itens_vencendo = []
        itens_estoque_baixo = []
        
        # 2. Processa as regras de negócio
        for p in produtos:
            nome = p.get("nome", "PRODUTO SEM NOME").upper()
            qtd = float(p.get("quantidade") or 0.0)
            qtd_min = float(p.get("quantidade_minima") or 0.0)
            unidade = p.get("unidade", "un")
            
            # Checa Estoque Mínimo
            if qtd <= qtd_min:
                itens_estoque_baixo.append(
                    f"<li>❌ <b>{nome}</b>: Estoque atual em {qtd}{unidade} (Mínimo configurado: {qtd_min}{unidade})</li>"
                )
            
            # Checa Validade
            data_v_str = p.get("data_validade")
            if data_v_str:
                try:
                    data_v = date.fromisoformat(data_v_str)
                    if data_v <= hoje:
                        itens_vencendo.append(
                            f"<li style='color: red;'>🚨 <b>{nome}</b>: <b>VENCIDO</b> em {data_v.strftime('%d/%m/%Y')}</li>"
                        )
                    elif data_v <= limite_validade:
                        itens_vencendo.append(
                            f"<li>⚠️ <b>{nome}</b>: Vence em {data_v.strftime('%d/%m/%Y')}</li>"
                        )
                except ValueError:
                    pass # Formato de data inválido, ignora

        # 3. Se houver alertas, monta o e-mail com layout de "Painel Executivo"
        if itens_vencendo or itens_estoque_baixo:
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px;">
                <h2 style="color: #1E3A8A; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px; margin-top: 0;">
                    📊 SmartLarder Pro — Relatório de Alertas Diários
                </h2>
                <p>Olá, Alex! Identificamos pontos de atenção no inventário do seu estoque hoje (<b>{hoje.strftime('%d/%m/%Y')}</b>):</p>
            """
            
            if itens_vencendo:
                html_content += f"""
                <h3 style="color: #B91C1C; margin-top: 20px;">⚠️ Alertas de Validade (Próximos 15 dias ou Vencidos)</h3>
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
                    SmartLarder Pro v2 — Gestão Inteligente e Lucrativa para seu Negócio.<br>
                    <i>Evitando o desperdício, maximizando seus lucros.</i>
                </p>
            </div>
            """
            
            # 4. Dispara o e-mail via Resend
            resend.Emails.send({
                "from": "SmartLarder Pro <onboarding@resend.dev>",
                "to": email_destino,
                "subject": f"⚠️ Alertas de Estoque - {hoje.strftime('%d/%m/%Y')}",
                "html": html_content
            })
            return True
            
    except Exception as e:
        print(f"Erro ao processar alertas de e-mail: {e}")
    return False
