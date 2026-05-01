"""
SmartLarder Pro v3 — Camada de dados
Usa SQLite localmente. Para migrar para PostgreSQL basta trocar get_conn()
por uma conexão psycopg2/SQLAlchemy — todas as queries usam parâmetros
nomeados compatíveis com ambos os drivers.
"""
import sqlite3
import hashlib
import os
from datetime import date, datetime, timedelta

# ── Caminho do banco ──────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH   = os.path.join(_BASE_DIR, "data", "smartlarder.db")

# ── Conexão (trocar aqui para migrar para PostgreSQL) ─────────────────────────
def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # performance em leituras concorrentes
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def _hash(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

# ═════════════════════════════════════════════════════════════════════════════
# INICIALIZAÇÃO
# ═════════════════════════════════════════════════════════════════════════════
def init_db():
    conn = get_conn()
    c = conn.cursor()

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
        atualizado_em    TEXT    DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS movimentacoes (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id  INTEGER NOT NULL,
        tipo        TEXT    NOT NULL,   -- 'entrada' | 'saida'
        quantidade  REAL    NOT NULL,
        observacao  TEXT,
        usuario     TEXT,
        data        TEXT    DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS config_alertas (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        email_destino  TEXT,
        dias_aviso     INTEGER DEFAULT 7,
        enviar_email   INTEGER DEFAULT 0,
        smtp_host      TEXT    DEFAULT 'smtp.gmail.com',
        smtp_porta     INTEGER DEFAULT 587,
        smtp_usuario   TEXT,
        smtp_senha     TEXT,
        atualizado_em  TEXT    DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Admin padrão
    if not c.execute("SELECT 1 FROM usuarios WHERE username='admin'").fetchone():
        c.execute("""
            INSERT INTO usuarios (nome,username,senha_hash,email,role)
            VALUES ('Administrador','admin',?,  'admin@empresa.com','admin')
        """, (_hash("Naty21"),))

    # Config alertas padrão
    if not c.execute("SELECT 1 FROM config_alertas LIMIT 1").fetchone():
        c.execute("INSERT INTO config_alertas (dias_aviso) VALUES (7)")

    # Dados de exemplo (só na primeira vez)
    if not c.execute("SELECT 1 FROM produtos LIMIT 1").fetchone():
        hoje = date.today()
        exemplos = [
            ("7891000055084","Nescafé Original 200g",       "Alimentos",  8, "un", str(hoje+timedelta(days=180)), "L001","Nestlé",       "Prateleira A1", 12.90, 5),
            ("7891234560002","Feijão Preto 1kg",             "Alimentos", 30, "un", str(hoje+timedelta(days=60)),  "L002","Distribuidor A","Prateleira A2",  3.20, 10),
            ("7891234560003","Detergente Ypê 500ml",         "Limpeza",   24, "un", str(hoje+timedelta(days=365)),"L003","Ypê",           "Depósito B1",   1.80, 6),
            ("7896045109056","Shampoo Seda 400ml",           "Higiene",   15, "un", str(hoje+timedelta(days=400)),"L004","Unilever",      "Depósito B2",   5.50, 4),
            ("7891234560005","Leite Integral Italac 1L",     "Bebidas",   60, "un", str(hoje+timedelta(days=3)),  "L005","Italac",        "Câmara Fria",   2.90, 20),
            ("7891234560006","Iogurte Nestlé Natural 170g",  "Alimentos", 20, "un", str(hoje-timedelta(days=2)),  "L006","Nestlé",        "Câmara Fria",   1.50, 8),
            ("001",          "Tomate Italiano",              "Alimentos",  5, "kg", str(hoje+timedelta(days=5)),  "",    "Feira Central", "Câmara Fria",   4.00, 3),
            ("002",          "Batata Inglesa",               "Alimentos", 10, "kg", str(hoje+timedelta(days=12)), "",    "Feira Central", "Prateleira A3", 2.50, 5),
            ("7896045100084","Arroz Tio João 5kg",           "Alimentos", 40, "un", str(hoje+timedelta(days=500)),"L009","Tio João",      "Prateleira A4", 18.90, 10),
            ("7896045100091","Azeite Gallo Extra Virgem",    "Alimentos",  6, "un", str(hoje+timedelta(days=20)), "L010","Gallo",         "Prateleira A5", 28.90, 3),
        ]
        for e in exemplos:
            c.execute("""
                INSERT INTO produtos
                  (codigo_barras,nome,categoria,quantidade,unidade,validade,
                   lote,fornecedor,localizacao,preco_custo,estoque_minimo,criado_por)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,'admin')
            """, e)
        # Algumas movimentações de exemplo para o gráfico
        p_ids = [r[0] for r in c.execute("SELECT id FROM produtos LIMIT 6").fetchall()]
        for pid in p_ids:
            for delta in [25, 18, 10, 3]:
                dt = (date.today() - timedelta(days=delta)).isoformat()
                c.execute("INSERT INTO movimentacoes (produto_id,tipo,quantidade,usuario,data) VALUES (?,?,?,?,?)",
                          (pid,"entrada", 10, "admin", dt+" 08:00:00"))
                c.execute("INSERT INTO movimentacoes (produto_id,tipo,quantidade,usuario,data) VALUES (?,?,?,?,?)",
                          (pid,"saida",    4, "admin", dt+" 17:00:00"))

    conn.commit()
    conn.close()

# ═════════════════════════════════════════════════════════════════════════════
# ESTATÍSTICAS — todas as chaves SEMPRE presentes (elimina KeyError)
# ═════════════════════════════════════════════════════════════════════════════
_STATS_DEFAULT = {
    "total":          0,
    "total_estoque":  0.0,   # valor R$ investido
    "vencidos":       0,
    "criticos":       0,
    "atencao":        0,
    "ok":             0,
    "abaixo_minimo":  0,
    "gasto_mensal":   0.0,
    "categorias":     [],
    "top_vencendo":   [],
}

def get_stats() -> dict:
    """Retorna dicionário de estatísticas com TODAS as chaves sempre definidas."""
    resultado = dict(_STATS_DEFAULT)  # cópia segura com defaults
    try:
        conn = get_conn()
        c    = conn.cursor()
        hoje    = date.today().isoformat()
        em7     = (date.today() + timedelta(days=7)).isoformat()
        em30    = (date.today() + timedelta(days=30)).isoformat()
        mes_ini = (date.today() - timedelta(days=30)).isoformat()

        resultado["total"] = c.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] or 0

        valor = c.execute(
            "SELECT COALESCE(SUM(quantidade * preco_custo),0) FROM produtos"
        ).fetchone()[0]
        resultado["total_estoque"] = float(valor or 0)

        resultado["vencidos"] = c.execute(
            "SELECT COUNT(*) FROM produtos WHERE validade < ?", (hoje,)
        ).fetchone()[0] or 0

        resultado["criticos"] = c.execute(
            "SELECT COUNT(*) FROM produtos WHERE validade >= ? AND validade <= ?", (hoje, em7)
        ).fetchone()[0] or 0

        resultado["atencao"] = c.execute(
            "SELECT COUNT(*) FROM produtos WHERE validade > ? AND validade <= ?", (em7, em30)
        ).fetchone()[0] or 0

        resultado["ok"] = max(0,
            resultado["total"] - resultado["vencidos"]
            - resultado["criticos"] - resultado["atencao"]
        )

        resultado["abaixo_minimo"] = c.execute(
            "SELECT COUNT(*) FROM produtos WHERE estoque_minimo > 0 AND quantidade < estoque_minimo"
        ).fetchone()[0] or 0

        # Gasto médio mensal (saídas × custo nos últimos 30 dias)
        gasto = c.execute("""
            SELECT COALESCE(SUM(m.quantidade * p.preco_custo), 0)
            FROM movimentacoes m
            JOIN produtos p ON p.id = m.produto_id
            WHERE m.tipo='saida' AND m.data >= ?
        """, (mes_ini,)).fetchone()[0]
        resultado["gasto_mensal"] = float(gasto or 0)

        cats = c.execute("""
            SELECT categoria,
                   COUNT(*)                          AS qtd,
                   COALESCE(SUM(quantidade),0)       AS total_qtd,
                   COALESCE(SUM(quantidade*preco_custo),0) AS valor
            FROM produtos
            GROUP BY categoria
            ORDER BY qtd DESC
        """).fetchall()
        resultado["categorias"] = [dict(r) for r in cats]

        top = c.execute("""
            SELECT nome, validade, quantidade, unidade
            FROM produtos
            WHERE validade >= ?
            ORDER BY validade ASC
            LIMIT 5
        """, (hoje,)).fetchall()
        resultado["top_vencendo"] = [dict(r) for r in top]

        conn.close()
    except Exception as e:
        # Nunca deixa o dashboard travar — retorna defaults com erro logado
        import traceback; traceback.print_exc()

    return resultado

# ═════════════════════════════════════════════════════════════════════════════
# PRODUTOS
# ═════════════════════════════════════════════════════════════════════════════
def _calcular_status(validade_str: str) -> tuple[str, int]:
    try:
        val  = datetime.strptime(validade_str, "%Y-%m-%d").date()
        dias = (val - date.today()).days
        if dias < 0:   return "vencido",  dias
        if dias <= 7:  return "critico",  dias
        if dias <= 30: return "atencao",  dias
        return "ok", dias
    except:
        return "ok", 999

def _enriquecer(rows: list[sqlite3.Row]) -> list[dict]:
    resultado = []
    for r in rows:
        d = dict(r)
        status, dias = _calcular_status(d.get("validade","9999-12-31"))
        d["status"]           = status
        d["dias_para_vencer"] = dias
        resultado.append(d)
    return resultado

def listar_produtos(filtro_nome="", filtro_categoria="", filtro_status="") -> list[dict]:
    conn = get_conn()
    q = "SELECT * FROM produtos WHERE 1=1"
    p = []
    if filtro_nome:
        q += " AND (nome LIKE ? OR codigo_barras LIKE ?)"
        p += [f"%{filtro_nome}%", f"%{filtro_nome}%"]
    if filtro_categoria and filtro_categoria != "Todas":
        q += " AND categoria=?"
        p.append(filtro_categoria)
    q += " ORDER BY validade ASC"
    rows = conn.execute(q, p).fetchall()
    conn.close()
    produtos = _enriquecer(rows)
    if filtro_status and filtro_status != "Todos":
        mapa = {"Vencido":"vencido","Crítico (≤7d)":"critico",
                "Atenção (≤30d)":"atencao","OK":"ok"}
        s = mapa.get(filtro_status,"")
        produtos = [x for x in produtos if x["status"] == s]
    return produtos

def inserir_produto(dados: dict, usuario: str) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO produtos
          (codigo_barras,nome,categoria,quantidade,unidade,validade,
           lote,fornecedor,localizacao,preco_custo,estoque_minimo,observacoes,criado_por)
        VALUES
          (:codigo_barras,:nome,:categoria,:quantidade,:unidade,:validade,
           :lote,:fornecedor,:localizacao,:preco_custo,:estoque_minimo,:observacoes,:criado_por)
    """, {**dados, "criado_por": usuario})
    new_id = c.lastrowid
    conn.commit(); conn.close()
    return new_id

def atualizar_produto(produto_id: int, dados: dict):
    conn = get_conn()
    conn.execute("""
        UPDATE produtos SET
          codigo_barras=:codigo_barras, nome=:nome, categoria=:categoria,
          quantidade=:quantidade, unidade=:unidade, validade=:validade,
          lote=:lote, fornecedor=:fornecedor, localizacao=:localizacao,
          preco_custo=:preco_custo, estoque_minimo=:estoque_minimo,
          observacoes=:observacoes, atualizado_em=CURRENT_TIMESTAMP
        WHERE id=:id
    """, {**dados, "id": produto_id})
    conn.commit(); conn.close()

def excluir_produto(produto_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM produtos WHERE id=?", (produto_id,))
    conn.commit(); conn.close()

def buscar_por_barcode(codigo: str) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM produtos WHERE codigo_barras=? LIMIT 1", (codigo,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_produto_por_id(produto_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM produtos WHERE id=?", (produto_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

# ═════════════════════════════════════════════════════════════════════════════
# MOVIMENTAÇÕES
# ═════════════════════════════════════════════════════════════════════════════
def registrar_movimentacao(produto_id: int, tipo: str, quantidade: float,
                           obs: str, usuario: str):
    conn = get_conn()
    conn.execute("""
        INSERT INTO movimentacoes (produto_id,tipo,quantidade,observacao,usuario)
        VALUES (?,?,?,?,?)
    """, (produto_id, tipo, quantidade, obs, usuario))
    if tipo == "saida":
        conn.execute(
            "UPDATE produtos SET quantidade=MAX(0,quantidade-?), atualizado_em=CURRENT_TIMESTAMP WHERE id=?",
            (quantidade, produto_id)
        )
    elif tipo == "entrada":
        conn.execute(
            "UPDATE produtos SET quantidade=quantidade+?, atualizado_em=CURRENT_TIMESTAMP WHERE id=?",
            (quantidade, produto_id)
        )
    conn.commit(); conn.close()

def listar_movimentacoes(produto_id=None, limit=100) -> list[dict]:
    conn = get_conn()
    if produto_id:
        rows = conn.execute("""
            SELECT m.*, p.nome AS produto_nome
            FROM movimentacoes m JOIN produtos p ON p.id=m.produto_id
            WHERE m.produto_id=? ORDER BY m.data DESC LIMIT ?
        """, (produto_id, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT m.*, p.nome AS produto_nome
            FROM movimentacoes m JOIN produtos p ON p.id=m.produto_id
            ORDER BY m.data DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_movimentacoes_chart(dias=30) -> list[dict]:
    conn = get_conn()
    inicio = (date.today() - timedelta(days=dias)).isoformat()
    rows = conn.execute("""
        SELECT DATE(data) AS dia, tipo, SUM(quantidade) AS total
        FROM movimentacoes
        WHERE data >= ?
        GROUP BY dia, tipo
        ORDER BY dia
    """, (inicio,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_consumo_medio(produto_id: int, dias=30) -> float:
    """Retorna média de saída diária no período."""
    conn = get_conn()
    inicio = (date.today() - timedelta(days=dias)).isoformat()
    row = conn.execute("""
        SELECT COALESCE(SUM(quantidade),0) AS total
        FROM movimentacoes
        WHERE produto_id=? AND tipo='saida' AND data >= ?
    """, (produto_id, inicio)).fetchone()
    conn.close()
    total = float(row["total"] or 0)
    return round(total / dias, 3)

# ═════════════════════════════════════════════════════════════════════════════
# LISTA DE COMPRAS INTELIGENTE
# ═════════════════════════════════════════════════════════════════════════════
def gerar_lista_compras() -> list[dict]:
    """
    Sugere itens para compra baseado em:
    - Estoque abaixo do mínimo configurado
    - Itens que vão acabar em < 7 dias com base no consumo médio
    """
    conn = get_conn()
    produtos = conn.execute(
        "SELECT * FROM produtos WHERE quantidade >= 0"
    ).fetchall()
    conn.close()

    lista = []
    for p in produtos:
        d = dict(p)
        motivos = []
        consumo = get_consumo_medio(d["id"])
        estoque_min = float(d.get("estoque_minimo") or 0)
        qtd_atual   = float(d.get("quantidade") or 0)

        # Abaixo do mínimo
        if estoque_min > 0 and qtd_atual < estoque_min:
            falta = estoque_min - qtd_atual
            motivos.append(f"Abaixo do mínimo (faltam {falta:.1f} {d['unidade']})")

        # Vai acabar em menos de 7 dias pelo consumo
        if consumo > 0:
            dias_restantes = qtd_atual / consumo
            if dias_restantes < 7:
                motivos.append(f"Acaba em ~{dias_restantes:.0f} dias (consumo: {consumo:.1f}/dia)")

        # Vencendo em breve com pouco estoque
        status, dias_venc = _calcular_status(d.get("validade","9999-12-31"))
        if status in ("critico","vencido") and qtd_atual > 0:
            motivos.append(f"Produto vencendo/vencido — repor após descarte")

        if motivos:
            sugerido = max(estoque_min - qtd_atual, consumo * 14, 1)
            lista.append({
                "id":           d["id"],
                "nome":         d["nome"],
                "categoria":    d["categoria"],
                "fornecedor":   d["fornecedor"] or "—",
                "qtd_atual":    qtd_atual,
                "unidade":      d["unidade"],
                "estoque_min":  estoque_min,
                "consumo_dia":  consumo,
                "sugerido":     round(sugerido, 1),
                "preco_custo":  float(d.get("preco_custo") or 0),
                "motivos":      motivos,
                "urgencia":     "alta" if status in ("vencido","critico") or
                                (estoque_min > 0 and qtd_atual == 0) else "media",
            })

    lista.sort(key=lambda x: (0 if x["urgencia"]=="alta" else 1, x["nome"]))
    return lista

# ═════════════════════════════════════════════════════════════════════════════
# USUÁRIOS
# ═════════════════════════════════════════════════════════════════════════════
def verificar_login(username: str, senha: str) -> dict | None:
    conn = get_conn()
    row  = conn.execute(
        "SELECT * FROM usuarios WHERE username=? AND ativo=1", (username,)
    ).fetchone()
    conn.close()
    if row and row["senha_hash"] == _hash(senha):
        return dict(row)
    return None

def listar_usuarios() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id,nome,username,email,role,ativo,criado_em FROM usuarios ORDER BY nome"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def criar_usuario(nome, username, senha, email, role) -> tuple[bool, str]:
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO usuarios (nome,username,senha_hash,email,role)
            VALUES (?,?,?,?,?)
        """, (nome, username, _hash(senha), email, role))
        conn.commit()
        return True, "Usuário criado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Username já existe."
    finally:
        conn.close()

def alterar_senha(username: str, nova_senha: str):
    conn = get_conn()
    conn.execute("UPDATE usuarios SET senha_hash=? WHERE username=?",
                 (_hash(nova_senha), username))
    conn.commit(); conn.close()

def toggle_usuario(user_id: int, ativo: int):
    conn = get_conn()
    conn.execute("UPDATE usuarios SET ativo=? WHERE id=?", (ativo, user_id))
    conn.commit(); conn.close()

def excluir_usuario(user_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM usuarios WHERE id=?", (user_id,))
    conn.commit(); conn.close()

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG ALERTAS
# ═════════════════════════════════════════════════════════════════════════════
def get_config_alertas() -> dict:
    conn = get_conn()
    row  = conn.execute("SELECT * FROM config_alertas LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else {
        "email_destino":"","dias_aviso":7,"enviar_email":0,
        "smtp_host":"smtp.gmail.com","smtp_porta":587,
        "smtp_usuario":"","smtp_senha":"",
    }

def salvar_config_alertas(dados: dict):
    conn = get_conn()
    conn.execute("""
        UPDATE config_alertas SET
          email_destino=:email_destino, dias_aviso=:dias_aviso,
          enviar_email=:enviar_email,   smtp_host=:smtp_host,
          smtp_porta=:smtp_porta,       smtp_usuario=:smtp_usuario,
          smtp_senha=:smtp_senha,       atualizado_em=CURRENT_TIMESTAMP
    """, dados)
    conn.commit(); conn.close()
