import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import imports  # noqa
import streamlit as st
import pandas as pd
from datetime import date
from utils.database import gerar_lista_compras

def _fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def show_lista_compras():
    st.markdown("## 🛒 Lista de Compras Inteligente")

    st.info(
        "🧠 **Como funciona?** O sistema analisa o **estoque atual vs mínimo configurado** "
        "e o **consumo médio dos últimos 30 dias** para estimar quando cada item acabará. "
        "Configure o Estoque Mínimo em cada produto para obter sugestões mais precisas."
    )

    with st.spinner("Analisando estoque e consumo..."):
        lista = gerar_lista_compras()

    if not lista:
        st.success(
            "🎉 **Estoque saudável!** Nenhum item precisa ser recomprado agora.\n\n"
            "**Dicas:** Configure o Estoque Mínimo de cada produto (Produtos → ✏️ Editar) "
            "e registre saídas regularmente para alimentar o cálculo de consumo médio."
        )
        return

    # ── Resumo ────────────────────────────────────────────
    alta  = [i for i in lista if i["urgencia"]=="alta"]
    media = [i for i in lista if i["urgencia"]=="media"]
    valor_total = sum(
        i["sugerido"] * i["preco_custo"]
        for i in lista if i["preco_custo"]
    )

    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown(
            f"""<div style='background:#fde8e8;border:1.5px solid #ffcdd2;
                border-radius:12px;padding:14px;text-align:center;'>
              <div style='font-size:2rem;font-weight:800;color:#c62828;'>{len(alta)}</div>
              <div style='font-size:0.79rem;color:#7f0000;font-weight:600;'>🚨 Urgência Alta</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with r2:
        st.markdown(
            f"""<div style='background:#fff3cd;border:1.5px solid #ffe082;
                border-radius:12px;padding:14px;text-align:center;'>
              <div style='font-size:2rem;font-weight:800;color:#e65100;'>{len(media)}</div>
              <div style='font-size:0.79rem;color:#bf360c;font-weight:600;'>⚠️ Urgência Média</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with r3:
        st.markdown(
            f"""<div style='background:#e8eaf6;border:1.5px solid #c5cae9;
                border-radius:12px;padding:14px;text-align:center;'>
              <div style='font-size:1.5rem;font-weight:800;color:#1a237e;'>{_fmt_brl(valor_total)}</div>
              <div style='font-size:0.79rem;color:#283593;font-weight:600;'>💰 Custo Estimado</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ── Exportar CSV ───────────────────────────────────────
    df_exp = pd.DataFrame([{
        "Produto":       i["nome"],
        "Categoria":     i["categoria"],
        "Fornecedor":    i["fornecedor"],
        "Estoque Atual": f"{i['qtd_atual']} {i['unidade']}",
        "Est. Mínimo":   f"{i['estoque_min']} {i['unidade']}",
        "Consumo/Dia":   f"{i['consumo_dia']:.2f}",
        "Qtd Sugerida":  f"{i['sugerido']} {i['unidade']}",
        "Custo Unit.":   _fmt_brl(i["preco_custo"]),
        "Custo Total":   _fmt_brl(i["sugerido"] * i["preco_custo"]),
        "Motivo":        " | ".join(i["motivos"]),
        "Urgência":      i["urgencia"].upper(),
    } for i in lista])

    csv = df_exp.to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(
        "📥 Exportar Lista de Compras (CSV)",
        data=csv,
        file_name=f"lista_compras_{date.today()}.csv",
        mime="text/csv",
    )

    st.markdown("---")

    # ── Itens por urgência ─────────────────────────────────
    grupos = [
        ("alta",  "🚨 Urgência Alta — Comprar Imediatamente",  "#e74c3c","#fff8f8"),
        ("media", "⚠️ Urgência Média — Comprar em Breve",       "#e67e22","#fffaf0"),
    ]

    for urgencia, titulo, cor, bg in grupos:
        grupo = [i for i in lista if i["urgencia"]==urgencia]
        if not grupo:
            continue

        st.markdown(
            f"<div style='font-size:0.95rem;font-weight:700;color:#1a1a1a;"
            f"border-left:4px solid {cor};padding-left:12px;"
            f"margin:18px 0 10px;'>{titulo}</div>",
            unsafe_allow_html=True,
        )

        for item in grupo:
            custo_total  = item["sugerido"] * item["preco_custo"]
            custo_txt    = _fmt_brl(custo_total) if item["preco_custo"] else "—"
            consumo_txt  = (f"{item['consumo_dia']:.2f}/dia"
                            if item["consumo_dia"] > 0 else "sem histórico")

            motivos_html = "".join(
                f"<span style='background:#f0f0f0;color:#555;padding:2px 8px;"
                f"border-radius:20px;font-size:0.74rem;margin-right:4px;'>{m}</span>"
                for m in item["motivos"]
            )

            st.markdown(
                f"""<div style='background:{bg};border:1px solid {cor}33;
                    border-left:4px solid {cor};border-radius:0 12px 12px 0;
                    padding:12px 16px;margin-bottom:8px;'>
                  <div style='display:flex;align-items:flex-start;
                              justify-content:space-between;flex-wrap:wrap;gap:8px;'>
                    <div style='flex:1;min-width:200px;'>
                      <div style='font-weight:700;font-size:0.92rem;color:#1a1a1a;'>
                        {item['nome']}
                      </div>
                      <div style='color:#666;font-size:0.78rem;margin:3px 0;'>
                        {item['categoria']} · {item['fornecedor']} · Consumo: {consumo_txt}
                      </div>
                      <div style='margin-top:4px;'>{motivos_html}</div>
                    </div>
                    <div style='text-align:right;white-space:nowrap;'>
                      <div style='font-size:0.81rem;color:#555;'>
                        Atual: <strong>{item['qtd_atual']} {item['unidade']}</strong>
                      </div>
                      <div style='font-size:0.81rem;color:#555;'>
                        Sugerido: <strong>{item['sugerido']} {item['unidade']}</strong>
                      </div>
                      <div style='font-size:0.82rem;color:#1a237e;font-weight:600;'>
                        {custo_txt}
                      </div>
                      <span style='background:{cor};color:white;padding:2px 10px;
                                   border-radius:20px;font-size:0.72rem;font-weight:700;'>
                        {urgencia.upper()}
                      </span>
                    </div>
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown(
        "> 💡 **Para melhorar as sugestões:** Configure o **Estoque Mínimo** em cada produto "
        "(Produtos → ✏️ Editar) e registre as **saídas** regularmente."
    )
