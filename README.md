# DistribuiMax S.A. — Sistema de Gestão

Projeto de Banco de Dados Relacional  
Disciplina: Banco de Dados II — UVV  
Grupo: Felipe, Frederico, Ian, Paulo, Pedro

---

## Estrutura do projeto

```
distribuimax/
├── banco.sql              ← Script SQL Server (cria banco + dados)
├── app.py                 ← Backend Python/Flask (API REST)
├── requirements.txt       ← Dependências Python
├── templates/
│   └── index.html         ← Frontend (HTML + CSS + JavaScript)
└── README.md
```

---

## Pré-requisitos

- Python 3.10 ou superior
- SQL Server 2019/2021 instalado localmente
- ODBC Driver 17 (ou 18) for SQL Server
- Visual Studio Code (recomendado)

---

## Passo 1 — Criar o banco de dados

1. Abra o **SQL Server Management Studio (SSMS)**
2. Abra o arquivo `banco.sql`
3. Execute com **F5**

O script cria automaticamente:
- O banco `DistribuiMax`
- 13 tabelas normalizadas até 3FN
- 3 triggers (valor_total de pedido, valor_total de nota, atualização de estoque)
- Dados de exemplo (5 filiais, 8 funcionários, 10 produtos, 8 empresas, 5 pedidos, 3 notas fiscais)

---

## Passo 2 — Configurar a conexão

Abra `app.py` e edite as linhas no topo:

```python
DB_SERVER   = "localhost"        # ou nome\instancia, ex: "localhost\SQLEXPRESS"
DB_NAME     = "DistribuiMax"
DB_USER     = "sa"               # seu usuário SQL Server
DB_PASSWORD = "SuaSenhaAqui"     # sua senha
DB_DRIVER   = "ODBC Driver 17 for SQL Server"
```

> **Dica:** Se usar autenticação Windows no lugar de usuário/senha, troque a
> connection string em `get_conn()` para usar `Trusted_Connection=yes`.

---

## Passo 3 — Instalar dependências

Abra o terminal no VSCode (`Ctrl + ```) e execute:

```bash
pip install flask pyodbc
```

---

## Passo 4 — Rodar a aplicação

```bash
python app.py
```

Acesse no navegador: **http://localhost:5000**

O indicador no canto superior direito mostra se o banco está conectado.

---

## Funcionalidades da interface

| Seção         | Listar | Buscar | Inserir | Editar | Excluir |
|---------------|:------:|:------:|:-------:|:------:|:-------:|
| Empresas      | ✅     | ✅     | ✅      | ✅     | ✅ (desativa) |
| Produtos      | ✅     | ✅     | ✅      | ✅     | ✅      |
| Pedidos       | ✅     | ✅     | ✅      | ✅     | ✅      |
| Notas Fiscais | ✅     | ✅     | ✅      | —      | ✅      |
| Funcionários  | ✅     | ✅     | ✅      | ✅     | ✅ (desativa) |
| Estoque       | ✅     | ✅     | —       | —      | —       |

---

## Decisões de modelagem (corrigidas pelo professor)

### 1. ENDERECO removida
Endereço foi incorporado diretamente em `EMPRESA` e `FILIAL`.
Uma tabela separada só se justifica em relação 1:N (empresa com vários endereços).
Como a relação é 1:1, a tabela separada era desnecessária.

### 2. EMPRESA unifica CLIENTE e FORNECEDOR
Uma empresa pode ser cliente, fornecedora ou ambas ao mesmo tempo — situação
comum no mercado. As flags `is_cliente` e `is_fornecedor` controlam o papel.
A constraint `CHECK (is_cliente=1 OR is_fornecedor=1)` garante que toda empresa
tenha pelo menos um papel definido.

### 3. NOTA_FISCAL com recebimento parcial
A relação entre `NOTA_FISCAL` e `PEDIDO` é **N:1** (não 1:1).
Um pedido pode gerar várias notas — recebimento parcial, produtos faltantes, etc.
A tabela `ITEM_NOTA` indica exatamente quais produtos e quantidades cada nota cobre.

---

## Rotas da API

| Método | Rota                        | Descrição                    |
|--------|-----------------------------|------------------------------|
| GET    | /api/health                 | Verifica conexão com o banco |
| GET    | /api/empresas               | Lista empresas (filtro: tipo)|
| POST   | /api/empresas               | Cria empresa                 |
| PUT    | /api/empresas/<id>          | Edita empresa                |
| DELETE | /api/empresas/<id>          | Desativa empresa             |
| GET    | /api/produtos               | Lista produtos               |
| POST   | /api/produtos               | Cria produto                 |
| PUT    | /api/produtos/<id>          | Edita produto                |
| DELETE | /api/produtos/<id>          | Exclui produto               |
| GET    | /api/pedidos                | Lista pedidos                |
| POST   | /api/pedidos                | Cria pedido                  |
| PUT    | /api/pedidos/<id>           | Edita pedido                 |
| DELETE | /api/pedidos/<id>           | Exclui pedido                |
| GET    | /api/notas                  | Lista notas fiscais          |
| GET    | /api/notas/<id>/itens       | Lista itens de uma NF        |
| POST   | /api/notas                  | Emite nota fiscal            |
| DELETE | /api/notas/<id>             | Exclui nota fiscal           |
| GET    | /api/funcionarios           | Lista funcionários           |
| POST   | /api/funcionarios           | Cria funcionário             |
| PUT    | /api/funcionarios/<id>      | Edita funcionário            |
| DELETE | /api/funcionarios/<id>      | Desativa funcionário         |
| GET    | /api/estoque                | Posição de estoque           |
| GET    | /api/categorias             | Lista categorias (dropdown)  |
| GET    | /api/filiais                | Lista filiais (dropdown)     |

---

## Tecnologias utilizadas

| Camada   | Tecnologia                        |
|----------|-----------------------------------|
| Banco    | SQL Server 2019/2021              |
| Backend  | Python 3 + Flask + pyodbc         |
| Frontend | HTML5 + CSS3 + JavaScript (puro)  |
