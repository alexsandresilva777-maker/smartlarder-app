# -*- coding: utf-8 -*-
import streamlit as st
import requests
from datetime import datetime
import pytz

_TZ = pytz.timezone("America/Sao_Paulo")

CATEGORIAS = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Medicamentos", "Outros"]
UNIDADES = ["un", "kg", "g", "L", "ml", "cx", "fardo", "pct", "dz"]

def _buscar_produto_apis(barcode: str) -> dict:
    """Busca inteligente em tempo real usando APIs públicas."""
    if not barcode or len(barcode) < 8:
        return {}
    try:
        url_off = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
        res = requests.get(url_off, timeout=4)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == 1:
                p = data.get("product", {})
                return {
                    "nome": p.get("product_name", "").upper(),
                    "categoria": "Alimentos",
                    "unidade": "un"
                }
    except Exception:
        pass
    return {}

def show_cadastro():
    st.markdown("### 1️⃣ Escanear ou Digitar Código")

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
            barcode_input = st.text_input("Código de Barras", placeholder="789...", key="barcode_scan")
        with c_btn:
            st.markdown("<div style='padding-top:24px;'></div>", unsafe_allow_html=True)
            if st.button("🔍 Buscar", use_container_width=True):
                if barcode_input.strip():
                    with st.spinner("Consultando bases..."):
                        info = _buscar_produto_apis(barcode_input.strip())
                        if info:
                            st.session_state["cadastro_nome"] = info.get("nome", "")
                            st.session_state["cadastro_cat"] = info.get("categoria", "Alimentos")
                            st.success("✅ Código processado. Insira as informações manuais abaixo.")
                        else:
                            st.warning("⚠️ Produto não localizado nas bases automatizadas. Insira os dados manualmente.")
                else:
                    st.error("Informe um código de barras válido.")

    st.markdown("<br>### 2️⃣ Informações de Cadastro", unsafe_allow_html=True)

    # Formulário Principal de Cadastro
    with st.form("form_cadastro_produtos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Produto *", value=st.session_state["cadastro_nome"])
            
            idx_cat = 0
            if st.session_state["cadastro_cat"] in CATEGORIAS:
                idx_cat = CATEGORIAS.index(st.session_state["cadastro_cat"])
            categoria = st.selectbox("Categoria *", CATEGORIAS, index=idx_cat)
            
            onde_comprou = st.text_input("Fornecedor / Marca", placeholder="Ex: ROBERTA / DOM PEDRO")
            lote = st.text_input("Número do Lote (Opcional)", placeholder="Ex: 02:41")
            quantidade_minima = st.number_input("Estoque Mínimo de Alerta", min_value=0.0, step=1.0, value=0.0)

        with col2:
            quantidade = st.number_input("Quantidade em Estoque *", min_value=0.0, step=1.0, value=1.0)
            unidade = st.selectbox("Unidade de Medida", UNIDADES, index=0)
            data_validade = st.date_input("Data de Validade *", value=datetime.now(_TZ).date())
            preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, step=0.01, format="%.2f")
            localizacao = st.text_input("Localização física no Almoxarifado", placeholder="Ex: ARMÁRIO DE ALIMENTOS / DESPENSA")

        observacoes = st.text_area("Observações Gerais", placeholder="Ex: PRODUTO OBTIDO ATRAVÉS DE DOAÇÃO DE CESTA BÁSICA")

        st.markdown("<br>", unsafe_allow_html=True)
        btn_salvar = st.form_submit_button("💾 Confirmar e Registrar no Supabase", type="primary", use_container_width=True)

    if btn_salvar:
        if not nome.strip():
            st.error("❌ O campo 'Nome do Produto' é obrigatório.")
            return

        # ENGENHARIA REVERSA DE TEXTO:
        # Juntamos as variáveis adicionais dentro do campo localizacao que já existe no banco.
        # Ficará visível assim no seu produtos.py: "ARMÁRIO DE ALIMENTOS [Fornecedor: ROBERTA | Lote: 02:41] Obs: DOAÇÃO"
        info_localizacao = localizacao.strip() if localizacao.strip() else "Almoxarifado"
        detalhes_extras = []
        
        if onde_comprou.strip(): detalhes_extras.append(f"Fornecedor: {onde_comprou.strip().upper()}")
        if lote.strip(): detalhes_extras.append(f"Lote: {lote.strip()}")
        if observacoes.strip(): detalhes_extras.append(f"Obs: {observacoes.strip().upper()}")
        
        if detalhes_extras:
            string_final_localizacao = f"{info_localizacao} [{' | '.join(detalhes_extras)}]"
        else:
            string_final_localizacao = info_localizacao

        # Payload montado estritamente com as colunas que seu produtos.py usa e aprova
        payload = {
            "empresa_id": int(empresa_id),
            "barcode": barcode_input.strip() if barcode_input.strip() else None,
            "nome": nome.strip().upper(),
            "categoria": categoria,
            "quantidade": float(quantidade),
            "unidade": unidade,
            "quantidade_minima": float(quantidade_minima),
            "preco_custo": float(preco_custo),
            "data_validade": str(data_validade),
            "localizacao": string_final_localizacao  # Salvando tudo aqui sem quebrar o schema cache
        }

        try:
            with st.spinner("Gravando dados no SmartLarder Pro..."):
                supabase.table("produtos").insert(payload).execute()
                st.success(f"🎉 Produto '{nome.strip().upper()}' cadastrado com sucesso!")
                
                # Reseta o formulário
                st.session_state["cadastro_nome"] = ""
                st.session_state["cadastro_cat"] = "Alimentos"
                st.rerun()
        except Exception as error:
            st.error(f"❌ Erro de persistência no Supabase. Motivo técnico: {error}")
