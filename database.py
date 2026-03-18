import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_NAME = "historico.db"

# =====================================================
# CONEXÃO
# =====================================================
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# =====================================================
# UTIL
# =====================================================
def coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    return coluna in [c[1] for c in cursor.fetchall()]


# =====================================================
# INIT + MIGRAÇÕES SEGURAS
# =====================================================
def init_db():
    with get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            origem TEXT NOT NULL,
            cliente TEXT NOT NULL,
            caminho TEXT NOT NULL,
            status TEXT DEFAULT 'REVISAO',
            setor TEXT,
            criado_em TEXT NOT NULL
        )
        """)


# =====================================================
# INSERT PRINCIPAL
# =====================================================
def salvar_documento(
    tipo,
    cliente,
    caminho,
    origem,
    status="REVISAO",
    setor=None
):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO documentos
            (tipo, origem, cliente, caminho, status, setor, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tipo,
                origem,
                cliente,
                caminho,
                status,
                setor,
                datetime.now().isoformat()
            )
        )


# =====================================================
# COMPATIBILIDADE COM APP (salvar_historico)
# =====================================================
def salvar_historico(dados: dict):
    """
    Mantém compatibilidade com app.py antigo
    """
    salvar_documento(
        tipo="CONTRATO",
        cliente=dados.get("cliente"),
        caminho=dados.get("arquivo"),
        origem=dados.get("usuario"),
        status=dados.get("status", "REVISAO"),
        setor=dados.get("setor")
    )


# =====================================================
# LISTAGENS / HISTÓRICO
# =====================================================
def listar_documentos(
    tipo=None,
    cliente=None,
    status=None,
    setor=None,
    usuario=None
):
    query = """
        SELECT
            id,
            tipo,
            origem AS usuario,
            cliente,
            caminho AS arquivo,
            status,
            setor,
            criado_em
        FROM documentos
        WHERE 1=1
    """
    params = []

    if tipo:
        query += " AND tipo = ?"
        params.append(tipo)

    if cliente:
        query += " AND cliente LIKE ?"
        params.append(f"%{cliente}%")

    if status:
        query += " AND status = ?"
        params.append(status)

    if setor:
        query += " AND setor = ?"
        params.append(setor)

    if usuario:
        query += " AND origem = ?"
        params.append(usuario)

    query += " ORDER BY datetime(criado_em) DESC"

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def buscar_por_id(doc_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM documentos WHERE id = ?",
            (doc_id,)
        ).fetchone()
        return dict(row) if row else None


def atualizar_status(doc_id, novo_status):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE documentos
            SET status = ?
            WHERE id = ?
            """,
            (novo_status, doc_id)
        )


# =====================================================
# DASHBOARD
# =====================================================
def listar_dashboard(cliente=None, setor=None, usuario=None):
    query = """
        SELECT status, COUNT(*) AS total
        FROM documentos
        WHERE 1=1
    """
    params = []

    if cliente:
        query += " AND cliente LIKE ?"
        params.append(f"%{cliente}%")

    if setor:
        query += " AND setor = ?"
        params.append(setor)

    if usuario:
        query += " AND origem = ?"
        params.append(usuario)

    query += " GROUP BY status"

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()

    dashboard = {
        "REVISAO": 0,
        "ASSINADO": 0,
        "CONCLUIDO": 0,
        "TOTAL": 0
    }

    for r in rows:
        dashboard["TOTAL"] += r["total"]
        if r["status"] in dashboard:
            dashboard[r["status"]] = r["total"]

    return dashboard


# =====================================================
# COMPATIBILIDADE TOTAL
# =====================================================
def listar_historico(*args, **kwargs):
    return listar_documentos(*args, **kwargs)
