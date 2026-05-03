import streamlit as st

def tem_permissao(acao):
    """
    Verifica se o usuário atual (armazenado na sessão) tem permissão 
    para realizar uma ação específica.
    """
    # Se não houver role definida, assume o nível mais básico por segurança
    role = st.session_state.get("role", "domestico")

    # Mapeamento de permissões por papel
    permissoes = {
        "admin": ["ver_financeiro", "editar_produto", "gerenciar_usuarios", "ver_fornecedores", "ver_perdas"],
        "comercial": ["ver_financeiro", "editar_produto", "ver_fornecedores", "ver_perdas"],
        "domestico": ["editar_produto"]
    }

    return acao in permissoes.get(role, [])
