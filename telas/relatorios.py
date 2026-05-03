import streamlit as st
from utils.database import listar_produtos

def show_relatorios():
    # Recupera o ID do usuário logado
    user_id = st.session_state.get("user_id")
    
    if not user_id:
        st.error("❌ Sessão expirada. Por favor, faça login novamente.")
        st.stop()

    st.markdown("## 📊 Painel de Relatórios")

    # Tabs para organizar as visões
    tab1, tab2, tab3 = st.tabs(["📦 Estoque Completo", "📈 Movimentações", "📅 Validade"])

    with tab1:
        st.subheader("Inventário Completo")
        try:
            # Busca os produtos do banco de dados
            produtos = listar_produtos(user_id)
            if produtos:
                st.dataframe(produtos, use_container_width=True)
            else:
                st.info("Nenhum produto encontrado no estoque.")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")

    with tab2:
        st.info("Funcionalidade de histórico de movimentações em desenvolvimento.")

    with tab3:
        st.info("Análise detalhada de validade em desenvolvimento.")
