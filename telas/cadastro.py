# -*- coding: utf-8 -*-
"""
telas/cadastro.py — SmartLarder Pro v2 (Versão Consolidada e Corrigida)
- Busca em cascata estável (Supabase -> Open Food Facts -> Brasil API)
- Reatividade blindada usando chaves de Session State (Resolve campos em branco)
- Suporte à câmera e leitores integrados
"""
import time
import requests
import streamlit as st
from datetime import date

# ── Constantes ────────────────────────────────────────────────────────────────
CATEGORIAS = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Medicamentos", "Embalagens", "Outros"]
UNIDADES = ["un", "kg", "g", "L", "ml", "cx", "fardo", "pct", "dz"]

# Chaves internas estruturadas
_K_CODIGO    = "cad_codigo"
_K_BUSCADO   = "cad_ultimo_buscado"
_K_CAM_ON    = "cad_cam_on"
_K_FORM_ID   = "form_id_cadastro"

# Chaves mapeadas diretamente para os componentes do formulário
FORM_KEYS = [
    "cad_nome", "cad_categoria", "cad_fornecedor", "cad_lote", 
    "cad_validade", "cad_quantidade", "cad_unidade", "cad_preco", 
    "cad_estoque_minimo", "cad_localizacao", "cad_observacoes"
]

_CAT_MAP = {
    "bebida": "Bebidas", "drink": "Bebidas", "suco": "Bebidas",
    "refrigerante": "Bebidas", "cerveja": "Bebidas", "vinho": "Bebidas",
    "agua": "Bebidas", "leite": "Bebidas", "cha": "Bebidas", "cafe": "Bebidas",
    "limpeza": "Limpeza", "detergente": "Limpeza", "sabao": "Limpeza",
    "desinfet": "Limpeza", "alvejante": "Limpeza", "amaciante": "Limpeza",
    "higiene": "Higiene", "sabonete": "Higiene", "shampoo": "Higiene",
    "creme": "Higiene", "dental": "Higiene", "desodorante": "Higiene",
    "cosmet": "Higiene", "perfume": "Higiene",
    "medic": "Medicamentos", "farmac": "Medicamentos",
    "suplement": "Medicamentos", "vitam": "Medicamentos",
    "embalagem": "Embalagens",
}

def _mapear_categoria(texto: str) -> str:
    t = texto.lower()
    for chave, cat in _CAT_MAP.items():
        if chave in t:
            return cat
    return "Alimentos"

# ── Inicialização do Estado (Garantindo persistência reativa) ──────────────────
def _init_state():
    if _K_CODIGO not in st.session_state:
        st.session_state[_K_CODIGO] = ""
    if _K_BUSCADO not in st.session_state:
        st.session_state[_K_BUSCADO] = ""
    if _K_CAM_ON not in st.session_state:
        st.session_state[_K_CAM_ON] = False
    if _K_FORM_ID not in st.session_state:
        st.session_state[_K_FORM_ID] = 0
    if "produto_existente" not in st.session_state:
        st.session_state["produto_existente"] = False
    if "produto_id" not in st.session_state:
        st.session_state["produto_id"] = None
    if "status_busca" not in st.session_state:
        st.session_state["status_busca"] = {}

    # Defaults para os inputs do formulário
    defaults = {
        "cad_nome": "",
        "cad_categoria": "Alimentos",
        "cad_fornecedor": "",
        "cad_lote": "",
        "cad_validade": date.today(),
        "cad_quantidade": 1.0,
        "cad_unidade": "un",
        "cad_preco": 0.0,
        "cad_estoque_minimo": 0.0,
        "cad_localizacao": "",
        "cad_observacoes": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── APIs de busca em cascata ──────────────────────────────────────────────────
def _buscar_off(codigo: str) -> dict:
    try:
        r = requests.get(
            f"https://world.openfoodfacts.org/api/v0/product/{codigo}.json",
            timeout=5,
            headers={"User-Agent": "SmartLarder-Pro/2.0"},
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        if data.get("status") != 1:
            return {}
        p = data.get("product", {})
        nome = (p.get("product_name_pt") or p.get("product_name") or "").strip()
        if not nome:
            return {}
        marca = (p.get("brands") or "").split(",")[0].strip()
        cats  = p.get("categories_tags") or p.get("categories") or ""
        if isinstance(cats, list):
            cats = " ".join(cats)
        return {
            "nome": nome.upper(),
            "categoria": _mapear_categoria(cats),
            "fornecedor": marca.upper(),
            "_fonte": "Open Food Facts",
        }
    except Exception:
        return {}

def _buscar_brasil_api(codigo: str) -> dict:
    try:
        r = requests.get(
            f"https://brasilapi.com.br/api/ean/v1/{codigo}",
            timeout=5,
            headers={"User-Agent": "SmartLarder-Pro/2.0"},
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        nome = (data.get("description") or data.get("nome") or "").strip()
        if not nome:
            return {}
        marca = (data.get("brand") or data.get("marca") or "").strip()
        cats  = data.get("category") or data.get("categoria") or ""
        return {
            "nome": nome.upper(),
            "categoria": _mapear_categoria(str(cats)),
            "fornecedor": marca.upper(),
            "_fonte": "Brasil API",
        }
    except Exception:
        return {}

def _buscar_supabase(db, empresa_id: int, codigo: str) -> dict:
    if not db or not codigo:
        return {}
    for coluna in ("codigo_barras", "codigo"):
        try:
            res = db.table("produtos").select("*").eq(coluna, codigo).eq("empresa_id", empresa_id).limit(1).execute()
            if res and hasattr(res, 'data') and res.data:
                return {**res.data[0], "_fonte": "banco_local"}
        except Exception as e:
            if any(w in str(e).lower() for w in ("column", "does not exist")):
                continue
            return {}
    return {}

# ── Lógica Central do Processamento ───────────────────────────────────────────
def _executar_busca(codigo: str, db, empresa_id: int):
    codigo = str(codigo).strip()
    if not codigo:
        return

    st.session_state[_K_CODIGO] = codigo
    st.session_state[_K_BUSCADO] = codigo

    # 1. Tenta Banco Local
    local = _buscar_supabase(db, empresa_id, codigo)
    if local:
        st.session_state["produto_existente"] = True
        st.session_state["produto_id"] = local.get("id")
        
        st.session_state["cad_nome"] = str(local.get("nome", "")).upper()
        st.session_state["cad_categoria"] = str(local.get("categoria", "Alimentos"))
        st.session_state["cad_fornecedor"] = str(local.get("fornecedor", "")).upper()
        st.session_state["cad_lote"] = str(local.get("lote", ""))
        st.session_state["cad_quantidade"] = float(local.get("quantidade", 1.0))
        st.session_state["cad_unidade"] = str(local.get("unidade", "un"))
        st.session_state["cad_preco"] = float(local.get("preco_custo", 0.0) or 0.0)
        st.session_state["cad_estoque_minimo"] = float(local.get("estoque_minimo", 0.0) or 0.0)
        st.session_state["cad_localizacao"] = str(local.get("localizacao", ""))
        st.session_state["cad_observacoes"] = str(local.get("observacoes", ""))
        
        if local.get("validade"):
            try: st.session_state["cad_validade"] = date.fromisoformat(local["validade"])
            except Exception: st.session_state["cad_validade"] = date.today()
        elif local.get("data_validade"):
            try: st.session_state["cad_validade"] = date.fromisoformat(local["data_validade"])
            except Exception: st.session_state["cad_validade"] = date.today()

        st.session_state["status_busca"] = {"tipo": "info", "msg": "📦 Produto encontrado no seu banco local. Editando registro."}
        st.session_state[_K_FORM_ID] += 1
        return

    # 2. Tenta Open Food Facts
    off = _buscar_off(codigo)
    if off:
        _aplicar_dados_externos(off)
        return

    # 3. Tenta Brasil API
    br = _buscar_brasil_api(codigo)
    if br:
        _aplicar_dados_externos(br)
        return

    # Caso não encontre em lugar nenhum
    st.session_state["produto_existente"] = False
    st.session_state["produto_id"] = None
    st.session_state["cad_nome"] = ""
    st.session_state["cad_categoria"] = "Alimentos"
    st.session_state["cad_fornecedor"] = ""
    st.session_state["cad_lote"] = ""
    st.session_state["cad_quantidade"] = 1.0
    st.session_state["cad_preco"] = 0.0
    st.session_state["cad_estoque_minimo"] = 0.0
    st.session_state["cad_localizacao"] = ""
    st.session_state["cad_observacoes"] = ""
    st.session_state["status_busca"] = {"tipo": "warning", "msg": "⚠️ Produto não encontrado nas bases. Preencha manualmente abaixo."}
    st.session_state[_K_FORM_ID] += 1

def _aplicar_dados_externos(res_api: dict):
    st.session_state["produto_existente"] = False
    st.session_state["produto_id"] = None
    st.session_state["cad_nome"] = res_api["nome"]
    st.session_state["cad_categoria"] = res_api["categoria"]
    st.session_state["cad_fornecedor"] = res_api["fornecedor"]
    
    # Limpa dados logísticos para evitar heranças incorretas
    st.session_state["cad_lote"] = ""
    st.session_state["cad_quantidade"] = 1.0
    st.session_state["cad_preco"] = 0.0
    st.session_state["cad_estoque_minimo"] = 0.0
    st.session_state["cad_localizacao"] = ""
    st.session_state["cad_observacoes"] = ""
    st.session_state["cad_validade"] = date.today()
    
    st.session_state["status_busca"] = {"tipo": "success", "msg": f"🌐 Encontrado via {res_api['_fonte']}: {res_api['nome']}"}
    st.session_state[_K_FORM_ID] += 1

# ── Renderização da Interface ─────────────────────────────────────────────────
def show_cadastro():
    _init_state()

    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    user_id = st.session_state.get("user_id", 1)
    username = st.session_state.get("username", "")

    st.markdown("## ➕ Cadastrar Produto")
    st.markdown("### 🔍 Código de Barras (EAN)")

    # Barra superior estável de Input do EAN
    col_ean, col_btn = st.columns([4, 1])
    with col_ean:
        codigo_input = st.text_input(
            "EAN",
            value=st.session_state[_K_CODIGO],
            placeholder="Digite, escaneie ou use a câmera...",
            key="cad_input_ean",
            label_visibility="collapsed",
        )
    with col_btn:
        btn_buscar = st.button("🔍 Buscar", use_container_width=True, type="primary")

    # Atualiza o estado se digitado algo
    if codigo_input != st.session_state[_K_CODIGO]:
        st.session_state[_K_CODIGO] = codigo_input

    # Gatilho de Busca Automática (leitor ou digitação completa)
    codigo_mudou = (
        codigo_input and 
        codigo_input != st.session_state[_K_BUSCADO] and 
        (len(codigo_input) >= 8 or (len(codigo_input) > 0 and not codigo_input[-1].isdigit()))
    )

    if (btn_buscar and codigo_input) or codigo_mudou:
        _executar_busca(codigo_input, db, empresa_id)
        st.rerun()

    # Controle de Câmera Integrado do Claude
    usar_camera = st.checkbox("📷 Usar câmera para escanear código de barras", value=st.session_state[_K_CAM_ON], key="cad_check_cam")
    st.session_state[_K_CAM_ON] = usar_camera

    if usar_camera:
        imagem = st.camera_input("Aponte para o código de barras", key="cad_camera_snap")
        if imagem:
            codigo_cam = _decodificar_imagem(imagem.getvalue())
            if codigo_cam == "IMPORT_ERROR":
                st.warning("⚠️ `pyzbar` ou `Pillow` não instalados. Ajuste o requirements.txt e packages.txt.")
            elif codigo_cam:
                st.success(f"✅ Código detectado: **{codigo_cam}**")
                st.session_state[_K_CAM_ON] = False
                _executar_busca(codigo_cam, db, empresa_id)
                st.rerun()
            else:
                st.warning("⚠️ Código não detectado. Melhore a iluminação.")

    # Exibição de alertas persistentes pós-busca
    status = st.session_state["status_busca"]
    if status:
        if status["tipo"] == "info": st.info(status["msg"])
        elif status["tipo"] == "success": st.success(status["msg"])
        elif status["tipo"] == "warning": st.warning(status["msg"])

    st.markdown("---")
    st.markdown("### 📝 Dados do Produto")

    # FORMULÁRIO DINÂMICO REATIVO (Usando Keys vinculadas ao State)
    with st.form(key=f"form_cadastro_produto_v3_{st.session_state[_K_FORM_ID]}", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Nome do Produto *", key="cad_nome", placeholder="Ex: ARROZ TIO JOÃO 5KG")
            st.selectbox("Categoria *", CATEGORIAS, key="cad_categoria")
            st.text_input("Fornecedor / Marca", key="cad_fornecedor", placeholder="Ex: Nestlé")
            st.text_input("Número do Lote", key="cad_lote", placeholder="Ex: L2025001")
        with c2:
            st.date_input("Data de Validade *", key="cad_validade", min_value=date(2000, 1, 1))
            st.number_input("Quantidade *", min_value=0.01, step=1.0, format="%.2f", key="cad_quantidade")
            st.selectbox("Unidade", UNIDADES, key="cad_unidade")
            st.number_input("Preço de Custo (R$)", min_value=0.0, step=0.01, format="%.2f", key="cad_preco")

        c3, c4 = st.columns(2)
        with c3:
            st.number_input("Estoque Mínimo", min_value=0.0, step=1.0, format="%.1f", key="cad_estoque_minimo", help="Alerta quando o estoque cair abaixo deste valor")
        with c4:
            st.text_input("Localização", key="cad_localizacao", placeholder="Ex: Prateleira A3")

        st.text_area("Observações", key="cad_observacoes", placeholder="Informações adicionais...", height=70)

        texto_btn_submit = "🔄 Atualizar Produto Existente" if st.session_state["produto_existente"] else "💾 Salvar Produto"
        submitted = st.form_submit_button(texto_btn_submit, type="primary", use_container_width=True)

    if submitted:
        # Recupera os dados validados diretamente das chaves ativas do form
        nome_val = st.session_state["cad_nome"].strip()
        qtd_val = st.session_state["cad_quantidade"]

        erros = []
        if not nome_val:
            erros.append("Nome do produto é obrigatório.")
        if qtd_val <= 0:
            erros.append("Quantidade deve ser maior que zero.")

        if erros:
            for e in erros:
                st.error(f"❌ {e}")
            return

        _salvar_produto(
            db=db,
            empresa_id=empresa_id,
            user_id=user_id,
            username=username,
            dados={
                "codigo_input": st.session_state[_K_CODIGO],
                "nome": nome_val,
                "categoria": st.session_state["cad_categoria"],
                "quantidade": qtd_val,
                "unidade": st.session_state["cad_unidade"],
                "validade": str(st.session_state["cad_validade"]),
                "lote": st.session_state["cad_lote"].strip() or None,
                "fornecedor": st.session_state["cad_fornecedor"].strip() or None,
                "localizacao": st.session_state["cad_localizacao"].strip() or None,
                "preco_custo": st.session_state["cad_preco"],
                "estoque_min": st.session_state["cad_estoque_minimo"],
                "observacoes": st.session_state["cad_observacoes"].strip() or None,
            },
        )

# ── Persistência com Tipos Rígidos e Segurança de Colunas ──────────────────────
def _salvar_produto(db, empresa_id, user_id, username, dados: dict):
    if not db:
        st.error("❌ Sem conexão com o banco de dados.")
        return

    payload_base = {
        "nome": dados["nome"].upper(),
        "categoria": dados["categoria"],
        "quantidade": float(dados["quantidade"]),
        "unidade": dados["unidade"],
        "preco_custo": float(dados["preco_custo"]),
        "empresa_id": int(empresa_id),
        "user_id": int(user_id),
        "criado_por": username,
    }

    # Tratamento flexível do nome da coluna de estoque mínimo mapeado na tabela
    payload_base["estoque_minimo"] = float(dados["estoque_min"])

    # Tratamento flexível da coluna de validade do banco
    payload_base["validade"] = dados["validade"]
    payload_base["data_validade"] = dados["validade"]

    for campo in ("lote", "fornecedor", "localizacao", "observacoes"):
        if dados.get(campo):
            payload_base[campo] = dados[campo]

    codigo = dados.get("codigo_input", "").strip()

    if not codigo:
        _inserir_supabase(db, payload_base)
        return

    # Tentativa dupla de colunas (Design Defensivo do Claude)
    for coluna in ("codigo_barras", "codigo"):
        payload = {**payload_base, coluna: codigo}
        if _inserir_supabase(db, payload, silencioso=True):
            return

    st.warning("⚠️ Estrutura de código não reconhecida. Salvando registro básico.")
    _inserir_supabase(db, payload_base)

def _inserir_supabase(db, payload: dict, silencioso: bool = False) -> bool:
    try:
        # Se for um update (produto existente)
        if st.session_state["produto_existente"] and st.session_state["produto_id"]:
            res = db.table("produtos").update(payload).eq("id", st.session_state["produto_id"]).execute()
        else:
            # Caso contrário, insere um novo
            res = db.table("produtos").insert(payload).execute()

        if res and hasattr(res, 'data') and res.data:
            if not silencioso:
                st.success(f"🎉 **{payload.get('nome')}** salvo com sucesso!")
                st.balloons()
                time.sleep(1)
                
                # Reseta o fluxo de estados pós inserção com sucesso
                st.session_state[_K_CODIGO] = ""
                st.session_state[_K_BUSCADO] = ""
                st.session_state["status_busca"] = {}
                st.session_state["produto_existente"] = False
                st.session_state["produto_id"] = None
                
                for k in FORM_KEYS:
                    if k in st.session_state:
                        del st.session_state[k]
                st.session_state[_K_FORM_ID] += 1
                st.rerun()
            return True
        return False
    except Exception as e:
        msg = str(e).lower()
        if silencioso and any(w in msg for w in ("column", "does not exist", "undefined")):
            return False
        if "duplicate" in msg or "unique" in msg:
            st.warning("⚠️ Um produto com este código de barras já se encontra registrado.")
            return True
        if not silencioso:
            st.error(f"❌ Falha ao salvar no Supabase: {e}")
        return False

def _decodificar_imagem(imagem_bytes: bytes) -> str:
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode as pyzbar_decode
        import io
        img = Image.open(io.BytesIO(imagem_bytes))
        codigos = pyzbar_decode(img)
        return codigos[0].data.decode("utf-8").strip() if codigos else ""
    except ImportError:
        return "IMPORT_ERROR"
    except Exception:
        return ""
