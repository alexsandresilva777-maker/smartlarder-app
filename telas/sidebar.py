# -*- coding: utf-8 -*-
import streamlit as st

_PAGES_BASE = [
    ("🏠", "Dashboard"),
    ("📋", "Produtos"),
    ("➕", "Cadastrar"),
    ("📥", "Recepção de Carga"),
    ("🛒", "Lista de Compras"),
    ("📊", "Relatórios"),
    ("🔔", "Alertas"),
    ("❓", "Ajuda"),
]

def show_sidebar(limpar_cookie_fn) -> str:
    role_raw = st.session_state.get("role", "domestico")
    role = str(role_raw).lower().strip()
    
    session_user = str(st.session_state.get("username", "") or st.session_state.get("sl_username", "")).lower().strip()
    nome = st.session_state.get("nome_completo", "Usuário")
    
    # Validação mestre para o Alex ser Admin global
    is_admin_user = "admin" in role or "alex" in session_user or "alex" in nome.lower()
    
    visual_role = "admin" if is_admin_user else role
    rc = {"admin": "#e74c3c", "comercial": "#e67e22", "domestico": "#2d6a4f"}.get(visual_role, "#2d6a4f")
    rb = {"admin": "#fde8e8", "comercial": "#fff3cd", "domestico": "#e8f5e9"}.get(visual_role, "#e8f5e9")

    with st.sidebar:
        st.markdown(
            "<div style='text-align:center;padding:16px 4px 14px'>"
            "<div style='display:inline-flex;align-items:center;justify-content:center;"
            "width:54px;height:54px;"
            "background:linear-gradient(135deg,#2d6a4f,#0f2318);"
            "border-radius:15px;font-size:28px;"
            "box-shadow:0 4px 16px rgba(45,106,79,.4);'>📦</div>"
            f"<div style='color:#d4f0df;font-size:1rem;font-weight:700;margin:9px 0 4px;'>"
            f"SmartLarder Pro</div>"
            f"<div style='color:#74c69d;font-size:0.77rem;margin-bottom:7px;'>👤 {nome}</div>"
            f"<span style='background:{rb};color:{rc};padding:3px 12px;border-radius:20px;"
            f"font-size:0.71rem;font-weight:700;'>{str(role_raw if not is_admin_user else 'ADMIN').upper()}</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div style='height:1px;background:linear-gradient(90deg,transparent,"
            "#2d6a4f,transparent);margin:0 8px 12px;'></div>",
            unsafe_allow_html=True,
        )

        alerts = st.session_state.get("alerts", {})
        if alerts.get("vencidos"):
            st.markdown(
                f"<div style='background:rgba(231,76,60,.18);border:1px solid rgba(231,76,60,.4);"
                f"border-radius:8px;padding:7px 12px;margin-bottom:5px;font-size:0.79rem;color:#ff8a80;'>"
                f"🚨 <strong>{alerts['vencidos']}</strong> produto(s) VENCIDO(S)</div>",
                unsafe_allow_html=True,
            )
        if alerts.get("criticos"):
            st.markdown(
                f"<div style='background:rgba(230,126,34,.18);border:1px solid rgba(230,126,34,.4);"
                f"border-radius:8px;padding:7px 12px;margin-bottom:5px;font-size:0.79rem;color:#ffb74d;'>"
                f"⚠️ <strong>{alerts['criticos']}</strong> vence(m) em ≤7 dias</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            "<div style='font-size:0.69rem;color:#4a8a5a;font-weight:700;"
            "letter-spacing:.1em;padding:8px 4px 5px;'>MENU</div>",
            unsafe_allow_html=True,
        )

        if "current_page" not in st.session_state:
            st.session_state.current_page = "Dashboard"

        pages = list(_PAGES_BASE)
        if is_admin_user or role == "comercial":
            pages.insert(5, ("🏭", "Fornecedores"))
            pages.insert(6, ("📉", "Perdas"))
        if is_admin_user:
            pages.insert(7, ("👥", "Usuários"))

        for icon, name in pages:
            ativo = st.session_state.current_page == name
            if st.button(f"{icon}  {name}", key=f"nav_{name}",
                         use_container_width=True,
                         type="primary" if ativo else "secondary"):
                st.session_state.current_page = name
                st.rerun()

        st.markdown(
            "<div style='height:1px;background:linear-gradient(90deg,transparent,"
            "#2d6a4f,transparent);margin:12px 8px 8px;'></div>",
            unsafe_allow_html=True,
        )

        if st.button("🚪  Sair", use_container_width=True):
            limpar_cookie_fn()
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    return st.session_state.current_page
