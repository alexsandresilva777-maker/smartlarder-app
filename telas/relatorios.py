# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz

_TZ = pytz.timezone("America/Sao_Paulo")

def show_relatorios():
    # Recupera a conexão do banco e dados da sessão
    supabase = st.session_state.get("db")
    user_id = st.session_state.get("user_id")
    empresa_id = st.session_state.get("empresa_id")
    
    if not user_id or not empresa_id:
        st.warning("⚠️ Identificação de segurança não encontrada.")
        if st.button("Ir para tela de Login"):
            st.session_state.current_page = "Login"
            st.rerun()
        st.stop()

    if supabase is None:
        st.error("Conexão com o banco de dados indisponível.")
        return

    st.markdown("## 📊 Painel de Relatórios")
    
    # ── CARGA DE DADOS (Isolamento por Empresa) ──────────────────────────────
    with st.spinner("Carregando dados consolidados..."):
        try:
            # 1. Busca os Produtos atuais
            res_prod = supabase.table("produtos").select("*").eq("empresa_id", empresa_id).execute()
            df_produtos = pd.DataFrame(res_prod.data or [])
            
            # 2. Busca o Histórico de Movimentações (Últimas 200 para não estourar a tela)
            res_mov = supabase.table("movimentacoes")\
                .select("id, tipo, quantidade, motivo, created_at, produto_id")\
                .eq("empresa_id", empresa_id)\
                .order("created_at", descending=True)\
                .limit(200)\
                .execute()
            df_movimentos = pd.DataFrame(res_mov.data or [])
            
        except Exception as e:
            st.error(f"Erro ao conectar com as tabelas do Supabase: {e}")
            st.stop()

    # Cria as abas de navegação
    tab1, tab2, tab3 = st.tabs(["📦 Estoque Atual", "📈 Giro de Estoque (Movimentações)", "📅 Gestão de Validade"])

    # 📌 --- ABA 1: ESTOQUE ---
    with tab1:
        st.subheader("Posição Geral de Itens")
        if df_produtos.empty:
            st.info("Nenhum produto cadastrado para a sua empresa.")
        else:
            # Reorganiza colunas amigáveis para exibição
            colunas_exibir = {
                "barcode": "Código de Barras",
                "nome": "Nome do Produto",
                "categoria": "Categoria",
                "quantidade": "Estoque Atual",
                "unidade": "Unidade",
                "quantidade_minima": "Est. Mínimo",
                "preco_custo": "Preço de Custo (R$)",
                "data_validade": "Próximo Vencimento",
                "localizacao": "Obs/Referência"
            }
            # Filtra apenas as colunas que existem no DataFrame real
            existentes = [c for c in colunas_exibir.keys() if c in df_produtos.columns]
            
            df_fmt = df_produtos[existentes].rename(columns=colunas_exibir)
            st.dataframe(df_fmt, use_container_width=True, hide_index=True)

    # 📌 --- ABA 2: MOVIMENTAÇÕES (Histórico Real) ---
    with tab2:
        st.subheader("Linha do Tempo de Entradas e Saídas")
        if df_movimentos.empty:
            st.info("Nenhuma movimentação de entrada ou saída registrada recentemente.")
        else:
            if not df_produtos.empty and "produto_id" in df_movimentos.columns:
                # Faz o mapeamento do ID para o Nome do produto para ficar legível
                mapa_nomes = dict(zip(df_produtos["id"], df_produtos["nome"]))
                df_movimentos["Produto"] = df_movimentos["produto_id"].map(mapa_nomes).fillna("Produto Removido")
            else:
                df_movimentos["Produto"] = "Desconhecido"
                
            # Tratamento visual e formatação de datas
            df_movimentos["Data/Hora"] = pd.to_datetime(df_movimentos["created_at"]).dt.tz_convert("America/Sao_Paulo").dt.strftime("%d/%m/%Y %H:%M")
            df_movimentos["Tipo"] = df_movimentos["tipo"].apply(lambda t: "📥 ENTRADA" if t == "entrada" else "📤 SAÍDA")
            
            colunas_mov = ["Data/Hora", "Produto", "Tipo", "quantidade", "motivo"]
            colunas_renomear = {
                "quantidade": "Qtd Movimentada",
                "motivo": "Motivo / Justificativa"
            }
            
            df_mov_exibir = df_movimentos[colunas_mov].rename(columns=colunas_renomear)
            st.dataframe(df_mov_exibir, use_container_width=True, hide_index=True)

    # 📌 --- ABA 3: VALIDADE ---
    with tab3:
        st.subheader("Análise de Perecibilidade")
        if df_produtos.empty:
            st.info("Sem produtos para analisar validade.")
        elif "data_validade" not in df_produtos.columns:
            st.warning("Coluna de data de validade não mapeada no banco.")
        else:
            df_v = df_produtos.copy()
            df_v["data_validade"] = pd.to_datetime(df_v["data_validade"], errors="coerce")

            hoje = datetime.now(_TZ).date()

            def definir_status(dt):
                if pd.isna(dt):
                    return "⚪ Sem data"
                dt_date = dt.date()
                if dt_date < hoje: 
                    return "❌ VENCIDO"
                if dt_date <= hoje + timedelta(days=15): 
                    return "⚠️ CRÍTICO (15 dias)"
                if dt_date <= hoje + timedelta(days=30): 
                    return "🟡 ALERTA (30 dias)"
                return "✅ Ok"

            df_v["Status"] = df_v["data_validade"].apply(definir_status)

            # Filtro interativo de Status
            opcoes = ["❌ VENCIDO", "⚠️ CRÍTICO (15 dias)", "🟡 ALERTA (30 dias)", "✅ Ok", "⚪ Sem data"]
            selecionados = st.multiselect("Foco de Atenção:", opcoes, default=opcoes[:3])

            if not selecionados:
                st.warning("Selecione ao menos um status para filtrar.")
            else:
                exibir = df_v[df_v["Status"].isin(selecionados)]
                if not exibir.empty:
                    # Ordena pondo os vencidos/críticos no topo
                    exibir = exibir.sort_values("data_validade", ascending=True, na_position="last")
                    
                    # Converte a coluna de data para string legível antes de exibir
                    exibir["Validade"] = exibir["data_validade"].dt.strftime("%d/%m/%Y").fillna("—")
                    
                    cols = [c for c in ["nome", "Validade", "quantidade", "unidade", "Status"] if c in exibir.columns]
                    cols_renomear = {"nome": "Produto", "quantidade": "Qtd Atual", "unidade": "Unidade"}
                    
                    st.dataframe(exibir[cols].rename(columns=cols_renomear), use_container_width=True, hide_index=True)
                else:
                    st.success("Nenhum produto se enquadra nos filtros de atenção selecionados!")
