# -*- coding: utf-8 -*-
import re
import time
import requests
import streamlit as st
from datetime import date

# =========================================================
# SESSION STATE
# =========================================================
def init_state():
    defaults = {
        "cad_nome": "",
        "cad_categoria": "Outros",
        "cad_unidade": "un",
        "cad_quantidade": 0,
        "cad_qtd_min": 0,
        "cad_preco": 0.0,
        "cad_validade": date.today(),
        "cad_localizacao": "",
        "cad_fornecedor": "",
        "cad_lote": "",
        "cad_obs": "",
        "ultimo_codigo_buscado": "",
        "produto_id": None,
        "produto_existente": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# =========================================================
# OPEN FOOD FACTS (MARCA INTEGRADA AO NOME)
# =========================================================
def buscar_openfoodfacts(codigo):
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{codigo}.json"
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("status") != 1:
            return None
        p = data.get("product", {})
        
        nome_base = p.get("product_name", "").strip()
        marca = p.get("brands", "").strip()
        
        if marca and nome_base:
            if nome_base.lower().startswith(marca.lower()):
                nome_completo = nome_base
            else:
                nome_completo = f"{marca} - {nome_base}"
        else:
            nome_completo = nome_base or marca

        categorias = str(p.get("categories", "")).lower()
        categoria = "Outros"

        if "bebida" in categorias or "drink" in categorias:
            categoria = "Bebidas"
        elif "food" in categorias or "alimento" in categorias:
            categoria = "Alimentos"

        return {"nome": nome_completo.upper(), "categoria": categoria}
    except Exception:
        return None

# =========================================================
# EXTRAIR F/L/O DA LOCALIZAÇÃO
# =========================================================
def parse_localizacao(txt):
    if not txt:
        return "", "", "", ""
    local = txt
    fornecedor = ""
    lote = ""
    obs = ""
    try:
        m = re.search(r"\[(.*?)\]", txt)
        if m:
            tags = m.group(1)
            local = txt[:m.start()].strip()
            for item in tags.split("|"):
                item = item.strip()
                if item.startswith("F:"):
                    fornecedor = item[2:].strip()
                elif item.startswith("L:"):
                    lote = item[2:].strip()
                elif item.startswith("O:"):
                    obs = item[2:].strip()
    except Exception:
        pass
    return local, fornecedor, lote, obs

# =========================================================
# BUSCA DIRETAMENTE NAS COLUNAS REAIS
# =========================================================
def buscar_produto(db, empresa_id, codigo):
    colunas = ["barcode", "codigo_barras", "codigo"]
    for coluna in colunas:
        try:
            r = db.table("produtos").select("*").eq("empresa_id", int(empresa_id)).eq(coluna, codigo).limit(1).execute()
            if r.data:
                return r.data[0]
        except Exception:
            pass
    return None

# =========================================================
# PROCESSAR BUSCA
# =========================================================
def processar_busca(db, empresa_id, codigo):
    codigo = str(codigo).strip()
    if not codigo:
        return

    st.session_state.ultimo_codigo_buscado = codigo

    with st.spinner("Buscando dados do produto..."):
        produto = buscar_produto(db, empresa_id, codigo)

        if produto:
            st.session_state.produto_existente = True
            st.session_state.produto_id = produto.get("id")

            local, forn, lote, obs = parse_localizacao(produto.get("localizacao", ""))

            st.session_state.cad_nome = str(produto.get("nome", "")).upper()
            st.session_state.cad_categoria = produto.get("categoria", "Outros")
            st.session_state.cad_quantidade = int(produto.get("quantidade", 0))
            st.session_state.cad_unidade = produto.get("unidade", "un")
            st.session_state.cad_qtd_min = int(produto.get("quantidade_minima", 0))
            st.session_state.cad_preco = float(produto.get("preco_custo", 0))
            st.session_state.cad_localizacao = local
            st.session_state.cad_fornecedor = forn
            st.session_state.cad_lote = lote
            st.session_state.cad_obs = obs

            if produto.get("data_validade"):
                try:
                    st.session_state.cad_validade = date.fromisoformat(produto["data_validade"])
                except Exception:
                    st.session_state.cad_validade = date.today()

            st.success("✅ Produto localizado no banco de dados!")
            return

        api = buscar_openfoodfacts(codigo)
        if api:
            if api.get("nome"):
                st.session_state.cad_nome = api["nome"].upper()
            st.session_state.cad_categoria = api.get("categoria", "Outros")
            st.info("🌐 Produto localizado na internet.")
        else:
            st.warning("⚠️ Produto não cadastrado. Continue manualmente.")

        st.session_state.produto_existente = False
        st.session_state.produto_id = None

# =========================================================
# COMPACTAR E CORTAR STRINGS (MÁXIMO 100 CARACTERES)
# =========================================================
def montar_localizacao(local, fornecedor, lote, obs):
    local = str(local).strip()
    extras = []
    if fornecedor.strip():
        extras.append(f"F:{fornecedor.strip().upper()}")
    if lote.strip():
        extras.append(f"L:{lote.strip().upper()}")
    if obs.strip():
        extras.append(f"O:{obs.strip().upper()}")

    if extras:
        final = f"{local} [{'|'.join(extras)}]"
    else:
        final = local

    return final.strip()[:100]

# =========================================================
# RENDERIZAÇÃO DA TELA
# =========================================================
def show_cadastro():
    init_state()

    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id")

    if not db:
        st.error("❌ Banco de dados não conectado.")
        return

    if not empresa_id:
        st.error("❌ Empresa inválida ou não identificada no sistema.")
        return

    st.markdown("## ➕ Cadastro de Produto")

    col1, col2 = st.columns([4, 1])
    with col1:
        # O widget gerencia seu próprio estado através da chave interna
        codigo = st.text_input("Código de Barras (EAN)", key="cad_barcode")
    with col2:
        st.markdown("<div style='padding-top:28px;'></div>", unsafe_allow_html=True)
        buscar = st.button("🔎 Buscar", use_container_width=True)

    if (buscar or (codigo and codigo != st.session_state.ultimo_codigo_buscado)) and codigo.strip():
        processar_busca(db, empresa_id, codigo)
        st.rerun()

    with st.form("form_cadastro_final", clear_on_submit=False):
        c1, c2 = st.columns(2)

        with c1:
            nome = st.text_input("Nome do Produto *", value=st.session_state.cad_nome)
            
            lista_categorias = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Medicamentos", "Outros"]
            idx_cat = lista_categorias.index(st.session_state.cad_categoria) if st.session_state.cad_categoria in lista_categorias else 5
            categoria = st.selectbox("Categoria *", lista_categorias, index=idx_cat)
            
            lista_unidades = ["un", "kg", "g", "L", "ml", "cx", "fardo", "pct", "dz"]
            idx_uni = lista_unidades.index(st.session_state.cad_unidade) if st.session_state.cad_unidade in lista_unidades else 0
            unidade = st.selectbox("Unidade de Medida *", lista_unidades, index=idx_uni)
            
            qtd = st.number_input("Quantidade Inicial *", min_value=0, step=1, value=int(st.session_state.cad_quantidade))
            qtd_min = st.number_input("Estoque Mínimo Desejado", min_value=0, step=1, value=int(st.session_state.cad_qtd_min))

        with c2:
            preco = st.number_input("Preço de Custo por Unidade (R$)", min_value=0.0, step=0.01, format="%.2f", value=st.session_state.cad_preco)
            validade = st.date_input("Data de Validade", value=st.session_state.cad_validade)
            localizacao = st.text_input("Localização / Armário", value=st.session_state.cad_localizacao)
            fornecedor = st.text_input("Fornecedor / Loja", value=st.session_state.cad_fornecedor)
            lote = st.text_input("Número do Lote", value=st.session_state.cad_lote)

        obs = st.text_area("Observações", value=st.session_state.cad_obs)

        texto_botao = "🔄 Atualizar Produto" if st.session_state.produto_existente else "💾 Salvar Produto"
        salvar = st.form_submit_button(texto_botao, type="primary", use_container_width=True)

        if salvar:
            nome_final = nome.strip().upper()

            if nome_final:
                local_final = montar_localizacao(localizacao, fornecedor, lote, obs)

                payload = {
                    "empresa_id": int(empresa_id),
                    "barcode": codigo.strip() if codigo.strip() else None,
                    "nome": nome_final,
                    "categoria": categoria,
                    "quantidade": int(qtd),
                    "unidade": unity if 'unity' in locals() else unidade,
                    "quantidade_minima": int(qtd_min),
                    "preco_custo": float(preco),
                    "data_validade": validade.strftime("%Y-%m-%d"),
                    "localizacao": local_final
                }

                try:
                    if st.session_state.produto_existente:
                        db.table("produtos").update(payload).eq("id", st.session_state.produto_id).execute()
                        st.success("🎉 Produto atualizado com sucesso!")
                    else:
                        db.table("produtos").insert(payload).execute()
                        st.success("🎉 Novo produto cadastrado com sucesso!")

                    time.sleep(1)

                    # Limpeza segura de chaves que NÃO estão amarradas a widgets via key direto no form
                     chaves_para_resetar = [
                        "cad_nome", "cad_categoria", "cad_unidade", "cad_quantidade", 
                        "cad_qtd_min", "cad_preco", "cad_localizacao", "cad_fornecedor", 
                        "cad_lote", "cad_obs", "ultimo_codigo_buscado"
                    ]
                    for k in chaves_para_resetar:
                        if k in st.session_state:
                            del st.session_state[k]
                    
                    st.session_state.produto_id = None
                    st.session_state.produto_existente = False

                    # O rerun recarrega o app limpando naturalmente os inputs controlados
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao persistir dados no Supabase: {e}")
            else:
                st.error("❌ O nome do produto é obrigatório.")
