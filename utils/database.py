# -*- coding: utf-8 -*-
"""
utils/database.py — SmartLarder Pro v4.1
Banco SQLite com multi-tenant, migração segura, cache EAN e conexão robusta.
"""
import sqlite3
import hashlib
import os
from datetime import date, datetime, timedelta
import pytz

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
    Cria tabelas se não existirem.
    Se já existirem, executa ALTER TABLE para adicionar colunas novas sem
    perder dados (migração segura).
    """
    conn = get_conn()
    c    = conn.cursor()
    # --- INÍCIO DA CORREÇÃO ---
    # 1. Garante que a tabela de usuários tenha a estrutura correta
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            senha TEXT,
            nome TEXT,
            role TEXT,
            empresa_id INTEGER DEFAULT 1
        )
    ''')

    # 2. MIGRAÇÃO: Se a tabela já existia sem a coluna empresa_id, este código a adiciona
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN empresa_id INTEGER DEFAULT 1")
        conn.commit()
    except:
        # Se a coluna já existir, o SQLite dará erro e o código apenas ignora e segue em frente
        pass
    # --- FIM DA CORREÇÃO ---

    # ── Criação das tabelas ────────────────────────────────────────────────────
    c.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        nome       TEXT    NOT NULL,
        username   TEXT    UNIQUE NOT NULL,
        senha_hash TEXT    NOT NULL,
        email      TEXT,
        role       TEXT    DEFAULT 'operador',
        ativo      INTEGER DEFAULT 1,
        criado_em  TEXT    DEFAULT CURRENT_TIMESTAMP
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

    # ── Migração segura: adiciona colunas novas sem perder dados ───────────────
    _migracao_segura(c, "produtos",      "user_id",  "INTEGER NOT NULL DEFAULT 1")
    _migracao_segura(c, "movimentacoes", "user_id",  "INTEGER NOT NULL DEFAULT 1")
    _migracao_segura(c, "config_alertas","user_id",  "INTEGER NOT NULL DEFAULT 1")
    _migracao_segura(c, "produtos",      "fornecedor","TEXT")
    _migracao_segura(c, "produtos",      "estoque_minimo", "REAL DEFAULT 0")
    _migracao_segura(c, "produtos",      "preco_custo",    "REAL DEFAULT 0")

    # ── Admin padrão ───────────────────────────────────────────────────────────
    if not c.execute("SELECT 1 FROM usuarios WHERE username='admin'").fetchone():
        c.execute("""
            INSERT INTO usuarios (nome, username, senha_hash, email, role)
            VALUES ('Administrador','admin',?,'admin@empresa.com','admin')
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
    """Adiciona coluna apenas se não existir — sem perda de dados."""
    try:
        cols = [r[1] for r in cursor.execute(f"PRAGMA table_info({tabela})").fetchall()]
        if coluna not in cols:
            cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
    except Exception:
        pass


def _inserir_exemplos(c):
    hoje = date.today()
    exemplos = [
        (1,"7891000055084","Nescafé Original 200g",      "Alimentos", 8,"un",str(hoje+timedelta(days=180)),"L001","Nestlé",       "Prateleira A1",12.90, 5),
        (1,"7891234560002","Feijão Preto 1kg",            "Alimentos",30,"un",str(hoje+timedelta(days=60)), "L002","Distribuidor A","Prateleira A2", 3.20,10),
        (1,"7891234560003","Detergente Ypê 500ml",        "Limpeza",  24,"un",str(hoje+timedelta(days=365)),"L003","Ypê",           "Depósito B1",   1.80, 6),
        (1,"7896045109056","Shampoo Seda 400ml",          "Higiene",  15,"un",str(hoje+timedelta(days=400)),"L004","Unilever",      "Depósito B2",   5.50, 4),
        (1,"7891234560005","Leite Integral Italac 1L",    "Bebidas",  60,"un",str(hoje+timedelta(days=3)),  "L005","Italac",        "Câmara Fria",   2.90,20),
        (1,"7891234560006","Iogurte Nestlé Natural 170g", "Alimentos",20,"un",str(hoje-timedelta(days=2)),  "L006","Nestlé",        "Câmara Fria",   1.50, 8),
        (1,"001",          "Tomate Italiano",             "Alimentos", 5,"kg",str(hoje+timedelta(days=5)),  "",    "Feira Central", "Câmara Fria",   4.00, 3),
        (1,"002",          "Batata Inglesa",              "Alimentos",10,"kg",str(hoje+timedelta(days=12)), "",    "Feira Central", "Prateleira A3", 2.50, 5),
    ]
    for e in exemplos:
        c.execute("""
            INSERT INTO produtos (user_id,codigo_barras,nome,categoria,quantidade,unidade,
              validade,lote,fornecedor,localizacao,preco_custo,estoque_minimo,criado_por)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'admin')
        """, e)
    pids = [r[0] for r in c.execute("SELECT id FROM produtos LIMIT 6").fetchall()]
    for pid in pids:
        for delta in [25,18,10,3]:
            dt = (date.today()-timedelta(days=delta)).isoformat()
            c.execute("INSERT INTO movimentacoes (user_id,produto_id,tipo,quantidade,usuario,data) VALUES (1,?,?,?,?,?)",
                      (pid,"entrada",10,"admin",dt+" 08:00:00"))
            c.execute("INSERT INTO movimentacoes (user_id,produto_id,tipo,quantidade,usuario,data) VALUES (1,?,?,?,?,?)",
                      (pid,"saida",4,"admin",dt+" 17:00:00"))


# ── Helpers de status ──────────────────────────────────────────────────────────
def _status_validade(validade_str: str) -> tuple[str, int]:
    try:
        hoje = datetime.now(_TZ).date()
        val  = datetime.strptime(validade_str, "%Y-%m-%d").date()
        dias = (val - hoje).days
        if dias < 0:   return "vencido", dias
        if dias <= 7:  return "critico", dias
        if dias <= 30: return "atencao", dias
        return "ok", dias
    except Exception:
        return "ok", 999


def _enriquecer(rows) -> list[dict]:
    resultado = []
    for r in rows:
        d = dict(r)
        d["status"], d["dias_para_vencer"] = _status_validade(d.get("validade","9999-12-31"))
        resultado.append(d)
    return resultado


# ── Alertas pós-login ──────────────────────────────────────────────────────────
def check_alerts(user_id: int) -> dict:
    """
    Chamada logo após o login. Retorna contagem de itens críticos
    para exibir notificação imediata ao usuário.
    """
    conn = get_conn()
    try:
        hoje  = datetime.now(_TZ).date().isoformat()
        em7   = (datetime.now(_TZ).date() + timedelta(days=7)).isoformat()
        em30  = (datetime.now(_TZ).date() + timedelta(days=30)).isoformat()
        v = conn.execute("SELECT COUNT(*) FROM produtos WHERE user_id=? AND validade<?",  (user_id,hoje)).fetchone()[0]
        c = conn.execute("SELECT COUNT(*) FROM produtos WHERE user_id=? AND validade>=? AND validade<=?", (user_id,hoje,em7)).fetchone()[0]
        a = conn.execute("SELECT COUNT(*) FROM produtos WHERE user_id=? AND validade>? AND validade<=?",  (user_id,em7,em30)).fetchone()[0]
        return {"vencidos":v or 0,"criticos":c or 0,"atencao":a or 0}
    finally:
        conn.close()


# ── Estatísticas ───────────────────────────────────────────────────────────────
_STATS_DEFAULT = {
    "total":0,"total_estoque":0.0,"vencidos":0,"criticos":0,
    "atencao":0,"ok":0,"abaixo_minimo":0,"gasto_mensal":0.0,
    "capital_em_risco":0.0,"categorias":[],"top_vencendo":[],
}

def get_stats(user_id: int) -> dict:
    resultado = dict(_STATS_DEFAULT)
    conn = get_conn()
    try:
        c      = conn.cursor()
        hoje   = datetime.now(_TZ).date().isoformat()
        em7    = (datetime.now(_TZ).date() + timedelta(days=7)).isoformat()
        em30   = (datetime.now(_TZ).date() + timedelta(days=30)).isoformat()
        mes_ini= (datetime.now(_TZ).date() - timedelta(days=30)).isoformat()

        resultado["total"]         = c.execute("SELECT COUNT(*) FROM produtos WHERE user_id=?", (user_id,)).fetchone()[0] or 0
        resultado["total_estoque"] = float(c.execute("SELECT COALESCE(SUM(quantidade*preco_custo),0) FROM produtos WHERE user_id=?", (user_id,)).fetchone()[0] or 0)
        resultado["vencidos"]      = c.execute("SELECT COUNT(*) FROM produtos WHERE user_id=? AND validade<?",  (user_id,hoje)).fetchone()[0] or 0
        resultado["criticos"]      = c.execute("SELECT COUNT(*) FROM produtos WHERE user_id=? AND validade>=? AND validade<=?", (user_id,hoje,em7)).fetchone()[0] or 0
        resultado["atencao"]       = c.execute("SELECT COUNT(*) FROM produtos WHERE user_id=? AND validade>? AND validade<=?",  (user_id,em7,em30)).fetchone()[0] or 0
        resultado["ok"]            = max(0, resultado["total"]-resultado["vencidos"]-resultado["criticos"]-resultado["atencao"])
        resultado["abaixo_minimo"] = c.execute("SELECT COUNT(*) FROM produtos WHERE user_id=? AND estoque_minimo>0 AND quantidade<estoque_minimo", (user_id,)).fetchone()[0] or 0
        resultado["gasto_mensal"]  = float(c.execute("SELECT COALESCE(SUM(m.quantidade*p.preco_custo),0) FROM movimentacoes m JOIN produtos p ON p.id=m.produto_id WHERE m.user_id=? AND m.tipo='saida' AND m.data>=?", (user_id,mes_ini)).fetchone()[0] or 0)
        resultado["capital_em_risco"] = float(c.execute("SELECT COALESCE(SUM(quantidade*preco_custo),0) FROM produtos WHERE user_id=? AND validade<=?", (user_id,em30)).fetchone()[0] or 0)

        cats = c.execute("SELECT categoria, COUNT(*) AS qtd, COALESCE(SUM(quantidade),0) AS total_qtd, COALESCE(SUM(quantidade*preco_custo),0) AS valor FROM produtos WHERE user_id=? GROUP BY categoria ORDER BY qtd DESC", (user_id,)).fetchall()
        resultado["categorias"] = [dict(r) for r in cats]

        top = c.execute("SELECT nome,validade,quantidade,unidade FROM produtos WHERE user_id=? AND validade>=? ORDER BY validade ASC LIMIT 5", (user_id,hoje)).fetchall()
        resultado["top_vencendo"] = [dict(r) for r in top]
    except Exception:
        import traceback; traceback.print_exc()
    finally:
        conn.close()
    return resultado


# ── Produtos ───────────────────────────────────────────────────────────────────
def listar_produtos(user_id: int, filtro_nome="", filtro_categoria="", filtro_status="") -> list[dict]:
    conn = get_conn()
    try:
        q, p = "SELECT * FROM produtos WHERE user_id=?", [user_id]
        if filtro_nome:
            q += " AND (nome LIKE ? OR codigo_barras LIKE ?)"; p += [f"%{filtro_nome}%"]*2
        if filtro_categoria and filtro_categoria != "Todas":
            q += " AND categoria=?"; p.append(filtro_categoria)
        q += " ORDER BY validade ASC"
        rows = conn.execute(q, p).fetchall()
        produtos = _enriquecer(rows)
        if filtro_status and filtro_status != "Todos":
            mapa = {"Vencido":"vencido","Crítico (≤7d)":"critico","Atenção (≤30d)":"atencao","OK":"ok"}
            s = mapa.get(filtro_status,"")
            produtos = [x for x in produtos if x["status"]==s]
        return produtos
    finally:
        conn.close()


def inserir_produto(dados: dict, user_id: int, usuario: str) -> int:
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO produtos (user_id,codigo_barras,nome,categoria,quantidade,unidade,validade,
              lote,fornecedor,localizacao,preco_custo,estoque_minimo,observacoes,criado_por)
            VALUES (:user_id,:codigo_barras,:nome,:categoria,:quantidade,:unidade,:validade,
              :lote,:fornecedor,:localizacao,:preco_custo,:estoque_minimo,:observacoes,:criado_por)
        """, {**dados,"user_id":user_id,"criado_por":usuario})
        new_id = c.lastrowid
        conn.commit()
        return new_id
    finally:
        conn.close()


def atualizar_produto(produto_id: int, user_id: int, dados: dict):
    conn = get_conn()
    try:
        conn.execute("""
            UPDATE produtos SET codigo_barras=:codigo_barras, nome=:nome, categoria=:categoria,
              quantidade=:quantidade, unidade=:unidade, validade=:validade, lote=:lote,
              fornecedor=:fornecedor, localizacao=:localizacao, preco_custo=:preco_custo,
              estoque_minimo=:estoque_minimo, observacoes=:observacoes,
              atualizado_em=CURRENT_TIMESTAMP
            WHERE id=:id AND user_id=:user_id
        """, {**dados,"id":produto_id,"user_id":user_id})
        conn.commit()
    finally:
        conn.close()


def excluir_produto(produto_id: int, user_id: int):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM produtos WHERE id=? AND user_id=?", (produto_id,user_id))
        conn.commit()
    finally:
        conn.close()


def buscar_por_barcode(codigo: str, user_id: int) -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM produtos WHERE codigo_barras=? AND user_id=? LIMIT 1", (codigo,user_id)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── EAN Cache (INSERT OR REPLACE) ─────────────────────────────────────────────
def get_ean_cache(codigo: str) -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM ean_cache WHERE codigo_barras=?", (codigo,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def salvar_ean_cache(codigo: str, dados: dict):
    """INSERT OR REPLACE evita erro de duplicidade em acessos simultâneos."""
    conn = get_conn()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO ean_cache
              (codigo_barras, nome, categoria, fornecedor, imagem_url, nutriscore, fonte, atualizado_em)
            VALUES (?,?,?,?,?,?,?,?)
        """, (codigo, dados.get("nome",""), dados.get("categoria",""), dados.get("fornecedor",""),
              dados.get("imagem_url",""), dados.get("nutriscore",""), dados.get("fonte",""), _now_br()))
        conn.commit()
    finally:
        conn.close()


# ── Movimentações ──────────────────────────────────────────────────────────────
def registrar_movimentacao(produto_id: int, user_id: int, tipo: str, quantidade: float, obs: str, usuario: str):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO movimentacoes (user_id,produto_id,tipo,quantidade,observacao,usuario,data) VALUES (?,?,?,?,?,?,?)",
                     (user_id,produto_id,tipo,quantidade,obs,usuario,_now_br()))
        if tipo == "saida":
            conn.execute("UPDATE produtos SET quantidade=MAX(0,quantidade-?),atualizado_em=CURRENT_TIMESTAMP WHERE id=? AND user_id=?", (quantidade,produto_id,user_id))
        elif tipo == "entrada":
            conn.execute("UPDATE produtos SET quantidade=quantidade+?,atualizado_em=CURRENT_TIMESTAMP WHERE id=? AND user_id=?", (quantidade,produto_id,user_id))
        conn.commit()
    finally:
        conn.close()


def listar_movimentacoes(user_id: int, produto_id=None, limit=100) -> list[dict]:
    conn = get_conn()
    try:
        if produto_id:
            rows = conn.execute("SELECT m.*,p.nome AS produto_nome FROM movimentacoes m JOIN produtos p ON p.id=m.produto_id WHERE m.user_id=? AND m.produto_id=? ORDER BY m.data DESC LIMIT ?", (user_id,produto_id,limit)).fetchall()
        else:
            rows = conn.execute("SELECT m.*,p.nome AS produto_nome FROM movimentacoes m JOIN produtos p ON p.id=m.produto_id WHERE m.user_id=? ORDER BY m.data DESC LIMIT ?", (user_id,limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_movimentacoes_chart(user_id: int, dias=30) -> list[dict]:
    conn = get_conn()
    try:
        inicio = (datetime.now(_TZ).date()-timedelta(days=dias)).isoformat()
        rows = conn.execute("SELECT DATE(data) AS dia,tipo,SUM(quantidade) AS total FROM movimentacoes WHERE user_id=? AND data>=? GROUP BY dia,tipo ORDER BY dia", (user_id,inicio)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_consumo_medio(produto_id: int, user_id: int, dias=30) -> float:
    conn = get_conn()
    try:
        inicio = (datetime.now(_TZ).date()-timedelta(days=dias)).isoformat()
        row = conn.execute("SELECT COALESCE(SUM(quantidade),0) AS total FROM movimentacoes WHERE user_id=? AND produto_id=? AND tipo='saida' AND data>=?", (user_id,produto_id,inicio)).fetchone()
        return round(float(row["total"] or 0)/dias, 3)
    finally:
        conn.close()


# ── Lista de compras inteligente ───────────────────────────────────────────────
def gerar_lista_compras(user_id: int) -> list[dict]:
    conn = get_conn()
    try:
        prods = conn.execute("SELECT * FROM produtos WHERE user_id=? AND quantidade>=0", (user_id,)).fetchall()
    finally:
        conn.close()

    lista = []
    for p in prods:
        d         = dict(p)
        consumo   = get_consumo_medio(d["id"], user_id)
        est_min   = float(d.get("estoque_minimo") or 0)
        qtd_atual = float(d.get("quantidade") or 0)
        motivos   = []
        status, _ = _status_validade(d.get("validade","9999-12-31"))

        if est_min > 0 and qtd_atual < est_min:
            motivos.append(f"Abaixo do mínimo (faltam {est_min-qtd_atual:.1f} {d['unidade']})")
        if consumo > 0 and qtd_atual/consumo < 7:
            motivos.append(f"Acaba em ~{qtd_atual/consumo:.0f} dias (consumo: {consumo:.1f}/dia)")
        if status in ("critico","vencido") and qtd_atual > 0:
            motivos.append("Produto vencendo/vencido — repor após descarte")

        if motivos:
            sugerido = max(est_min-qtd_atual, consumo*14, 1)
            urgencia = "alta" if status in ("vencido","critico") or (est_min>0 and qtd_atual==0) else "media"
            lista.append({"id":d["id"],"nome":d["nome"],"categoria":d["categoria"],
                          "fornecedor":d.get("fornecedor") or "—","qtd_atual":qtd_atual,
                          "unidade":d["unidade"],"estoque_min":est_min,"consumo_dia":consumo,
                          "sugerido":round(sugerido,1),"preco_custo":float(d.get("preco_custo") or 0),
                          "motivos":motivos,"urgencia":urgencia})

    lista.sort(key=lambda x:(0 if x["urgencia"]=="alta" else 1, x["nome"]))
    return lista


# ── Usuários ───────────────────────────────────────────────────────────────────
def verificar_login(username: str, senha: str) -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM usuarios WHERE username=? AND ativo=1", (username,)).fetchone()
        return dict(row) if row and row["senha_hash"]==_hash(senha) else None
    finally:
        conn.close()


def listar_usuarios() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT id,nome,username,email,role,ativo,criado_em FROM usuarios ORDER BY nome").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def criar_usuario(nome, username, senha, email, role) -> tuple[bool, str]:
    conn = get_conn()
    try:
        conn.execute("INSERT INTO usuarios (nome,username,senha_hash,email,role) VALUES (?,?,?,?,?)",
                     (nome, username, _hash(senha), email, role))
        conn.commit()
        return True, "Usuário criado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Username já existe."
    finally:
        conn.close()


def alterar_senha(username: str, nova: str):
    conn = get_conn()
    try:
        conn.execute("UPDATE usuarios SET senha_hash=? WHERE username=?", (_hash(nova), username))
        conn.commit()
    finally:
        conn.close()


def toggle_usuario(user_id: int, ativo: int):
    conn = get_conn()
    try:
        conn.execute("UPDATE usuarios SET ativo=? WHERE id=?", (ativo, user_id))
        conn.commit()
    finally:
        conn.close()


def excluir_usuario(user_id: int):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM usuarios WHERE id=?", (user_id,))
        conn.commit()
    finally:
        conn.close()


# ── Config alertas ─────────────────────────────────────────────────────────────
def get_config_alertas(user_id: int) -> dict:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM config_alertas WHERE user_id=? LIMIT 1", (user_id,)).fetchone()
        if not row:
            conn2 = get_conn()
            try:
                conn2.execute("INSERT OR IGNORE INTO config_alertas (user_id,dias_aviso) VALUES (?,7)", (user_id,))
                conn2.commit()
            finally:
                conn2.close()
            return {"email_destino":"","dias_aviso":7,"enviar_email":0,
                    "smtp_host":"smtp.gmail.com","smtp_porta":587,"smtp_usuario":"","smtp_senha":""}
        return dict(row)
    finally:
        conn.close()


def salvar_config_alertas(user_id: int, dados: dict):
    conn = get_conn()
    try:
        conn.execute("""UPDATE config_alertas SET email_destino=:email_destino,dias_aviso=:dias_aviso,
            enviar_email=:enviar_email,smtp_host=:smtp_host,smtp_porta=:smtp_porta,
            smtp_usuario=:smtp_usuario,smtp_senha=:smtp_senha,atualizado_em=CURRENT_TIMESTAMP
            WHERE user_id=:user_id""", {**dados,"user_id":user_id})
        conn.commit()
    finally:
        conn.close()
def migracao_segura(conn, tabela, coluna, definicao):
    """
    Adiciona coluna em tabela SQLite apenas se ela não existir.
    Seguro para produção básica.
    """
    import sqlite3

    try:
        cursor = conn.cursor()

        # Verifica se a tabela existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (tabela,))
        
        if not cursor.fetchone():
            print(f"[AVISO] Tabela '{tabela}' não existe. Migração ignorada.")
            return

        # Verifica colunas existentes
        cursor.execute(f"PRAGMA table_info({tabela})")
        colunas = [info[1] for info in cursor.fetchall()]

        # Se não existir, adiciona
        if coluna not in colunas:
            cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")
            conn.commit()
            print(f"[OK] Coluna '{coluna}' adicionada à tabela '{tabela}'.")
        else:
            print(f"[INFO] Coluna '{coluna}' já existe em '{tabela}'.")

    except sqlite3.OperationalError as e:
        print(f"[ERRO SQLite] {e}")
    except Exception as e:
        print(f"[ERRO Geral] {e}")
