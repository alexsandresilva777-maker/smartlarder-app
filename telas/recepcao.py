# -*- coding: utf-8 -*-
"""
Modo Recepção de Carga — bipagem sequencial com buffer batch_list.
O operador bipa vários produtos, preenche validade/qtd de cada um,
e faz um único commit no final.
"""
import streamlit as st
from datetime import date
from utils.database import inserir_produto, buscar_por_barcode, get_ean_cache, salvar_ean_cache
from utils.barcode_lookup import buscar_por_ean

CATEGORIAS = ["Alimentos","Bebidas","Limpeza","Higiene","Medicamentos","Outros"]
UNIDADES   = ["un","kg","g","L","ml","cx","fardo","pct","dz"]


def _is_ean(codigo: str) -> bool:
    c = str(codigo).strip()
    return c.isdigit() and len(c) in (8, 12, 13)


def show_recepcao():
    user_id = st.session_state.get("user_id", 1)

    st.markdown("## 📥 Recepção de Carga")
    st.info(
        "**Modo Bipagem em Lote** — escaneie vários produtos em sequência. "
        "Os itens ficam no buffer até você confirmar o **Commit Final**."
    )

    # Garante que o buffer existe
    if "batch_list" not in st.session_state:
        st.session_state.batch_list = []

    # ── Painel de bipagem ──────────────────────────────────────────────────────
    st.markdown("### 1️⃣ Escanear / Digitar Código")

    col_ean, col_btn = st.columns([3, 1])
    with col_ean:
        codigo = st.text_input("Código EAN ou Manual",
                               placeholder="Bipe ou digite o código",
                               key="recepcao_ean")
    with col_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        buscar = st.button("🔍 Buscar", type="primary", use_container_width=True)

    # Estado do item sendo adicionado
    if "recepcao_item" not in st.session_state:
        st.session_state.recepcao_item = None

    if buscar and codigo.strip():
        cod = codigo.strip()
        # 1. Tenta cache local primeiro (evita chamada de API repetida)
        cached = get_ean_cache(cod)
        if cached:
            st.session_state.recepcao_item = {**cached, "codigo_barras": cod, "fonte": cached.get("fonte","Cache")}
            st.success(f"✅ **{cached['nome']}** (do cache local)")
        elif _is_ean(cod):
            with st.spinner("🌐 Consultando base global..."):
                resultado = buscar_por_ean(cod)
            if resultado:
                salvar_ean_cache(cod, resultado)
                st.session_state.recepcao_item = {**resultado, "codigo_barras": cod}
                st.success(f"✅ **{resultado['nome']}** encontrado!")
            else:
                st.session_state.recepcao_item = {"codigo_barras": cod, "nome": "", "categoria": "Alimentos", "fornecedor": ""}
                st.warning("Produto não encontrado. Preencha manualmente.")
        else:
            st.session_state.recepcao_item = {"codigo_barras": cod, "nome": "", "categoria": "Alimentos", "fornecedor": ""}
            st.info(f"Código manual **{cod}** — preencha os dados abaixo.")

    # ── Formulário do item ─────────────────────────────────────────────────────
    item = st.session_state.recepcao_item
    if item is not None:
        st.markdown("### 2️⃣ Confirmar Dados do Item")
        modo_rapido = bool(item.get("nome"))

        with st.form("form_recepcao_item", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nome = st.text_input("Nome *", value=item.get("nome",""),
                                     disabled=modo_rapido)
                cat_val = item.get("categoria","Alimentos")
                cat_idx = CATEGORIAS.index(cat_val) if cat_val in CATEGORIAS else 0
                categoria = st.selectbox("Categoria", CATEGORIAS, index=cat_idx,
                                         disabled=modo_rapido)
                fornecedor = st.text_input("Fornecedor", value=item.get("fornecedor",""),
                                           disabled=modo_rapido)
            with c2:
                validade   = st.date_input("Validade *", value=date.today(),
                                           min_value=date(2000,1,1))
                quantidade = st.number_input("Quantidade *", min_value=0.01,
                                             step=1.0, value=1.0, format="%.2f")
                unidade    = st.selectbox("Unidade", UNIDADES)
                preco      = st.number_input("Preço Custo (R$)",
                                             min_value=0.0, step=0.01, format="%.2f")

            add = st.form_submit_button("➕ Adicionar ao Buffer", type="primary",
                                        use_container_width=True)

        if add:
            if not nome.strip():
                st.error("Nome obrigatório.")
            else:
                st.session_state.batch_list.append({
                    "codigo_barras":  item.get("codigo_barras",""),
                    "nome":           nome.strip(),
                    "categoria":      categoria,
                    "fornecedor":     fornecedor.strip() or None,
                    "quantidade":     quantidade,
                    "unidade":        unidade,
                    "validade":       str(validade),
                    "preco_custo":    preco,
                    "estoque_minimo": 0.0,
                    "lote":           None,
                    "localizacao":    None,
                    "observacoes":    None,
                })
                st.session_state.recepcao_item = None
                st.success(f"✅ **{nome.strip()}** adicionado ao buffer! "
                           f"({len(st.session_state.batch_list)} item(ns) no buffer)")
                st.rerun()

    # ── Buffer atual ───────────────────────────────────────────────────────────
    batch = st.session_state.batch_list
    if batch:
        st.markdown(f"### 3️⃣ Buffer de Carga — {len(batch)} item(ns)")

        for i, item in enumerate(batch):
            emoji, cor = ("🔴","#e74c3c") if (
                date.today() >= date.fromisoformat(item["validade"])
            ) else ("🟢","#2d6a4f")
            col_info, col_del = st.columns([5, 1])
            with col_info:
                st.markdown(
                    f"<div style='padding:8px 14px;background:#f8fdf9;"
                    f"border-left:3px solid {cor};border-radius:0 8px 8px 0;margin-bottom:4px;'>"
                    f"<strong>{emoji} {item['nome']}</strong> · "
                    f"{item['quantidade']} {item['unidade']} · "
                    f"Venc: <code>{item['validade']}</code> · "
                    f"{item['categoria']}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with col_del:
                if st.button("🗑️", key=f"del_batch_{i}", help="Remover do buffer"):
                    st.session_state.batch_list.pop(i)
                    st.rerun()

        st.markdown("")
        col_commit, col_limpar = st.columns(2)
        with col_commit:
            if st.button("💾 Commit Final — Salvar Todos no Estoque",
                         type="primary", use_container_width=True):
                erros = 0
                for item in batch:
                    try:
                        inserir_produto(item, user_id,
                                        st.session_state.get("username",""))
                    except Exception:
                        erros += 1
                salvos = len(batch) - erros
                st.session_state.batch_list = []
                st.session_state.recepcao_item = None
                if erros == 0:
                    st.success(f"✅ {salvos} produto(s) salvos no estoque com sucesso!")
                    st.balloons()
                else:
                    st.warning(f"⚠️ {salvos} salvos, {erros} com erro. Verifique os logs.")
                st.rerun()

        with col_limpar:
            if st.button("🗑️ Limpar Buffer", use_container_width=True):
                st.session_state.batch_list = []
                st.session_state.recepcao_item = None
                st.rerun()
    else:
        st.markdown("")
        st.info("Buffer vazio — escaneie o primeiro produto acima.")
