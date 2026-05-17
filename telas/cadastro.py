# -*- coding: utf-8 -*-
import streamlit as st
import requests
from datetime import datetime
import pytz

_TZ = pytz.timezone("America/Sao_Paulo")

CATEGORIAS = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Medicamentos", "Outros"]
UNIDADES = ["un", "kg", "g", "L", "ml", "cx", "fardo", "pct", "dz"]

def _buscar_produto_apis(barcode: str) -> dict:
    """
    Busca inteligente em tempo real usando APIs públicas.
    Zero dados fixos no código.
    """
    if not barcode or len(barcode) < 8:
        return {}

    # 1ª Tentativa: Open Food Facts
    try:
        url_off = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
        res = requests.get(url_off, timeout=4)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == 1:
                p = data.get("product", {})
                return {
                    "nome": p.get("product_name", ""),
                    "categoria": "Alimentos",
                    "unidade": "un"
                }
    except Exception:
        pass

    # 2ª Tentativa: Fallback de API Pública
    try:
        url_br = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
        res = requests.get(url_br, timeout=4)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == 1:
                p = data.get("product", {})
                return {
                    "nome": p.get("product_name", ""),
                    "categoria": "Alimentos",
                    "unidade": "un"
                }
    except Exception:
        pass

    return {}

def show_cadastro():
    st.markdown("## ➕ Cadastrar Novo Produto")

    supabase = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)

    if not supabase:
        st.error("❌ Conexão com o banco de dados não encontrada no sistema.")
        return

    if "cadastro_nome" not in st.session_state: 
        st.session_state["cadastro_nome"] = ""
    if "cadastro_cat" not in st.session_state: 
        st.session_state["cadastro_cat"] = "Alimentos"

    # Bloco de Busca por Código de Barras
    with st.container():
        c_busca, c_btn = st.columns([3, 1])
        with c_busca:
            barcode_input = st.text_input("Código de Barras (Digite ou use o Leitor)", key="barcode_scan")
        with c_btn:
            st.markdown("<div style='padding-top:24px;'></div>", unsafe_allow_html=True)
            if st.button("🔍 Buscar Produto", use_container_width=True):
                if barcode_input.strip():
                    with st.spinner("Consultando bases de dados inteligentes..."):
                        info = _buscar_produto_apis(barcode_input.strip())
                        if info:
                            st.session_state["cadastro_nome"] = info.get("nome", "")
                            st.session_state["cadastro_cat"] = info.get("categoria", "Alimentos")
                            st.success("✅ Dados localizados com sucesso!")
                        else:
                            st.warning("⚠️ Produto não encontrado. Digite os dados manualmente abaixo.")
                else:
                    st.error("Informe um código de barras válido.")

    st.markdown("---")

    # Formulário Principal de Cadastro
    with st.form("form_cadastro_produtos", clear_on_submit=True):
        st.markdown("### Detalhes do Produto")
        
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Produto *", value=st.session_state["cadastro_nome"])
            
            idx_cat = 0
            if st.session_state["cadastro_cat"] in CATEGORIAS:
                idx_cat = CATEGORIAS.index(st.session_state["cadastro_cat"])
            categoria = st.selectbox("Categoria *", CATEGORIAS, index=idx_cat)
            
            localizacao = st.text_input("Localização / Armário", placeholder="Ex: Despensa A, Prateleira 2")

        with col2:
            quantidade = st.number_input("Quantidade Inicial *", min_value=0.0, step=1.0, value=0.0)
            unidade = st.selectbox("Unidade de Medida *", UNIDADES, index=0)
            quantidade_minima = st.number_input("Estoque Mínimo Desejado", min_value=0.0, step=1.0, value=0.0)

        st.markdown("### Informações de Custo e Validade")
        col3, col4 = st.columns(2)
        with col3:
            preco_custo = st.number_input("Preço de Custo por Unidade (R$)", min_value=0.0, step=0.01, format="%.2f")
        with col4:
            data_validade = st.date_input("Data de Validade", value=datetime.now(_TZ).date())

        st.markdown("<br>", unsafe_allow_html=True)
        btn_salvar = st.form_submit_button("💾 Finalizar Cadastro do Produto", type="primary", use_container_width=True)

    if btn_salvar:
        if not nome.strip():
            st.error("❌ O campo 'Nome do Produto' é obrigatório.")
            return

        payload = {
            "empresa_id": int(empresa_id),
            "barcode": barcode_input.strip() if barcode_input.strip() else None,
            "nome": nome.strip(),
            "categoria": categoria,
            "quantidade": float(quantidade),
            "unidade": unidade,
            "quantidade_minima": float(quantidade_minima),
            "preco_custo": float(preco_custo) if preco_custo > 0 else 0.0,
            "data_validade": str(data_validade),
            "localizacao": localizacao.strip() if localizacao.strip() else None
        }

        try:
            with st.spinner("Gravando dados no SmartLarder Pro..."):
                supabase.table("produtos").insert(payload).execute()
                st.success(f"🎉 Produto '{nome}' cadastrado com sucesso!")
                
                st.session_state["cadastro_nome"] = ""
                st.session_state["cadastro_cat"] = "Alimentos"
                st.rerun()
        except Exception as error:
            st.error(f"❌ Erro de persistência no Supabase. Detalhes técnicos: {error}")
