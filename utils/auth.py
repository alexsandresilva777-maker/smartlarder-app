# -*- coding: utf-8 -*-
import streamlit as st


def logout():
    """Limpa completamente a sessão e redireciona para login."""
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()
