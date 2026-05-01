import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date
from utilitarios.database import get_stats, listar_produtos, get_movimentacoes_chart

# ── helpers ──────────────────────────────────────────────────
def _fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def _kpi_card(col, emoji_label: str, valor, cor: str, bg: str, border: str,
              prefixo="", sufixo=""):
    with col:
        st.markdown(
            f"""<div style='background:{bg};border:1.5px solid {border};
                border-radius:14px;padding:16px 10px;text-align:center;
                box-shadow:0 2px 12px rgba(0,0,0,.06);'>
              <div style='font-size:1.75rem;font-weight:800;color:{cor};
                          line-height:1.1;'>{prefixo}{valor}{sufixo}</div>
              <div style='font-size:0.74rem;color:#555;margin-top:5px;
                          font-weight:500;'>{emoji_label}</div>
            </div>""",
            unsafe_allow_html=True,
        )

# ── página ────────────────────────────────────────────────────
def show_dashboard():
    nome = st.session_state.get("nome_completo","Usuário").split()[0]
    hoje = date.today().strftime("%d/%m/%Y")

    # Header — único bloco HTML, sem divs soltos
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

    # Busca stats — todas as chaves sempre presentes
    s = get_stats()

    # ── KPIs — Estoque ─────────────────────────────────────
    st.markdown("#### 📦 Situação do Estoque")
    c1,c2,c3,c4,c5 = st.columns(5)
    _kpi_card(c1,"📦 Total Itens",   s["total"],    "#0f2318","#e8f5e9","#c8e6c9")
    _kpi_card(c2,"🚨 Vencidos",      s["vencidos"], "#b71c1c","#fde8e8","#ffcdd2")
    _kpi_card(c3,"⚠️ Críticos ≤7d",  s["criticos"], "#e65100","#fff3cd","#ffe0b2")
    _kpi_card(c4,"🕐 Atenção ≤30d",  s["atencao"],  "#f57f17","#fffde7","#fff9c4")
    _kpi_card(c5,"✅ OK",             s["ok"],       "#1b5e20","#e8f5e9","#c8e6c9")

    st.markdown("")   # espaço seguro sem div HTML

    # ── KPIs — Financeiro ──────────────────────────────────
    st.markdown("#### 💰 Visão Financeira")
    f1,f2,f3 = st.columns(3)
    _kpi_card(f1,"💵 Valor em Estoque",   _fmt_brl(s["total_estoque"]),
              "#1a237e","#e8eaf6","#c5cae9")
    _kpi_card(f2,"📉 Gasto Médio/Mês",    _fmt_brl(s["gasto_mensal"]),
              "#4a148c","#f3e5f5","#e1bee7")
    _kpi_card(f3,"🔴 Abaixo do Mínimo",   s["abaixo_minimo"],
              "#b71c1c","#fde8e8","#ffcdd2")

    st.markdown("")

    # ── Gráficos ───────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 🍩 Status dos Produtos")
        labels = ["OK","Atenção (≤30d)","Crítico (≤7d)","Vencido"]
        values = [s["ok"], s["atencao"], s["criticos"], s["vencidos"]]
        cores  = ["#2d6a4f","#f0a500","#e67e22","#e74c3c"]
        fig = go.Figure(go.Pie(
            labels=labels, values=values, marker_colors=cores,
            hole=0.52, textinfo="label+percent", textfont_size=11,
            hovertemplate="%{label}: %{value}<extra></extra>",
        ))
        fig.update_layout(
            showlegend=False,
            margin=dict(t=10,b=10,l=10,r=10),
            height=255,
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("#### 🗂️ Valor por Categoria (R$)")
        cats = s.get("categorias", [])
        if cats:
            df_cat = pd.DataFrame(cats)
            if "valor" in df_cat.columns:
                df_cat = df_cat[df_cat["valor"] > 0].sort_values("valor", ascending=True)
                fig2 = px.bar(
                    df_cat, x="valor", y="categoria", orientation="h",
                    color="valor",
                    color_continuous_scale=["#d8f3dc","#52b788","#1b4332"],
                    labels={"valor":"R$","categoria":""},
                )
                fig2.update_layout(
                    showlegend=False, coloraxis_showscale=False,
                    margin=dict(t=10,b=10,l=10,r=10), height=255,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                )
                fig2.update_traces(marker_line_width=0)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Cadastre preços de custo para ver o valor por categoria.")
        else:
            st.info("Sem dados de categoria.")

    # ── Produtos críticos ──────────────────────────────────
    st.markdown("#### 🔔 Itens que precisam de atenção")
    todos    = listar_produtos()
    proximos = sorted(
        [p for p in todos if p["status"] in ("critico","atencao","vencido")],
        key=lambda x: x["dias_para_vencer"],
    )[:10]

    if proximos:
        cols = st.columns(2)
        for i, p in enumerate(proximos):
            if p["status"] == "vencido":
                cor="#e74c3c"; bg="#fde8e8"; emoji="🚨"; txt="VENCIDO"
            elif p["status"] == "critico":
                cor="#e67e22"; bg="#fff3cd"; emoji="⚠️"; txt=f"{p['dias_para_vencer']}d"
            else:
                cor="#f0a500"; bg="#fffde7"; emoji="🕐"; txt=f"{p['dias_para_vencer']}d"

            preco_txt = (_fmt_brl(p["preco_custo"])
                         if p.get("preco_custo") else "")
            loc_txt   = f" · 📍 {p['localizacao']}" if p.get("localizacao") else ""

            with cols[i % 2]:
                st.markdown(
                    f"""<div style='display:flex;align-items:center;
                        justify-content:space-between;padding:10px 14px;
                        background:{bg};border-left:4px solid {cor};
                        border-radius:0 10px 10px 0;margin-bottom:8px;'>
                      <div>
                        <div style='font-weight:600;font-size:0.88rem;color:#1a1a1a;'>
                          {emoji} {p['nome']}
                        </div>
                        <div style='color:#777;font-size:0.76rem;margin-top:2px;'>
                          {p['categoria']} · {p['quantidade']} {p['unidade']}
                          {" · "+preco_txt if preco_txt else ""}{loc_txt}
                        </div>
                      </div>
                      <span style='background:{cor};color:white;padding:3px 10px;
                                   border-radius:20px;font-size:0.76rem;font-weight:700;
                                   white-space:nowrap;margin-left:10px;'>{txt}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )
    else:
        st.success("🎉 Tudo sob controle! Nenhum produto crítico no momento.")

    # ── Movimentações ──────────────────────────────────────
    st.markdown("#### 📈 Movimentações — últimos 30 dias")
    mov = get_movimentacoes_chart(30)
    if mov:
        df_mov = pd.DataFrame(mov)
        fig3 = px.bar(
            df_mov, x="dia", y="total", color="tipo",
            color_discrete_map={"entrada":"#2d6a4f","saida":"#e74c3c"},
            barmode="group",
            labels={"dia":"Data","total":"Quantidade","tipo":"Tipo"},
        )
        fig3.update_layout(
            margin=dict(t=10,b=10,l=0,r=0), height=220,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.12, x=0),
        )
        fig3.update_traces(marker_line_width=0)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Sem movimentações ainda. Registre entradas e saídas na tela de Produtos.")
