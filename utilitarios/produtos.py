import streamlit as st
from datetime import datetime, date
from utilitarios.database import (listar_produtos, excluir_produto,
                             atualizar_produto, registrar_movimentacao)

CATEGORIAS = ["Alimentos","Bebidas","Limpeza","Higiene","Medicamentos","Outros"]
UNIDADES   = ["un","kg","g","L","ml","cx","fardo","pct","dz"]

_STATUS = {
    "vencido": ("🚨","#e74c3c","#fde8e8","Vencido"),
    "critico": ("⚠️","#e67e22","#fff3cd","≤7 dias"),
    "atencao": ("🕐","#f0a500","#fffde7","≤30 dias"),
    "ok":      ("✅","#2d6a4f","#e8f5e9","OK"),
}

def _fmt_brl(v):
    return f"R$ {v:.2f}".replace(".",",")

def show_produtos():
    st.markdown("## 📋 Produtos em Estoque")

    with st.expander("🔍 Filtros", expanded=True):
        f1, f2, f3 = st.columns(3)
        with f1:
            fn = st.text_input("Buscar por nome ou código",
                               placeholder="Ex: Arroz / 7891...")
        with f2:
            fc = st.selectbox("Categoria", ["Todas"] + CATEGORIAS)
        with f3:
            fs = st.selectbox("Status",
                              ["Todos","Vencido","Crítico (≤7d)","Atenção (≤30d)","OK"])

    produtos = listar_produtos(fn, fc, fs)

    if not produtos:
        st.info("Nenhum produto encontrado com os filtros aplicados.")
        return

    valor_total = sum((p.get("preco_custo") or 0) * p["quantidade"] for p in produtos)
    st.markdown(
        f"**{len(produtos)} produto(s)** · "
        f"Valor filtrado: **{_fmt_brl(valor_total)}**"
    )

    for p in produtos:
        emoji, cor, bg, label = _STATUS.get(p["status"], ("","#333","#fff",""))
        preco_txt  = _fmt_brl(p["preco_custo"]) if p.get("preco_custo") else "—"
        abaixo_min = (
            (p.get("estoque_minimo") or 0) > 0
            and p["quantidade"] < (p.get("estoque_minimo") or 0)
        )

        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 1.2, 1.4, 1.6, 2.2])

            with c1:
                min_warn = " 🔴" if abaixo_min else ""
                st.markdown(
                    f"<div style='padding:2px 0;'>"
                    f"<span style='font-weight:600;font-size:0.92rem;'>{p['nome']}{min_warn}</span><br>"
                    f"<span style='color:#888;font-size:0.78rem;'>"
                    f"{p.get('codigo_barras') or '—'} · {p['categoria']}"
                    f"{' · 📍 '+p['localizacao'] if p.get('localizacao') else ''}"
                    f"</span></div>",
                    unsafe_allow_html=True,
                )
            with c2:
                min_txt = f"/{p.get('estoque_minimo',0):.0f}" if p.get("estoque_minimo") else ""
                st.markdown(f"**{p['quantidade']:.1f}**{min_txt} {p['unidade']}")
            with c3:
                st.markdown(f"📅 `{p['validade']}`")
            with c4:
                st.markdown(
                    f"<span style='background:{cor};color:white;padding:3px 11px;"
                    f"border-radius:20px;font-size:0.77rem;font-weight:700;'>"
                    f"{emoji} {label}</span>"
                    f"&nbsp;<span style='font-size:0.77rem;color:#666;'>{preco_txt}</span>",
                    unsafe_allow_html=True,
                )
            with c5:
                b1, b2, b3 = st.columns(3)
                with b1:
                    if st.button("✏️", key=f"e_{p['id']}", help="Editar"):
                        st.session_state[f"edit_{p['id']}"] = True
                with b2:
                    if st.button("📦", key=f"m_{p['id']}", help="Movimentar"):
                        st.session_state[f"mov_{p['id']}"]  = True
                with b3:
                    if st.session_state.get("role") == "admin":
                        if st.button("🗑️", key=f"d_{p['id']}", help="Excluir"):
                            st.session_state[f"del_{p['id']}"] = True

            # Confirmação de exclusão
            if st.session_state.get(f"del_{p['id']}"):
                st.warning(f"Confirma exclusão de **{p['nome']}**?")
                y, n = st.columns(2)
                with y:
                    if st.button("✅ Confirmar", key=f"dy_{p['id']}"):
                        excluir_produto(p["id"])
                        st.session_state.pop(f"del_{p['id']}", None)
                        st.rerun()
                with n:
                    if st.button("❌ Cancelar", key=f"dn_{p['id']}"):
                        st.session_state.pop(f"del_{p['id']}", None)
                        st.rerun()

            if st.session_state.get(f"edit_{p['id']}"):
                with st.expander(f"✏️ Editando: {p['nome']}", expanded=True):
                    _form_edicao(p)

            if st.session_state.get(f"mov_{p['id']}"):
                with st.expander(f"📦 Movimentar: {p['nome']}", expanded=True):
                    _form_mov(p)

        st.markdown(
            "<hr style='margin:5px 0;border-color:#eef2ee;'>",
            unsafe_allow_html=True,
        )

def _form_edicao(p):
    with st.form(f"fe_{p['id']}"):
        c1, c2 = st.columns(2)
        with c1:
            nome       = st.text_input("Nome",     value=p["nome"])
            codigo     = st.text_input("Código de Barras",
                                       value=p.get("codigo_barras") or "")
            categoria  = st.selectbox(
                "Categoria", CATEGORIAS,
                index=CATEGORIAS.index(p["categoria"]) if p["categoria"] in CATEGORIAS else 0,
            )
            lote       = st.text_input("Lote", value=p.get("lote") or "")
        with c2:
            quantidade = st.number_input("Quantidade",
                                         value=float(p["quantidade"]),
                                         min_value=0.0, step=0.1)
            unidade    = st.selectbox(
                "Unidade", UNIDADES,
                index=UNIDADES.index(p["unidade"]) if p["unidade"] in UNIDADES else 0,
            )
            try:
                val_date = datetime.strptime(p["validade"], "%Y-%m-%d").date()
            except Exception:
                val_date = date.today()
            validade   = st.date_input("Validade", value=val_date)
            preco      = st.number_input("Preço Custo (R$)",
                                         value=float(p.get("preco_custo") or 0),
                                         min_value=0.0, step=0.01, format="%.2f")

        c3, c4 = st.columns(2)
        with c3:
            estoque_min = st.number_input("Estoque Mínimo",
                                          value=float(p.get("estoque_minimo") or 0),
                                          min_value=0.0, step=1.0)
            fornecedor  = st.text_input("Fornecedor", value=p.get("fornecedor") or "")
        with c4:
            localizacao = st.text_input("Localização", value=p.get("localizacao") or "")
            obs         = st.text_input("Observações", value=p.get("observacoes") or "")

        s1, s2 = st.columns(2)
        with s1:
            salvar   = st.form_submit_button("💾 Salvar", type="primary")
        with s2:
            cancelar = st.form_submit_button("❌ Cancelar")

    if salvar:
        atualizar_produto(p["id"], dict(
            codigo_barras=codigo, nome=nome, categoria=categoria,
            quantidade=quantidade, unidade=unidade, validade=str(validade),
            lote=lote, fornecedor=fornecedor, localizacao=localizacao,
            preco_custo=preco, estoque_minimo=estoque_min, observacoes=obs,
        ))
        st.session_state.pop(f"edit_{p['id']}", None)
        st.success("✅ Produto atualizado!")
        st.rerun()
    if cancelar:
        st.session_state.pop(f"edit_{p['id']}", None)
        st.rerun()

def _form_mov(p):
    with st.form(f"fm_{p['id']}"):
        st.info(
            f"Estoque atual: **{p['quantidade']} {p['unidade']}** "
            f"| Mínimo: **{p.get('estoque_minimo',0) or 0} {p['unidade']}**"
        )
        tipo = st.radio(
            "Tipo", ["entrada","saida"], horizontal=True,
            format_func=lambda x: "📥 Entrada" if x=="entrada" else "📤 Saída",
        )
        qtd  = st.number_input("Quantidade", min_value=0.01, step=0.1, value=1.0)
        obs  = st.text_input("Observação",
                             placeholder="Ex: Recebimento NF 1234 / Venda balcão")
        s1, s2 = st.columns(2)
        with s1:
            salvar   = st.form_submit_button("💾 Registrar", type="primary")
        with s2:
            cancelar = st.form_submit_button("❌ Cancelar")

    if salvar:
        if tipo == "saida" and qtd > p["quantidade"]:
            st.error("Quantidade de saída maior que o estoque disponível!")
        else:
            registrar_movimentacao(
                p["id"], tipo, qtd, obs,
                st.session_state.get("username",""),
            )
            st.session_state.pop(f"mov_{p['id']}", None)
            st.success(f"✅ {'Entrada' if tipo=='entrada' else 'Saída'} registrada!")
            st.rerun()
    if cancelar:
        st.session_state.pop(f"mov_{p['id']}", None)
        st.rerun()
