# DistribuiMax S.A. — Sistema de Gestão

Projeto final da disciplina de **Banco de Dados II — UVV**.

O sistema simula a gestão de uma distribuidora de grande porte, com controle de empresas, produtos, pedidos, notas fiscais, funcionários, filiais, veículos, entregas, estoque e relatórios gerenciais.

---

## Tecnologias utilizadas

- **SQL Server 2019/2021**
- **Python 3**
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

## Banco de dados

O arquivo `banco.sql` cria o banco `DistribuiMax` do zero.

Ele contém:

- **14 tabelas**
- **27 stored procedures**
- **5 views**
- **3 triggers**
- Dados de exemplo para teste

### Tabelas principais

- `FILIAL`
- `FUNCIONARIO`
- `CATEGORIA`
- `PRODUTO`
- `EMPRESA`
- `FORNECE`
- `PEDIDO`
- `ITEM_PEDIDO`
- `NOTA_FISCAL`
- `ITEM_NOTA`
- `VEICULO`
- `ENTREGA`
- `ESTOQUE`
- `MOVIMENTACAO`

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

## Como executar

### 1. Criar o banco

Abra o arquivo `banco.sql` no SQL Server Management Studio ou Azure Data Studio e execute o script completo.

Caso o banco já exista e esteja em uso, feche outras conexões com o banco antes de executar novamente.

---

### 2. Instalar dependências

No terminal, dentro da pasta do projeto, execute:

```bash
pip install -r requirements.txt
```

Se não houver `requirements.txt`, instale manualmente:

```bash
pip install flask pyodbc
```

---

### 3. Configurar a conexão

No arquivo `app.py`, ajuste os dados de conexão conforme seu SQL Server:

```python
DB_SERVER   = "localhost\\SQLEXPRESS"
DB_NAME     = "DistribuiMax"
DB_USER     = "sa"
DB_PASSWORD = "sua_senha"
DB_DRIVER   = "ODBC Driver 17 for SQL Server"
```

---

### 4. Rodar a aplicação

Execute:

```bash
python app.py
```

Depois acesse no navegador:

```text
http://localhost:5000
```

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

## Rotas principais da API

### Sistema

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/health` | Verifica conexão com o banco |

### Empresas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/empresas` | Lista empresas |
| GET | `/api/empresas/<id>` | Busca empresa por ID |
| POST | `/api/empresas` | Cadastra empresa |
| PUT | `/api/empresas/<id>` | Atualiza empresa |
| DELETE | `/api/empresas/<id>` | Desativa empresa |

### Produtos

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/produtos` | Lista produtos |
| GET | `/api/produtos/<id>` | Busca produto por ID |
| POST | `/api/produtos` | Cadastra produto |
| PUT | `/api/produtos/<id>` | Atualiza produto |
| DELETE | `/api/produtos/<id>` | Desativa produto |

### Pedidos

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/pedidos` | Lista pedidos |
| GET | `/api/pedidos/<id>` | Busca pedido por ID |
| POST | `/api/pedidos` | Cadastra pedido |
| PUT | `/api/pedidos/<id>` | Atualiza pedido |
| DELETE | `/api/pedidos/<id>` | Cancela pedido |

### Notas fiscais

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/notas` | Lista notas fiscais |
| GET | `/api/notas/<id>/itens` | Lista itens da nota |
| POST | `/api/notas` | Emite nota fiscal |
| DELETE | `/api/notas/<id>` | Exclui nota fiscal |

### Funcionários, filiais, veículos e entregas

| Método | Rota | Descrição |
|---|---|---|
| GET/POST | `/api/funcionarios` | Lista ou cadastra funcionários |
| PUT/DELETE | `/api/funcionarios/<id>` | Atualiza ou desativa funcionário |
| GET/POST | `/api/filiais` | Lista ou cadastra filiais |
| PUT/DELETE | `/api/filiais/<id>` | Atualiza ou desativa filial |
| GET/POST | `/api/veiculos` | Lista ou cadastra veículos |
| PUT/DELETE | `/api/veiculos/<id>` | Atualiza ou desativa veículo |
| GET/POST | `/api/entregas` | Lista ou cadastra entregas |
| PUT/DELETE | `/api/entregas/<id>` | Atualiza ou cancela entrega |

### Apoio e relatórios

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/categorias` | Lista categorias |
| GET | `/api/estoque` | Lista estoque |
| GET | `/api/relatorios/pedidos-clientes` | Relatório de pedidos por cliente |
| GET | `/api/relatorios/estoque-filial` | Relatório de estoque por filial |
| GET | `/api/relatorios/produtos-fornecedor` | Relatório de produtos por fornecedor |
| GET | `/api/relatorios/faturamento-cliente` | Relatório de faturamento por cliente |
| GET | `/api/relatorios/entregas-motorista-veiculo` | Relatório de entregas por motorista e veículo |

---

## Decisões de modelagem

### Empresa unificada

A tabela `EMPRESA` substitui a separação entre cliente e fornecedor. Uma empresa pode ser cliente, fornecedora ou ambas, usando os campos `is_cliente` e `is_fornecedor`. O banco garante pelo menos um dos dois via constraint `CK_EMPRESA_PAPEL`.

### Nota fiscal parcial

A relação entre `PEDIDO` e `NOTA_FISCAL` é N:1. Assim, um pedido pode gerar mais de uma nota fiscal, permitindo recebimento parcial ou produtos faltantes.

### Endereço direto nas entidades

Os dados de endereço foram mantidos diretamente em `EMPRESA` e `FILIAL`, evitando uma tabela separada para uma relação 1:1.

### Exclusões lógicas

Em vários módulos, a exclusão na interface representa desativação ou cancelamento, preservando o histórico do sistema. Os campos `ativo` e `status` controlam esse comportamento, com valores DEFAULT definidos no próprio banco.

### Separação entre ITEM_PEDIDO e ITEM_NOTA

As tabelas `ITEM_PEDIDO` e `ITEM_NOTA` são separadas porque o que foi pedido pode ser diferente do que foi faturado — especialmente com a lógica de nota parcial. Ambas possuem o campo `desconto_pct` para registrar o desconto aplicado em cada item, e o valor total é recalculado automaticamente pelas triggers correspondentes.

### Tabela FORNECE com atributo próprio

A relação entre empresa e produto não é simples — ela carrega um dado próprio, que é o preço negociado. Por isso existe uma tabela associativa `FORNECE` em vez de uma chave estrangeira direta, permitindo registrar o preço combinado entre fornecedor e produto.

### Nomenclatura de colunas

As colunas seguem a convenção `id_` para chaves primárias e `fk_` para chaves estrangeiras, tornando explícita a natureza de cada campo diretamente pelo nome.

---

## Observações

- O projeto foi desenvolvido para execução local.
- O banco deve estar criado antes de iniciar o Flask.
- O indicador no topo da tela mostra se a conexão com o banco está funcionando.
- Os dados inseridos no SQL são fictícios e servem apenas para demonstração.