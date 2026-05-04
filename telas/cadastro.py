import streamlit as st
from datetime import date
import utils.database as db
from utils.barcode_lookup import buscar_por_ean
from pyzbar.pyzbar import decode
from PIL import Image, ImageOps

CATEGORIAS = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Medicamentos", "Outros"]
UNIDADES = ["un", "kg", "g", "L", "ml", "cx", "fardo", "pct", "dz"]

def show_cadastro():
    user_id = st.session_state.get("user_id", 1)
    st.markdown("## ➕ Cadastrar Produto")

    # --- Inicialização de Estados ---
    if "lk_codigo" not in st.session_state: st.session_state.lk_codigo = ""
    if "dados_busca" not in st.session_state: st.session_state.dados_busca = {}
    if "scanner_ativo" not in st.session_state: st.session_state.scanner_ativo = False

    # --- Scanner de Câmera Inteligente ---
    ativar = st.checkbox("📸 Acionar Scanner (Câmera)", value=st.session_state.scanner_ativo)
    
    if ativar:
        # A key="input_camera" é essencial para podermos limpar a foto depois
        img_file = st.camera_input("Centralize o código de barras", key="input_camera")
        
        if img_file:
            try:
                img = Image.open(img_file)
                img_proc = ImageOps.grayscale(img)
                img_proc = ImageOps.autocontrast(img_proc)
                
                decoded_objects = decode(img_proc)
                
                if decoded_objects:
                    codigo_scan = decoded_objects[0].data.decode("utf-8")
                    
                    # 1. Salva o resultado
                    st.session_state.lk_codigo = codigo_scan
                    
                    # 2. Mata o Loop: Desliga o scanner e limpa o buffer da foto
                    st.session_state.scanner_ativo = False
                    if "input_camera" in st.session_state:
                        del st.session_state["input_camera"]
                    
                    # 3. Busca Automática (Local ou Nuvem)
                    res_local = db.buscar_produto_por_codigo(codigo_scan, user_id)
                    if res_local:
                        st.session_state.dados_busca = dict(res_local)
                    else:
                        res_gb = buscar_por_ean(codigo_scan)
                        st.session_state.dados_busca = res_gb if res_gb else {}
                    
                    st.success(f"🎯 Código Detectado: {codigo_scan}")
                    st.rerun() 
                else:
                    st.warning("⚠️ Código não detectado. Tente ajustar o ângulo ou a luz.")
            except Exception as e:
                st.error(f"Erro no scanner: {e}")

    st.markdown("---")

    # --- Área de Busca Manual ---
    st.markdown("### 🔍 Busca Manual")
    col_input, col_buscar = st.columns([4, 1])
    
    with col_input:
        codigo_digitado = st.text_input(
            "Digite o código de barras", 
            value=st.session_state.lk_codigo,
            key="input_direto"
        )
    
    with col_buscar:
        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
        btn_disparar = st.button("Buscar", type="primary", use_container_width=True)

    if btn_disparar and codigo_digitado:
        st.session_state.lk_codigo = codigo_digitado.strip()
        res_local = db.buscar_produto_por_codigo(st.session_state.lk_codigo, user_id)
        if res_local:
            st.session_state.dados_busca = dict(res_local)
        else:
            with st.spinner("Buscando na nuvem..."):
                res_gb = buscar_por_ean(st.session_state.lk_codigo)
                st.session_state.dados_busca = res_gb if res_gb else {}

    # --- Formulário de Cadastro ---
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
                "lote": "",            
                "fornecedor": info.get("fornecedor", ""),
                "criado_por": st.session_state.get("username", "admin")
            }
            db.inserir_produto(novo_prod, user_id, novo_prod["criado_por"])
            st.success(f"✅ {nome} salvo com sucesso!")
            st.session_state.lk_codigo = ""
            st.session_state.dados_busca = {}
            st.rerun()
