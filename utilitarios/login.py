import streamlit as st
from utilitarios.database import verificar_login # Caminho ajustado para a nova pasta
def show_login():
    st.markdown("""
    <style>
      section[data-testid="stSidebar"] { display:none !important; }
      .main .block-container { max-width:460px !important; padding-top:60px !important; }
    </style>
    """, unsafe_allow_html=True)

    # Bloco central — HTML único e fechado
    st.markdown(
        """<div style='text-align:center;margin-bottom:32px;'>
          <div style='display:inline-flex;align-items:center;justify-content:center;
                      width:76px;height:76px;
                      background:linear-gradient(135deg,#2d6a4f 0%,#0f2318 100%);
                      border-radius:22px;font-size:38px;
                      box-shadow:0 8px 28px rgba(45,106,79,.40);
                      margin-bottom:16px;'>📦</div>
          <h1 style='font-family:"Playfair Display",Georgia,serif;font-size:2rem;
                     color:#0f2318;margin:0 0 6px;letter-spacing:-0.5px;'>
            SmartLarder Pro
          </h1>
          <p style='color:#6b8f71;font-size:0.92rem;margin:0;'>
            Controle inteligente de validade e estoque
          </p>
        </div>""",
        unsafe_allow_html=True,
    )

    username = st.text_input("Usuário", placeholder="seu.usuario", key="li_user")
    senha    = st.text_input("Senha", type="password", placeholder="••••••••", key="li_pass")
    st.markdown("")

    if st.button("Entrar →", use_container_width=True, type="primary"):
        if not username or not senha:
            st.warning("Preencha usuário e senha.")
            return
        user = verificar_login(username.strip(), senha)
        if user:
            st.session_state.logged_in     = True
            st.session_state.username      = user["username"]
            st.session_state.nome_completo = user["nome"]
            st.session_state.role          = user["role"]
            st.rerun()
        else:
            st.error("Credenciais inválidas ou conta inativa.")

    st.markdown(
        "<div style='text-align:center;margin-top:20px;color:#9ab;font-size:0.82rem;'>"
        "Acesso inicial: <code>admin</code> / <code>admin123</code><br>"
        "<span style='color:#e67e22;'>⚠️ Troque a senha após o primeiro acesso.</span>"
        "</div>",
        unsafe_allow_html=True,
    )
