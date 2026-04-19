import streamlit as st
import pandas as pd
from datetime import datetime

# CONFIGURAÇÃO DE MARCA E LAYOUT
st.set_page_config(page_title="SmartLarder - Inteligência Doméstica", layout="wide", page_icon="🧼")

# ESTILO CUSTOMIZADO (Para dar um ar profissional)
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# CABEÇALHO
st.title("🧼 SmartLarder")
st.caption("Advanced Household Inventory & Expiration Management")
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO DO BANCO DE DADOS (GRATUITO) ---
def criar_banco():
    conn = sqlite3.connect('smartlarder.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS estoque 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  produto TEXT, categoria TEXT, validade DATE, quantidade INTEGER)''')
    conn.commit()
    conn.close()

def salvar_item(nome, cat, data, qtd):
    conn = sqlite3.connect('smartlarder.db')
    c = conn.cursor()
    c.execute("INSERT INTO estoque (produto, categoria, validade, quantidade) VALUES (?, ?, ?, ?)",
              (nome, cat, data, qtd))
    conn.commit()
    conn.close()

def carregar_dados():
    conn = sqlite3.connect('smartlarder.db')
    df = pd.read_sql_query("SELECT produto as Produto, categoria as Categoria, validade as Vencimento, quantidade as Qtd FROM estoque", conn)
    conn.close()
    return df

# --- INICIALIZAÇÃO ---
criar_banco()
st.set_page_config(page_title="SmartLarder - Gestão Inteligente", layout="wide", page_icon="📈")

# --- INTERFACE ---
st.title("🧼 SmartLarder")
st.caption("Gestão Avançada de Estoque e Validades")

# MENU LATERAL
st.sidebar.title("Navegação")
menu = st.sidebar.radio("Ir para:", ["Painel Geral", "Cadastrar Produtos", "Configurar Alertas"])

if menu == "Painel Geral":
    st.header("📊 Visão Geral da Dispensa")
    dados = carregar_dados()
    
    if not dados.empty:
        # Métricas Simples
        m1, m2 = st.columns(2)
        m1.metric("Itens no Estoque", len(dados))
        m2.metric("Economia Mensal Estimada", "R$ 85,50") # Exemplo fixo por enquanto
        
        st.divider()
        st.subheader("📦 Itens Cadastrados")
        st.dataframe(dados, use_container_width=True)
    else:
        st.info("Sua dispensa está vazia. Comece cadastrando um item!")

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
        
        botao = st.form_submit_button("Registrar Item no Banco de Dados")
        
        if botao:
            if nome:
                salvar_item(nome, cat, data, qtd)
                st.success(f"**{nome}** salvo com sucesso no SmartLarder!")
            else:
                st.error("Por favor, digite o nome do produto.")

elif menu == "Configurar Alertas":
    st.header("🤖 Configurações do Robô")
    st.write("Em breve: Integração automática com o Telegram do cliente.")
    st.text_input("Token do Bot (Seu Código Secreto)")
    st.text_input("Seu ID do Telegram")
    st.button("Salvar Configurações")