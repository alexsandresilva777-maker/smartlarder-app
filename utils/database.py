# -*- coding: utf-8 -*-
"""
utils/database.py — SmartLarder Pro
Única responsabilidade: retornar o cliente autenticado do Supabase.
Todas as queries ficam nas telas, acessando st.session_state["db"].
"""
import streamlit as st


def get_conn():
    """
    Retorna o cliente Supabase autenticado.
    Lê SUPABASE_URL e SUPABASE_KEY dos st.secrets do Streamlit Cloud.
    """
    from supabase import create_client, Client

    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]

    return create_client(url, key)


def init_db():
    """
    Compatibilidade com chamadas existentes.
    No Supabase o banco já existe — esta função não faz nada,
    mas evita erros de ImportError nas telas que a chamavam.
    """
    pass
