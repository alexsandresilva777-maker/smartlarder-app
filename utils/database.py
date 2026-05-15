# -*- coding: utf-8 -*-
"""
utils/database.py — SmartLarder Pro v4.1 (Corrigido)
Banco SQLite com multi-tenant, migração segura, cache EAN e conexão robusta.
"""
import sqlite3
import hashlib
import os
import streamlit as st
from datetime import date, datetime, timedelta
import pytz
from supabase import create_client, Client

# Conexão com o Supabase usando os Secrets do Streamlit (Mantido para uso futuro)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

_TZ     = pytz.timezone("America/Sao_Paulo")
_BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_BASE, "data", "smartlarder.db")


# ── Conexão ────────────────────────────────────────────────────────────────────
def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _now_br() -> str:
    return datetime.now(_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _hash(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


# ── Inicialização e migração ───────────────────────────────────────────────────
def init_db():
    """
    Cria tabelas se não existirem de forma segura.
    """
    conn = get_conn()
    c    = conn.cursor()
    
    # ── Criação das tabelas com todas as colunas necessárias ───────────────────
    c.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id   INTEGER DEFAULT 1,
        nome         TEXT    NOT NULL,
        username     TEXT    UNIQUE NOT NULL,
        senha_hash   TEXT    NOT NULL,
        email        TEXT,
        role         TEXT    DEFAULT 'operador',
        ativo        INTEGER DEFAULT 1,
        criado_em    TEXT    DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS produtos (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id          INTEGER NOT NULL DEFAULT 1,
        codigo_barras    TEXT,
        nome             TEXT    NOT NULL,
        categoria        TEXT    DEFAULT 'Alimentos',
        quantidade       REAL    NOT NULL DEFAULT 0,
        unidade          TEXT    DEFAULT 'un',
        validade         TEXT    NOT NULL,
        lote             TEXT,
        fornecedor       TEXT,
        localizacao      TEXT,
        preco_custo      REAL    DEFAULT 0,
        estoque_minimo   REAL    DEFAULT 0,
        observacoes      TEXT,
        criado_por       TEXT,
        criado_em        TEXT    DEFAULT CURRENT_TIMESTAMP,
        atualizado_em    TEXT    DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES usuarios(id)
    );

    CREATE TABLE IF NOT EXISTS movimentacoes (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL DEFAULT 1,
        produto_id  INTEGER NOT NULL,
        tipo        TEXT    NOT NULL,
        quantidade  REAL    NOT NULL,
        observacao  TEXT,
        usuario     TEXT,
        data        TEXT    DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id)    REFERENCES usuarios(id)
    );

    CREATE TABLE IF NOT EXISTS config_alertas (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id        INTEGER NOT NULL DEFAULT 1,
        email_destino  TEXT,
        dias_aviso     INTEGER DEFAULT 7,
        enviar_email   INTEGER DEFAULT 0,
        smtp_host      TEXT    DEFAULT 'smtp.gmail.com',
        smtp_porta     INTEGER DEFAULT 587,
        smtp_usuario   TEXT,
        smtp_senha     TEXT,
        atualizado_em  TEXT    DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES usuarios(id)
    );

    CREATE TABLE IF NOT EXISTS ean_cache (
        codigo_barras TEXT    PRIMARY KEY,
        nome          TEXT,
        categoria     TEXT,
        fornecedor    TEXT,
        imagem_url    TEXT,
        nutriscore    TEXT,
        fonte         TEXT,
        atualizado_em TEXT    DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # ── Migrações estruturais dinâmicas (Garante conformidade) ─────────────────
    _migracao_segura(c, "usuarios",      "senha_hash", "TEXT NOT NULL DEFAULT ''")
    _migracao_segura(c, "usuarios",      "empresa_id", "INTEGER DEFAULT 1")
    _migracao_segura(c, "produtos",      "user_id",  "INTEGER NOT NULL DEFAULT 1")
    _migracao_segura(c, "movimentacoes", "user_id",  "INTEGER NOT NULL DEFAULT 1")
    _migracao_segura(c, "config_alertas","user_id",  "INTEGER NOT NULL DEFAULT 1")
    _migracao_segura(c, "produtos",      "fornecedor","TEXT")
    _migracao_segura(c, "produtos",      "estoque_minimo", "REAL DEFAULT 0")
    _migracao_segura(c, "produtos",      "preco_custo",    "REAL DEFAULT 0")

    # ── Admin padrão ───────────────────────────────────────────────────────────
    if not c.execute("SELECT 1 FROM usuarios WHERE username='admin'").fetchone():
        c.execute("""
            INSERT INTO usuarios (nome, username, senha_hash, email, role, empresa_id)
            VALUES ('Administrador','admin',?,'admin@empresa.com','admin', 1)
        """, (_hash("admin123"),))

    # ── Config alertas padrão ──────────────────────────────────────────────────
    if not c.execute("SELECT 1 FROM config_alertas WHERE user_id=1 LIMIT 1").fetchone():
        c.execute("INSERT INTO config_alertas (user_id, dias_aviso) VALUES (1, 7)")

    # ── Dados de exemplo (só na primeira execução) ─────────────────────────────
    if not c.execute("SELECT 1 FROM produtos LIMIT 1").fetchone():
        _inserir_exemplos(c)

    conn.commit()
    conn.close()


def _migracao_segura(cursor, tabela: str, coluna: str, tipo: str):
    try:
        cols = [r[1] for r
