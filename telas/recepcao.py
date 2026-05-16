# -*- coding: utf-8 -*-
"""
Modo Recepção de Carga — bipagem sequencial com buffer batch_list.
O operador bipa vários produtos, preenche validade/qtd de cada um,
e faz um único commit no final integrado diretamente ao Supabase.
"""
import streamlit as st
from datetime import date, datetime
from utils.barcode_lookup import buscar_por_ean

CATEGORIAS = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Medicamentos", "Outros"]
UNIDADES   = ["un", "kg", "g", "L", "ml", "cx", "fardo", "pct", "dz"]


def _is_ean(codigo: str) -> bool:
    c = str(codigo).strip()
    return c.isdigit() and len(c) in (8, 12, 13)


def _get_ean_cache(codigo: str) -> dict:
    """Busca o produto no cache local em memória do Streamlit"""
    if "ean_cache" not in st.session_state:
        st.session_state["ean_cache"] = {}
    return st.session_state["ean_cache"].get(codigo)


def _salvar_ean_cache(codigo: str, dados: dict):
    """Guarda o resultado da API global no cache do Streamlit"""
    if "ean_cache" not in st.session_state:
        st.session_state["ean_cache"] = {}
    st.session_state["ean_cache"][codigo] = dados


def show_recepcao():
    supabase = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)

    st.markdown("## 📥 Recepção de Carga")
    st.info(
        "**Modo Bipagem em Lote** — escaneie vários produtos em sequência. "
        "Os itens ficam no buffer até você confirmar o **Commit Final**."
    )

    if supabase is None:
        st.error("Conexão com o banco de dados indisponível.")
        return

    # Garante que o buffer temporário de lote existe
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
        # 1. Tenta cache local em memória primeiro (evita chamadas redundantes de API)
        cached = _get_ean_cache(cod)
        if cached:
            st.session_state.recepcao_item = {**cached, "barcode": cod, "fonte": "Cache Local"}
            st.success(f"✅ **{cached['nome']}** (do cache local)")
        elif _is_ean(cod):
            with st.spinner("🌐 Consultando base global..."):
                resultado = buscar_por_ean(cod)
            if resultado:
                _salvar_ean_cache(cod, resultado)
                st.session_state.recepcao_item = {**resultado, "barcode": cod}
                st.success(f"✅ **{resultado['nome']}** encontrado!")
            else:
                st.session_state.recepcao_item = {"barcode": cod, "nome": "", "categoria": "Alimentos", "fornecedor": ""}
                st.warning("Produto não encontrado globalmente. Preencha manualmente.")
        else:
            st.session_state.recepcao_item = {"barcode": cod, "nome": "", "categoria": "Alimentos", "fornecedor": ""}
            st.info(f"Código manual **{cod}** — preencha os dados abaixo.")

    # ── Formulário do item ─────────────────────────────────────────────────────
    item = st.session_state.recepcao_item
    if item is not None:
        st.markdown("### 2️⃣ Confirmar Dados do Item")
        modo_rapido = bool(item.get("nome"))

        with st.form("form_recepcao_item", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nome = st.text_input("Nome *", value=item.get("nome", ""), disabled=modo_rapido)
                cat_val = item.get("categoria", "Alimentos")
                cat_idx = CATEGORIAS.index(cat_val) if cat_val in CATEGORIAS else 0
                categoria = st.selectbox("Categoria", CATEGORIAS, index=cat_idx, disabled=modo_rapido)
                # Fornecedor não é coluna direta da nossa tabela 'produtos', mas pode ir nas Observações se desejado.
                fornecedor = st.text_input("Fornecedor", value=item.get("fornecedor", ""), disabled=modo_rapido)
            with c2:
                validade   = st.date_input("Validade *", value=date.today(), min_value=date(2000, 1, 1))
