import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SmartLarder - Gestão na Nuvem", layout="wide", page_icon="📈")

# --- CONEXÃO COM GOOGLE SHEETS ---
# O Streamlit busca as credenciais que você colou na aba "Secrets"
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para ler os dados da planilha de forma segura
def carregar_dados():
    try:
        return conn.read(ttl="0s")
    except Exception:
        # Retorna um DataFrame vazio com as colunas corretas se a planilha estiver limpa
        return pd.DataFrame(columns=["Produto", "Categoria", "Vencimento", "Quantidade"])

# --- INTERFACE DO USUÁRIO ---
st.title("🧼 SmartLarder")
st.caption("Sistema de Gestão de Inventário Conectado ao Google Sheets")

# MENU LATERAL
st.sidebar.title("Navegação")
menu = st.sidebar.radio("Ir para:", ["Painel Geral", "Cadastrar Produtos", "Configurar Alertas"])

if menu == "Painel Geral":
    st.header("📊 Visão Geral da Dispensa")
    df = carregar_dados()
    
    if df is not None and not df.empty:
        st.subheader("📦 Itens em Estoque")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Sua dispensa na nuvem está vazia ou a planilha ainda não foi populada.")

elif menu == "Cadastrar Produtos":
    st.header("📝 Adicionar à Dispensa")
    st.write("Preencha os dados abaixo para salvar diretamente na Planilha Google.")
    
    with st.form("form_cadastro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome do Produto (ex: Arroz 5kg)")
            cat = st.selectbox("Categoria", ["Laticínios", "Grãos", "Enlatados", "Limpeza", "Higiene", "Outros"])
        with c2:
            data = st.date_input("Data de Vencimento")
            qtd = st.number_input("Quantidade", min_value=1, step=1)
        
        botao = st.form_submit_button("Registrar Item na Nuvem")
        
        if botao:
            if nome:
                try:
                    # 1. Busca o que já existe lá
                    df_atual = carregar_dados()
                    
                    # 2. Prepara o novo registro
                    novo_item = pd.DataFrame([{
                        "Produto": nome, 
                        "Categoria": cat, 
                        "Vencimento": str(data), 
                        "Quantidade": qtd
                    }])
                    
                    # 3. Junta tudo
                    df_final = pd.concat([df_atual, novo_item], ignore_index=True)
                    
                    # 4. Envia de volta para a planilha (substitua 'Página1' se mudou o nome da aba)
                    conn.update(worksheet="Página1", data=df_final)
                    
                    st.success(f"✅ **{nome}** salvo com sucesso na nuvem!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro de conexão: Verifique se a planilha está como 'Editor' para todos. Detalhe: {e}")
            else:
                st.error("O nome do produto é obrigatório para o cadastro.")

elif menu == "Configurar Alertas":
    st.header("🤖 Inteligência e Automação")
    st.info("Esta funcionalidade está em desenvolvimento para enviar avisos via Telegram/WhatsApp.")
