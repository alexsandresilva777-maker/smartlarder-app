import streamlit as st
import requests
from datetime import datetime

CATEGORIAS = [
    "Alimentos",
    "Bebidas",
    "Limpeza",
    "Higiene",
    "Medicamentos",
    "Outros"
]

UNIDADES = [
    "un", "kg", "g", "L", "ml",
    "cx", "fardo", "pct", "dz"
]


def show_cadastro():
    st.title("📦 Cadastro de Produto")
    
    # Inicializar session_state para evitar loops
    if "ultimo_codigo_buscado" not in st.session_state:
        st.session_state["ultimo_codigo_buscado"] = ""
    
    if "produto_existe" not in st.session_state:
        st.session_state["produto_existe"] = False
    
    # Inicializar campos do formulário
    campos_iniciais = {
        "codigo_barras": "",
        "nome": "",
        "categoria": "Alimentos",
        "unidade": "un",
        "quantidade_inicial": 0.0,
        "estoque_minimo": 0.0,
        "preco_custo": 0.0,
        "data_validade": "",
        "localizacao": "",
        "fornecedor": "",
        "numero_lote": "",
        "observacoes": ""
    }
    
    for chave, valor in campos_iniciais.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor
    
    # Formulário布局
    with st.form("cadastro_produto_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            codigo_barras = st.text_input(
                "🔍 Código de Barras (EAN)",
                value=st.session_state["codigo_barras"],
                key="input_codigo_barras",
                placeholder="Digite ou bip o código"
            )
            nome = st.text_input(
                "📝 Nome do Produto",
                value=st.session_state["nome"],
                key="input_nome"
            )
            categoria = st.selectbox(
                "📂 Categoria",
                CATEGORIAS,
                index=CATEGORIAS.index(st.session_state["categoria"]) if st.session_state["categoria"] in CATEGORIAS else 0,
                key="input_categoria"
            )
            unidade = st.selectbox(
                "📏 Unidade",
                UNIDADES,
                index=UNIDADES.index(st.session_state["unidade"]) if st.session_state["unidade"] in UNIDADES else 0,
                key="input_unidade"
            )
            quantidade_inicial = st.number_input(
                "🔢 Quantidade Inicial",
                min_value=0.0,
                value=st.session_state["quantidade_inicial"],
                format="%.2f",
                key="input_quantidade_inicial"
            )
            estoque_minimo = st.number_input(
                "⚠️ Estoque Mínimo",
                min_value=0.0,
                value=st.session_state["estoque_minimo"],
                format="%.2f",
                key="input_estoque_minimo"
            )
        
        with col2:
            preco_custo = st.number_input(
                "💰 Preço de Custo",
                min_value=0.0,
                value=st.session_state["preco_custo"],
                format="%.2f",
                key="input_preco_custo"
            )
            data_validade = st.date_input(
                "📅 Data de Validade",
                value=st.session_state["data_validade"] if st.session_state["data_validade"] else None,
                key="input_data_validade"
            )
            localizacao = st.text_input(
                "📍 Localização Física",
                value=st.session_state["localizacao"],
                key="input_localizacao",
                placeholder="Ex: Almoxarifado Central"
            )
            fornecedor = st.text_input(
                "🏪 Fornecedor / Onde foi comprado",
                value=st.session_state["fornecedor"],
                key="input_fornecedor"
            )
            numero_lote = st.text_input(
                "🔢 Número do Lote",
                value=st.session_state["numero_lote"],
                key="input_numero_lote"
            )
            observacoes = st.text_area(
                "📝 Observações",
                value=st.session_state["observacoes"],
                key="input_observacoes",
                height=70
            )
        
        submitted = st.form_submit_button("💾 Salvar Produto", use_container_width=True)
        cancelar = st.form_submit_button("🔄 Limpar Formulário", use_container_width=True)
    
    # Ação de cancelar
    if cancelar:
        for chave in campos_iniciais.keys():
            st.session_state[chave] = campos_iniciais[chave]
        st.session_state["ultimo_codigo_buscado"] = ""
        st.session_state["produto_existe"] = False
        st.rerun()
    
    # Busca automática de EAN
    if codigo_barras and codigo_barras != st.session_state["ultimo_codigo_buscado"]:
        st.session_state["ultimo_codigo_buscado"] = codigo_barras
        st.session_state["produto_existe"] = False
        
        # Busca no Supabase
        produto_encontrado = None
        try:
            # Tenta em barcode primeiro
            result = st.session_state["db"].table("produtos").select("*").eq("empresa_id", int(st.session_state["empresa_id"])).eq("barcode", codigo_barras).execute()
            if result.data:
                produto_encontrado = result.data[0]
        except Exception:
            pass
        
        # Se não achou, tenta em codigo_barras
        if not produto_encontrado:
            try:
                result = st.session_state["db"].table("produtos").select("*").eq("empresa_id", int(st.session_state["empresa_id"])).eq("codigo_barras", codigo_barras).execute()
                if result.data:
                    produto_encontrado = result.data[0]
            except Exception:
                pass
        
        # Se ainda não achou, tenta em codigo
        if not produto_encontrado:
            try:
                result = st.session_state["db"].table("produtos").select("*").eq("empresa_id", int(st.session_state["empresa_id"])).eq("codigo", codigo_barras).execute()
                if result.data:
                    produto_encontrado = result.data[0]
            except Exception:
                pass
        
        # Se achou no banco, popula os campos
        if produto_encontrado:
            st.session_state["produto_existe"] = True
            st.session_state["nome"] = produto_encontrado.get("nome", "")
            st.session_state["categoria"] = produto_encontrado.get("categoria", "Alimentos")
            st.session_state["unidade"] = produto_encontrado.get("unidade", "un")
            st.session_state["quantidade_inicial"] = float(produto_encontrado.get("quantidade", 0))
            st.session_state["estoque_minimo"] = float(produto_encontrado.get("quantidade_minima", 0))
            st.session_state["preco_custo"] = float(produto_encontrado.get("preco_custo", 0))
            
            data_valid = produto_encontrado.get("data_validade")
            if data_valid:
                try:
                    if isinstance(data_valid, str):
                        st.session_state["data_validade"] = datetime.strptime(data_valid, "%Y-%m-%d").date()
                    else:
                        st.session_state["data_validade"] = data_valid
                except Exception:
                    st.session_state["data_validade"] = None
            else:
                st.session_state["data_validade"] = None
            
            # Leitura reversa da localização
            local_raw = produto_encontrado.get("localizacao", "")
            fornecedor_val = ""
            lote_val = ""
            obs_val = ""
            
            if "[F:" in local_raw and "|L:" in local_raw and "|O:]" in local_raw:
                try:
                    local_limpo = local_raw.split("[F:")[0].strip()
                    resto = local_raw.split("[F:")[1].rsplit("]", 1)[0]
                    
                    parts = resto.split("|")
                    for part in parts:
                        if part.startswith("F:"):
                            fornecedor_val = part[2:]
                        elif part.startswith("L:"):
                            lote_val = part[2:]
                        elif part.startswith("O:"):
                            obs_val = part[2:]
                    
                    st.session_state["localizacao"] = local_limpo
                    st.session_state["fornecedor"] = fornecedor_val
                    st.session_state["numero_lote"] = lote_val
                    st.session_state["observacoes"] = obs_val
                except Exception:
                    st.session_state["localizacao"] = local_raw
            else:
                st.session_state["localizacao"] = local_raw
            
            st.info(f"✅ Produto encontrado! Editando: {st.session_state['nome']}")
        
        else:
            # Busca no OpenFoodFacts
            try:
                url = f"https://world.openfoodfacts.org/api/v0/product/{codigo_barras}.json"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == 1 and data.get("product"):
                        product = data["product"]
                        if product.get("product_name"):
                            st.session_state["nome"] = product["product_name"]
                        if product.get("categories"):
                            cats = product["categories"].split(",")[0].strip()
                            for cat_padrao in CATEGORIAS:
                                if cat_padrao.lower() in cats.lower():
                                    st.session_state["categoria"] = cat_padrao
                                    break
            except Exception:
                pass
    
    # Ação de salvar
    if submitted:
        if not nome.strip():
            st.error("❌ O nome do produto é obrigatório.")
            return
        
        # Compactação da localização
        localizacao_compactada = localizacao.strip()
        if fornecedor.strip() or numero_lote.strip() or observacoes.strip():
            partes_extra = []
            if fornecedor.strip():
                partes_extra.append(f"F:{fornecedor.strip()}")
            if numero_lote.strip():
                partes_extra.append(f"L:{numero_lote.strip()}")
            if observacoes.strip():
                partes_extra.append(f"O:{observacoes.strip()}")
            
            if partes_extra:
                localizacao_compactada = f"{localizacao_compactada} [{'|'.join(partes_extra)}]"
        
        # REGRA ABSOLUTA: truncar para 100 caracteres
        string_final = f"{localizacao_compactada}".strip()[:100]
        
        # Formatar data
        data_validade_str = ""
        if data_validade:
            data_validade_str = data_validade.strftime("%Y-%m-%d")
        
        # Payload literal - apenas colunas existentes
        payload = {
            "empresa_id": int(st.session_state["empresa_id"]),
            "barcode": codigo_barras or None,
            "nome": nome.strip().upper(),
            "categoria": categoria,
            "quantidade": float(quantidade_inicial),
            "unidade": unidade,
            "quantidade_minima": float(estoque_minimo),
            "preco_custo": float(preco_custo),
            "data_validade": data_validade_str,
            "localizacao": string_final
        }
        
        try:
            if st.session_state["produto_existe"] and codigo_barras:
                # Atualizar produto existente
                st.session_state["db"].table("produtos").update(payload).eq("empresa_id", int(st.session_state["empresa_id"])).eq("barcode", codigo_barras).execute()
                st.success("✅ Produto atualizado com sucesso!")
            else:
                # Inserir novo produto
                st.session_state["db"].table("produtos").insert(payload).execute()
                st.success("✅ Produto cadastrado com sucesso!")
            
            # Limpar campos
            for chave in campos_iniciais.keys():
                st.session_state[chave] = campos_iniciais[chave]
            st.session_state["ultimo_codigo_buscado"] = ""
            st.session_state["produto_existe"] = False
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar: {str(e)}")


if __name__ == "__main__":
    show_cadastro()
