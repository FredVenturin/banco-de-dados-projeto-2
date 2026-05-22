"""
DistribuiMax S.A. — Backend
Python + Flask + pyodbc → SQL Server
Todas as operações usam Stored Procedures
"""

import os
from flask import Flask, jsonify, request, render_template
import pyodbc

app = Flask(__name__)

DB_SERVER = os.environ.get("DB_SERVER",   "localhost")
DB_NAME = os.environ.get("DB_NAME",     "DistribuiMax")
DB_USER = os.environ.get("DB_USER",     "sa")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "Distribuimax@2026")
DB_DRIVER = os.environ.get("DB_DRIVER",   "ODBC Driver 17 for SQL Server")


def get_conn():
    return pyodbc.connect(
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        "Trusted_Connection=yes;"
    )


def to_list(cursor):
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def erro_banco(e):
    """Extrai mensagem legível de erros do pyodbc/SQL Server."""
    msg = str(e)
    # Tenta pegar só a parte descritiva da mensagem do SQL Server
    if "[SQL Server]" in msg:
        msg = msg.split("[SQL Server]")[-1].strip()
    elif "HY000" in msg or "23000" in msg:
        msg = msg.split("\n")[0].strip()
    # Remove códigos de estado ODBC do início
    import re
    msg = re.sub(r"^\([A-Z0-9]+\)\s*", "", msg)
    return msg[:300]  # limita tamanho


def exec_sp(sp, params=[]):
    with get_conn() as conn:
        cur = conn.cursor()
        placeholders = ','.join(['?'] * len(params))
        sql = f"EXEC {sp}" if not params else f"EXEC {sp} {placeholders}"
        cur.execute(sql, params)
        conn.commit()


def query_sp(sp, params=[]):
    with get_conn() as conn:
        cur = conn.cursor()
        placeholders = ','.join(['?'] * len(params))
        sql = f"EXEC {sp}" if not params else f"EXEC {sp} {placeholders}"
        cur.execute(sql, params)
        return to_list(cur)


def _safe_interpolate(sql, params):
    """Substitui ? por valores diretamente no SQL.
    Aceita apenas int, float e str (com escape de aspas simples).
    Evita o erro 8180 do pyodbc com SQL Server, que ocorre ao tentar
    preparar statements com JOIN parametrizados via cursor.execute(sql, params)."""
    result = sql
    for v in params:
        if v is None:
            literal = "NULL"
        elif isinstance(v, bool):
            literal = "1" if v else "0"
        elif isinstance(v, int):
            literal = str(v)
        elif isinstance(v, float):
            literal = str(v)
        else:
            # string: escapa aspas simples
            literal = "'" + str(v).replace("'", "''") + "'"
        result = result.replace("?", literal, 1)
    return result


def query_sql(sql, params=[]):
    with get_conn() as conn:
        cur = conn.cursor()
        final_sql = _safe_interpolate(sql, params) if params else sql
        cur.execute(final_sql)
        return to_list(cur)


def execute_sql(sql, params=[]):
    with get_conn() as conn:
        cur = conn.cursor()
        final_sql = _safe_interpolate(sql, params) if params else sql
        cur.execute(final_sql)
        conn.commit()
        return cur.rowcount

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
    try:
        tipo = request.args.get("tipo", "todos")
        return jsonify(query_sp("sp_listar_empresas", [tipo]))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/empresas/<int:id>")
def get_empresa(id):
    try:
        r = query_sql("SELECT * FROM EMPRESA WHERE id_empresa=?", [id])
        return jsonify(r[0]) if r else ("", 404)
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/empresas", methods=["POST"])
def criar_empresa():
    try:
        d = request.json
        lc = d.get("limite_credito", 0)
        if lc and float(lc) > 9999999999.99:
            return jsonify({"ok": False, "detalhe": "Limite de crédito muito alto. Máximo: R$ 9.999.999.999,99."}), 400
        exec_sp("sp_inserir_empresa", [
            d["razao_social"], d["cnpj"], d.get("telefone"), d.get("email"),
            d.get("contato_responsavel"), int(d.get("is_cliente", 0)),
            int(d.get("is_fornecedor", 0)), d.get("limite_credito", 0),
            d["logradouro"], d["bairro"], d["cep"], d["cidade"], d["estado"]
        ])
        return jsonify({"ok": True}), 201
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/empresas/<int:id>", methods=["PUT"])
def editar_empresa(id):
    try:
        d = request.json
        lc = d.get("limite_credito", 0)
        if lc and float(lc) > 9999999999.99:
            return jsonify({"ok": False, "detalhe": "Limite de crédito muito alto. Máximo: R$ 9.999.999.999,99."}), 400
        exec_sp("sp_atualizar_empresa", [
            id, d["razao_social"], d["cnpj"], d.get(
                "telefone"), d.get("email"),
            d.get("contato_responsavel"), int(d.get("is_cliente", 0)),
            int(d.get("is_fornecedor", 0)), d.get("limite_credito", 0),
            d["logradouro"], d["bairro"], d["cep"], d["cidade"], d["estado"],
            int(d.get("ativo", 1))
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/empresas/<int:id>", methods=["DELETE"])
def deletar_empresa(id):
    try:
        r = query_sql("SELECT * FROM EMPRESA WHERE id_empresa=?", [id])
        if not r:
            return jsonify({"ok": False, "detalhe": "Empresa não encontrada."}), 404
        e = r[0]
        exec_sp("sp_atualizar_empresa", [
            id, e["razao_social"], e["cnpj"], e.get(
                "telefone"), e.get("email"),
            e.get("contato_responsavel"), int(e.get("is_cliente", 0)),
            int(e.get("is_fornecedor", 0)), e.get("limite_credito", 0),
            e["logradouro"], e["bairro"], e["cep"], e["cidade"], e["estado"], 0
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400

# ═════════════════════════════════════════════════
# PRODUTOS
# ═════════════════════════════════════════════════


@app.route("/api/produtos")
def listar_produtos():
    try:
        return jsonify(query_sp("sp_listar_produtos"))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/produtos/<int:id>")
def get_produto(id):
    try:
        r = query_sql("SELECT * FROM PRODUTO WHERE id_produto=?", [id])
        return jsonify(r[0]) if r else ("", 404)
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/produtos", methods=["POST"])
def criar_produto():
    try:
        d = request.json
        custo = float(d.get("preco_custo") or 0)
        venda = float(d.get("preco_venda") or 0)
        peso = d.get("peso_kg")
        if custo <= 0:
            return jsonify({"ok": False, "detalhe": "Preço de custo deve ser maior que zero."}), 400
        if custo > 99999999.99:
            return jsonify({"ok": False, "detalhe": "Preço de custo muito alto. Máximo: R$ 99.999.999,99."}), 400
        if venda <= 0:
            return jsonify({"ok": False, "detalhe": "Preço de venda deve ser maior que zero."}), 400
        if venda > 99999999.99:
            return jsonify({"ok": False, "detalhe": "Preço de venda muito alto. Máximo: R$ 99.999.999,99."}), 400
        if venda <= custo:
            return jsonify({"ok": False, "detalhe": "Preço de venda deve ser maior que o preço de custo."}), 400
        if peso is not None and float(peso) <= 0:
            return jsonify({"ok": False, "detalhe": "Peso deve ser maior que zero."}), 400
        if peso is not None and float(peso) > 99999.999:
            return jsonify({"ok": False, "detalhe": "Peso muito alto. Máximo: 99.999 kg."}), 400
        exec_sp("sp_inserir_produto", [
            d["fk_categoria"], d["codigo_sku"], d["descricao"],
            d["unidade_medida"], custo, venda, peso or None
        ])
        return jsonify({"ok": True}), 201
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/produtos/<int:id>", methods=["PUT"])
def editar_produto(id):
    try:
        d = request.json
        custo = float(d.get("preco_custo") or 0)
        venda = float(d.get("preco_venda") or 0)
        peso = d.get("peso_kg")
        if custo <= 0:
            return jsonify({"ok": False, "detalhe": "Preço de custo deve ser maior que zero."}), 400
        if custo > 99999999.99:
            return jsonify({"ok": False, "detalhe": "Preço de custo muito alto. Máximo: R$ 99.999.999,99."}), 400
        if venda <= 0:
            return jsonify({"ok": False, "detalhe": "Preço de venda deve ser maior que zero."}), 400
        if venda > 99999999.99:
            return jsonify({"ok": False, "detalhe": "Preço de venda muito alto. Máximo: R$ 99.999.999,99."}), 400
        if venda <= custo:
            return jsonify({"ok": False, "detalhe": "Preço de venda deve ser maior que o preço de custo."}), 400
        if peso is not None and float(peso) <= 0:
            return jsonify({"ok": False, "detalhe": "Peso deve ser maior que zero."}), 400
        if peso is not None and float(peso) > 99999.999:
            return jsonify({"ok": False, "detalhe": "Peso muito alto. Máximo: 99.999 kg."}), 400
        exec_sp("sp_atualizar_produto", [
            id, d["fk_categoria"], d["codigo_sku"], d["descricao"],
            d["unidade_medida"], custo, venda,
            peso or None, int(d.get("ativo", 1))
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/produtos/<int:id>", methods=["DELETE"])
def deletar_produto(id):
    try:
        r = query_sql("SELECT * FROM PRODUTO WHERE id_produto=?", [id])
        if not r:
            return jsonify({"ok": False, "detalhe": "Produto não encontrado."}), 404
        p = r[0]
        exec_sp("sp_atualizar_produto", [
            id, p["fk_categoria"], p["codigo_sku"], p["descricao"],
            p["unidade_medida"], p["preco_custo"], p["preco_venda"],
            p.get("peso_kg"), 0
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400

# ═════════════════════════════════════════════════
# PEDIDOS
# ═════════════════════════════════════════════════


@app.route("/api/pedidos")
def listar_pedidos():
    try:
        return jsonify(query_sp("sp_listar_pedidos"))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/pedidos/<int:id>")
def get_pedido(id):
    try:
        r = query_sql(
            "SELECT p.*,e.razao_social AS cliente,f.nome AS filial "
            "FROM PEDIDO p JOIN EMPRESA e ON e.id_empresa=p.fk_empresa "
            "JOIN FILIAL f ON f.id_filial=p.fk_filial WHERE p.id_pedido=?",
            [id]
        )
        return jsonify(r[0]) if r else ("", 404)
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/pedidos", methods=["POST"])
def criar_pedido():
    try:
        d = request.json
        exec_sp("sp_inserir_pedido", [
            d["fk_empresa"], d["fk_filial"], d.get("dt_prevista_entrega"),
            d.get("status", "AGUARDANDO"), d.get("observacao")
        ])
        return jsonify({"ok": True}), 201
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/pedidos/<int:id>", methods=["PUT"])
def editar_pedido(id):
    try:
        d = request.json
        exec_sp("sp_atualizar_pedido", [
            id, d["status"], d.get("dt_prevista_entrega"), d.get("observacao")
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/pedidos/<int:id>", methods=["DELETE"])
def deletar_pedido(id):
    try:
        r = query_sql(
            "SELECT dt_prevista_entrega, observacao FROM PEDIDO WHERE id_pedido=?", [id])
        if not r:
            return jsonify({"ok": False, "detalhe": "Pedido não encontrado."}), 404
        p = r[0]
        exec_sp("sp_atualizar_pedido", [
            id, "CANCELADO", p.get("dt_prevista_entrega"), p.get("observacao")
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400

# ═════════════════════════════════════════════════
# ITENS DE PEDIDO
# ═════════════════════════════════════════════════


@app.route("/api/pedidos/<int:id>/itens")
def itens_pedido(id):
    try:
        r = query_sql(
            "SELECT ip.fk_pedido, ip.fk_produto, "
            "ip.quantidade, ip.preco_unitario, "
            "ISNULL(ip.desconto_pct,0) AS desconto_pct, "
            "p.descricao AS produto, p.codigo_sku "
            "FROM ITEM_PEDIDO ip "
            "JOIN PRODUTO p ON p.id_produto = ip.fk_produto "
            "WHERE ip.fk_pedido = ?",
            [int(id)]
        )
        return jsonify(r)
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/pedidos/<int:id>/itens", methods=["POST"])
def adicionar_item_pedido(id):
    try:
        d = request.json
        qtd = int(d.get("quantidade", 0))
        preco = float(d.get("preco_unitario", 0))
        desc = float(d.get("desconto_pct", 0))
        if qtd <= 0:
            return jsonify({"ok": False, "detalhe": "Quantidade deve ser maior que zero."}), 400
        if preco <= 0:
            return jsonify({"ok": False, "detalhe": "Preço unitário deve ser maior que zero."}), 400
        if desc < 0 or desc > 100:
            return jsonify({"ok": False, "detalhe": "Desconto deve ser entre 0 e 100%."}), 400
        execute_sql(
            "INSERT INTO ITEM_PEDIDO (fk_pedido,fk_produto,quantidade,preco_unitario,desconto_pct) "
            "VALUES (?,?,?,?,?)",
            [id, d["fk_produto"], qtd, preco, desc]
        )
        return jsonify({"ok": True}), 201
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/pedidos/<int:fk_pedido>/itens/<int:fk_produto>", methods=["DELETE"])
def remover_item_pedido(fk_pedido, fk_produto):
    try:
        execute_sql(
            "DELETE FROM ITEM_PEDIDO WHERE fk_pedido=? AND fk_produto=?",
            [fk_pedido, fk_produto]
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


# ═════════════════════════════════════════════════
# MOVIMENTAÇÕES DE ESTOQUE
# ═════════════════════════════════════════════════


@app.route("/api/movimentacoes", methods=["POST"])
def criar_movimentacao():
    try:
        d = request.json
        if not d:
            return jsonify({"ok": False, "detalhe": "Body JSON ausente."}), 400
        for campo in ["fk_produto", "fk_filial", "fk_funcionario", "quantidade", "tipo"]:
            if d.get(campo) in (None, ""):
                return jsonify({"ok": False, "detalhe": f"Campo obrigatório ausente: {campo}"}), 400
        qtd = int(d["quantidade"])
        tipo = str(d["tipo"]).upper()
        fk_produto = int(d["fk_produto"])
        fk_filial = int(d["fk_filial"])
        fk_funcionario = int(d["fk_funcionario"])
        if tipo not in ("ENTRADA", "SAIDA"):
            return jsonify({"ok": False, "detalhe": "Tipo deve ser ENTRADA ou SAIDA."}), 400
        if qtd <= 0:
            return jsonify({"ok": False, "detalhe": "Quantidade deve ser maior que zero."}), 400

        # Para SAIDA: valida saldo disponível antes de inserir
        if tipo == "SAIDA":
            saldo = query_sql(
                "SELECT ISNULL(e.quantidade, 0) AS saldo, p.descricao, f.nome AS filial "
                "FROM PRODUTO p "
                "JOIN FILIAL f ON f.id_filial = ? "
                "LEFT JOIN ESTOQUE e ON e.fk_produto = p.id_produto AND e.fk_filial = ? "
                "WHERE p.id_produto = ?",
                [fk_filial, fk_filial, fk_produto]
            )
            if not saldo:
                return jsonify({"ok": False, "detalhe": "Produto ou filial não encontrado."}), 404
            saldo_atual = saldo[0]["saldo"]
            if saldo_atual < qtd:
                nome_prod = saldo[0]["descricao"]
                nome_filial = saldo[0]["filial"]
                return jsonify({
                    "ok": False,
                    "detalhe": (
                        f"Saldo insuficiente: '{nome_prod}' na filial '{nome_filial}' "
                        f"tem {saldo_atual} em estoque, mas a saída pede {qtd}."
                    )
                }), 400

        execute_sql(
            "INSERT INTO MOVIMENTACAO (fk_produto,fk_filial,fk_funcionario,tipo,quantidade,motivo) "
            "VALUES (?,?,?,?,?,?)",
            [fk_produto, fk_filial, fk_funcionario,
                tipo, qtd, d.get("motivo") or None]
        )
        return jsonify({"ok": True}), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/movimentacoes")
def listar_movimentacoes():
    try:
        r = query_sql(
            "SELECT m.id_movimentacao, m.tipo, m.quantidade, m.motivo, m.dt_movimentacao, "
            "p.descricao AS produto, p.codigo_sku, f.nome AS filial, fu.nome AS funcionario "
            "FROM MOVIMENTACAO m "
            "JOIN PRODUTO p ON p.id_produto=m.fk_produto "
            "JOIN FILIAL f ON f.id_filial=m.fk_filial "
            "JOIN FUNCIONARIO fu ON fu.id_funcionario=m.fk_funcionario "
            "ORDER BY m.dt_movimentacao DESC"
        )
        return jsonify(r)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/estoque/minimo", methods=["PUT"])
def atualizar_estoque_minimo():
    """Atualiza o estoque_minimo de um par produto+filial.
    Cria o registro em ESTOQUE se ainda não existir."""
    try:
        d = request.json
        fk_produto = int(d["fk_produto"])
        fk_filial = int(d["fk_filial"])
        minimo = int(d["estoque_minimo"])
        if minimo < 0:
            return jsonify({"ok": False, "detalhe": "Estoque mínimo não pode ser negativo."}), 400
        # upsert: atualiza se existir, insere se não existir
        execute_sql(
            "IF EXISTS (SELECT 1 FROM ESTOQUE WHERE fk_produto=? AND fk_filial=?) "
            "    UPDATE ESTOQUE SET estoque_minimo=?, dt_atualizacao=GETDATE() "
            "    WHERE fk_produto=? AND fk_filial=? "
            "ELSE "
            "    INSERT INTO ESTOQUE (fk_produto,fk_filial,quantidade,estoque_minimo) "
            "    VALUES (?,?,0,?)",
            [fk_produto, fk_filial,
             minimo, fk_produto, fk_filial,
             fk_produto, fk_filial, minimo]
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/movimentacoes/diagnostico")
def diagnostico_movimentacoes():
    """Rota de diagnóstico: verifica conexão e retorna contagem das tabelas envolvidas."""
    try:
        resultado = {}
        resultado["movimentacao_count"] = query_sql(
            "SELECT COUNT(*) AS n FROM MOVIMENTACAO")[0]["n"]
        resultado["estoque_count"] = query_sql(
            "SELECT COUNT(*) AS n FROM ESTOQUE")[0]["n"]
        resultado["produtos"] = query_sql(
            "SELECT TOP 5 id_produto, descricao FROM PRODUTO WHERE ativo=1")
        resultado["filiais"] = query_sql(
            "SELECT TOP 5 id_filial, nome FROM FILIAL WHERE ativo=1")
        resultado["funcionarios"] = query_sql(
            "SELECT TOP 5 id_funcionario, nome FROM FUNCIONARIO WHERE ativo=1")
        resultado["estoque_amostra"] = query_sql(
            "SELECT TOP 5 e.fk_produto, p.descricao, e.fk_filial, f.nome AS filial, e.quantidade "
            "FROM ESTOQUE e JOIN PRODUTO p ON p.id_produto=e.fk_produto "
            "JOIN FILIAL f ON f.id_filial=e.fk_filial"
        )
        return jsonify({"ok": True, **resultado})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


# ═════════════════════════════════════════════════
# NOTAS FISCAIS
# ═════════════════════════════════════════════════


@app.route("/api/notas")
def listar_notas():
    try:
        return jsonify(query_sp("sp_listar_notas"))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/notas/<int:id>/itens")
def itens_nota(id):
    try:
        return jsonify(query_sp("sp_listar_itens_nota", [id]))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/notas", methods=["POST"])
def criar_nota():
    try:
        d = request.json
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "EXEC sp_inserir_nota ?,?,?,?",
                d["fk_pedido"], d["numero_nf"],
                d.get("serie", "001"), d.get("chave_acesso")
            )
            id_nf = int(cur.fetchone()[0])
            for it in d.get("itens", []):
                cur.execute(
                    "INSERT INTO ITEM_NOTA (fk_nf,fk_produto,quantidade,preco_unitario,desconto_pct) VALUES (?,?,?,?,?)",
                    id_nf, it["fk_produto"], it["quantidade"], it["preco_unitario"],
                    it.get("desconto_pct", 0)
                )
            conn.commit()
        return jsonify({"ok": True, "id_nf": id_nf}), 201
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/notas/<int:id>", methods=["DELETE"])
def deletar_nota(id):
    try:
        exec_sp("sp_deletar_nota", [id])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400

# ═════════════════════════════════════════════════
# FUNCIONÁRIOS
# ═════════════════════════════════════════════════


@app.route("/api/funcionarios")
def listar_funcionarios():
    try:
        return jsonify(query_sp("sp_listar_funcionarios"))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/funcionarios/<int:id>")
def get_funcionario(id):
    try:
        r = query_sql("SELECT * FROM FUNCIONARIO WHERE id_funcionario=?", [id])
        return jsonify(r[0]) if r else ("", 404)
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/funcionarios", methods=["POST"])
def criar_funcionario():
    try:
        d = request.json
        cpf = ''.join(c for c in (d.get("cpf") or "") if c.isdigit())
        if len(cpf) != 11:
            return jsonify({"ok": False, "detalhe": "CPF deve ter exatamente 11 dígitos."}), 400
        if not d.get("dt_admissao"):
            return jsonify({"ok": False, "detalhe": "Informe a data de admissão."}), 400
        if not d.get("salario") or float(d["salario"]) <= 0:
            return jsonify({"ok": False, "detalhe": "Salário deve ser maior que zero."}), 400
        if float(d["salario"]) > 99999999.99:
            return jsonify({"ok": False, "detalhe": "Salário muito alto. Máximo: R$ 99.999.999,99."}), 400
        exec_sp("sp_inserir_funcionario", [
            d["fk_filial"], d["nome"], cpf,
            d["cargo"], d["salario"], d["dt_admissao"]
        ])
        return jsonify({"ok": True}), 201
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/funcionarios/<int:id>", methods=["PUT"])
def editar_funcionario(id):
    try:
        d = request.json
        if not d.get("salario") or float(d["salario"]) <= 0:
            return jsonify({"ok": False, "detalhe": "Salário deve ser maior que zero."}), 400
        if float(d["salario"]) > 99999999.99:
            return jsonify({"ok": False, "detalhe": "Salário muito alto. Máximo: R$ 99.999.999,99."}), 400
        exec_sp("sp_atualizar_funcionario", [
            id, d["nome"], d["cargo"], d["salario"], int(d.get("ativo", 1))
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/funcionarios/<int:id>", methods=["DELETE"])
def deletar_funcionario(id):
    try:
        r = query_sql("SELECT * FROM FUNCIONARIO WHERE id_funcionario=?", [id])
        if not r:
            return jsonify({"ok": False, "detalhe": "Funcionário não encontrado."}), 404
        f = r[0]
        exec_sp("sp_atualizar_funcionario", [
            id, f["nome"], f["cargo"], f["salario"], 0
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400

# ═════════════════════════════════════════════════
# FILIAIS
# ═════════════════════════════════════════════════


@app.route("/api/filiais")
def listar_filiais():
    try:
        return jsonify(query_sp("sp_listar_filiais"))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/filiais/<int:id>")
def get_filial(id):
    try:
        r = query_sql("SELECT * FROM FILIAL WHERE id_filial=?", [id])
        return jsonify(r[0]) if r else ("", 404)
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/filiais", methods=["POST"])
def criar_filial():
    try:
        d = request.json
        tel = ''.join(c for c in (d.get("telefone") or "") if c.isdigit())
        if tel and (len(tel) < 10 or len(tel) > 11):
            return jsonify({"ok": False, "detalhe": "Telefone deve ter 10 ou 11 dígitos (com DDD)."}), 400
        if not d.get("dt_inauguracao"):
            return jsonify({"ok": False, "detalhe": "Informe a data de inauguração."}), 400
        exec_sp("sp_inserir_filial", [
            d["nome"], d["cnpj"], tel or None, d["dt_inauguracao"],
            d["logradouro"], d["bairro"], d["cep"], d["cidade"], d["estado"]
        ])
        return jsonify({"ok": True}), 201
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/filiais/<int:id>", methods=["PUT"])
def editar_filial(id):
    try:
        d = request.json
        tel = ''.join(c for c in (d.get("telefone") or "") if c.isdigit())
        if tel and (len(tel) < 10 or len(tel) > 11):
            return jsonify({"ok": False, "detalhe": "Telefone deve ter 10 ou 11 dígitos (com DDD)."}), 400
        if not d.get("dt_inauguracao"):
            return jsonify({"ok": False, "detalhe": "Informe a data de inauguração."}), 400
        exec_sp("sp_atualizar_filial", [
            id, d["nome"], d["cnpj"], tel or None, d["dt_inauguracao"],
            d["logradouro"], d["bairro"], d["cep"], d["cidade"], d["estado"],
            int(d.get("ativo", 1))
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/filiais/<int:id>", methods=["DELETE"])
def deletar_filial(id):
    try:
        r = query_sql("SELECT * FROM FILIAL WHERE id_filial=?", [id])
        if not r:
            return jsonify({"ok": False, "detalhe": "Filial não encontrada."}), 404
        f = r[0]
        exec_sp("sp_atualizar_filial", [
            id, f["nome"], f["cnpj"], f.get("telefone"), f["dt_inauguracao"],
            f["logradouro"], f["bairro"], f["cep"], f["cidade"], f["estado"], 0
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400

# ═════════════════════════════════════════════════
# VEÍCULOS
# ═════════════════════════════════════════════════


@app.route("/api/veiculos")
def listar_veiculos():
    try:
        return jsonify(query_sp("sp_listar_veiculos"))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/veiculos/<int:id>")
def get_veiculo(id):
    try:
        r = query_sql("SELECT * FROM VEICULO WHERE id_veiculo=?", [id])
        return jsonify(r[0]) if r else ("", 404)
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/veiculos", methods=["POST"])
def criar_veiculo():
    try:
        d = request.json
        placa = (d.get("placa") or "").strip()
        if len(placa) < 7:
            return jsonify({"ok": False, "detalhe": "Placa deve ter no mínimo 7 caracteres."}), 400
        ano = d.get("ano")
        if ano is not None:
            try:
                ano = int(ano)
                if ano < 1900 or ano > 2100:
                    return jsonify({"ok": False, "detalhe": "Ano deve estar entre 1900 e 2100."}), 400
            except (ValueError, TypeError):
                return jsonify({"ok": False, "detalhe": "Ano inválido."}), 400
        cap = d.get("capacidade_kg")
        if cap is not None and float(cap) <= 0:
            return jsonify({"ok": False, "detalhe": "Capacidade deve ser maior que zero."}), 400
        if cap is not None and float(cap) > 999999.99:
            return jsonify({"ok": False, "detalhe": "Capacidade muito alta. Máximo: 999.999,99 kg."}), 400
        exec_sp("sp_inserir_veiculo", [
            d["fk_filial"], placa, d["modelo"],
            d.get("marca"), ano, cap
        ])
        return jsonify({"ok": True}), 201
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/veiculos/<int:id>", methods=["PUT"])
def editar_veiculo(id):
    try:
        d = request.json
        placa = (d.get("placa") or "").strip()
        if len(placa) < 7:
            return jsonify({"ok": False, "detalhe": "Placa deve ter no mínimo 7 caracteres."}), 400
        ano = d.get("ano")
        if ano is not None:
            try:
                ano = int(ano)
                if ano < 1900 or ano > 2100:
                    return jsonify({"ok": False, "detalhe": "Ano deve estar entre 1900 e 2100."}), 400
            except (ValueError, TypeError):
                return jsonify({"ok": False, "detalhe": "Ano inválido."}), 400
        cap = d.get("capacidade_kg")
        if cap is not None and float(cap) <= 0:
            return jsonify({"ok": False, "detalhe": "Capacidade deve ser maior que zero."}), 400
        if cap is not None and float(cap) > 999999.99:
            return jsonify({"ok": False, "detalhe": "Capacidade muito alta. Máximo: 999.999,99 kg."}), 400
        exec_sp("sp_atualizar_veiculo", [
            id, d["fk_filial"], placa, d["modelo"],
            d.get("marca"), ano, cap, int(d.get("ativo", 1))
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/veiculos/<int:id>", methods=["DELETE"])
def deletar_veiculo(id):
    try:
        r = query_sql("SELECT * FROM VEICULO WHERE id_veiculo=?", [id])
        if not r:
            return jsonify({"ok": False, "detalhe": "Veículo não encontrado."}), 404
        v = r[0]
        exec_sp("sp_atualizar_veiculo", [
            id, v["fk_filial"], v["placa"], v["modelo"],
            v.get("marca"), v.get("ano"), v.get("capacidade_kg"), 0
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400

# ═════════════════════════════════════════════════
# ENTREGAS
# ═════════════════════════════════════════════════


@app.route("/api/entregas")
def listar_entregas():
    try:
        return jsonify(query_sp("sp_listar_entregas"))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/entregas/<int:id>")
def get_entrega(id):
    try:
        r = query_sql("SELECT * FROM ENTREGA WHERE id_entrega=?", [id])
        return jsonify(r[0]) if r else ("", 404)
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/entregas", methods=["POST"])
def criar_entrega():
    try:
        d = request.json
        exec_sp("sp_inserir_entrega", [
            d["fk_pedido"], d["fk_funcionario"], d["fk_veiculo"],
            d["dt_saida"], d.get("dt_chegada"),
            d.get("status", "PENDENTE"), d.get("observacao")
        ])
        return jsonify({"ok": True}), 201
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/entregas/<int:id>", methods=["PUT"])
def editar_entrega(id):
    try:
        d = request.json
        exec_sp("sp_atualizar_entrega", [
            id, d["fk_pedido"], d["fk_funcionario"], d["fk_veiculo"],
            d["dt_saida"], d.get("dt_chegada"),
            d["status"], d.get("observacao")
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400


@app.route("/api/entregas/<int:id>", methods=["DELETE"])
def deletar_entrega(id):
    try:
        r = query_sql("SELECT * FROM ENTREGA WHERE id_entrega=?", [id])
        if not r:
            return jsonify({"ok": False, "detalhe": "Entrega não encontrada."}), 404
        e = r[0]
        exec_sp("sp_atualizar_entrega", [
            id, e["fk_pedido"], e["fk_funcionario"], e["fk_veiculo"],
            e["dt_saida"], e.get(
                "dt_chegada"), "CANCELADA", e.get("observacao")
        ])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 400

# ═════════════════════════════════════════════════
# AUXILIARES
# ═════════════════════════════════════════════════


@app.route("/api/categorias")
def categorias():
    try:
        return jsonify(query_sp("sp_listar_categorias"))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/estoque")
def estoque():
    try:
        return jsonify(query_sql(
            "SELECT e.fk_produto, e.fk_filial, e.quantidade, e.estoque_minimo, "
            "e.dt_atualizacao, p.descricao AS produto, p.codigo_sku, f.nome AS filial "
            "FROM ESTOQUE e "
            "JOIN PRODUTO p ON p.id_produto=e.fk_produto "
            "JOIN FILIAL  f ON f.id_filial=e.fk_filial "
            "ORDER BY p.descricao, f.nome"
        ))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500

# ═════════════════════════════════════════════════
# RELATÓRIOS / VIEWS
# ═════════════════════════════════════════════════


@app.route("/api/relatorios/pedidos-clientes")
def rel_pedidos_clientes():
    try:
        return jsonify(query_sql("SELECT * FROM vw_pedidos_por_cliente"))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/relatorios/estoque-filial")
def rel_estoque_filial():
    try:
        return jsonify(query_sql("SELECT * FROM vw_posicao_estoque_filial"))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/relatorios/produtos-fornecedor")
def rel_produtos_fornecedor():
    try:
        return jsonify(query_sql("SELECT * FROM vw_produtos_por_fornecedor"))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/relatorios/faturamento-cliente")
def rel_faturamento_cliente():
    try:
        return jsonify(query_sql("SELECT * FROM vw_faturamento_por_cliente"))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


@app.route("/api/relatorios/entregas-motorista-veiculo")
def rel_entregas_motorista_veiculo():
    try:
        return jsonify(query_sql("SELECT * FROM vw_entregas_por_motorista_veiculo"))
    except Exception as e:
        return jsonify({"ok": False, "detalhe": erro_banco(e)}), 500


# ─────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
