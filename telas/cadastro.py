# -*- coding: utf-8 -*-
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
# OPEN FOOD FACTS API
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
# BUSCA EXCLUSIVA NA COLUNA REAL (barcode)
# =========================================================
def buscar_produto(db, empresa_id, codigo):
    try:
        res = db.table("produtos").select("*").eq("empresa_id", int(empresa_id)).eq("barcode", str(codigo).strip()).execute()
        if res and hasattr(res, 'data') and res.data:
            return dict(res.data[0])
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

    res_banco = buscar_produto(db, empresa_id, codigo)

    if res_banco:
        st.session_state.produto_existente = True
        st.session_state.produto_id = res_banco.get("id")

        st.session_state.cad_nome = str(res_banco.get("nome", "")).upper()
        st.session_state.cad_categoria = str(res_banco.get("categoria", "Outros"))
        st.session_state.cad_quantidade = int(res_banco.get("quantidade", 0))
        st.session_state.cad_unidade = str(res_banco.get("unidade", "un"))
        st.session_state.cad_qtd_min = int(res_banco.get("quantidade_minima", 0))
        st.session_state.cad_preco = float(res_banco.get("preco_custo", 0) or 0.0)
        st.session_state.cad_localizacao = str(res_banco.get("localizacao", ""))
        st.session_state.cad_fornecedor = ""
        st.session_state.cad_lote = ""
        st.session_state.cad_obs = ""

        if res_banco.get("data_validade"):
            try:
                st.session_state.cad_validade = date.fromisoformat(res_banco["data_validade"])
            except Exception:
                st.session_state.cad_validade = date.today()

        st.success(f"✅ Produto encontrado no estoque: {st.session_state.cad_nome}")
        st.session_state.form_id_cadastro += 1
        st.rerun()
        return

    # Se não achou no banco, tenta na Internet
    api = buscar_openfoodfacts(codigo)
    if api:
        st.session_state.cad_nome = str(api.get("nome", "")).upper()
        st.session_state.cad_categoria = str(api.get("categoria", "Outros"))
        st.info("🌐 Produto localizado na Internet!")
    else:
        st.session_state.cad_nome = ""
        st.session_state.cad_categoria = "Outros"
        st.warning("⚠️ Produto não cadastrado no estoque nem na internet.")

    st.session_state.produto_existente = False
    st.session_state.produto_id = None
    st.session_state.form_id_cadastro += 1
    st.rerun()

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

    # Forçamos o código digitado a atualizar o state imediatamente
    codigo = st.text_input("Código de Barras (EAN)", value=st.session_state.ultimo_codigo_buscado, key="cad_barcode_input_final")
    
    # Se o código na caixinha mudou em relação à última busca, ele dispara o processador sozinho
    if codigo.strip() and codigo.strip() != st.session_state.ultimo_codigo_buscado:
        processar_busca(db, empresa_id, codigo)

    if st.session_state.produto_existente:
        st.info(f"🔗 Editando produto existente (ID no banco: {st.session_state.produto_id})")

    # Formulário renderiza os dados injetados pelo processar_busca
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
            localizacao = st.text_input("Localização / Armário", value=st.session_state.cad_localizacao, max_chars=100)
            fornecedor = st.text_input("Fornecedor / Loja (Opcional)", value=st.session_state.cad_fornecedor)
            lote = st.text_input("Número do Lote (Opcional)", value=st.session_state.cad_lote)

        obs_usuario = st.text_area("Observações", value=st.session_state.cad_obs)

        texto_botao = "🔄 Atualizar Produto Existente" if st.session_state.produto_existente else "💾 Salvar Novo Produto"
        salvar = st.form_submit_button(texto_botao, type="primary", use_container_width=True)

        if salvar:
            nome_final = nome.strip().upper()

            if nome_final:
                notas_finais = []
                if fornecedor.strip():
                    notas_finais.append(f"Fornecedor: {fornecedor.strip().upper()}")
                if lote.strip():
                    notas_finais.append(f"Lote: {lote.strip().upper()}")
                if obs_usuario.strip():
                    notas_finais.append(obs_usuario.strip())
                
                observacao_compilada = " | ".join(notas_finais)

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
                    "localizacao": localizacao.strip()[:100]
                }

                try:
                    if st.session_state.produto_existente:
                        db.table("produtos").update(payload).eq("id", st.session_state.produto_id).execute()
                        st.success("🎉 Produto atualizado com sucesso!")
                    else:
                        db.table("produtos").insert(payload).execute()
                        st.success("🎉 Novo produto cadastrado com sucesso!")

                    time.sleep(1)

                    # Reset total pós-salvamento
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
                    st.error(f"❌ Erro de persistência no Supabase: {e}")
            else:
                st.error("❌ O nome do produto é obrigatório.")
