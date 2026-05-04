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
        tz = pytz.timezone("America/Sao_Paulo")
        agora = datetime.now(tz)

        def definir_status(dt):
            if pd.isna(dt): return "⚪ Sem data"
            # Garante que a comparação ignore horas para ser justo com o dia
            dt_aware = dt.tz_localize(tz) if dt.tzinfo is None else dt.astimezone(tz)
            if dt_aware < agora: return "❌ VENCIDO"
            if dt_aware <= agora + timedelta(days=15): return "⚠️ CRÍTICO (15 dias)"
            if dt_aware <= agora + timedelta(days=30): return "🟡 ALERTA (30 dias)"
            return "✅ Ok"

        df_v['Status'] = df_v['validade'].apply(definir_status)
        
        # Filtro interativo
        opcoes = ["❌ VENCIDO", "⚠️ CRÍTICO (15 dias)", "🟡 ALERTA (30 dias)", "✅ Ok"]
        selecionados = st.multiselect("Foco de Atenção:", opcoes, default=opcoes[:2])
        
        exibir = df_v[df_v['Status'].isin(selecionados)].sort_values('validade')
        st.dataframe(exibir[['nome', 'validade', 'quantidade', 'Status']], use_container_width=True)
