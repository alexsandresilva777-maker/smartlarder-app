# -*- coding: utf-8 -*-
import streamlit as st
import requests
import time
from datetime import date

# =========================
# Inicialização do estado
# =========================
def init_state():
    defaults = {
        "cad_barcode": "",
        "cad_nome": "",
        "cad_categoria": "Outros",
        "cad_ultimo_codigo": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# =========================
# Busca OpenFoodFacts
# =========================
def buscar_openfoodfacts(codigo):
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{codigo}.json"
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("status") != 1:
            return None
        produto = data.get("product", {})
        return {
            "nome": produto.get("product_name", ""),
            "categoria": produto.get("categories", "")
        }
    except Exception:
        return None

# =========================
# Busca Supabase defensiva
# =========================
def buscar_produto_supabase(db, empresa_id, codigo):
    # tentativa 1 -> barcode
    try:
        resp = db.table("produtos").select("*").eq("empresa_id", int(empresa_id)).eq("barcode", codigo).limit(1).execute()
        if resp.data: return resp.data[0]
    except Exception: pass

    # tentativa 2 -> codigo_barras
    try:
        resp = db.table("produtos").select("*").eq("empresa_id", int(empresa_id)).eq("codigo_barras", codigo).limit(1).execute()
        if resp.data: return resp.data[0]
    except Exception: pass

    # tentativa 3 -> codigo
    try:
        resp = db.table("produtos").select("*").eq("empresa_id", int(empresa_id)).eq("codigo", codigo).limit(1).execute()
        if resp.data: return resp.data[0]
    except Exception: pass

    return None

# =========================
# Processa busca
# =========================
def processar_busca(db, empresa_id, codigo):
    if not codigo:
        return

    codigo = codigo.strip()
    st.session_state.cad_ultimo_codigo = codigo

    # 1 -> banco local
    produto = buscar_produto_supabase(db, empresa_id, codigo)
    if produto:
        st.session_state.cad_nome = produto.get("nome", "") or ""
        st.session_state.cad_categoria = produto.get("categoria", "Outros") or "Outros"
        st.success("✅ Produto localizado no banco.")
        return

    # 2 -> internet
    api = buscar_openfoodfacts(codigo)
    if api:
        if api.get("nome"):
            st.session_state.cad_nome = api["nome"]

        categoria_api = api.get("categoria", "").lower()
        categoria_final = "Outros"

        if "drink" in categoria_api or "bebida" in categoria_api:
            categoria_final = "Bebidas"
        elif "food" in categoria_api or "alimento" in categoria_api:
            categoria_final = "Alimentos"

        st.session_state.cad_categoria = categoria_final
        st.info("🌐 Produto encontrado na internet.")
    else:
        st.warning("Produto não encontrado. Continue preenchendo manualmente.")

# =========================
# Tela principal
# =========================
def show_cadastro():
    init_state()

    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id")

    if db is None:
        st.error("❌ Banco não conectado.")
        return

    if not empresa_id:
        st.error("❌ Empresa não identificada.")
        return

    st.markdown("## ➕ Cadastro de Produto")

    # =========================
    # Busca EAN
    # =========================
    col_busca1, col_busca2 = st.columns([4, 1])

    with col_busca1:
        codigo = st.text_input("Código de Barras (EAN)", key="cad_barcode")

    with col_busca2:
        st.write("")
        buscar_manual = st.button("🔎 Buscar", use_container_width=True)

    # Ação de busca centralizada para evitar loops de renderização
    if buscar_manual and codigo.strip():
        processar_busca(db, empresa_id, codigo)

    # =========================
    # Formulário
    # =========================
    with st.form("form_cadastro", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("Nome do Produto *", value=st.session_state.cad_nome)
            
            categorias_lista = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Medicamentos", "Outros"]
            try:
                idx_cat = categorias_lista.index(st.session_state.cad_categoria)
            except ValueError:
                idx_cat = 5 # Padrão: Outros

            categoria = st.selectbox("Categoria", categorias_lista, index=idx_cat)
            unidade = st.selectbox("Unidade", ["un", "kg", "g", "L", "ml", "cx", "fardo", "pct", "dz"])
            quantidade = st.number_input("Quantidade Inicial", min_value=0.0, value=0.0, step=1.0)
            qtd_min = st.number_input("Estoque Mínimo", min_value=0.0, value=0.0, step=1.0)

        with col2:
            preco = st.number_input("Preço de Custo (R$)", min_value=0.0, value=0.0, step=0.01, format="%.2f")
            validade = st.date_input("Data de Validade", value=date.today())
            localizacao = st.text_input("Localização Física")
            fornecedor = st.text_input("Fornecedor / Onde foi comprado")
            lote = st.text_input("Número do Lote")

        observacoes = st.text_area("Observações")
        salvar = st.form_submit_button("💾 Salvar Produto", type="primary", use_container_width=True)

        # =========================
        # SALVAR PROCESSAMENTO
        # =========================
        if salvar:
            nome_final = nome.strip().upper() if nome else ""

            if not nome_final:
                st.error("❌ Nome do produto é obrigatório.")
            else:
                extras = []
                if fornecedor.strip():
                    extras.append(f"Fornecedor: {fornecedor.strip().upper()}")
                if lote.strip():
                    extras.append(f"Lote: {lote.strip()}")
                if observacoes.strip():
                    extras.append(f"Obs: {observacoes.strip().upper()}")

                local_final = localizacao.strip()
                if extras:
                    local_final = f"{local_final} [{' | '.join(extras)}]" if local_final else f"[{' | '.join(extras)}]"

                payload = {
                    "empresa_id": int(empresa_id),
                    "barcode": codigo.strip() if codigo.strip() else None,
                    "nome": nome_final,
                    "categoria": categoria,
                    "quantidade": float(quantidade),
                    "unidade": unidade,
                    "quantidade_minima": float(qtd_min),
                    "preco_custo": float(preco),
                    "data_validade": validade.strftime("%Y-%m-%d"),
                    "localizacao": local_final if local_final else "Almoxarifado"
                }

                try:
                    db.table("produtos").insert(payload).execute()
                    st.success("🎉 Produto salvo com sucesso!")
                    time.sleep(1)
                    
                    # Reset amigável de estado sem quebrar os widgets
                    st.session_state.cad_barcode = ""
                    st.session_state.cad_nome = ""
                    st.session_state.cad_categoria = "Outros"
                    st.session_state.cad_ultimo_codigo = ""
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Falha ao salvar no Supabase: {e}")
