# -*- coding: utf-8 -*-
import streamlit as st
import datetime

def DB_buscar_produto_por_codigo(codigo):
    """Busca um produto direto no Supabase pelo código de barras de forma segura"""
    db = st.session_state.get("db")
    empresa_id = st.session_state.get("empresa_id", 1)
    if not db or not codigo:
        return None
    try:
        res = db.table("produtos").select("*").eq("empresa_id", empresa_id).eq("codigo_barras", str(codigo)).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.warning(f"Aviso na busca por código: {e}")
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
        # Fallback seguro caso a tabela de fornecedores ainda não tenha sido criada no Supabase
        return ["Padrão / Geral", "Itambé Distribuidora", "Ambev S/A", "Nestlé Atacado"]

def DB_salvar_novo_produto(dados):
    """Insere um novo produto no banco de dados Supabase"""
    db = st.session_state.get("db")
    if not db:
        return False, "Banco de dados inacessível."
    try:
        db.table("produtos").insert(dados).execute()
        return True, "Produto cadastrado com sucesso!"
    except Exception as e:
        return False, f"Erro ao salvar no banco: {e}"

def show_cadastro():
    st.markdown("## ➕ Cadastrar Novo Produto")
    st.markdown("---")
    
    # Seção 1: Busca/Verificação prévia do código de barras
    st.markdown("### 1️⃣ Verificação de Código de Barras")
    c_codigo = st.text_input("Digite ou escaneie o código de barras (EAN)", key="cadastro_cod_barras")
    
    produto_existente = None
    if c_codigo.strip():
        produto_existente = DB_buscar_produto_por_codigo(c_codigo.strip())
        if produto_existente:
            st.warning(f"📦 Atenção: O produto **{produto_existente.get('nome')}** já está cadastrado com este código de barras!")
            with st.expander("Visualizar dados do produto existente"):
                st.json(produto_existente)
            return

    st.markdown("### 2️⃣ Dados do Produto")
    
    # Carrega a lista de fornecedores de forma segura
    lista_fornecedores = DB_listar_fornecedores_cadastro()
    
    # Formulário do Streamlit com botão de envio obrigatório no final
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
        
        # Botão de envio do formulário (Submit)
        btn_salvar = st.form_submit_button("💾 Salvar Produto no Estoque", type="primary", use_container_width=True)
        
        if btn_salvar:
            if not p_nome.strip():
                st.error("❌ O nome do produto é obrigatório!")
            elif not c_codigo.strip():
                st.error("❌ É necessário informar um código de barras válido antes de salvar.")
            else:
                # Monta a estrutura de dados exatamente como o banco espera
                novo_produto = {
                    "codigo_barras": str(c_codigo.strip()),
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
                else:
                    st.error(f"❌ {mensagem}")
