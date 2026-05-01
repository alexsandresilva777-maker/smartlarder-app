import streamlit as st
from datetime import date
from utilitarios.database import inserir_produto, buscar_por_barcode
from utilitarios.barcode_lookup import buscar_por_ean

CATEGORIAS = ["Alimentos","Bebidas","Limpeza","Higiene","Medicamentos","Outros"]
UNIDADES   = ["un","kg","g","L","ml","cx","fardo","pct","dz"]

def _is_ean(codigo: str) -> bool:
    c = str(codigo).strip()
    return c.isdigit() and len(c) in (8, 12, 13)

def _badge(txt, bg, cor):
    return (f"<span style='background:{bg};color:{cor};padding:2px 10px;"
            f"border-radius:20px;font-size:11px;font-weight:600;'>{txt}</span>")

def show_cadastro():
    st.markdown("## ➕ Cadastrar Produto")

    # ── Estado da sessão ──────────────────────────────────
    for k, v in [("lk_result",None),("lk_codigo",""),
                 ("lk_done",False),("lk_manual",False),("show_cam",False)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Bloco de busca ────────────────────────────────────
    st.info(
        "🔍 **Consulta Automática:** EAN com 8/12/13 dígitos → busca online automática. "
        "Código curto (ex: **001**) → cadastro manual (feira, hortifrúti)."
    )

    col_ean, col_buscar, col_cam = st.columns([3, 1, 1])
    with col_ean:
        codigo_input = st.text_input(
            "Código EAN / Código Manual",
            value=st.session_state.lk_codigo,
            placeholder="Ex: 7891000055084  ou  001",
            key="campo_ean",
        )
    with col_buscar:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        btn_buscar = st.button("🔍 Buscar", type="primary", use_container_width=True)
    with col_cam:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("📷 Câmera", use_container_width=True):
            st.session_state.show_cam = not st.session_state.show_cam
            st.rerun()

    # ── Câmera nativa ─────────────────────────────────────
    if st.session_state.show_cam:
        with st.expander("📷 Scanner de câmera", expanded=True):
            st.info("Aponte a câmera para o código. Após capturar, copie o número e cole no campo acima.")
            img = st.camera_input("Capturar código de barras", key="cam_snap")
            if img:
                try:
                    from PIL import Image
                    from pyzbar import pyzbar
                    import io
                    pil     = Image.open(io.BytesIO(img.getvalue()))
                    codigos = pyzbar.decode(pil)
                    if codigos:
                        detected = codigos[0].data.decode("utf-8")
                        st.session_state.lk_codigo = detected
                        st.success(f"✅ Código detectado: **{detected}** — clique em 🔍 Buscar")
                        st.rerun()
                    else:
                        st.warning("Código não detectado. Tente aproximar mais ou digitar manualmente.")
                except ImportError:
                    st.info("Para decodificação automática: `pip install pyzbar Pillow`")
                except Exception:
                    st.warning("Não foi possível decodificar. Digite o código manualmente.")

    # ── Processar busca ───────────────────────────────────
    if btn_buscar and codigo_input.strip():
        codigo = codigo_input.strip()
        st.session_state.lk_codigo = codigo
        st.session_state.lk_result = None
        st.session_state.lk_done   = False
        st.session_state.lk_manual = False

        existente = buscar_por_barcode(codigo)
        if existente:
            st.warning(
                f"⚠️ Código já cadastrado como **{existente['nome']}**. "
                "Você pode cadastrar novamente com validade/lote diferente."
            )

        if _is_ean(codigo):
            with st.spinner(f"🌐 Consultando base global para **{codigo}**..."):
                resultado = buscar_por_ean(codigo)
            if resultado:
                st.session_state.lk_result = resultado
                st.session_state.lk_done   = True
            else:
                st.session_state.lk_done   = True
                st.session_state.lk_manual = True
                st.warning("⚠️ Produto não encontrado nas bases públicas. Preencha manualmente.")
        else:
            st.session_state.lk_done   = True
            st.session_state.lk_manual = True
            st.info(f"📝 Código **{codigo}** identificado como código manual. Preencha os dados abaixo.")

    # ── Card do produto encontrado ────────────────────────
    res = st.session_state.lk_result
    modo_rapido = bool(res)

    if res:
        ns   = res.get("nutriscore","")
        nsc  = {"A":"#2d6a4f","B":"#52b788","C":"#f0a500","D":"#e67e22","E":"#e74c3c"}.get(ns,"#888")
        nsbg = {"A":"#e8f5e9","B":"#f0faf2","C":"#fff8e1","D":"#fff3cd","E":"#fde8e8"}.get(ns,"#f5f5f5")

        col_img, col_info = st.columns([1, 5])
        with col_img:
            if res.get("imagem_url"):
                st.image(res["imagem_url"], width=88)
            else:
                st.markdown(
                    "<div style='width:88px;height:88px;background:#e8f5e9;"
                    "border-radius:12px;display:flex;align-items:center;"
                    "justify-content:center;font-size:34px;border:1px solid #c8e6c9;'>📦</div>",
                    unsafe_allow_html=True,
                )
        with col_info:
            badges = " ".join(filter(None, [
                _badge("✅ Encontrado","#e8f5e9","#1a3a2a"),
                _badge(res["fonte"],"#eef2ff","#3730a3") if res.get("fonte") else "",
                _badge(f"Nutri-Score {ns}", nsbg, nsc) if ns else "",
            ]))
            marca_txt = f"🏷️ <b>{res['marca']}</b> &nbsp;" if res.get("marca") else ""
            emb_txt   = f"📦 {res['quantidade_embalagem']} &nbsp;" if res.get("quantidade_embalagem") else ""
            st.markdown(
                f"""<div style='background:#fafdfb;border:1.5px solid #95d5b2;
                    border-radius:12px;padding:14px 18px;'>
                  <div style='display:flex;align-items:center;gap:8px;
                              flex-wrap:wrap;margin-bottom:6px;'>
                    <span style='font-size:1.04rem;font-weight:700;color:#0f2318;'>{res['nome']}</span>
                    {badges}
                  </div>
                  <div style='font-size:0.82rem;color:#5a7a6a;'>
                    {marca_txt}{emb_txt}🗂️ {res['categoria']}
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.success("⚡ **Modo Rápido** — Dados preenchidos automaticamente. "
                   "Informe apenas **validade** e **quantidade**.")

    # ── Formulário ────────────────────────────────────────
    st.markdown("---")
    pf = res or {}

    with st.form("form_cad_v31", clear_on_submit=True):

        c1, c2 = st.columns([3, 2])
        with c1:
            nome = st.text_input(
                "Nome do Produto *",
                value=pf.get("nome",""),
                placeholder="Ex: Arroz Tio João 5kg",
                disabled=modo_rapido,
            )
        with c2:
            codigo_barras = st.text_input(
                "Código de Barras",
                value=st.session_state.lk_codigo or "",
                placeholder="EAN ou código manual",
            )

        # Destaque para campos obrigatórios
        st.markdown("**📅 Campos obrigatórios**")
        v1, v2, v3 = st.columns(3)
        with v1:
            validade   = st.date_input("Data de Validade *",
                                       value=date.today(), min_value=date(2000,1,1))
        with v2:
            quantidade = st.number_input("Quantidade *",
                                         min_value=0.01, step=1.0,
                                         value=1.0, format="%.2f")
        with v3:
            un_idx = 0
            emb = pf.get("quantidade_embalagem","")
            if emb:
                for i, u in enumerate(UNIDADES):
                    if u.lower() in emb.lower():
                        un_idx = i; break
            unidade = st.selectbox("Unidade", UNIDADES, index=un_idx)

        c3, c4 = st.columns(2)
        with c3:
            cat_val = pf.get("categoria","Alimentos")
            cat_idx = CATEGORIAS.index(cat_val) if cat_val in CATEGORIAS else 0
            categoria = st.selectbox("Categoria *", CATEGORIAS,
                                     index=cat_idx, disabled=modo_rapido)
        with c4:
            fornecedor = st.text_input("Fornecedor / Marca",
                                       value=pf.get("fornecedor",""),
                                       placeholder="Ex: Nestlé, Distribuidor X",
                                       disabled=modo_rapido)

        c5, c6, c7 = st.columns(3)
        with c5:
            preco = st.number_input("Preço de Custo (R$)",
                                    min_value=0.0, step=0.01, format="%.2f")
        with c6:
            estoque_min = st.number_input(
                "Estoque Mínimo",
                min_value=0.0, step=1.0, value=0.0, format="%.1f",
                help="Sistema alerta quando estoque cair abaixo deste valor",
            )
        with c7:
            lote = st.text_input("Lote", placeholder="Ex: L2025001")

        c8, c9 = st.columns(2)
        with c8:
            localizacao = st.text_input("Localização", placeholder="Ex: Prateleira A3")
        with c9:
            obs = st.text_input("Observações", placeholder="Informação extra...")

        bs1, bs2, _ = st.columns([2, 1, 2])
        with bs1:
            submitted = st.form_submit_button("💾 Cadastrar Produto",
                                              type="primary", use_container_width=True)
        with bs2:
            limpar = st.form_submit_button("🔄 Limpar", use_container_width=True)

    # ── Pós-form ──────────────────────────────────────────
    if limpar:
        st.session_state.lk_result = None
        st.session_state.lk_codigo = ""
        st.session_state.lk_done   = False
        st.session_state.lk_manual = False
        st.rerun()

    if submitted:
        erros = []
        if not nome.strip():
            erros.append("Nome do produto é obrigatório.")
        if quantidade <= 0:
            erros.append("Quantidade deve ser maior que zero.")
        for e in erros:
            st.error(f"❌ {e}")

        if not erros:
            dados = dict(
                codigo_barras  = codigo_barras.strip() or None,
                nome           = nome.strip(),
                categoria      = categoria,
                quantidade     = quantidade,
                unidade        = unidade,
                validade       = str(validade),
                lote           = lote.strip() or None,
                fornecedor     = fornecedor.strip() or None,
                localizacao    = localizacao.strip() or None,
                preco_custo    = preco if preco > 0 else 0.0,
                estoque_minimo = estoque_min,
                observacoes    = obs.strip() or None,
            )
            try:
                inserir_produto(dados, st.session_state.get("username",""))
                st.session_state.lk_result = None
                st.session_state.lk_codigo = ""
                st.session_state.lk_done   = False
                st.session_state.lk_manual = False
                st.success(f"✅ **{nome.strip()}** cadastrado com sucesso!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    with st.expander("ℹ️ Como usar leitor de código de barras USB/Bluetooth"):
        st.markdown("""
        **Leitores USB ou Bluetooth** (pistola) funcionam como teclado:
        1. Clique no campo **Código EAN** para focar
        2. Aponte o leitor → código inserido automaticamente
        3. Clique **🔍 Buscar** → nome, marca e categoria preenchidos
        4. Digite apenas **validade** e **quantidade** → Salvar

        **EAN 8/12/13 dígitos** → consulta online automática  
        **Código curto (001, A1...)** → cadastro manual (feiras, itens sem código)

        > Para decodificação automática via câmera: `pip install pyzbar Pillow`
        """)
