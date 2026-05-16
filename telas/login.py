# -*- coding: utf-8 -*-
import streamlit as st
import hashlib


def show_login(cookies, salvar_cookie_fn):
    """
    Tela de login integrada ao Supabase utilizando a gaveta global st.session_state["db"].
    cookies          — instância do EncryptedCookieManager (vem do app.py)
    salvar_cookie_fn — função _salvar_cookie() do app.py
    """
    st.markdown(
        "<div style='text-align:center;margin-bottom:32px;'>"
        "<div style='display:inline-flex;align-items:center;justify-content:center;"
        "width:76px;height:76px;"
        "background:linear-gradient(135deg,#2d6a4f 0%,#0f2318 100%);"
        "border-radius:22px;font-size:38px;"
        "box-shadow:0 8px 28px rgba(45,106,79,.40);margin-bottom:16px;'>📦</div>"
        "<h1 style='font-family:Georgia,serif;font-size:2rem;"
        "color:#0f2318;margin:0 0 6px;'>SmartLarder Pro</h1>"
        "<p style='color:#6b8f71;font-size:0.92rem;margin:0;'>"
        "Controle inteligente de validade e estoque</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 2, 1])
    with col:
        username = st.text_input("Usuário", placeholder="seu.usuario", key="li_user")
        senha    = st.text_input("Senha", type="password",
                                 placeholder="sua senha", key="li_pass")
        st.markdown("")

        if st.button("Entrar", use_container_width=True, type="primary"):
        if not username or not senha:
            st.warning("Preencha usuário e senha.")
            return

        user = _verificar_login(username.strip(), senha)
        if user:
            # Preenche o session_state usando o padrão dicionário (seguro contra quebras)
            st.session_state["logged_in"]     = True
            st.session_state["user_id"]       = user["id"]
            st.session_state["username"]      = user["username"]
            st.session_state["nome_completo"] = user.get("nome") or user.get("name", "Usuário")
            st.session_state["role"]          = user.get("role", "domestico")
            st.session_state["empresa_id"]    = user.get("empresa_id", 1)
            st.session_state["alerts"]        = {}
            st.session_state["batch_list"]    = []
            
            # Salva cookie para persistência
            salvar_cookie_fn(user)
            st.rerun()
        else:
            st.error("Credenciais inválidas ou conta inativa.")

    st.markdown(
        "<div style='text-align:center;margin-top:16px;"
        "color:#9ab;font-size:0.82rem;'>"
        "Acesso inicial: <code>admin</code> / <code>admin123</code><br>"
        "<span style='color:#e67e22;'>"
        "Troque a senha após o primeiro acesso.</span>"
        "</div>",
        unsafe_allow_html=True,
    )


def _verificar_login(username: str, senha: str) -> dict | None:
    """
    Consulta a tabela 'usuarios' no Supabase buscando a conexão ativa do session_state.
    Aceita dois formatos de senha:
      1. Hash SHA-256 armazenado na coluna senha_hash
      2. Senha em texto puro (fallback para migração)
    """
    # Resgata a conexão centralizada gerada pelo app.py
    db = st.session_state.get("db")
    if db is None:
        st.error("Sem conexão com o banco de dados ativo.")
        return None

    try:
        res = (db.table("usuarios")
                 .select("*")
                 .eq("username", username)
                 .eq("ativo", 1)
                 .execute())

        if not res.data:
            return None

        user = res.data[0]

        senha_hash_informada = hashlib.sha256(senha.encode("utf-8")).hexdigest()
        senha_hash_armazenada = str(user.get("senha_hash", ""))

        # Aceita hash SHA-256 ou senha em texto puro (para migração)
        if (senha_hash_informada == senha_hash_armazenada
                or senha == senha_hash_armazenada):
            return user

        return None

    except Exception as e:
        st.error(f"Erro ao verificar login no banco: {e}")
        return None
