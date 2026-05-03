import streamlit as st
from utils.database import (listar_usuarios, criar_usuario,
                             toggle_usuario, excluir_usuario, alterar_senha)

ROLES = ["operador","gerente","admin"]
ROLE_LABEL = {"operador":"👷 Operador","gerente":"👔 Gerente","admin":"🔑 Admin"}
ROLE_COR   = {"admin":"#e74c3c","gerente":"#e67e22","operador":"#2d6a4f"}
ROLE_BG    = {"admin":"#fde8e8","gerente":"#fff3cd","operador":"#e8f5e9"}

def show_usuarios():
    user_id = st.session_state.get("user_id", 1)
    st.markdown("## 👥 Gerenciamento de Usuários")

    tab1, tab2 = st.tabs(["👁️ Usuários", "➕ Novo Usuário"])
    with tab1: _listar()
    with tab2: _criar()

def _listar():
    usuarios = listar_usuarios()
    if not usuarios:
        st.info("Nenhum usuário cadastrado."); return

    st.markdown(f"**{len(usuarios)} usuário(s)**")

    for u in usuarios:
        rc = ROLE_COR.get(u["role"],"#888")
        rb = ROLE_BG.get(u["role"],"#f5f5f5")
        at_bg  = "#e8f5e9" if u["ativo"] else "#fde8e8"
        at_txt = "✅ Ativo"  if u["ativo"] else "❌ Inativo"
        eu_mesmo = u["username"] == st.session_state.get("username")

        with st.container():
            c1,c2,c3,c4,c5 = st.columns([2.5,1.5,1.2,1.5,2])
            with c1:
                st.markdown(f"""
                <div>
                  <strong>{u['nome']}</strong><br>
                  <span style='color:#888;font-size:0.8rem;'>
                    @{u['username']} · {u.get('email') or '—'}
                  </span>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <span style='background:{rb};color:{rc};padding:3px 10px;
                             border-radius:20px;font-size:0.8rem;font-weight:700;'>
                  {ROLE_LABEL.get(u['role'],u['role'])}
                </span>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <span style='background:{at_bg};padding:3px 10px;
                             border-radius:20px;font-size:0.8rem;'>
                  {at_txt}
                </span>""", unsafe_allow_html=True)
            with c4:
                st.markdown(f"<span style='color:#aaa;font-size:0.78rem;'>"
                            f"{u['criado_em'][:10] if u.get('criado_em') else '—'}</span>",
                            unsafe_allow_html=True)
            with c5:
                if not eu_mesmo:
                    b1,b2 = st.columns(2)
                    with b1:
                        lbl = "🔒 Desativar" if u["ativo"] else "🔓 Ativar"
                        if st.button(lbl, key=f"tg_{u['id']}", use_container_width=True):
                            toggle_usuario(u["id"], 0 if u["ativo"] else 1)
                            st.rerun()
                    with b2:
                        if st.button("🗑️ Excluir", key=f"du_{u['id']}", use_container_width=True):
                            st.session_state[f"cdu_{u['id']}"] = True
                else:
                    st.caption("(você)")

            if st.session_state.get(f"cdu_{u['id']}"):
                st.warning(f"Confirma exclusão de **{u['nome']}**?")
                y,n = st.columns(2)
                with y:
                    if st.button("✅ Confirmar", key=f"ydu_{u['id']}"):
                        excluir_usuario(u["id"])
                        st.session_state.pop(f"cdu_{u['id']}", None)
                        st.rerun()
                with n:
                    if st.button("❌ Cancelar", key=f"ndu_{u['id']}"):
                        st.session_state.pop(f"cdu_{u['id']}", None)
                        st.rerun()

            with st.expander(f"🔑 Alterar senha — {u['username']}", expanded=False):
                with st.form(f"fsp_{u['id']}"):
                    ns = st.text_input("Nova Senha", type="password", key=f"ns_{u['id']}")
                    cs = st.text_input("Confirmar",  type="password", key=f"cs_{u['id']}")
                    if st.form_submit_button("💾 Salvar Senha", type="primary"):
                        if not ns:         st.error("Informe a senha.")
                        elif ns != cs:     st.error("Senhas não coincidem.")
                        elif len(ns) < 6:  st.error("Mínimo 6 caracteres.")
                        else:
                            alterar_senha(u["username"], ns)
                            st.success("✅ Senha alterada!")

        st.markdown("<hr style='margin:5px 0;border-color:#eef2ee;'>", unsafe_allow_html=True)

def _criar():
    with st.form("fc_v3"):
        st.markdown("### Dados do Novo Usuário")
        c1,c2 = st.columns(2)
        with c1:
            nome     = st.text_input("Nome Completo *")
            username = st.text_input("Username *")
            email    = st.text_input("E-mail")
        with c2:
            senha    = st.text_input("Senha *", type="password")
            confirma = st.text_input("Confirmar Senha *", type="password")
            role     = st.selectbox("Perfil *", ROLES, format_func=lambda x: ROLE_LABEL[x])

        st.markdown("""
        | Perfil | Permissões |
        |---|---|
        | 👷 Operador | Cadastrar e visualizar produtos |
        | 👔 Gerente  | + Relatórios, alertas e lista de compras |
        | 🔑 Admin    | Acesso total, incluindo usuários |
        """)
        submitted = st.form_submit_button("✅ Criar Usuário", type="primary", use_container_width=True)

    if submitted:
        erros = []
        if not nome.strip():    erros.append("Nome obrigatório.")
        if not username.strip():erros.append("Username obrigatório.")
        if not senha:           erros.append("Senha obrigatória.")
        if senha != confirma:   erros.append("Senhas não coincidem.")
        if len(senha) < 6:      erros.append("Mínimo 6 caracteres.")
        for e in erros: st.error(f"❌ {e}")
        if not erros:
            ok, msg = criar_usuario(nome.strip(), username.strip(), senha, email.strip(), role)
            if ok:   st.success(f"✅ {msg}"); st.rerun()
            else:    st.error(f"❌ {msg}")
