import streamlit as st
from datetime import date
import utils.database as db
from utils.barcode_lookup import buscar_por_ean

CATEGORIAS = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Medicamentos", "Outros"]
UNIDADES = ["un", "kg", "g", "L", "ml", "cx", "fardo", "pct", "dz"]

def show_cadastro():
    user_id = st.session_state.get("user_id", 1)
    st.markdown("## ➕ Cadastrar Produto")

    # --- Inicialização Simplificada ---
    if "lk_codigo" not in st.session_state: st.session_state.lk_codigo = ""
    if "dados_busca" not in st.session_state: st.session_state.dados_busca = {}

    # --- Área de Busca ---
    col_input, col_buscar = st.columns([4, 1])
    
    with col_input:
        codigo_digitado = st.text_input(
            "Digite ou bipa o código", 
            value=st.session_state.lk_codigo,
            key="input_direto"
        )
    
    with col_buscar:
        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
        btn_disparar = st.button("🔍 Buscar", type="primary", use_container_width=True)

    # --- Lógica de Processamento (Igual à Recepção) ---
    if btn_disparar and codigo_digitado:
        st.session_state.lk_codigo = codigo_digitado.strip()
        
        # 1. Busca Local (O que você adicionou no database.py)
        res_local = db.buscar_produto_por_codigo(st.session_state.lk_codigo, user_id)
        
        if res_local:
            st.session_state.dados_busca = dict(res_local)
            st.success(f"✅ Produto encontrado no estoque!")
        else:
            # 2. Busca Global (EAN)
            with st.spinner("Consultando base global..."):
                res_global = buscar_por_ean(st.session_state.lk_codigo)
                if res_global:
                    st.session_state.dados_busca = res_global
                    st.info("🌐 Dados carregados da nuvem.")
                else:
                    st.session_state.dados_busca = {}
                    st.warning("Novo produto: preencha os dados abaixo.")

    # --- Formulário de Cadastro ---
    st.markdown("---")
    info = st.session_state.dados_busca

    with st.form("form_final_cadastro", clear_on_submit=True):
        c1, c2 = st.columns([3, 2])
        with c1:
            nome = st.text_input("Nome do Produto *", value=info.get("nome", ""))
        with c2:
            barcode = st.text_input("Código de Barras", value=st.session_state.lk_codigo)

        v1, v2, v3 = st.columns(3)
        with v1:
            validade = st.date_input("Validade *", value=date.today())
        with v2:
            quantidade = st.number_input("Qtd Inicial *", min_value=0.0, value=1.0)
        with v3:
            unidade = st.selectbox("Unidade", UNIDADES)

        cat_val = info.get("categoria", "Alimentos")
        cat_idx = CATEGORIAS.index(cat_val) if cat_val in CATEGORIAS else 0
        categoria = st.selectbox("Categoria *", CATEGORIAS, index=cat_idx)

        submitted = st.form_submit_button("💾 Salvar no SmartLarder", type="primary", use_container_width=True)

    if submitted:
        if not nome:
            st.error("O nome é obrigatório!")
        else:
            novo_prod = {
                "codigo_barras": barcode,
                "nome": nome,
                "categoria": categoria,
                "quantidade": quantidade,
                "unidade": unidade,
                "validade": str(validade),
                "criado_por": st.session_state.get("username", "admin")
            }
            db.inserir_produto(novo_prod, user_id, novo_prod["criado_por"])
            st.success("Cadastrado com sucesso!")
            # Limpa tudo para o próximo
            st.session_state.lk_codigo = ""
            st.session_state.dados_busca = {}
            st.rerun()
