# -*- coding: utf-8 -*-
import streamlit as st
import datetime

def show_alertas():
    st.markdown("## 🔔 Central de Alertas e Validades")
    st.markdown("---")
    
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    
    if not db:
        st.error("Banco de dados inacessível.")
        return

    try:
        # Busca os produtos para checarmos as colunas existentes em tempo de execução
        res = db.table("produtos").select("*").eq("empresa_id", empresa_id).execute()
        
        if not res.data:
            st.success("🎉 Nenhum produto cadastrado ou em inconformidade no momento!")
            return
            
        hoje = datetime.date.today()
        vencidos = 0
        criticos = 0
        
        # Identifica dinamicamente qual nome de coluna de data está sendo usado
        primeiro_reg = res.data[0]
        coluna_data = None
        for possivel_nome in ["validade", "data_validade", "vencimento", "data_vencimento"]:
            if possivel_nome in primeiro_reg:
                coluna_data = possivel_nome
                break
        
        if not coluna_data:
            st.warning("⚠️ Nota: Nenhuma coluna de data de validade mapeada no banco de dados. Exibindo lista geral.")
            st.dataframe(res.data, use_container_width=True)
            return

        for p in res.data:
            if p.get(coluna_data):
                try:
                    # Tenta converter o formato de data vindo do banco
                    dt_val = datetime.datetime.strptime(str(p[coluna_data])[:10], "%Y-%m-%d").date()
                    if dt_val < hoje:
                        vencidos += 1
                    elif (dt_val - hoje).days <= 7:
                        criticos += 1
                except:
                    pass
                    
        col1, col2 = st.columns(2)
        col1.metric("Produtos Vencidos", vencidos, delta="- Crítico" if vencidos > 0 else None, delta_color="inverse")
        col2.metric("Produtos em Alerta (≤ 7 dias)", criticos, delta="- Atenção" if criticos > 0 else None, delta_color="off")
        
        st.markdown("### 📋 Todos os Itens e Prazos")
        st.dataframe(res.data, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao processar alertas: {e}")
