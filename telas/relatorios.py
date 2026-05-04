import streamlit as st
import pandas as pd
import pytz
from datetime import datetime, timedelta
from utils.database import listar_produtos

def show_relatorios():
   # Recupera credenciais com valores padrão para evitar o crash imediato
    user_id = st.session_state.get("user_id")
    empresa_id = st.session_state.get("empresa_id")
    
    if not user_id or not empresa_id:
        st.warning("⚠️ Identificação de segurança não encontrada.")
        if st.button("Ir para tela de Login"):
            st.session_state.current_page = "Login" # ou o nome da sua tela inicial
            st.rerun()
        st.stop()
    st.markdown("## 📊 Painel de Relatórios")
    
    # Busca dados com foco no isolamento por empresa
    dados_banco = listar_produtos(user_id, empresa_id)
    df_raw = pd.DataFrame(dados_banco)
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
        cols = [c for c in ['nome', 'quantidade', 'unidade'] if c in df_raw.columns]
        st.table(df_raw[cols])

    # --- ABA 3: VALIDADE ---
    with tab3:
        df_v = df_raw.copy()

        # Segurança: garante que a coluna existe
        if 'validade' not in df_v.columns:
            st.warning("Coluna 'validade' não encontrada.")
            return

        df_v['validade'] = pd.to_datetime(df_v['validade'], errors='coerce')

        # Versão estável (sem problemas de timezone)
        agora = datetime.now()
        hoje = agora.date()

        def definir_status(dt):
            if pd.isna(dt):
                return "⚪ Sem data"
            try:
                dt_date = dt.date()
            except:
                return "⚪ Sem data"

            if dt_date < hoje: return "❌ VENCIDO"
            if dt_date <= hoje + timedelta(days=15): return "⚠️ CRÍTICO (15 dias)"
            if dt_date <= hoje + timedelta(days=30): return "🟡 ALERTA (30 dias)"
            return "✅ Ok"

        # 🔥 AGORA ESTÁ NO LUGAR CERTO (dentro do tab3)
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
        
    
