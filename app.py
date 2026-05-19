"""
DistribuiMax S.A. — Backend
Python + Flask + pyodbc → SQL Server
Todas as operações usam Stored Procedures
"""

import os
from flask import Flask, jsonify, request, render_template
import pyodbc

app = Flask(__name__)

# ─────────────────────────────────────────────────
# CONFIGURAÇÃO — edite aqui com seus dados
# ─────────────────────────────────────────────────
DB_SERVER   = os.environ.get("DB_SERVER",   "localhost\\SQLEXPRESS")
DB_NAME     = os.environ.get("DB_NAME",     "DistribuiMax")
DB_USER     = os.environ.get("DB_USER",     "sa")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "Distribuimax@2026")
DB_DRIVER   = os.environ.get("DB_DRIVER",   "ODBC Driver 17 for SQL Server")

def get_conn():
    return pyodbc.connect(
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        "TrustServerCertificate=yes;"
    )

def to_list(cursor):
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def exec_sp(sp, params=[]):
    # executa uma stored procedure que não retorna dados (INSERT, UPDATE, DELETE)
    with get_conn() as conn:
        cur = conn.cursor()
        placeholders = ','.join(['?'] * len(params))
        sql = f"EXEC {sp}" if not params else f"EXEC {sp} {placeholders}"
        cur.execute(sql, params)
        conn.commit()

def query_sp(sp, params=[]):
    # executa uma stored procedure que retorna dados (SELECT)
    with get_conn() as conn:
        cur = conn.cursor()
        placeholders = ','.join(['?'] * len(params))
        sql = f"EXEC {sp}" if not params else f"EXEC {sp} {placeholders}"
        cur.execute(sql, params)
        return to_list(cur)

def query_sql(sql, params=[]):
    # usada apenas para buscar um registro antes de chamar uma SP de atualização
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return to_list(cur)

def execute_sql(sql, params=[]):
    # usada apenas em tabelas auxiliares que não possuem SP própria no SQL final
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()

# ─────────────────────────────────────────────────
# PÁGINAS
# ─────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health():
    try:
        with get_conn() as c:
            c.cursor().execute("SELECT 1")
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "erro", "detalhe": str(e)}), 500

# ═════════════════════════════════════════════════
# EMPRESAS
# ═════════════════════════════════════════════════
@app.route("/api/empresas")
def listar_empresas():
    tipo = request.args.get("tipo", "todos")
    return jsonify(query_sp("sp_listar_empresas", [tipo]))

@app.route("/api/empresas/<int:id>")
def get_empresa(id):
    r = query_sql("SELECT * FROM EMPRESA WHERE id_empresa=?", [id])
    return jsonify(r[0]) if r else ("", 404)

@app.route("/api/empresas", methods=["POST"])
def criar_empresa():
    d = request.json
    exec_sp("sp_inserir_empresa", [
        d["razao_social"], d["cnpj"], d.get("telefone"), d.get("email"),
        d.get("contato_responsavel"), int(d.get("is_cliente", 0)),
        int(d.get("is_fornecedor", 0)), d.get("limite_credito", 0),
        d["logradouro"], d["bairro"], d["cep"], d["cidade"], d["estado"]
    ])
    return jsonify({"ok": True}), 201

@app.route("/api/empresas/<int:id>", methods=["PUT"])
def editar_empresa(id):
    d = request.json
    exec_sp("sp_atualizar_empresa", [
        id, d["razao_social"], d["cnpj"], d.get("telefone"), d.get("email"),
        d.get("contato_responsavel"), int(d.get("is_cliente", 0)),
        int(d.get("is_fornecedor", 0)), d.get("limite_credito", 0),
        d["logradouro"], d["bairro"], d["cep"], d["cidade"], d["estado"],
        int(d.get("ativo", 1))
    ])
    return jsonify({"ok": True})

@app.route("/api/empresas/<int:id>", methods=["DELETE"])
def deletar_empresa(id):
    r = query_sql("SELECT * FROM EMPRESA WHERE id_empresa=?", [id])
    if not r:
        return ("", 404)

    e = r[0]
    exec_sp("sp_atualizar_empresa", [
        id, e["razao_social"], e["cnpj"], e.get("telefone"), e.get("email"),
        e.get("contato_responsavel"), int(e.get("is_cliente", 0)),
        int(e.get("is_fornecedor", 0)), e.get("limite_credito", 0),
        e["logradouro"], e["bairro"], e["cep"], e["cidade"], e["estado"], 0
    ])
    return jsonify({"ok": True})

# ═════════════════════════════════════════════════
# PRODUTOS
# ═════════════════════════════════════════════════
@app.route("/api/produtos")
def listar_produtos():
    return jsonify(query_sp("sp_listar_produtos"))

@app.route("/api/produtos/<int:id>")
def get_produto(id):
    r = query_sql("SELECT * FROM PRODUTO WHERE id_produto=?", [id])
    return jsonify(r[0]) if r else ("", 404)

@app.route("/api/produtos", methods=["POST"])
def criar_produto():
    d = request.json
    exec_sp("sp_inserir_produto", [
        d["id_categoria"], d["codigo_sku"], d["descricao"],
        d["unidade_medida"], d["preco_custo"], d["preco_venda"], d.get("peso_kg")
    ])
    return jsonify({"ok": True}), 201

@app.route("/api/produtos/<int:id>", methods=["PUT"])
def editar_produto(id):
    d = request.json
    exec_sp("sp_atualizar_produto", [
        id, d["id_categoria"], d["codigo_sku"], d["descricao"],
        d["unidade_medida"], d["preco_custo"], d["preco_venda"],
        d.get("peso_kg"), int(d.get("ativo", 1))
    ])
    return jsonify({"ok": True})

@app.route("/api/produtos/<int:id>", methods=["DELETE"])
def deletar_produto(id):
    r = query_sql("SELECT * FROM PRODUTO WHERE id_produto=?", [id])
    if not r:
        return ("", 404)

    p = r[0]
    exec_sp("sp_atualizar_produto", [
        id, p["id_categoria"], p["codigo_sku"], p["descricao"],
        p["unidade_medida"], p["preco_custo"], p["preco_venda"],
        p.get("peso_kg"), 0
    ])
    return jsonify({"ok": True})

# ═════════════════════════════════════════════════
# PEDIDOS
# ═════════════════════════════════════════════════
@app.route("/api/pedidos")
def listar_pedidos():
    return jsonify(query_sp("sp_listar_pedidos"))

@app.route("/api/pedidos/<int:id>")
def get_pedido(id):
    r = query_sql(
        "SELECT p.*,e.razao_social AS cliente,f.nome AS filial "
        "FROM PEDIDO p JOIN EMPRESA e ON e.id_empresa=p.id_empresa "
        "JOIN FILIAL f ON f.id_filial=p.id_filial WHERE p.id_pedido=?",
        [id]
    )
    return jsonify(r[0]) if r else ("", 404)

@app.route("/api/pedidos", methods=["POST"])
def criar_pedido():
    d = request.json
    exec_sp("sp_inserir_pedido", [
        d["id_empresa"], d["id_filial"], d.get("dt_prevista_entrega"),
        d.get("status", "AGUARDANDO"), d.get("observacao")
    ])
    return jsonify({"ok": True}), 201

@app.route("/api/pedidos/<int:id>", methods=["PUT"])
def editar_pedido(id):
    d = request.json
    exec_sp("sp_atualizar_pedido", [
        id, d["status"], d.get("dt_prevista_entrega"), d.get("observacao")
    ])
    return jsonify({"ok": True})

@app.route("/api/pedidos/<int:id>", methods=["DELETE"])
def deletar_pedido(id):
    r = query_sql("SELECT dt_prevista_entrega, observacao FROM PEDIDO WHERE id_pedido=?", [id])
    if not r:
        return ("", 404)

    p = r[0]
    exec_sp("sp_atualizar_pedido", [
        id, "CANCELADO", p.get("dt_prevista_entrega"), p.get("observacao")
    ])
    return jsonify({"ok": True})

# ═════════════════════════════════════════════════
# NOTAS FISCAIS
# ═════════════════════════════════════════════════
@app.route("/api/notas")
def listar_notas():
    return jsonify(query_sp("sp_listar_notas"))

@app.route("/api/notas/<int:id>/itens")
def itens_nota(id):
    return jsonify(query_sp("sp_listar_itens_nota", [id]))

@app.route("/api/notas", methods=["POST"])
def criar_nota():
    d = request.json
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "EXEC sp_inserir_nota ?,?,?,?",
            d["id_pedido"], d["numero_nf"],
            d.get("serie", "001"), d.get("chave_acesso")
        )
        id_nf = int(cur.fetchone()[0])

        # ITEM_NOTA não possui SP própria no SQL final.
        # A trigger trg_valor_nota recalcula o valor_total automaticamente.
        for it in d.get("itens", []):
            cur.execute(
                "INSERT INTO ITEM_NOTA (id_nf,id_produto,quantidade,preco_unitario) VALUES (?,?,?,?)",
                id_nf, it["id_produto"], it["quantidade"], it["preco_unitario"]
            )

        conn.commit()

    return jsonify({"ok": True, "id_nf": id_nf}), 201

@app.route("/api/notas/<int:id>", methods=["DELETE"])
def deletar_nota(id):
    exec_sp("sp_deletar_nota", [id])
    return jsonify({"ok": True})

# ═════════════════════════════════════════════════
# FUNCIONÁRIOS
# ═════════════════════════════════════════════════
@app.route("/api/funcionarios")
def listar_funcionarios():
    return jsonify(query_sp("sp_listar_funcionarios"))

@app.route("/api/funcionarios/<int:id>")
def get_funcionario(id):
    r = query_sql("SELECT * FROM FUNCIONARIO WHERE id_funcionario=?", [id])
    return jsonify(r[0]) if r else ("", 404)

@app.route("/api/funcionarios", methods=["POST"])
def criar_funcionario():
    d = request.json
    exec_sp("sp_inserir_funcionario", [
        d["id_filial"], d["nome"], d["cpf"],
        d["cargo"], d["salario"], d["dt_admissao"]
    ])
    return jsonify({"ok": True}), 201

@app.route("/api/funcionarios/<int:id>", methods=["PUT"])
def editar_funcionario(id):
    d = request.json
    exec_sp("sp_atualizar_funcionario", [
        id, d["nome"], d["cargo"], d["salario"], int(d.get("ativo", 1))
    ])
    return jsonify({"ok": True})

@app.route("/api/funcionarios/<int:id>", methods=["DELETE"])
def deletar_funcionario(id):
    r = query_sql("SELECT * FROM FUNCIONARIO WHERE id_funcionario=?", [id])
    if not r:
        return ("", 404)

    f = r[0]
    exec_sp("sp_atualizar_funcionario", [
        id, f["nome"], f["cargo"], f["salario"], 0
    ])
    return jsonify({"ok": True})

# ═════════════════════════════════════════════════
# FILIAIS
# ═════════════════════════════════════════════════
@app.route("/api/filiais")
def listar_filiais():
    return jsonify(query_sp("sp_listar_filiais"))

@app.route("/api/filiais/<int:id>")
def get_filial(id):
    r = query_sql("SELECT * FROM FILIAL WHERE id_filial=?", [id])
    return jsonify(r[0]) if r else ("", 404)

@app.route("/api/filiais", methods=["POST"])
def criar_filial():
    d = request.json
    exec_sp("sp_inserir_filial", [
        d["nome"], d["cnpj"], d.get("telefone"), d["dt_inauguracao"],
        d["logradouro"], d["bairro"], d["cep"], d["cidade"], d["estado"]
    ])
    return jsonify({"ok": True}), 201

@app.route("/api/filiais/<int:id>", methods=["PUT"])
def editar_filial(id):
    d = request.json
    exec_sp("sp_atualizar_filial", [
        id, d["nome"], d["cnpj"], d.get("telefone"), d["dt_inauguracao"],
        d["logradouro"], d["bairro"], d["cep"], d["cidade"], d["estado"],
        int(d.get("ativo", 1))
    ])
    return jsonify({"ok": True})

@app.route("/api/filiais/<int:id>", methods=["DELETE"])
def deletar_filial(id):
    r = query_sql("SELECT * FROM FILIAL WHERE id_filial=?", [id])
    if not r:
        return ("", 404)

    f = r[0]
    exec_sp("sp_atualizar_filial", [
        id, f["nome"], f["cnpj"], f.get("telefone"), f["dt_inauguracao"],
        f["logradouro"], f["bairro"], f["cep"], f["cidade"], f["estado"], 0
    ])
    return jsonify({"ok": True})

# ═════════════════════════════════════════════════
# VEÍCULOS
# ═════════════════════════════════════════════════
@app.route("/api/veiculos")
def listar_veiculos():
    return jsonify(query_sp("sp_listar_veiculos"))

@app.route("/api/veiculos/<int:id>")
def get_veiculo(id):
    r = query_sql("SELECT * FROM VEICULO WHERE id_veiculo=?", [id])
    return jsonify(r[0]) if r else ("", 404)

@app.route("/api/veiculos", methods=["POST"])
def criar_veiculo():
    d = request.json
    exec_sp("sp_inserir_veiculo", [
        d["id_filial"], d["placa"], d["modelo"],
        d.get("marca"), d.get("ano"), d.get("capacidade_kg")
    ])
    return jsonify({"ok": True}), 201

@app.route("/api/veiculos/<int:id>", methods=["PUT"])
def editar_veiculo(id):
    d = request.json
    exec_sp("sp_atualizar_veiculo", [
        id, d["id_filial"], d["placa"], d["modelo"],
        d.get("marca"), d.get("ano"), d.get("capacidade_kg"), int(d.get("ativo", 1))
    ])
    return jsonify({"ok": True})

@app.route("/api/veiculos/<int:id>", methods=["DELETE"])
def deletar_veiculo(id):
    r = query_sql("SELECT * FROM VEICULO WHERE id_veiculo=?", [id])
    if not r:
        return ("", 404)

    v = r[0]
    exec_sp("sp_atualizar_veiculo", [
        id, v["id_filial"], v["placa"], v["modelo"],
        v.get("marca"), v.get("ano"), v.get("capacidade_kg"), 0
    ])
    return jsonify({"ok": True})

# ═════════════════════════════════════════════════
# ENTREGAS
# ═════════════════════════════════════════════════
@app.route("/api/entregas")
def listar_entregas():
    return jsonify(query_sp("sp_listar_entregas"))

@app.route("/api/entregas/<int:id>")
def get_entrega(id):
    r = query_sql("SELECT * FROM ENTREGA WHERE id_entrega=?", [id])
    return jsonify(r[0]) if r else ("", 404)

@app.route("/api/entregas", methods=["POST"])
def criar_entrega():
    d = request.json
    exec_sp("sp_inserir_entrega", [
        d["id_pedido"], d["id_funcionario"], d["id_veiculo"],
        d["dt_saida"], d.get("dt_chegada"),
        d.get("status", "PENDENTE"), d.get("observacao")
    ])
    return jsonify({"ok": True}), 201

@app.route("/api/entregas/<int:id>", methods=["PUT"])
def editar_entrega(id):
    d = request.json
    exec_sp("sp_atualizar_entrega", [
        id, d["id_pedido"], d["id_funcionario"], d["id_veiculo"],
        d["dt_saida"], d.get("dt_chegada"),
        d["status"], d.get("observacao")
    ])
    return jsonify({"ok": True})

@app.route("/api/entregas/<int:id>", methods=["DELETE"])
def deletar_entrega(id):
    r = query_sql("SELECT * FROM ENTREGA WHERE id_entrega=?", [id])
    if not r:
        return ("", 404)

    e = r[0]
    exec_sp("sp_atualizar_entrega", [
        id, e["id_pedido"], e["id_funcionario"], e["id_veiculo"],
        e["dt_saida"], e.get("dt_chegada"), "CANCELADA", e.get("observacao")
    ])
    return jsonify({"ok": True})

# ═════════════════════════════════════════════════
# AUXILIARES
# ═════════════════════════════════════════════════
@app.route("/api/categorias")
def categorias():
    return jsonify(query_sp("sp_listar_categorias"))

@app.route("/api/estoque")
def estoque():
    return jsonify(query_sp("sp_listar_estoque"))

# ═════════════════════════════════════════════════
# RELATÓRIOS / VIEWS
# ═════════════════════════════════════════════════
@app.route("/api/relatorios/pedidos-clientes")
def rel_pedidos_clientes():
    return jsonify(query_sql("SELECT * FROM vw_pedidos_por_cliente"))

@app.route("/api/relatorios/estoque-filial")
def rel_estoque_filial():
    return jsonify(query_sql("SELECT * FROM vw_posicao_estoque_filial"))

@app.route("/api/relatorios/produtos-fornecedor")
def rel_produtos_fornecedor():
    return jsonify(query_sql("SELECT * FROM vw_produtos_por_fornecedor"))

@app.route("/api/relatorios/faturamento-cliente")
def rel_faturamento_cliente():
    return jsonify(query_sql("SELECT * FROM vw_faturamento_por_cliente"))

@app.route("/api/relatorios/entregas-motorista-veiculo")
def rel_entregas_motorista_veiculo():
    return jsonify(query_sql("SELECT * FROM vw_entregas_por_motorista_veiculo"))

# ─────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
