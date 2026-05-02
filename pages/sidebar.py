import streamlit as st
from utils.auth import logout
from utils.database import listar_produtos

_PAGES = [
    ("🏠", "Dashboard"),
    ("📋", "Produtos"),
    ("➕", "Cadastrar"),
    ("🛒", "Lista de Compras"),
    ("📊", "Relatórios"),
    ("🔔", "Alertas"),
    ("❓", "Ajuda"),
]

def show_sidebar() -> str:
    with st.sidebar:
        role = st.session_state.get("role","operador")
        nome = st.session_state.get("nome_completo","Usuário")
        rc   = {"admin":"#e74c3c","gerente":"#e67e22","operador":"#2d6a4f"}.get(role,"#2d6a4f")
        rb   = {"admin":"#fde8e8","gerente":"#fff3cd","operador":"#e8f5e9"}.get(role,"#e8f5e9")

        st.markdown(
            f"""<div style='text-align:center;padding:16px 4px 14px;'>
              <div style='display:inline-flex;align-items:center;justify-content:center;
                          width:54px;height:54px;
                          background:linear-gradient(135deg,#2d6a4f,#0f2318);
                          border-radius:15px;font-size:28px;
                          box-shadow:0 4px 16px rgba(45,106,79,.4);'>📦</div>
              <div style='color:#d4f0df;font-size:1.02rem;font-weight:700;
                          margin:9px 0 4px;'>SmartLarder Pro</div>
              <div style='color:#74c69d;font-size:0.77rem;margin-bottom:7px;'>👤 {nome}</div>
              <span style='background:{rb};color:{rc};padding:3px 12px;
                           border-radius:20px;font-size:0.71rem;font-weight:700;
                           letter-spacing:.06em;'>{role.upper()}</span>
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div style='height:1px;background:linear-gradient(90deg,transparent,"
            "#2d6a4f,transparent);margin:0 8px 12px;'></div>",
            unsafe_allow_html=True,
        )

        # Alertas rápidos
        try:
            todos    = listar_produtos()
            vencidos = sum(1 for p in todos if p["status"]=="vencido")
            criticos = sum(1 for p in todos if p["status"]=="critico")
            if vencidos:
                st.markdown(
                    f"<div style='background:rgba(231,76,60,.18);border:1px solid "
                    f"rgba(231,76,60,.4);border-radius:8px;padding:7px 12px;"
                    f"margin-bottom:5px;font-size:0.79rem;color:#ff8a80;'>"
                    f"🚨 <strong>{vencidos}</strong> produto(s) VENCIDO(S)</div>",
                    unsafe_allow_html=True,
                )
            if criticos:
                st.markdown(
                    f"<div style='background:rgba(230,126,34,.18);border:1px solid "
                    f"rgba(230,126,34,.4);border-radius:8px;padding:7px 12px;"
                    f"margin-bottom:5px;font-size:0.79rem;color:#ffb74d;'>"
                    f"⚠️ <strong>{criticos}</strong> vence(m) em ≤7 dias</div>",
                    unsafe_allow_html=True,
                )
        except Exception:
            pass

        st.markdown(
            "<div style='font-size:0.69rem;color:#4a8a5a;font-weight:700;"
            "letter-spacing:.1em;padding:8px 4px 5px;'>MENU</div>",
            unsafe_allow_html=True,
        )

        if "current_page" not in st.session_state:
            st.session_state.current_page = "Dashboard"

        pages = list(_PAGES)
        if role == "admin":
            pages.insert(-1, ("👥","Usuários"))  # antes de Ajuda

        for icon, name in pages:
            ativo = st.session_state.current_page == name
            if st.button(
                f"{icon}  {name}",
                key=f"nav_{name}",
                use_container_width=True,
                type="primary" if ativo else "secondary",
            ):
                st.session_state.current_page = name
                st.rerun()

        st.markdown(
            "<div style='height:1px;background:linear-gradient(90deg,transparent,"
            "#2d6a4f,transparent);margin:12px 8px 10px;'></div>",
            unsafe_allow_html=True,
        )
        if st.button("🚪  Sair", use_container_width=True):
            logout()

    return st.session_state.current_page
