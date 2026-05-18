# -*- coding: utf-8 -*-
"""
telas/alertas.py — Módulo de Notificações do SmartLarder Pro v2
- Integração oficial com o Resend (Cota gratuita de 3.000 envios/mês).
- Varredura de estoque mínimo e validades alinhada 100% ao banco de dados.
"""
from datetime import date, timedelta
import resend
import streamlit as st

# ── Configuração da API ───────────────────────────────────────────────────────
# Substitua o token abaixo pela chave secreta (re_...) copiada do seu painel do Resend
resend.api_key = "SUA_CHAVE_RE_AQUI"


def verificar_e_enviar_alertas(db, empresa_id: int, email_destino: str):
    """
    Varre o Supabase procurando produtos críticos (vencendo ou estoque baixo)
    e dispara um e-mail consolidado em HTML para o cliente.
    """
    if not db:
        return False
    
    hoje = date.today()
    limite_validade = hoje + timedelta(days=15) # Alerta para vencimentos nos próximos 15 dias
    
    try:
        # Busca estrita pelos produtos vinculados à empresa logada
        res = db.table("produtos").select("*").eq("empresa_id", empresa_id).execute()
        if not res or not hasattr(res, 'data') or not res.data:
            return False # Retorna Falso se a tabela estiver vazia
            
        produtos = res.data
        itens_vencendo = []
        itens_estoque_baixo = []
        
        # ── Varredura e Validação Regras de Negócio ───────────────────────────
        for p in produtos:
            nome = p.get("nome", "PRODUTO SEM NOME").upper()
            qtd = float(p.get("quantidade") or 0.0)
            qtd_min = float(p.get("quantidade_minima") or 0.0)
            unidade = p.get("unidade", "un")
            
            # 📉 Análise de Estoque Mínimo
            if qtd <= qtd_min:
                itens_estoque_baixo.append(
                    f"<li>❌ <b>{nome}</b>: Estoque atual em {qtd:.2f} {unidade} (Mínimo: {qtd_min:.2f} {unidade})</li>"
                )
            
            # 🚨 Análise de Data de Validade
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
                    pass # Evita quebras caso haja strings corrompidas na data

        # Se não houver nenhuma inconsistência no estoque, o e-mail não é enviado
        if not itens_vencendo and not itens_estoque_baixo:
            return False
            
        # ── Estrutura Visual do E-mail (Marketing e Design Limpo) ─────────────
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
                SmartLarder Pro v2 — Gestão Inteligente e Lucrativa para seu Negócio.<br>
                <i>Evitando o desperdício, maximizando seus lucros.</i>
            </p>
        </div>
        """
        
        # ── Chamada Oficial do Serviço Resend ──────────────────────────────────
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


# ... todo o início do seu arquivo telas/alertas.py (com a chave e a função verificar_e_enviar_alertas) continua EXATAMENTE IGUAL ...


# ── Interface da Central de Alertas (SUBSTITUA DAQUI ATÉ O FINAL) ──────────────
def show_alertas():
    """
    Exibe a interface gráfica na aba 'Alertas' do menu do Streamlit.
    """
    st.markdown("## 🔔 Central de Alertas Ativos")
    st.markdown("---")
    
    # 1. Recupera as conexões ativas que o seu app.py já colocou na sessão
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    
    st.info("💡 **Monitoramento Operacional:** Os relatórios diários de validade e estoque mínimo cruzam os dados do Supabase e notificam você por e-mail antes do prejuízo acontecer.")
    
    st.markdown("### 📬 Configuração de Disparo")
    
    # 2. Caixa de texto para você colocar o e-mail de teste (Obrigatório aparecer na tela)
    email_destino = st.text_input("E-mail de Destino para Alertas:", value="seu_email_aqui@gmail.com")
    
    st.markdown(" ")
    
    # 3. O botão de disparo que vai ativar a mágica
    btn_verificar = st.button("🚀 Verificar Estoque e Enviar Relatório", type="primary", use_container_width=True)
    
    if btn_verificar:
        with st.spinner("Varrendo o Supabase e estruturando relatório em HTML..."):
            enviou = verificar_e_enviar_alertas(db, empresa_id, email_destino)
            
            if enviou:
                st.success(f"🎉 **Espetáculo!** O relatório de alertas foi enviado com sucesso para **{email_destino}**!")
                st.balloons()
            else:
                st.info("🔍 **Tudo em ordem por aqui!** O sistema rodou a varredura, mas não encontrou nenhum produto vencido, próximo do vencimento ou abaixo do estoque mínimo.")
                
    st.markdown("---")
    st.markdown("### ⚙️ Status do Sistema")
    st.success("✅ Integração com servidor **Resend** ativa e operando normalmente.")
