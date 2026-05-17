# -*- coding: utf-8 -*-
"""
telas/cadastro.py — SmartLarder Pro
Busca comercial externa (EAN) com autopreenchimento automático e tratamento numérico rígido.
"""
import streamlit as st
import requests
from datetime import date

# Lista de categorias oficiais do seu sistema
CATEGORIAS = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Medicamentos", "Embalagens", "Outros"]
UNIDADES = ["un", "kg", "g", "L", "ml", "cx", "fardo", "pct", "dz"]

# Chaves de memória do Streamlit
_K_CODIGO   = "cad_codigo"
_K_RESULTADO = "cad_resultado"  # Guarda os dados retornados da internet/banco
_K_CAM_ON   = "cad_cam_on"

def _init_state():
    if _K_CODIGO not in st.session_state: st.session_state[_K_CODIGO] = ""
    if _K_RESULTADO not in st.session_state: st.session_state[_K_RESULTADO] = {}
    if _K_CAM_ON not in st.session_state: st.session_state[_K_CAM_ON] = False

def _consultar_banco_mundial_ean(codigo: str) -> dict:
    """
    Consulta bases de dados comerciais e abertas na internet para capturar 
    qualquer tipo de produto do mercado brasileiro (Alimentos, Limpeza, Higiene, etc.)
    """
    codigo = "".join(filter(str.isdigit, codigo.strip())) # Mantém apenas números
    if not codigo:
        return {}

    try:
        url_off = f"https://world.openfoodfacts.org/api/v0/product/{codigo}.json"
        r = requests.get(url_off, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == 1:
                p = data.get("product", {})
                nome = p.get("product_name_pt") or p.get("product_name") or p.get("generic_name_pt") or ""
                marca = p.get("brands") or p.get("manufacturers") or ""
                
                # Inteligência de Categoria Computada
                cats = str(p.get("categories", "")).lower()
                categoria_detectada = "Alimentos"
                if any(w in cats for w in ("limpeza", "detergente", "sabão", "cleaning", "lavar")):
                    categoria_detectada = "Limpeza"
                elif any(w in cats for w in ("higiene", "shampoo", "sabonete", "cosmetics", "creme", "dental")):
                    categoria_detectada = "Higiene"
                elif any(w in cats for w in ("bebida", "beverage", "refrigerante", "suco", "cerveja", "vinho")):
                    categoria_detectada = "Bebidas"
                elif any(w in cats for w in ("remedio", "medicamento", "pharma", "comprimido")):
                    categoria_detectada = "Medicamentos"
                
                if nome:
                    return {
                        "nome": nome.strip().upper(),
                        "categoria": categoria_detectada,
                        "fornecedor": marca.split(",")[0].strip().upper() if marca else "PADRÃO / GERAL"
                    }
    except Exception:
        pass
    return {}

def _decodificar_imagem(imagem_bytes) -> str:
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode as pyzbar_decode
        import io
        img = Image.open(io.BytesIO(imagem_bytes))
        codigos = pyzbar_decode(img)
        if codigos:
            return codigos[0].data.decode("utf-8").strip()
        return ""
    except Exception:
        return ""

def _disparar_busca(codigo: str):
    if not codigo.strip():
        return
    st.session_state[_K_CODIGO] = codigo.strip()
    dados_da_internet = _consultar_banco_mundial_ean(codigo.strip())
    if dados_da_internet:
        st.session_state[_K_RESULTADO] = {**dados_da_internet, "_status": "encontrado"}
    else:
        st.session_state[_K_RESULTADO] = {"_status": "nao_encontrado"}

# ── RENDERIZAÇÃO DA TELA ──────────────────────────────────────────────────────
def show_cadastro():
    _init_state()

    db         = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    user_id    = st.session_state.get("user_id", 1)
    username   = st.session_state.get("username", "")

    st.markdown("## ➕ Cadastrar Produto por EAN")
    st.markdown("---")

    # Entrada do Código de Barras
    st.markdown("### 1️⃣ Escanear ou Digitar Código")
    
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        codigo_atual = st.text_input(
            "Código de Barras (EAN)",
            value=st.session_state[_K_CODIGO],
            placeholder="Aperte Enter ao digitar ou use o leitor físico",
            key="campo_ean_real",
            label_visibility="collapsed"
        )
    with col_btn:
        btn_forcar = st.button("🔍 Buscar", use_container_width=True)

    if codigo_atual and codigo_atual != st.session_state[_K_CODIGO]:
        _disparar_busca(codigo_atual)
        st.rerun()
        
    if btn_forcar and codigo_atual:
        _disparar_busca(codigo_atual)
        st.rerun()

    usar_cam = st.checkbox("📸 Ligar câmera do dispositivo para escanear", value=st.session_state[_K_CAM_ON])
    st.session_state[_K_CAM_ON] = usar_cam

    if usar_cam:
        foto = st.camera_input("Centralize o código de barras na linha da câmera", key="captura_camera")
        if foto:
            codigo_capturado = _decodificar_imagem(foto.getvalue())
            if codigo_capturado:
                st.success(f"🎉 Código identificado: {codigo_capturado}")
                _disparar_busca(codigo_capturado)
                st.session_state[_K_CAM_ON] = False
                st.rerun()

    res_atual = st.session_state[_K_RESULTADO]
    status_busca = res_atual.get("_status", "")

    if status_busca == "encontrado":
        st.success(f"⚡ **Autopreenchimento Ativo:** O produto **'{res_atual.get('nome')}'** foi localizado com sucesso!")

    st.markdown("---")
    st.markdown("### 2️⃣ Informações de Cadastro")

    val_nome  = res_atual.get("nome", "")
    val_cat   = res_atual.get("categoria", "Alimentos")
    val_marca = res_atual.get("fornecedor", "PADRÃO / GERAL")

    idx_cat = CATEGORIAS.index(val_cat) if val_cat in CATEGORIAS else 0

    with st.form("formulario_cadastro_smart", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            prod_nome = st.text_input("Nome do Produto *", value=val_nome)
            prod_cat  = st.selectbox("Categoria *", CATEGORIAS, index=idx_cat)
            prod_fab  = st.text_input("Fornecedor / Marca", value=val_marca)
            prod_lote = st.text_input("Número do Lote (Opcional)")
            
        with c2:
            prod_qtd  = st.number_input("Quantidade em Estoque *", min_value=0.0, step=1.0, value=1.0, format="%.2f")
            prod_un   = st.selectbox("Unidade de Medida", UNIDADES, index=0)
            prod_val  = st.date_input("Data de Validade *", value=date.today())
            prod_cost = st.number_input("Preço de Custo (R$)", min_value=0.0, step=0.01, format="%.2f")

        c3, c4 = st.columns(2)
        with c3:
            prod_min = st.number_input("Estoque Mínimo de Alerta", min_value=0.0, step=1.0, value=0.0, format="%.1f")
        with c4:
            prod_loc = st.text_input("Localização física no Almoxarifado")

        prod_obs = st.text_area("Observações Gerais")

        st.markdown("<br>", unsafe_allow_html=True)
        btn_salvar = st.form_submit_button("💾 Confirmar e Registrar no Supabase", type="primary", use_container_width=True)

    if btn_salvar:
        if not prod_nome.strip():
            st.error("❌ O nome do produto precisa estar preenchido!")
        elif prod_qtd < 0:
            st.error("❌ A quantidade inicial não pode ser negativa!")
        else:
            if not db:
                st.error("❌ Banco de dados local inacessível.")
                return

            payload = {
                "nome":            prod_nome.strip().upper(),
                "categoria":       prod_cat,
                "quantidade":      float(prod_qtd),
                "unidade":         prod_un,
                "validade":        str(prod_val),
                "lote":            prod_lote.strip() or None,
                "fornecedor":      prod_fab.strip() or "PADRÃO / GERAL",
                "localizacao":     prod_loc.strip() or "DISPENSA",
                "preco_custo":     float(prod_cost),
                "estoque_minimo":  float(prod_min),
                "observacoes":     prod_obs.strip() or None,
                "empresa_id":      int(empresa_id),
                "user_id":         int(user_id),
                "criado_por":      str(username)
            }

            # Envio seguro tentando mapear o nome correto da coluna de código
            for col_nome in ("codigo_barras", "codigo"):
                try:
                    envio = payload.copy()
                    if st.session_state[_K_CODIGO]:
                        envio[col_nome] = st.session_state[_K_CODIGO]
                    
                    res = db.table("produtos").insert(envio).execute()
                    if res.data:
                        st.success(f"🎉 Produto registrado com sucesso no estoque!")
                        st.balloons()
                        st.session_state[_K_CODIGO] = ""
                        st.session_state[_K_RESULTADO] = {}
                        st.rerun()
                        return
                except Exception:
                    continue
            
            st.error("❌ Não foi possível estruturar o salvamento. Verifique os campos do banco.")
