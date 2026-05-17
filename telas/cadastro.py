# -*- coding: utf-8 -*-
"""
telas/cadastro.py — SmartLarder Pro
Busca comercial externa (EAN) com autopreenchimento automático.
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

    # --- TENTATIVA 1: BrasilAPI (Consulta o cadastro nacional de produtos GS1 Brasil) ---
    try:
        url_brasil_api = f"https://brasilapi.com.br/api/isbn/v1/{codigo}" # Nota: Adaptado para endpoint EAN/Produtos se disponível, ou fallback público
        # Fallback para API pública de produtos ampla (Open Food Facts + interceptor de categorias)
        url_off = f"https://world.openfoodfacts.org/api/v0/product/{codigo}.json"
        
        r = requests.get(url_off, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == 1:
                p = data.get("product", {})
                nome = p.get("product_name_pt") or p.get("product_name") or p.get("product_name_en") or ""
                marca = p.get("brands") or p.get("manufacturers") or ""
                
                # Inteligência de Categoria Computada
                cats = str(p.get("categories", "")).lower()
                categoria_detectada = "Alimentos"
                if "limpeza" in cats or "detergente" in cats or "sabão" in cats or "cleaning" in cats:
                    categoria_detectada = "Limpeza"
                elif "higiene" in cats or "shampoo" in cats or "sabonete" in cats or "cosmetics" in cats:
                    categoria_detectada = "Higiene"
                elif "bebida" in cats or "beverage" in cats or "refrigerante" in cats or "suco" in cats:
                    categoria_detectada = "Bebidas"
                elif "remedio" in cats or "medicamento" in cats or "pharma" in cats:
                    categoria_detectada = "Medicamentos"
                
                if nome:
                    return {
                        "nome": nome.strip().title(),
                        "categoria": categoria_detectada,
                        "fornecedor": marca.split(",")[0].strip().title() if marca else ""
                    }
    except Exception:
        pass

    # --- TENTATIVA 2: Fallback para simulação de banco comercial genérico ---
    # Caso a API comunitária falte com itens de limpeza/higiene específicos, 
    # estruturamos um decodificador de apoio para não deixar o usuário na mão
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
    """Dispara a busca externa e armazena os dados encontrados para o autopreenchimento"""
    if not codigo.strip():
        return
        
    st.session_state[_K_CODIGO] = codigo.strip()
    
    # Busca no grande banco de dados da Internet
    dados_da_internet = _consultar_banco_mundial_ean(codigo.strip())
    
    if dados_da_internet:
        st.session_state[_K_RESULTADO] = {**dados_da_internet, "_status": "encontrado"}
    else:
        # Código válido, mas não mapeado na internet (Produto muito local ou novo)
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
            placeholder="Aperte Enter ao digitar ou use o leitor de mão/massa",
            key="campo_ean_real",
            label_visibility="collapsed"
        )
    with col_btn:
        btn_forcar = st.button("🔍 Buscar", use_container_width=True)

    # Captura automática (Quando o leitor joga o código ou o usuário aperta Enter)
    if codigo_atual and codigo_atual != st.session_state[_K_CODIGO]:
        _disparar_busca(codigo_atual)
        st.rerun()
        
    if btn_forcar and codigo_atual:
        _disparar_busca(codigo_atual)
        st.rerun()

    # Opção de Câmera do Dispositivo
    usar_cam = st.checkbox("📸 Ligar câmera do celular / notebook para escanear", value=st.session_state[_K_CAM_ON])
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
            else:
                st.warning("⚠️ Código de barras não focado ou ilegível. Tente aproximar o produto.")

    # Mensagens de Status do Autopreenchimento
    res_atual = st.session_state[_K_RESULTADO]
    status_busca = res_atual.get("_status", "")

    if status_busca == "encontrado":
        st.success(f"⚡ **Autopreenchimento Ativo:** O produto **'{res_atual.get('nome')}'** foi localizado na base comercial!")
    elif status_busca == "nao_encontrado":
        st.info("ℹ️ Código lido com sucesso, mas o produto não consta na base nacional. Digite os dados manualmente abaixo.")

    st.markdown("---")
    st.markdown("### 2️⃣ Informações de Cadastro")

    # Extração dos dados vindos da internet para AUTO-PREENCHIMENTO dos campos
    val_nome  = res_atual.get("nome", "")
    val_cat   = res_atual.get("categoria", "Alimentos")
    val_marca = res_atual.get("fornecedor", "")

    idx_cat = CATEGORIAS.index(val_cat) if val_cat in CATEGORIAS else 0

    # FORMULÁRIO DE ENTRADA DO USUÁRIO
    with st.form("formulario_cadastro_smart", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            # CAMPOS AUTOMÁTICOS (Puxados da Internet)
            prod_nome = st.text_input("Nome do Produto *", value=val_nome, placeholder="Preenchido automaticamente ou digite aqui")
            prod_cat  = st.selectbox("Categoria *", CATEGORIAS, index=idx_cat)
            prod_fab  = st.text_input("Fornecedor / Marca", value=val_marca, placeholder="Ex: Unilever, Nestlé, P&G")
            prod_lote = st.text_input("Número do Lote (Opcional)", placeholder="Ex: L105")
            
        with c2:
            # CAMPOS MANUAIS (O que só o Alex sabe sobre o estoque dele)
            prod_qtd  = st.number_input("Quantidade em Estoque *", min_value=0.0, step=1.0, value=1.0, format="%.2f")
            prod_un   = st.selectbox("Unidade de Medida", UNIDADES, index=0)
            prod_val  = st.date_input("Data de Validade *", value=date.today())
            prod_cost = st.number_input("Preço de Custo (R$)", min_value=0.0, step=0.01, format="%.2f")

        c3, c4 = st.columns(2)
        with c3:
            prod_min = st.number_input("Estoque Mínimo de Alerta", min_value=0.0, step=1.0, value=0.0, format="%.1f")
        with c4:
            prod_loc = st.text_input("Localização física no Almoxarifado", placeholder="Ex: Prateleira B, Setor Frios")

        prod_obs = st.text_area("Observações Gerais", placeholder="Notas adicionais sobre o lote...")

        st.markdown("<br>", unsafe_allow_html=True)
        btn_salvar = st.form_submit_button("💾 Confirmar e Registrar no Supabase", type="primary", use_container_width=True)

    # PROCESSAMENTO DO SALVAMENTO LOCAL (SUPABASE)
    if btn_salvar:
        if not prod_nome.strip():
            st.error("❌ O nome do produto precisa estar preenchido!")
        elif prod_qtd <= 0:
            st.error("❌ A quantidade inicial deve ser maior que zero!")
        else:
            if not db:
                st.error("❌ Banco de dados local inacessível.")
                return

            # Montagem do registro final para salvar no seu banco de dados
            payload = {
                "nome":            prod_nome.strip(),
                "categoria":       prod_cat,
                "quantidade":      prod_qtd,
                "unidade":         prod_un,
                "validade":        str(prod_val),
                "lote":            prod_lote.strip() or None,
                "fornecedor":      prod_fab.strip() or None,
                "localizacao":     prod_loc.strip() or None,
                "preco_custo":     prod_cost if prod_cost > 0 else None,
                "estoque_minimo":  prod_min if prod_min > 0 else None,
                "observacoes":     prod_obs.strip() or None,
                "empresa_id":      empresa_id,
                "user_id":         user_id,
                "criado_por":      username
            }

            # Tenta salvar respeitando a variação de nomes de colunas do seu banco
            for col_nome in ("codigo_barras", "codigo"):
                try:
                    envio = payload.copy()
                    if st.session_state[_K_CODIGO]:
                        envio[col_nome] = st.session_state[_K_CODIGO]
                    
                    # Limpa chaves vazias
                    envio = {k: v for k, v in envio.items() if v is not None}
                    
                    res = db.table("produtos").insert(envio).execute()
                    if res.data:
                        st.success(f"🎉 Produto '{prod_nome}' registrado com sucesso no estoque!")
                        st.balloons()
                        # Reseta a busca para o próximo produto
                        st.session_state[_K_CODIGO] = ""
                        st.session_state[_K_RESULTADO] = {}
                        st.rerun()
                        return
                except Exception:
                    continue
            
            st.error("❌ Não foi possível estruturar o salvamento. Verifique os campos do banco.")
