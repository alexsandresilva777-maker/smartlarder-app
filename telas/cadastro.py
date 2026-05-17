# -*- coding: utf-8 -*-
import streamlit as st
import datetime

def DB_buscar_produto_por_codigo(codigo):
    """Busca um produto no Supabase tentando as variações comuns de nome de coluna"""
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    if not db or not codigo:
        return None
    
    # Tentativa 1: Coluna 'codigo_barras'
    try:
        res = db.table("produtos").select("*").eq("empresa_id", empresa_id).eq("codigo_barras", str(codigo)).execute()
        if res.data: return res.data[0]
    except:
        pass

    # Tentativa 2: Coluna 'codigo'
    try:
        res = db.table("produtos").select("*").eq("empresa_id", empresa_id).eq("codigo", str(codigo)).execute()
        if res.data: return res.data[0]
    except:
        pass
        
    return None

def DB_listar_fornecedores_cadastro():
    """Busca fornecedores para o selectbox. Retorna fallback caso a tabela não exista."""
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    if not db:
        return ["Padrão / Geral"]
    try:
        res = db.table("fornecedores").select("nome").eq("empresa_id", empresa_id).execute()
        if res.data:
            return [f["nome"] for f in res.data]
        return ["Padrão / Geral"]
    except:
        return ["Padrão / Geral", "Itambé Distribuidora", "Ambev S/A", "Nestlé Atacado"]

def DB_salvar_novo_produto(dados):
    """Insere um novo produto adaptando o nome da coluna de código de barras se necessário"""
    db = st.session_state.get("db")
    if not db:
        return False, "Banco de dados inacessível."
    
    try:
        db.table("produtos").insert(dados).execute()
        return True, "Produto cadastrado com sucesso!"
    except Exception as e:
        msg_erro = str(e)
        if "codigo_barras" in msg_erro or "42703" in msg_erro:
            try:
                dados_adaptados = dados.copy()
                if "codigo_barras" in dados_adaptados:
                    dados_adaptados["codigo"] = dados_adaptados.pop("codigo_barras")
                db.table("produtos").insert(dados_adaptados).execute()
                return True, "Produto cadastrado com sucesso! (Mapeamento adaptado)"
            except Exception as err_interno:
                return False, f"Erro ao salvar no banco (Adaptado): {err_interno}"
        return False, f"Erro ao salvar no banco: {e}"

def show_cadastro():
    st.markdown("## ➕ Cadastrar Novo Produto")
    st.markdown("---")
    
    st.markdown("### 1️⃣ Identificação do Produto")
    
    # Ativador da Câmera
    usar_camera = st.checkbox("📸 Acionar Scanner (Câmera do Celular/PC)", key="scanner_camera")
    
    if usar_camera:
        img_file = st.camera_input("Posicione o código de barras na câmera")
        if img_file:
            st.info("📋 Imagem obtida com sucesso. Digite o número correspondente no campo abaixo para validar.")
    
    # Campo de digitação sempre visível e persistente
    c_codigo = st.text_input("Digite ou escaneie o código de barras (EAN)", key="cadastro_cod_barras")
    
    # BOTÃO BUSCAR SEMPRE FIXO NA TELA
    btn_buscar = st.button("🔍 Verificar Código no Banco", type="secondary", use_container_width=True)
    
    # Lógica de verificação persistente baseada no clique do botão ou valor existente
    if c_codigo.strip():
        if btn_buscar or st.session_state.get("ultimo_codigo_checado") == c_codigo.strip():
            st.session_state["ultimo_codigo_checado"] = c_codigo.strip()
            
            produto_existente = DB_buscar_produto_por_codigo(c_codigo.strip())
            if produto_existente:
                st.warning(f"📦 Atenção: O produto **{produto_existente.get('nome')}** já está cadastrado!")
                with st.expander("Visualizar dados do produto existente"):
                    st.json(produto_existente)
            else:
                st.success("✅ Código livre para novo cadastro!")

    st.markdown("---")
    st.markdown("### 2️⃣ Dados do Produto")
    lista_fornecedores = DB_listar_fornecedores_cadastro()
    
    with st.form("form_cadastro_produto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            p_nome = st.text_input("Nome do Produto *", placeholder="Ex: Leite Integral Itambé 1L")
            p_categoria = st.selectbox("Categoria *", ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Frios/Laticínios", "Outros"])
            p_fornecedor = st.selectbox("Fornecedor Principal", lista_fornecedores)
            
        with col2:
            p_qtd = st.number_input("Quantidade Inicial em Estoque", min_value=0, value=0, step=1)
            p_validade = st.date_input("Data de Validade (Se houver)", value=datetime.date.today() + datetime.timedelta(days=90))
            p_unidade = st.selectbox("Unidade de Medida", ["Unidade (Un)", "Quilo (Kg)", "Litro (L)", "Caixa (Cx)", "Pacote (Pct)"])
            
        st.markdown("<small>* Campos obrigatórios</small>", unsafe_allow_html=True)
        
        btn_salvar = st.form_submit_button("💾 Salvar Produto no Estoque", type="primary", use_container_width=True)
        
        if btn_salvar:
            # Puxa o código atual direto do input text
            codigo_final = st.session_state.get("cadastro_cod_barras", "").strip()
            
            if not p_nome.strip():
                st.error("❌ O nome do produto é obrigatório!")
            elif not codigo_final:
                st.error("❌ É necessário informar um código de barras válido antes de salvar.")
            else:
                novo_produto = {
                    "codigo_barras": str(codigo_final),
                    "nome": str(p_nome.strip()),
                    "categoria": str(p_categoria),
                    "quantidade": int(p_qtd),
                    "validade": str(p_validade),
                    "unidade": str(p_unidade),
                    "fornecedor": str(p_fornecedor),
                    "empresa_id": int(st.session_state.get("empresa_id", 1))
                }
                
                sucesso, mensagem = DB_salvar_novo_produto(novo_produto)
                if sucesso:
                    st.success(f"🎉 {mensagem}")
                    if "ultimo_codigo_checado" in st.session_state:
                        del st.session_state["ultimo_codigo_checado"]
                    st.rerun()
                else:
                    st.error(f"❌ {mensagem}")
