# -*- coding: utf-8 -*-
"""
telas/cadastro.py — SmartLarder Pro
Cadastro de produto com:
- Busca automática por EAN (digitação, USB, Bluetooth)
- Câmera via pyzbar + PIL
- Fallback Open Food Facts
- Persistência via Supabase (st.session_state["db"])
"""
import streamlit as st
import requests
from datetime import date

# ── Constantes ────────────────────────────────────────────────────────────────
CATEGORIAS = [
    "Alimentos", "Bebidas", "Limpeza", "Higiene",
    "Medicamentos", "Embalagens", "Outros",
]
UNIDADES = ["un", "kg", "g", "L", "ml", "cx", "fardo", "pct", "dz"]

_OFF_URL = "https://world.openfoodfacts.org/api/v0/product/{}.json"

# Chaves do session_state usadas nesta tela
_K_CODIGO   = "cad_codigo"
_K_RESULTADO = "cad_resultado"   # dict com dados do produto encontrado ou {}
_K_CAM_ON   = "cad_cam_on"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _init_state():
    for k, v in [(_K_CODIGO, ""), (_K_RESULTADO, {}), (_K_CAM_ON, False)]:
        if k not in st.session_state:
            st.session_state[k] = v


def _buscar_supabase(db, empresa_id: int, codigo: str) -> dict:
    """
    Busca produto no Supabase pelo código de barras.
    Tenta 'codigo_barras' primeiro; se falhar por coluna inexistente, tenta 'codigo'.
    Retorna {} se não encontrar ou em qualquer erro.
    """
    if not db or not codigo:
        return {}

    for coluna in ("codigo_barras", "codigo"):
        try:
            res = (
                db.table("produtos")
                .select("*")
                .eq(coluna, codigo)
                .eq("empresa_id", empresa_id)
                .limit(1)
                .execute()
            )
            if res.data:
                # Normaliza o retorno para o formulário usar 'codigo_barras' internamente
                prod = res.data[0]
                if coluna == "codigo" and "codigo" in prod:
                    prod["codigo_barras"] = prod["codigo"]
                return prod
        except Exception as e:
            msg = str(e).lower()
            if any(w in msg for w in ("column", "does not exist", "undefined column")):
                continue
            return {}

    return {}


def _buscar_off(codigo: str) -> dict:
    """Consulta Open Food Facts. Retorna dict com 'nome' e 'categoria' ou {}."""
    try:
        r = requests.get(_OFF_URL.format(codigo), timeout=5)
        if r.status_code != 200:
            return {}
        data = r.json()
        if data.get("status") != 1:
            return {}
        produto = data.get("product", {})
        nome = (
            produto.get("product_name_pt")
            or produto.get("product_name")
            or ""
        ).strip()
        if not nome:
            return {}
        
        cats_raw = produto.get("categories", "")
        categoria = "Alimentos"
        if cats_raw:
            partes = [p.strip() for p in cats_raw.replace(",", ";").split(";") if p.strip()]
            if partes:
                ultima = partes[-1].split(":")[-1].replace("-", " ").strip().title()
                for cat in CATEGORIAS:
                    if cat.lower() in ultima.lower():
                        categoria = cat
                        break
        return {"nome": nome, "categoria": categoria}
    except Exception:
        return {}


def _decodificar_imagem(imagem_bytes) -> str:
    """Decodifica código de barras de uma imagem via pyzbar + PIL."""
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode as pyzbar_decode
        import io

        img = Image.open(io.BytesIO(imagem_bytes))
        codigos = pyzbar_decode(img)
        if codigos:
            return codigos[0].data.decode("utf-8").strip()
        return ""
    except ImportError:
        return "IMPORT_ERROR"
    except Exception:
        return ""


def _executar_busca(codigo: str, db, empresa_id: int):
    """Busca completa: Supabase → Open Food Facts."""
    codigo = codigo.strip()
    if not codigo:
        return

    st.session_state[_K_CODIGO] = codigo

    encontrado = _buscar_supabase(db, empresa_id, codigo)
    if encontrado:
        st.session_state[_K_RESULTADO] = {**encontrado, "_fonte": "supabase"}
        return

    off = _buscar_off(codigo)
    if off:
        st.session_state[_K_RESULTADO] = {**off, "_fonte": "off"}
        return

    st.session_state[_K_RESULTADO] = {"_fonte": "manual"}


# ── Tela principal ────────────────────────────────────────────────────────────

def show_cadastro():
    _init_state()

    db         = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    user_id    = st.session_state.get("user_id", 1)
    username   = st.session_state.get("username", "")

    st.markdown("## ➕ Cadastrar Produto")

    # ── Bloco EAN ─────────────────────────────────────────────────────────────
    st.markdown("### 🔍 Código de Barras")

    col_ean, col_btn = st.columns([4, 1])
    with col_ean:
        codigo_input = st.text_input(
            "EAN / Código do produto",
            value=st.session_state[_K_CODIGO],
            placeholder="Digite e aperte Enter, escaneie ou use a câmera",
            key="cad_input_ean",
            label_visibility="collapsed",
        )
    with col_btn:
        btn_buscar = st.button("🔍 Buscar", use_container_width=True, type="primary")

    # Busca acionada por mudança de valor (Enter ou Leitor de Código de barras)
    if codigo_input and codigo_input != st.session_state[_K_CODIGO]:
        _executar_busca(codigo_input, db, empresa_id)
        st.rerun()

    if btn_buscar and codigo_input:
        _executar_busca(codigo_input, db, empresa_id)
        st.rerun()

    # ── Câmera ────────────────────────────────────────────────────────────────
    usar_camera = st.checkbox("📷 Usar câmera para escanear código de barras",
                               value=st.session_state[_K_CAM_ON],
                               key="cad_check_cam")
    st.session_state[_K_CAM_ON] = usar_camera

    if usar_camera:
        imagem = st.camera_input("Aponte para o código de barras", key="cad_camera_snap")
        if imagem:
            resultado_decode = _decodificar_imagem(imagem.getvalue())

            if resultado_decode == "IMPORT_ERROR":
                st.warning(
                    "⚠️ As bibliotecas `pyzbar` e/ou `Pillow` não estão prontas no servidor. "
                    "Certifique-se de incluir `libzbar0` no seu arquivo packages.txt."
                )
            elif resultado_decode:
                st.success(f"✅ Código detectado: **{resultado_decode}**")
                _executar_busca(resultado_decode, db, empresa_id)
                st.session_state[_K_CAM_ON] = False
                st.rerun()
            else:
                st.warning("⚠️ Não foi possível detectar o código. Aproxime mais ou melhore a iluminação.")

    # ── Banner do resultado ───────────────────────────────────────────────────
    resultado = st.session_state[_K_RESULTADO]
    fonte = resultado.get("_fonte", "")

    if fonte == "supabase":
        st.info(f"📦 Produto **{resultado.get('nome','')}** já existente no estoque. Campos preenchidos para nova entrada.")
    elif fonte == "off":
        st.success(f"🌐 Produto encontrado na internet (Open Food Facts): **{resultado.get('nome','')}**.")
    elif fonte == "manual" and st.session_state[_K_CODIGO]:
        st.warning("Produto não encontrado nas bases. Preencha os dados manualmente.")

    st.markdown("---")

    # ── Formulário ────────────────────────────────────────────────────────────
    st.markdown("### 📝 Dados do Produto")

    # Tratamento seguro de conversão numérica para evitar falhas de renderização
    try: pre_preco = float(resultado.get("preco_custo", 0) or 0)
    except: pre_preco = 0.0

    try: pre_estmin = float(resultado.get("estoque_minimo", 0) or 0)
    except: pre_estmin = 0.0

    pre_nome       = resultado.get("nome", "")
    pre_categoria  = resultado.get("categoria", "Alimentos")
    pre_fornecedor = resultado.get("fornecedor", "")
    pre_unidade    = resultado.get("unidade", "un")
    pre_lote       = resultado.get("lote", "")
    pre_local      = resultado.get("localizacao", "")
    pre_obs        = resultado.get("observacoes", "")

    cat_idx = CATEGORIAS.index(pre_categoria) if pre_categoria in CATEGORIAS else 0
    un_idx  = UNIDADES.index(pre_unidade) if pre_unidade in UNIDADES else 0

    with st.form("form_cadastro_produto", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            nome       = st.text_input("Nome do Produto *", value=pre_nome, placeholder="Ex: Arroz Tio João 5kg")
            categoria  = st.selectbox("Categoria *", CATEGORIAS, index=cat_idx)
            fornecedor = st.text_input("Fornecedor / Marca", value=pre_fornecedor, placeholder="Ex: Nestlé")
            lote       = st.text_input("Número do Lote", value=pre_lote, placeholder="Ex: L2025001")
        with c2:
            validade   = st.date_input("Data de Validade *", value=date.today())
            quantidade = st.number_input("Quantidade *", min_value=0.01, step=1.0, value=1.0, format="%.2f")
            unidade    = st.selectbox("Unidade", UNIDADES, index=un_idx)
            preco      = st.number_input("Preço de Custo (R$)", min_value=0.0, step=0.01, value=pre_preco, format="%.2f")

        c3, c4 = st.columns(2)
        with c3:
            estoque_min = st.number_input("Estoque Mínimo", min_value=0.0, step=1.0, value=pre_estmin, format="%.1f")
        with c4:
            localizacao = st.text_input("Localização no Estoque", value=pre_local, placeholder="Ex: Prateleira A3")

        obs = st.text_area("Observações", value=pre_obs, placeholder="Informações adicionais...", height=70)

        submitted = st.form_submit_button("💾 Salvar Produto", type="primary", use_container_width=True)

    if submitted:
        if not nome.strip():
            st.error("❌ Nome do produto é obrigatório.")
        elif quantidade <= 0:
            st.error("❌ Quantidade deve ser maior que zero.")
        else:
            _salvar_produto(
                db=db,
                empresa_id=empresa_id,
                user_id=user_id,
                username=username,
                dados={
                    "nome":           nome.strip(),
                    "categoria":      categoria,
                    "quantidade":     quantidade,
                    "unidade":        unidade,
                    "validade":       str(validade),
                    "lote":           lote.strip() or None,
                    "fornecedor":     fornecedor.strip() or None,
                    "localizacao":    localizacao.strip() or None,
                    "preco_custo":    preco if preco > 0 else None,
                    "estoque_minimo": estoque_min if estoque_min > 0 else None,
                    "observacoes":    obs.strip() or None,
                },
                codigo_val=st.session_state[_K_CODIGO] or None
            )


def _salvar_produto(db, empresa_id, user_id, username, dados: dict, codigo_val):
    """Insere o produto aplicando salvamento defensivo para nomes de coluna (codigo_barras vs codigo)"""
    if not db:
        st.error("❌ Sem conexão com o banco de dados.")
        return

    # Monta o dicionário base
    payload_base = {
        **dados,
        "empresa_id": empresa_id,
        "user_id":    user_id,
        "criado_por": username,
    }
    payload_base = {k: v for k, v in payload_base.items() if v is not None}

    # Tentativa 1: Salvando com a coluna 'codigo_barras'
    try:
        payload = payload_base.copy()
        if codigo_val:
            payload["codigo_barras"] = codigo_val
        res = db.table("produtos").insert(payload).execute()
        if res.data:
            st.success(f"✅ **{dados.get('nome')}** cadastrado com sucesso!")
            st.balloons()
            st.session_state[_K_CODIGO] = ""
            st.session_state[_K_RESULTADO] = {}
            st.rerun()
            return
    except Exception as e:
        msg = str(e).lower()
        # Se o erro não for de coluna inexistente, interrompe e avisa duplicidade
        if not any(w in msg for w in ("column", "does not exist", "undefined column")):
            if "duplicate" in msg or "unique" in msg:
                st.warning("⚠️ Já existe um produto com este código de barras.")
            else:
                st.error(f"❌ Erro ao salvar produto: {e}")
            return

    # Tentativa 2: Salvando com a coluna 'codigo' (Fallback defensivo)
    try:
        payload = payload_base.copy()
        if codigo_val:
            payload["codigo"] = codigo_val
        res = db.table("produtos").insert(payload).execute()
        if res.data:
            st.success(f"✅ **{dados.get('nome')}** cadastrado com sucesso! (Mapeamento Alternativo)")
            st.balloons()
            st.session_state[_K_CODIGO] = ""
            st.session_state[_K_RESULTADO] = {}
            st.rerun()
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "unique" in msg:
            st.warning("⚠️ Já existe um produto com este código de barras.")
        else:
            st.error(f"❌ Erro ao salvar produto no modo adaptado: {e}")
