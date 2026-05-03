import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from utils.database import listar_produtos, listar_movimentacoes, get_stats

def show_relatorios():
    user_id = st.session_state.get("user_id", 1)
    st.markdown("## 📊 Relatórios")
    tab1, tab2, tab3 = st.tabs(["📋 Estoque Completo", "📈 Movimentações", "📉 Análise de Validade"])
    with tab1: _estoque()
    with tab2: _movimentacoes()
    with tab3: _validade()

def _cor_status(val):

    return {
        "vencido": "background-color:#fde8e8;color:#7a0000",
        "critico": "background-color:#fff3cd;color:#7a4500",
        "atencao": "background-color:#fff8e1;color:#5a4500",
        "ok":      "background-color:#e8f5e9;color:#1a4a1a",
    }.get(str(val).lower(), "")

def _estoque():
    st.markdown("### 📋 Inventário Completo")
    produtos = listar_produtos(user_id, )
    if not produtos:
        st.info("Nenhum produto cadastrado.")
        return

    df = pd.DataFrame(produtos)
    valor_total = (df["preco_custo"].fillna(0) * df["quantidade"]).sum()
    abaixo = df[df.apply(
        lambda r: (r.get("estoque_minimo") or 0) > 0
                  and r["quantidade"] < (r.get("estoque_minimo") or 0), axis=1
    )]

    m1, m2, m3 = st.columns(3)
    m1.metric("Total de Itens", len(produtos))
    m2.metric("Valor Total em Estoque",
              f"R$ {valor_total:,.2f}".replace(",","X").replace(".",",").replace("X","."))
    m3.metric("🔴 Abaixo do Mínimo", len(abaixo))

    cols_show = [c for c in
                 ["nome","codigo_barras","categoria","quantidade","unidade",
                  "validade","preco_custo","estoque_minimo","lote",
                  "fornecedor","localizacao","status"]
                 if c in df.columns]

    sf = st.multiselect(
        "Filtrar por Status",
        ["ok","atencao","critico","vencido"],
        default=["ok","atencao","critico","vencido"],
        format_func=lambda x: {"ok":"✅ OK","atencao":"🕐 Atenção",
                                "critico":"⚠️ Crítico","vencido":"🚨 Vencido"}[x]
    )
    df_filt = df[df["status"].isin(sf)] if "status" in df.columns else df
    df_view = df_filt[cols_show].copy()


    if "status" in df_view.columns:
        styled = df_view.style.map(_cor_status, subset=["status"])
    else:
        styled = df_view.style

    st.dataframe(styled, use_container_width=True, height=380)

    csv = df_filt[cols_show].to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(
        "📥 Exportar CSV",
        data=csv,
        file_name=f"estoque_{date.today()}.csv",
        mime="text/csv",
    )

def _movimentacoes():
    st.markdown("### 📈 Histórico de Movimentações")
    c1, c2 = st.columns(2)
    with c1:
        dias = st.slider("Período (dias)", 7, 90, 30)
    with c2:
        tf = st.selectbox("Tipo", ["Todos","Entrada","Saída"])

    movs = listar_movimentacoes(user_id, limit=1000)
    if not movs:
        st.info("Nenhuma movimentação registrada.")
        return

    df = pd.DataFrame(movs)
    df["data"] = pd.to_datetime(df["data"])
    inicio = pd.Timestamp.now() - pd.Timedelta(days=dias)
    df = df[df["data"] >= inicio]

    if tf != "Todos":
        df = df[df["tipo"] == ("entrada" if tf == "Entrada" else "saida")]

    if df.empty:
        st.info("Nenhuma movimentação no período selecionado.")
        return

    df_agg = (df.groupby([df["data"].dt.date, "tipo"])["quantidade"]
                .sum().reset_index())
    df_agg.columns = ["Data","Tipo","Quantidade"]

    fig = px.line(
        df_agg, x="Data", y="Quantidade", color="Tipo",
        color_discrete_map={"entrada":"#2d6a4f","saida":"#e74c3c"},
        markers=True,
    )
    fig.update_layout(
        margin=dict(t=10,b=10,l=0,r=0), height=260,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.12, x=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    df_show = df[["data","produto_nome","tipo","quantidade","observacao","usuario"]].copy()
    df_show.columns = ["Data/Hora","Produto","Tipo","Qtd","Observação","Usuário"]
    df_show["Data/Hora"] = df_show["Data/Hora"].dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(df_show, use_container_width=True, height=300)

    csv = df_show.to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(
        "📥 Exportar Movimentações",
        data=csv,
        file_name=f"movimentacoes_{date.today()}.csv",
        mime="text/csv",
    )

def _validade():
    st.markdown("### 📉 Análise de Vencimentos")
    produtos = listar_produtos(user_id, )
    if not produtos:
        st.info("Sem produtos cadastrados.")
        return

    df = pd.DataFrame(produtos)
    df["validade_dt"] = pd.to_datetime(df["validade"])
    df["mes_venc"] = df["validade_dt"].dt.to_period("M").astype(str)
    df_mes = (df.groupby("mes_venc").size()
                .reset_index(name="qtd")
                .sort_values("mes_venc").head(24))

    fig = px.bar(
        df_mes, x="mes_venc", y="qtd",
        color="qtd",
        color_continuous_scale=["#2d6a4f","#f0a500","#e74c3c"],
        labels={"mes_venc":"Mês de Vencimento","qtd":"Produtos"},
    )
    fig.update_layout(
        margin=dict(t=10,b=10,l=0,r=0), height=270,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Status × Categoria")
    df_cs = df.groupby(["categoria","status"]).size().reset_index(name="qtd")
    fig2 = px.bar(
        df_cs, x="categoria", y="qtd", color="status",
        color_discrete_map={"ok":"#2d6a4f","atencao":"#f0a500",
                            "critico":"#e67e22","vencido":"#e74c3c"},
        barmode="stack",
        labels={"categoria":"Categoria","qtd":"Quantidade"},
    )
    fig2.update_layout(
        margin=dict(t=10,b=10,l=0,r=0), height=260,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.12),
    )
    st.plotly_chart(fig2, use_container_width=True)

    s = get_stats(user_id)
    st.markdown("#### 📌 Resumo Executivo")
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Total de Itens", s["total"])
    e2.metric("🚨 Vencidos",    s["vencidos"])
    e3.metric("⚠️ Críticos",    s["criticos"])
    e4.metric(
        "💰 Valor em Estoque",
        f"R$ {s['total_estoque']:,.2f}".replace(",","X").replace(".",",").replace("X","."),
    )
