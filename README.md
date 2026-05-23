# DistribuiMax S.A. — Sistema de Gestão

Projeto final da disciplina de **Banco de Dados II — UVV**.

O sistema simula a gestão de uma distribuidora de grande porte, com controle de empresas, produtos, pedidos, notas fiscais, funcionários, filiais, veículos, entregas, estoque e relatórios gerenciais.

---

## Tecnologias utilizadas

- **SQL Server 2019/2021**
- **Python 3.10+**
- **Flask**
- **pyodbc**
- **HTML, CSS e JavaScript puro**

---

## Estrutura do projeto

```text
distribuimax_final/
├── app.py
├── banco.sql
├── requirements.txt
├── README.md
└── templates/
    └── index.html
```

---

## Pré-requisitos

Antes de começar, certifique-se de que os seguintes programas estão instalados na máquina:

- **SQL Server 2019 ou 2021** (Express ou Developer) — [download](https://www.microsoft.com/pt-br/sql-server/sql-server-downloads)
- **SQL Server Management Studio (SSMS)** — [download](https://aka.ms/ssmsfullsetup)
- **Python 3.10 ou superior** — [download](https://www.python.org/downloads/)
- **ODBC Driver 17 for SQL Server** — [download](https://learn.microsoft.com/pt-br/sql/connect/odbc/download-odbc-driver-for-sql-server)

> **Atenção:** Durante a instalação do Python, marque a opção **"Add Python to PATH"**.

---

## Instalação passo a passo

### 1. Criar o banco de dados

1. Abra o **SQL Server Management Studio (SSMS)**
2. Conecte ao servidor (normalmente `localhost\SQLEXPRESS` ou `localhost`)
3. Clique em **Arquivo → Abrir → Arquivo...** e selecione o arquivo `banco.sql`
4. Clique em **Executar (F5)**
5. Aguarde a mensagem `Banco DistribuiMax criado com sucesso!!!!`

> Se aparecer erro dizendo que o banco já existe e está em uso, feche todas as outras janelas do SSMS conectadas ao banco e execute novamente.

---

### 2. Instalar as dependências Python

Abra o terminal (Prompt de Comando ou PowerShell) na pasta do projeto e execute:

```bash
pip install flask pyodbc
```

Se preferir usar o arquivo de dependências:

```bash
pip install -r requirements.txt
```

O `requirements.txt` deve conter:

```
flask
pyodbc
```

---

### 3. Configurar a conexão com o banco

Abra o arquivo `app.py` e localize o bloco de configuração no início do arquivo:

```python
DB_SERVER   = "localhost"
DB_NAME     = "DistribuiMax"
DB_USER     = "sa"
DB_PASSWORD = "Distribuimax@2026"
DB_DRIVER   = "ODBC Driver 17 for SQL Server"
```

Ajuste conforme o seu ambiente:

| Campo | O que colocar |
|---|---|
| `DB_SERVER` | Nome do servidor SQL. Use `localhost` ou `localhost\SQLEXPRESS` conforme sua instalação |
| `DB_NAME` | Deixe `DistribuiMax` |
| `DB_USER` | Usuário do SQL Server, normalmente `sa` |
| `DB_PASSWORD` | Senha do usuário `sa` definida na instalação |
| `DB_DRIVER` | Deixe `ODBC Driver 17 for SQL Server` se instalou o driver correto |

> **Como descobrir o nome do servidor:** No SSMS, o nome aparece na tela de conexão em "Nome do servidor". Copie exatamente esse valor.

---

### 4. Verificar se o ODBC Driver está instalado

No Windows, abra o **Painel de Controle → Ferramentas Administrativas → Fontes de Dados ODBC (64 bits)**. Na aba **Drivers**, procure por `ODBC Driver 17 for SQL Server`. Se não aparecer, instale pelo link na seção de pré-requisitos.

---

### 5. Rodar a aplicação

No terminal, dentro da pasta do projeto, execute:

```bash
python app.py
```

A saída esperada é:

```
* Running on http://0.0.0.0:5000
* Debug mode: on
```

Depois acesse no navegador:

```
http://localhost:5000
```

O indicador no canto superior direito da tela mostrará **✅ Banco conectado** se tudo estiver funcionando.

---


## Banco de dados

O arquivo `banco.sql` cria o banco `DistribuiMax` do zero. Ele contém:

- **14 tabelas**
- **27 stored procedures**
- **5 views**
- **3 triggers**
- Dados de exemplo para teste

### Tabelas principais

`FILIAL`, `FUNCIONARIO`, `CATEGORIA`, `PRODUTO`, `EMPRESA`, `FORNECE`, `PEDIDO`, `ITEM_PEDIDO`, `NOTA_FISCAL`, `ITEM_NOTA`, `VEICULO`, `ENTREGA`, `ESTOQUE`, `MOVIMENTACAO`

### Triggers

- `trg_valor_pedido` — recalcula o valor total do pedido automaticamente a cada inserção, alteração ou remoção de itens, já considerando o desconto percentual de cada item.
- `trg_valor_nota` — mesmo comportamento para a nota fiscal.
- `trg_atualiza_estoque` — atualiza o saldo do estoque após cada movimentação. Se ainda não existir registro de estoque para aquele produto e filial, cria automaticamente antes de atualizar.

### Views de relatório

- `vw_pedidos_por_cliente`
- `vw_posicao_estoque_filial`
- `vw_produtos_por_fornecedor`
- `vw_faturamento_por_cliente`
- `vw_entregas_por_motorista_veiculo`

---

## Funcionalidades da interface

| Módulo | Funcionalidades |
|---|---|
| Empresas | Listar, buscar, cadastrar, editar e desativar |
| Produtos | Listar, buscar, cadastrar, editar e desativar |
| Pedidos | Listar, buscar, cadastrar, editar e cancelar |
| Notas Fiscais | Listar, emitir, visualizar itens e excluir |
| Funcionários | Listar, buscar, cadastrar, editar e desativar |
| Filiais | Listar, buscar, cadastrar, editar e desativar |
| Veículos | Listar, buscar, cadastrar, editar e desativar |
| Entregas | Listar, buscar, cadastrar, editar e cancelar |
| Estoque | Consultar posição de estoque por produto e filial |
| Produtos por Fornecedor | Consultar fornecedores e produtos vinculados |
| Categorias | Listar categorias para apoio ao cadastro de produtos |

---
