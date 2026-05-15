# -*- coding: utf-8 -*-
import streamlit as st
from utils.auth import tem_permissao
import os
import hashlib
from streamlit_cookies_manager import EncryptedCookieManager

st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none !important;}
    button[data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        display: flex !important;
        background-color: #2d6a4f !important;
        color: white !important;
        z-index: 999999 !important;
    }
    .block-container {padding-top: 1rem !important;}
</style>
""", unsafe_allow_html=True)

_COOKIE_PREFIX   = "smartlarder/"
_COOKIE_PASSWORD = st.secrets.get("COOKIES_PASSWORD", "smartlarder-secret-key-32chars!!")

cookies = EncryptedCookieManager(
    prefix=_COOKIE_PREFIX,
    password=_COOKIE_PASSWORD,
)

if not cookies.ready():
    st.stop()


def _salvar_sessao_no_cookie(user: dict):
    try:
        cookies["sl_user_id"]    = str(user.get("id", ""))
        cookies["sl_username"]   = str(user.get("username", ""))
        cookies["sl_nome"]       = str(user.get("nome", ""))
        cookies["sl_role"]       = str(user.get("role", "domestico"))
        cookies["sl_empresa_id"] = str(user.get("empresa_id", "1"))
        cookies["sl_token"]      = hashlib.sha256(
            user.get("senha_hash", "").encode()
        ).hexdigest()[:16]
        cookies.save()
    except Exception:
        pass


def _restaurar_sessao_do_cookie():
    try:
        user_id    = cookies.get("sl_user_id", "")
        username   = cookies.get("sl_username", "")
        token      = cookies.get("sl_token", "")
        empresa_id = cookies.get("sl_empresa_id", "1")
        role       = cookies.get("sl_role", "domestico")
        nome       = cookies.get("sl_nome", "")

        if not user_id or not username or not token:
            return

        from utils.database import get_conn
        supabase = get_conn()
        res = supabase.table("usuarios").select("*") \
            .eq("id", int(user_id)) \
            .eq("username", username) \
            .eq("ativo", 1) \
            .execute()
        row = res.data[0] if res.data else None

        if not row:
            _limpar_cookie()
            return

        token_esperado = hashlib.sha256(
            row["senha_hash"].encode()
        ).hexdigest()[:16]

        if token != token_esperado:
            _limpar_cookie()
            return

        st.session_state.logged_in     = True
        st.session_state.user_id       = int(user_id)
        st.session_state.username      = username
        st.session_state.nome_completo = nome
        st.session_state.role          = role
        st.session_state.empresa_id    = int(empresa_id)
        st.session_state.alerts        = {}
        st.session_state.batch_list    = []

    except Exception:
        _limpar_cookie()


def _limpar_cookie():
    try:
        for key in ["sl_user_id", "sl_username", "sl_nome",
                    "sl_role", "sl_empresa_id", "sl_token"]:
            if key in cookies:
                cookies[key] = ""
        cookies.save()
    except Exception:
        pass


def add_pwa_support():
    pwa_html = (
        "<meta name='viewport' content='width=device-width, initial-scale=1, "
        "maximum-scale=1, user-scalable=no, viewport-fit=cover'>"
        "<meta name='apple-mobile-web-app-capable' content='yes'>"
        "<meta name='apple-mobile-web-app-status-bar-style' content='black-translucent'>"
        "<meta name='mobile-web-app-capable' content='yes'>"
        "<style>"
        "html { overflow: hidden; height: 100%; }"
        "body { height: 100%; overflow: auto; -webkit-overflow-scrolling: touch; }"
        "</style>"
    )
    st.markdown(pwa_html, unsafe_allow_html=True)
