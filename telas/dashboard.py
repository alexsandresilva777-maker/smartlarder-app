# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import pytz

_TZ = pytz.timezone("America/Sao_Paulo")

def _fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def _kpi_card(col, emoji_label: str, valor, cor: str, bg: str, border: str,
             prefixo="", sufixo="", help_txt=""):
    with col:
        tooltip = f" title='{help_txt}'" if help_txt else ""
        st.markdown(
            f"""<div{tooltip} style='background:{bg};border:1.5px solid {border};
                border-radius:14px;padding:16px 10px;text-align:center;
                box-shadow:0 2px 12px rgba(0,0,0,.06);'>
              <div style='font-size:1.75rem;font-weight:800;color:{cor};line-height:1.1;'>
                {prefixo}{valor}{sufixo}
              </div>
              <div style='font-size:0.74rem;color:#555;margin-top:5px;font-weight:500;'>
                {emoji_label}
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

def _buscar_dados_supabase(supabase, user_id: int):
    """Substitui o antigo utils.database puxando os dados reais do Supabase"""
    stats = {
        "total": 0, "vencidos": 0, "criticos": 0, "atencao": 0, "ok": 0,
        "total_estoque": 0.0, "gasto_mensal": 0.0, "abaixo_minimo": 0,
        "capital_em_risco": 0.0, "categorias": []
    }
    produtos = []
    movimentacoes = []
    
    try:
        # 1. Busca todos os produtos vinculados ao usuário/empresa
        res_prod = supabase.table("produtos").select("*").execute()
        if res_prod.data:
            produtos = res_prod.data
            stats["total"] = len(produtos)
            
            # Agrupamento por categorias para o gráfico de barras
            cat_dict = {}
            
            for p in produtos:
                status = p.get("status", "ok")
                qtd = p.get("quantidade", 0)
                minimo = p.get("quantidade_minima", 0)
                custo = p.get("preco_custo", 0.0) or 0.0
                valor_item = qtd * custo
                
                # Incrementa contadores de status
                if status in stats:
                    stats[status] += 1
                else:
                    stats["ok"] += 1
                    
                if qtd < minimo:
                    stats["abaixo_minimo"] += 1
                    
                stats["total_estoque"] += valor_item
                
                if status in ("vencido", "critico", "atencao"):
                    stats["capital_em_risco"] += valor_item
                
                # Processa categorias
                cat_nome = p.get("categoria", "Outros")
                cat_dict[cat_nome] = cat_dict.get(cat_nome, 0.0) + valor_item

            # Converte dicionário de categorias para o formato do Plotly
            stats["categorias"] = [{"categoria": k, "valor": v} for k, v in cat_dict.items()]

        # 2. Busca movimentações dos últimos 30 dias para o gráfico histórico
        res_mov = supabase.table("movimentacoes").select("created_at, tipo, quantidade").execute()
        if res_mov.data:
            df_mov_raw = pd.DataFrame(res_mov.data)
            if not df_mov_raw.empty:
                df_mov_raw["created_at"] = pd.to_datetime(df_mov_raw["created_at"])
                df_mov_raw["dia"] = df_mov_raw["created_at"].dt.strftime("%d/%m")
                df_grouped = df_mov_raw.groupby(["dia", "tipo"])["quantidade"].sum().reset_index()
                df_grouped.columns = ["dia", "tipo", "total"]
                movimentacoes = df_grouped.to_dict(orient="records")

    except Exception as e:
        st.warning(f"Aviso ao carregar dados do banco: {e}")
        
    return stats, produtos, movimentacoes

def show_dashboard(supabase): # Recebe a conexão do app.py
    user_id = st.session_state.get("user_id", 1)
    nome    = st.session_state.get("nome_completo","Usuário").split()[0]
    hoje    = datetime.now(_TZ).strftime("%d/%m/%Y")

    st.markdown(
        f"""<div style='background:linear-gradient(135deg,#0f2318 0%,#1b4332 60%,#2d6a4f 100%);
            border-radius:16px;padding:22px 28px;margin-bottom:22px;
            box-shadow:0 4px 20px rgba(15,35,24,.3);
            display:flex;align-items:center;justify-content:space-between;'>
          <div>
            <div style='font-size:1.45rem;font-weight:700;color:#d4f0df;
                        font-family:"Playfair Display",Georgia,serif;'>
              Olá, {nome}! 👋
            </div>
            <div style='color:#74c69d;font-size:0.83rem;margin-top:3px;'>
              Painel de controle · {hoje}
            </div>
          </div>
          <div style='font-size:3rem;opacity:.9;'>📦</div>
        </div>""",
        unsafe_allow_html=True,
    )

    # Processa os dados diretamente do Supabase
    s, todos, mov = _buscar_dados_supabase(supabase, user_id)

    # ── KPIs Estoque ───────────────────────────────────────────────────────────
    st.markdown("#### 📦 Situação do Estoque")
    c1,c2,c3,c4,c5 = st.columns(5)
    _kpi_card(c1,"📦 Total Itens",   s["total"],    "#0f2318","#e8f5e9","#c8e6c9")
    _kpi_card(c2,"🔴 Vencidos",      s["vencidos"], "#b71c1c","#fde8e8","#ffcdd2")
    _kpi_card(c3,"🟡 Críticos ≤7d",  s["criticos"], "#e65100","#fff3cd","#ffe0b2")
    _kpi_card(c4,"🟡 Atenção ≤30d",  s["atencao"],  "#f57f17","#fffde7","#fff9c4")
    _kpi_card(c5,"🟢 OK",            s["ok"],       "#1b5e20","#e8f5e9","#c8e6c9")

    st.markdown("")

    # ── KPIs Financeiro ────────────────────────────────────────────────────────
    st.markdown("#### 💰 Visão Financeira")
    f1,f2,f3,f4 = st.columns(4)
    _kpi_card(f1,"💵 Valor em Estoque",  _fmt_brl(s["total_estoque"]),
              "#1a237e","#e8eaf6","#c5cae9")
    _kpi_card(f2,"📉 Gasto Médio/Mês",   _fmt_brl(s["gasto_mensal"]),
              "#4a148c","#f3e5f5","#e1bee7")
    _kpi_card(f3,"🔴 Abaixo do Mínimo",  s["abaixo_minimo"],
              "#b71c1c","#fde8e8","#ffcdd2")
    _kpi_card(f4,"⚠️ Capital em Risco",  _fmt_brl(s.get("capital_em_risco",0.0)),
              "#e65100","#fff3e0","#ffccbc",
              help_txt="Valor de custo dos itens vencidos, críticos e em atenção (≤30d)")

    st.markdown("")

    # ── Gráficos ───────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 🍩 Status dos Produtos")
        labels = ["🟢 OK","🟡 Atenção (≤30d)","🔴 Crítico (≤7d)","🔴 Vencido"]
        values = [s["ok"], s["atencao"], s["criticos"], s["vencidos"]]
        cores  = ["#2d6a4f","#f0a500","#e67e22","#e74c3c"]
        fig = go.Figure(go.Pie(
            labels=labels, values=values, marker_colors=cores,
            hole=0.52, textinfo="label+percent", textfont_size=11,
            hovertemplate="%{label}: %{value}<extra></extra>",
        ))
        fig.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=10),
                          height=255, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("#### 🗂️ Valor por Categoria (R$)")
        cats = s.get("categorias", [])
        if cats:
            df_cat = pd.DataFrame(cats)
            if "valor" in df_cat.columns and not df_cat.empty:
                df_cat = df_cat[df_cat["valor"] > 0].sort_values("valor", ascending=True)
                if not df_cat.empty:
                    df_cat["valor_fmt"] = df_cat["valor"].apply(
                        lambda v: f"R$ {v:,.0f}".replace(",","X").replace(".",",").replace("X",".")
                    )
                    fig2 = px.bar(
                        df_cat, x="valor", y="categoria", orientation="h",
                        color="valor",
                        color_continuous_scale=["#d8f3dc","#52b788","#1b4332"],
                        text="valor_fmt",
                        labels={"valor":"R$","categoria":""},
                    )
                    fig2.update_traces(marker_line_width=0, textposition="outside", textfont_size=11)
                    fig2.update_layout(showlegend
