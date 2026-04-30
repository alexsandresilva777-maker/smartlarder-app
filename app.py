import streamlit as st

# 1. Configuração que limpa o menu e define o visual largo
st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Importação segura da nova pasta
try:
    from utilitários import cadastro, dashboard, relatorios
except ImportError as e:
    st.error(f"Erro ao carregar módulos: {e}. Verifique se a pasta se chama 'utilitários'.")

# 3. Interface da Barra Lateral (Sidebar)
with st.sidebar:
    st.image("https://raw.githubusercontent.com/alexsandresilva777-maker/smartlarder-app/main/ativos/logo.png", width=100) # Exemplo de link para seu logo
    st.title("SmartLarder Pro")
    st.info("Logado como: Administrador")
    
    escolha = st.radio(
        "Navegação",
        ["Início / Dashboard", "Cadastrar Novo Produto", "Relatórios de Estoque"]
    )

# 4. Direcionamento das Páginas
if escolha == "Início / Dashboard":
    dashboard.exibir() 
elif escolha == "Cadastrar Novo Produto":
    cadastro.exibir()
elif escolha == "Relatórios de Estoque":
    relatorios.exibir()
