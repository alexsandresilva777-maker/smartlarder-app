# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import pytz

_TZ = pytz.timezone("America/Sao_Paulo")

def _fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _processar_lista_inteligente(supabase, empresa_id) -> list:
    """Calcula dinamicamente a necessidade de recompra com base em estoque_minimo e saídas"""
    try:
        # 1. Busca todos os produtos da empresa
        res_prod = supabase.table("produtos").select("*").eq("empresa_id", empresa_id).execute()
        if not res_prod.data:
            return []
            
        produtos = res_prod.data
        
        # 2. Busca saídas dos últimos 30 dias para cálculo de consumo médio
        data_limite = (datetime.now(_TZ) - timedelta(days=30)).isoformat()
        res_mov = supabase.table("movimentacoes")\
            .select("produto_id, quantidade")\
            .eq("empresa_id", empresa_id)\
            .eq("tipo", "saida")\
            .gte("created_at", data_limite)\
            .execute()
            
        movimentacoes = res_mov.data or []
        
        # Consolida consumo por produto
        consumo_map = {}
        for m in movimentacoes:
            pid = m.get("produto_id")
            qtd = float(m.get("quantidade", 0) or 0)
            consumo_map[pid] = consumo_map.get(pid, 0.0) + qtd

        lista_sugestoes = []
        hoje = datetime.now(_TZ).date()

        for p in produtos:
            pid = p["id"]
            nome = p["nome"]
            categoria = p.get("categoria", "Outros")
            unidade = p.get("unidade", "un")
            qtd_atual = float(p.get("quantidade", 0) or 0)
            qtd_minima = float(p.get("quantidade_minima", 0) or 0)
            preco_custo = float(p.get("preco_custo", 0) or 0)
            
            # Localização servirá de fallback descritivo caso queira mapear fornecedor
            localizacao = p.get("localizacao") or "Não Informado"
            
            # Cálculo do Consumo Diário (Média dos últimos 30 dias)
            total_saidas_30_dias = consumo_map.get(pid, 0.0)
            consumo_dia = total_saidas_30_dias / 30.0
            
            motivos = []
            urgencia = None
            sugerido = 0.0
            
            # Regra 1: Validade crítica ou vencida
            val_raw = p.get("data_validade")
            if val_raw:
                try:
                    if isinstance(val_raw, str):
                        val_date = datetime.strptime(val_raw[:10], "%Y-%m-%d").date()
                    else:
                        val_date = val_raw
                    dias_restantes = (val_date - hoje).days
                    if dias_restantes < 0:
                        urgencia = "alta"
                        motivos.append("Produto Vencido")
                    elif dias_restantes <= 7:
                        urgencia = "alta"
                        motivos.append(f"Validade Crítica ({dias_restantes} dias)")
                except Exception:
                    pass

            # Regra 2: Abaixo do estoque mínimo
            if qtd_minima > 0 and qtd_atual < qtd_minima:
                if not urgencia:
                    urgencia = "alta" if qtd_atual == 0 else "media"
                motivos.append("Abaixo do Mínimo")
                # Sugere repor para o mínimo + uma margem de segurança baseada no consumo
                sugerido = (qtd_minima - qtd_atual) + (consumo_dia * 7)
            
            # Regra 3: Risco de desabastecimento por consumo
            if consumo_dia > 0 and qtd_atual > 0:
                dias_duracao = qtd_atual / consumo_dia
                if dias_duracao <= 5 and "Abaixo do Mínimo" not in motivos:
                    urgencia = "alta"
                    motivos.append(f"Esgota em {int(dias_duracao)} dias")
                    sugerido = max(sugerido, consumo_dia * 15) # Sugere estoque para 15 dias

            # Se o item precisa de atenção, consolida na lista
            if urgencia and (sugerido > 0 or qtd_atual == 0):
                if sugerido <= 0:
                    sugerido = qtd_minima if qtd_minima > 0 else 1.0 # Fallback de segurança
                
                lista_sugestoes.append({
                    "id": pid,
                    "nome": nome,
                    "categoria": categoria,
                    "fornecedor": localizacao,
                    "qtd_atual": qtd_atual,
                    "estoque_min": qtd_minima,
                    "consumo_dia": consumo_dia,
                    "sugerido": round(sugerido, 1),
                    "preco_custo": preco_custo,
                    "urgencia": urgencia,
                    "motivos": motivos if motivos else ["Reposição Preventiva"],
                    "unidade": unidade
                })

        # Ordena por urgência (alta primeiro)
        lista_sugestoes.sort(key=lambda x: 0 if x["urgencia"] == "alta" else 1)
        return lista_sugestoes

    except Exception as e:
        st.error(f"Erro ao computar lista de compras: {e}")
        return []

def show_lista_compras():
    supabase = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    
    st.markdown("## 🛒 Lista de Compras Inteligente")

    st.info(
        "🧠 **Como funciona?** O sistema analisa o **estoque atual vs mínimo configurado** "
        "e o **consumo médio dos últimos 30 dias** registrados nas movimentações para estimar demandas. "
        "Configure o Estoque Mínimo no cadastro de produtos para obter sugestões perfeitamente refinadas."
    )

    if supabase is None:
        st.error("Conexão com o banco de dados indisponível.")
        return

    with st.spinner("Analisando estoque e histórico de consumo dinâmico..."):
        lista = _processar_lista_inteligente(supabase, empresa_id)

    if not lista:
        st.success(
            "🎉 **Estoque saudável!** Nenhum item precisa ser recomprado agora.\n\n"
            "**Dicas:** Configure a Quantidade Mínima de cada produto (Estoque → ✏️ Editar) "
            "e lembre-se de registrar as saídas regularmente para alimentar a inteligência de consumo."
        )
        return

    # ── Resumo das Urgências ────────────────────────────────────────────
    alta  = [i for i in lista if i["urgencia"] == "alta"]
    media = [i for i in lista if i["urgencia"] == "media"]
    valor_total = sum(i["sugerido"] * i["preco_custo"] for i in lista if i["preco_custo"])

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
        "Referência/Local": i["fornecedor"],
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

    # ── Renderização dos Cards na Tela ─────────────────────────────────
    grupos = [
        ("alta",  "🚨 Urgência Alta — Comprar Imediatamente",  "#e74c3c", "#fff8f8"),
        ("media", "⚠️ Urgência Média — Comprar em Breve",       "#e67e22", "#fffaf0"),
    ]

    for urgencia, titulo, cor, bg in grupos:
        grupo = [i for i in lista if i["urgencia"] == urgencia]
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
            consumo_txt  = f"{item['consumo_dia']:.2f}/dia" if item["consumo_dia"] > 0 else "Sem histórico"

            motivos_html = "".join(
                f"<span style='background:#eec5c5 if urgencia=='alta' else #fce8db;color:#333;padding:2px 8px;"
                f"border-radius:20px;font-size:0.74rem;margin-right:4px;font-weight:500;'>{m}</span>"
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
                        {item['categoria']} · Obs/Ref: {item['fornecedor']} · Giro: {consumo_txt}
                      </div>
                      <div style='margin-top:6px;'>{motivos_html}</div>
                    </div>
                    <div style='text-align:right;white-space:nowrap;'>
                      <div style='font-size:0.81rem;color:#555;'>
                        Atual: <strong>{item['qtd_atual']} {item['unidade']}</strong>
                      </div>
                      <div style='font-size:0.81rem;color:#555;'>
                        Mínimo: <strong>{item['estoque_min']} {item['unidade']}</strong>
                      </div>
                      <div style='font-size:0.85rem;color:#1a237e;font-weight:700;margin-top:2px;'>
                        Sugerido: <span style='color:#2d6a4f;'>+{item['sugerido']} {item['unidade']}</span>
                      </div>
                      <div style='font-size:0.82rem;color:#1a237e;font-weight:600;margin-bottom:4px;'>
                        Custo: {custo_txt}
                      </div>
                    </div>
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("---")
