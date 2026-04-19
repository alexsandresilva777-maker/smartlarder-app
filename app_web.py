import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SmartLarder - Nuvem", layout="wide", page_icon="📈")

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para ler os dados da planilha
def carregar_dados():
    return conn.read(ttl="0s") # ttl=0 garante que ele pegue os dados mais frescos

# --- INTERFACE ---
st.title("🧼 SmartLarder")
st.caption("Conectado à Base de Dados em Tempo Real (Google Sheets)")

# MENU LATERAL
st.sidebar.title("Navegação")
menu = st.sidebar.radio("Ir para:", ["Painel Geral", "Cadastrar Produtos", "Configurar Alertas"])

if menu == "Painel Geral":
    st.header("📊 Visão Geral da Dispensa")
    df = carregar_dados()
    
    if df is not None and not df.empty:
        st.subheader("📦 Itens Cadastrados")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Sua dispensa na nuvem está vazia. Comece cadastrando um item!")

elif menu == "Cadastrar Produtos":
    st.header("📝 Adicionar à Dispensa")
    with st.form("form_cadastro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome do Produto")
            cat = st.selectbox("Categoria", ["Laticínios", "Grãos", "Enlatados", "Limpeza", "Higiene", "Outros"])
        with c2:
            data = st.date_input("Data de Vencimento")
            qtd = st.number_input("Quantidade", min_value=1)
        
        botao = st.form_submit_button("Registrar Item na Nuvem")
        
        if botao:
            if nome:
                # Carrega dados atuais
                df_atual = carregar_dados()
                # Cria o novo item
                novo_item = pd.DataFrame([{"Produto": nome, "Categoria": cat, "Vencimento": str(data), "Quantidade": qtd}])
                # Junta e salva
                df_final = pd.concat([df_atual, novo_item], ignore_index=True)
                conn.update(data=df_final)
                st.success(f"**{nome}** salvo com sucesso na sua Planilha Google!")
                st.balloons() # Celebração!
            else:
                st.error("Por favor, digite o nome do produto.")

elif menu == "Configurar Alertas":
    st.header("🤖 Configurações do Robô")
    st.write("Em breve: Integração automática com o Telegram.")
