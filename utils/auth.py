import streamlit as st
from utils.database import verificar_login

def check_login() -> bool:
    return st.session_state.get("logged_in", False)

def logout():
    for k in ["logged_in", "username", "nome_completo", "role", "current_page"]:
        st.session_state.pop(k, None)
    st.rerun()
