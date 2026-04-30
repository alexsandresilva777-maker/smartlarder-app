import streamlit as st

# 1. Configuração da página (O código DEVE ser em inglês)
st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Importação dos seus módulos da pasta utilitários
try:
    from utilitários import cadastro, dashboard, relatorios
except ImportError as e:
    # Se ainda der erro de acento, mudaremos a pasta para 'utilitarios' depois
    st.error(f"Erro ao carregar módulos: {e}")

# 3. Interface da Barra Lateral
with st.sidebar:
    st.title("SmartLarder Pro")
    st.info("Logado como: Administrador")
    
    escolha = st.radio(
        "Navegação",
        ["Início / Dashboard", "Cadastrar Novo Produto", "Relatórios de Estoque"]
    )

# 4. Direcionamento
if escolha == "Início / Dashboard":
    dashboard.exibir()
elif escolha == "Cadastrar Novo Produto":
    cadastro.exibir()
elif escolha == "Relatórios de Estoque":
    relatorios.exibir()
