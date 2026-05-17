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
        "form_id_cadastro": 0, 
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# =========================================================
# OPEN FOOD FACTS (COM DIAGNÓSTICO)
# =========================================================
def buscar_openfoodfacts(codigo):
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{codigo}.json"
        st.info(f"🌐 [Diagnóstico API] Chamando URL: {url}")
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            st.error(f"❌ [Diagnóstico API] Erro HTTP {r.status_code}")
            return None
        data = r.json()
        st.info(f"📦 [Diagnóstico API] Status retornado pela API: {data.get('status')}")
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
    except Exception as e:
        st.error(f"💥 [Diagnóstico API] Exceção na chamada: {e}")
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
# BUSCA NO SUPABASE (COM DIAGNÓSTICO)
# =========================================================
def buscar_produto(db, empresa_id, codigo):
    colunas = ["barcode", "codigo_barras", "codigo"]
    st.info(f"🔍 [Diagnóstico Banco] Iniciando varredura para código: '{codigo}' (Empresa: {empresa_id})")
    for coluna in colunas:
        try:
            res = db.table("produtos").select("*").eq("empresa_id", int(empresa_id)).eq(coluna, str(codigo).strip()).execute()
            st.info(f"📊 [Diagnóstico Banco] Coluna '{coluna}' retornou objeto do tipo: {type(res)}")
            if res and hasattr(res, 'data'):
                st.info(f"💾 [Diagnóstico Banco] Conteúdo bruto de res.data na coluna '{coluna}': {res.data}")
                if res.data and len(res.data) > 0:
                    return dict(res.data[0])
        except Exception as e:
            st.error(f"💥 [Diagnóstico Banco] Erro ao consultar coluna '{coluna}': {e}")
    return None

# =========================================================
# PROCESSAR BUSCA
# =========================================================
def processar_busca(db, empresa_id, codigo):
    codigo = str(codigo).strip()
    st.warning(f"🚀 [Diagnóstico Processo] Entrada recebida no processador: '{codigo}'")
    if not codigo:
        st.error("❌ [Diagnóstico Processo] Código de barras vazio abortado.")
        return

    st.session_state.ultimo_codigo_buscado = codigo
    st.session_state.produto_existente = False
    st.session_state.produto_id = None

    res_banco = buscar_produto(db, empresa_id, codigo)

    if res_banco:
        st.success("🎯 [Diagnóstico Processo] Encontrado no banco!")
        st.session_state.produto_existente = True
        st.session_state.produto_id = res_banco.get("id")

        local, forn, lote, obs = parse_localizacao(res_banco.get("localizacao", ""))

        st.session_state.cad_nome = str(res_banco.get("nome", "")).upper()
        st.session_state.cad_categoria = str(res_banco.get("categoria", "Outros"))
        st.session_state.cad_quantidade = int(res_banco.get("quantidade", 0))
        st.session_state.cad_unidade = str(res_banco.get("unidade", "un"))
        st.session_state.cad_qtd_min = int(res_banco.get("quantidade_minima", 0))
        st.session_state.cad_preco = float(res_banco.get("preco_custo", 0) or 0.0)
        st.session_state.cad_localizacao = local
        st.session_state.cad_fornecedor = forn
        st.session_state.cad_lote = lote
        st.session_state.cad_obs = obs

        if res_banco.get("data_validade"):
            try:
                st.session_state.cad_validade = date.fromisoformat(res_banco["data_validade"])
            except Exception:
                st.session_state.cad_validade = date.today()

        st.session_state.form_id_cadastro += 1
        return

    st.warning("⚠️ [Diagnóstico Processo] Não achou no banco de dados. Pulando para API da Internet...")
    api = buscar_openfoodfacts(codigo)
    if api:
        st.success("🎯 [Diagnóstico Processo] Encontrado na Internet!")
        st.session_state.cad_nome = str(api.get("nome", "")).upper()
        st.session_state.cad_categoria = str(api.get("categoria", "Outros"))
        st.session_state.form_id_cadastro += 1
    else:
        st.error("❌ [Diagnóstico Processo] Produto completamente desconhecido.")

# =========================================================
# COMPACTAR LOCALIZAÇÃO
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

    # Input totalmente limpo e assistido pelo state
    codigo = st.text_input("Código de Barras (EAN)", value=st.session_state.ultimo_codigo_buscado, key="cad_barcode_input_unique")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        buscar = st.button("🔎 Buscar Produto", type="secondary", use_container_width=True)
    with col2:
        st.write(f"*Código memorizado na sessão:* `{st.session_state.ultimo_codigo_buscado}`")

    # Gatilho de busca
    if (buscar or (codigo and codigo.strip() != st.session_state.ultimo_codigo_buscado)) and codigo.strip():
        processar_busca(db, empresa_id, codigo)
        st.rerun()

    with st.form(key=f"form_main_cadastro_{st.session_state.form_id_cadastro}", clear_on_submit=False):
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

        texto_botao = "🔄 Atualizar Produto Existente" if st.session_state.produto_existente else "💾 Salvar Novo Produto"
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
                    "unidade": unidade,
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
                    
                    st.session_state.cad_nome = ""
                    st.session_state.cad_categoria = "Outros"
                    st.session_state.cad_unidade = "un"
                    st.session_state.cad_quantidade = 0
                    st.session_state.cad_qtd_min = 0
                    st.session_state.cad_preco = 0.0
                    st.session_state.cad_validade = date.today()
                    st.session_state.cad_localizacao = ""
                    st.session_state.cad_fornecedor = ""
                    st.session_state.cad_lote = ""
                    st.session_state.cad_obs = ""
                    st.session_state.ultimo_codigo_buscado = ""
                    st.session_state.produto_id = None
                    st.session_state.produto_existente = False
                    st.session_state.form_id_cadastro += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {e}")
            else:
                st.error("❌ O nome do produto é obrigatório.")
