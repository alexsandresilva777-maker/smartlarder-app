import streamlit as st
from datetime import date
from utils.database import inserir_produto, buscar_por_barcode
from utils.barcode_lookup import buscar_por_ean

CATEGORIAS = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Medicamentos", "Outros"]
UNIDADES = ["un", "kg", "g", "L", "ml", "cx", "fardo", "pct", "dz"]

def _is_ean(codigo: str) -> bool:
    c = str(codigo).strip()
    return c.isdigit() and len(c) in (8, 12, 13)

def _badge(txt, bg, cor):
    return (f'<span style="background:{bg};color:{cor};padding:2px 10px;'
            f'border-radius:20px;font-size:11px;font-weight:600;">{txt}</span>')

def show_cadastro():
    user_id = st.session_state.get("user_id", 1)
    st.markdown("## ➕ Cadastrar Produto")

    # --- Estado da sessão ---
    for k, v in [("lk_result", None), ("lk_codigo", ""),
                 ("lk_done", False), ("lk_manual", False), ("show_cam", False)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # --- Bloco de busca ---
    st.info("🔍 **Consulta Automática:** EAN com 8/12/13 dígitos + busca online automática.")
    
    col_input, col_buscar, col_cam = st.columns([3, 1, 1])
    
    with col_input:
        codigo_input = st.text_input(
            "Digite ou capture o código",
            value=st.session_state.lk_codigo,
            placeholder="Ex: 7891000055084 ou 001",
            key="campo_ean"
        )
    
    with col_buscar:
        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
        btn_buscar = st.button("🔍 Buscar", type="primary", use_container_width=True)
        
    with col_cam:
        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
        if st.button("📷 Câmera", use_container_width=True):
            st.session_state.show_cam = not st.session_state.show_cam
            st.rerun()

    # --- Câmera nativa ---
    if st.session_state.show_cam:
        with st.expander("📷 Scanner de câmera", expanded=True):
            st.info("Aponte a câmera para o código. Após capturar, clique em Buscar.")
            img = st.camera_input("Capturar código de barras", key="cam_snap")
            if img:
                try:
                    from PIL import Image, ImageOps
                    from pyzbar import pyzbar
                    import io
                    
                    # Processamento e Otimização para celular
                    pil = Image.open(io.BytesIO(img.getvalue()))
                    pil = ImageOps.grayscale(pil)
                    pil = ImageOps.autocontrast(pil)
                    
                    codigos = pyzbar.decode(pil)
                    if codigos:
                        detected = codigos[0].data.decode("utf-8")
                        st.session_state.lk_codigo = detected
                        st.success(f"✅ Código detectado: **{detected}** – clique em 🔍 Buscar")
                        st.rerun()
                    else:
                        st.warning("Código não detectado. Tente aproximar mais ou digitar manualmente.")
                except Exception:
                    st.warning("Não foi possível decodificar. Digite o código manualmente.")

    # --- LÓGICA DE BUSCA AUTOMÁTICA ---
    detalhes_produto = {}
    codigo_para_busca = st.session_state.get("lk_codigo", "")

    if codigo_para_busca:
        from utils.database import buscar_produto_por_codigo
        res_local = buscar_produto_por_codigo(codigo_para_busca, st.session_state.get("empresa_id"))
        if res_local:
            detalhes_produto = res_local

    # Processar busca global se o botão for clicado
    if btn_buscar and codigo_input.strip():
        codigo = codigo_input.strip()
        st.session_state.lk_codigo = codigo
        st.session_state.lk_result = None
        
        # 1. Verifica se já existe no seu estoque
        existente = buscar_por_barcode(codigo, user_id)
        if existente:
            st.warning(f"⚠️ Código já cadastrado como **{existente['nome']}**.")
            
        # 2. Busca na base global se for EAN
        if _is_ean(codigo):
            with st.spinner(f"🌐 Consultando base global para **{codigo}**..."):
                resultado = buscar_por_ean(codigo)
                if resultado:
                    st.session_state.lk_result = resultado
                    st.session_state.lk_done = True
                else:
                    st.session_state.lk_done = True
                    st.session_state.lk_manual = True

    # --- Card do produto encontrado ---
    res = st.session_state.lk_result
    modo_rapido = bool(res)

    if res:
        st.success("✨ **Modo Rápido** – Dados preenchidos automaticamente.")
        col_img, col_info = st.columns([1, 5])
        with col_img:
            if res.get("image_url"):
                st.image(res["image_url"], width=88)
            else:
                st.markdown('<div style="width:88px;height:88px;background:#e8f5e9;border-radius:12px;"></div>', unsafe_allow_html=True)
        with col_info:
            st.markdown(f"**{res.get('nome', 'Sem nome')}**")
            st.caption(f"{res.get('categoria', '')} | {res.get('marca', '')}")

    # --- Formulário ---
    st.markdown("---")
    pf = res or {}

    with st.form("form_cad_v32", clear_on_submit=True):
        c1, c2 = st.columns([3, 2])
        with c1:
            # Prioriza nome do banco local, depois da busca global
            nome_sugerido = detalhes_produto.get("nome") or pf.get("nome", "")
            nome = st.text_input(
                "Nome do Produto *",
                value=nome_sugerido,
                placeholder="Ex: Arroz Tio João 5kg",
                disabled=modo_rapido
            )
        with c2:
            codigo_barras = st.text_input(
                "Código de Barras",
                value=st.session_state.lk_codigo,
                placeholder="EAN ou código manual"
            )

        st.markdown("***📋 Campos obrigatórios***")
        v1, v2, v3 = st.columns(3)
        with v1:
            validade = st.date_input("Data de Validade *", value=date.today())
        with v2:
            quantidade = st.number_input("Quantidade *", min_value=0.01, step=1.0, value=1.0)
        with v3:
            un_idx = 0
            emb = pf.get("quantidade_embalagem", "")
            for i, u in enumerate(UNIDADES):
                if u.lower() in str(emb).lower():
                    un_idx = i
                    break
            unidade = st.selectbox("Unidade", UNIDADES, index=un_idx)

        c3, c4 = st.columns(2)
        with c3:
            cat_val = pf.get("categoria", "Alimentos")
            cat_idx = CATEGORIAS.index(cat_val) if cat_val in CATEGORIAS else 0
            categoria = st.selectbox("Categoria *", CATEGORIAS, index=cat_idx, disabled=modo_rapido)
        with c4:
            fornecedor = st.text_input("Fornecedor / Marca", value=pf.get("brand", ""), disabled=modo_rapido)

        c5, c6, c7 = st.columns(3)
        with c5:
            preco = st.number_input("Preço de Custo (R$)", min_value=0.0, step=0.01)
        with c6:
            estoque_min = st.number_input("Estoque Mínimo", min_value=0.0, value=0.0)
        with c7:
            lote = st.text_input("Lote", placeholder="Ex: L2025")

        localizacao = st.text_input("Localização", placeholder="Ex: Prateleira A3")
        obs = st.text_input("Observações")

        bs1, bs2, _ = st.columns([2, 1, 2])
        with bs1:
            submitted = st.form_submit_button("💾 Cadastrar Produto", type="primary", use_container_width=True)
        with bs2:
            limpar = st.form_submit_button("🧹 Limpar", use_container_width=True)

    # --- Lógica de Botões ---
    if limpar:
        st.session_state.lk_result = None
        st.session_state.lk_codigo = ""
        st.rerun()

    if submitted:
        if not nome.strip():
            st.error("❌ O nome do produto é obrigatório.")
        else:
            dados = {
                "codigo_barras": codigo_barras.strip() or None,
                "nome": nome.strip(),
                "categoria": categoria,
                "quantidade": quantidade,
                "unidade": unidade,
                "validade": str(validade),
                "lote": lote.strip() or None,
                "fornecedor": fornecedor.strip() or None,
                "localizacao": localizacao.strip() or None,
                "preco_custo": preco if preco > 0 else 0.0,
                "estoque_minimo": estoque_min,
                "observacoes": obs.strip() or None
            }
            try:
                inserir_produto(dados, user_id, st.session_state.get("username", ""))
                st.success(f"✅ **{nome}** cadastrado com sucesso!")
                st.balloons()
                # Limpa busca após sucesso
                st.session_state.lk_result = None
                st.session_state.lk_codigo = ""
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

if __name__ == "__main__":
    show_cadastro()
