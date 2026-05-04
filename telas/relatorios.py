import streamlit as st
import pandas as pd
import pytz
from datetime import datetime, timedelta
from utils.database import listar_produtos

def show_relatorios():
    # Recupera credenciais do SaaS
    user_id = st.session_state.get("user_id")
    empresa_id = st.session_state.get("empresa_id")
    
    if not user_id or not empresa_id:
        st.error("❌ Sessão inválida. Reabra o app.")
        st.stop()

    st.markdown("## 📊 Painel de Relatórios")
    
    # Busca dados com foco no isolamento por empresa
    df_raw = listar_produtos(user_id, empresa_id)

    tab1, tab2, tab3 = st.tabs(["📦 Estoque", "📈 Movimentos", "📅 Gestão de Validade"])

    if df_raw is None or df_raw.empty:
        st.info("Nenhum dado encontrado para sua empresa.")
        st.stop()

    # --- ABA 1: ESTOQUE ---
    with tab1:
        st.dataframe(df_raw, use_container_width=True)

    # --- ABA 2: MOVIMENTAÇÕES ---
    with tab2:
        st.subheader("Giro de Estoque")
        # Seleção segura de colunas
        cols = [c for c in ['nome', 'quantidade', 'unidade'] if c in df_raw.columns]
        st.table(df_raw[cols])

    # --- ABA 3: VALIDADE (Versão SaaS Segura) ---
    with tab3:
        df_v = df_raw.copy()
        df_v['validade'] = pd.to_datetime(df_v['validade'], errors='coerce')
        
        # Ajuste de Fuso Horário Local
       # Ajuste de Fuso Horário Local (VERSÃO SEGURA)
tz = pytz.timezone("America/Sao_Paulo")
agora = datetime.now(tz)
hoje = agora.date()

def to_local(dt):
    if pd.isna(dt):
        return None
    try:
        if dt.tzinfo is None:
            return dt.tz_localize(tz)
        return dt.tz_convert(tz)
    except:
        return None

def definir_status(dt):
    dt_aware = to_local(dt)
    if dt_aware is None:
        return "⚪ Sem data"

    dt_date = dt_aware.date()

    if dt_date < hoje: return "❌ VENCIDO"
    if dt_date <= hoje + timedelta(days=15): return "⚠️ CRÍTICO (15 dias)"
    if dt_date <= hoje + timedelta(days=30): return "🟡 ALERTA (30 dias)"
    return "✅ Ok"

df_v['Status'] = df_v['validade'].apply(definir_status)

# Filtro interativo
opcoes = ["❌ VENCIDO", "⚠️ CRÍTICO (15 dias)", "🟡 ALERTA (30 dias)", "✅ Ok"]
selecionados = st.multiselect("Foco de Atenção:", opcoes, default=opcoes[:2])

if not selecionados:
    st.warning("Selecione ao menos um status.")
else:
    exibir = df_v[df_v['Status'].isin(selecionados)].sort_values('validade')

    cols = [c for c in ['nome', 'validade', 'quantidade', 'Status'] if c in exibir.columns]
    st.dataframe(exibir[cols], use_container_width=True)
