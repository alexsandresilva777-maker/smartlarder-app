# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, date
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

def _buscar_dados_supabase(user_id: int, empresa_id: int):
    """Puxa dados reais do Supabase aplicando os filtros corretos de escopo e calculando status dinamicamente."""
    stats = {
        "total": 0, "vencidos": 0, "criticos": 0, "atencao": 0, "ok": 0,
        "total_estoque": 0.0, "gasto_mensal": 0.0, "abaixo_minimo": 0,
        "capital_em_risco": 0.0, "categorias": []
    }
    produtos = []
    movimentacoes = []
    
    try:
        supabase = st.session_state.get("db")
        if supabase is None:
            return stats, produtos, movimentacoes
        
        # 1. Busca produtos filtrando estritamente pela empresa do usuário conectado
        res_prod = supabase.table("produtos").select("*").eq("empresa_id", empresa_id).execute()
        
        if res_prod.data:
            hoje = datetime.now(_TZ).date()
            cat_dict = {}
            
            for p in res_prod.data:
                qtd = p.get("quantidade", 0) or 0
                minimo = p.get("quantidade_minima", 0) or 0
                custo = p.get("preco_custo", 0.0) or 0.0
                valor_item = qtd * custo
                
                # --- Cálculo Dinâmico de Validade ---
                status = "ok"
                dias_para_vencer = 999
                val_raw = p.get("data_validade")
                
                if val_raw:
                    try:
                        # Trata formatos de data vindo do banco (YYYY-MM-DD)
                        if isinstance(val_raw, str):
                            dt_validade = datetime.strptime(val_raw[:10], "%Y-%m-%d").date()
                        else:
                            dt_validade = val_raw
                        
                        dias_para_vencer = (dt_validade - hoje).days
                        
                        if dias_para_vencer < 0:
                            status = "vencido"
                        elif dias_para_vencer <= 7:
                            status = "critico"
                        elif dias_para_vencer <= 30:
                            status = "atencao"
                    except Exception:
                        status = "ok"

                # Injeta os calculos de volta no dicionário do produto para uso posterior
                p["status"] = status
                p["dias_para_vencer"] = dias_para_vencer
                produtos.append(p)

                # Incrementa contadores de status com fallback seguro
                if status == "vencido":
                    stats["vencidos"] += 1
                elif status == "critico":
                    stats["criticos"] += 1
                elif status == "atencao":
                    stats["atencao"] += 1
                else:
                    stats["ok"] += 1
                    
                if qtd < minimo:
                    stats["abaixo_minimo"] += 1
                    
                stats["total_estoque"] += valor_item
                
                if status in ("vencido", "critico", "atencao"):
                    stats["capital_em_risco"] += valor_item
                
                cat_nome = p.get("categoria", "Outros") or "Outros"
                cat_dict[cat_nome] = cat_dict.get(cat_nome, 0.0) + valor_item

            stats["total"] = len(produtos)
            stats["categorias"] = [{"categoria": k, "valor": v} for k, v in cat_dict.items()]

        # 2. Busca movimentações dos últimos 30 dias com segurança nas colunas
        res_mov = supabase.table("movimentacoes").select("*").eq("empresa_id", empresa_id).execute()
        if res_mov.data:
            df_mov_raw = pd.DataFrame(res_mov.data)
            if not df_mov_raw.empty and "created_at" in df_mov_raw.columns:
                df_mov_raw["created_at"] = pd.to_datetime(df_mov_raw["created_at"])
                df_mov_raw["dia"] = df_mov_raw["created_at"].dt.strftime("%d/%m")
                
                # Garante os nomes corretos mapeados no dataframe
                col_tipo = "tipo" if "tipo" in df_mov_raw.columns else df_mov_raw.columns[1]
                col_qtd = "quantidade" if "quantidade" in df_mov_raw.columns else df_mov_raw.columns[2]
                
                df_grouped = df_mov_raw.groupby(["dia", col_tipo])[col_qtd].sum().reset_index()
                df_grouped.columns = ["dia", "tipo", "total"]
                movimentacoes = df_grouped.to_dict(orient="records")

    except Exception as e:
        st.error(f"Erro ao processar dados do Dashboard: {e}")
        
    return stats, produtos, movimentacoes

def show_dashboard():
    user_id = st.session_state.get("user_id", 1)
    empresa_id = st.session_state.get("empresa_id", 1)
    nome = st.session_state.get("nome_completo", "Usuário").split()[0]
    hoje = datetime.now(_TZ).strftime("%d/%m/%Y")

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

    # Processamento blindado passando user e empresa
    s, todos, mov = _buscar_dados_supabase(user_id, empresa_id)

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
        
        if sum(values) > 0:
            fig = go.Figure(go.Pie(
                labels=labels, values=values, marker_colors=cores,
                hole=0.52, textinfo="label+percent", textfont_size=11,
                hovertemplate="%{label}: %{value}<extra></extra>",
            ))
            fig.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=10),
                              height=255, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
