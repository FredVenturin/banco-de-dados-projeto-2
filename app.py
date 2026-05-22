"""
DistribuiMax S.A. — Backend
Python + Flask + pyodbc → SQL Server
Todas as operações usam Stored Procedures
"""

import os
from flask import Flask, jsonify, request, render_template
import pyodbc

app = Flask(__name__)

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

def query_sql(sql, params=[]):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return to_list(cur)

def execute_sql(sql, params=[]):
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
            id, d["razao_social"], d["cnpj"], d.get("telefone"), d.get("email"),
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
            id, e["razao_social"], e["cnpj"], e.get("telefone"), e.get("email"),
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
        peso  = d.get("peso_kg")
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
        peso  = d.get("peso_kg")
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
        r = query_sql("SELECT dt_prevista_entrega, observacao FROM PEDIDO WHERE id_pedido=?", [id])
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
            e["dt_saida"], e.get("dt_chegada"), "CANCELADA", e.get("observacao")
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
        return jsonify(query_sp("sp_listar_estoque"))
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