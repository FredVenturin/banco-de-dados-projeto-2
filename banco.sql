-- ============================================================
--  DistribuiMax S.A. — Banco de Dados
--  SQL Server 2019/2021
--  UVV — Disciplina de Banco de Dados II
-- ============================================================
--
--  GO
--    Separa os blocos de código pra o SQL Server executar um por vez.
--    Necessário entre CREATE TABLE, CREATE TRIGGER e CREATE PROCEDURE.
--
--  IDENTITY(1,1)
--    Gera o id automaticamente começando em 1 e somando 1 a cada registro novo.
--    Assim não precisamos informar o id manualmente ao inserir.
--
--  PRIMARY KEY
--    Identifica cada linha de forma única na tabela.
--    Pode ser um campo só (id_filial) ou dois campos juntos (id_pedido + id_produto).
--
--  FOREIGN KEY ... REFERENCES
--    Liga uma tabela a outra. Garante que não existam registros "soltos"
--    — ex: um pedido não pode referenciar um cliente que não existe.
--
--  UNIQUE
--    Garante que o valor não se repita na coluna. Usado em CNPJ, CPF, placa etc.
--
--  NOT NULL / NULL
--    NOT NULL = campo obrigatório. NULL = campo opcional.
--
--  DEFAULT
--    Define um valor padrão quando o campo não é informado.
--    Ex: DEFAULT 1 em "ativo" faz todo registro começar como ativo.
--    Ex: DEFAULT GETDATE() preenche a data/hora atual automaticamente.
--
--  BIT
--    Tipo de dado pra valores verdadeiro/falso. 1 = ativo, 0 = inativo.
--
--  SMALLINT
--    Número inteiro menor que INT. Usado em "ano" pois não precisa de um número grande.
--
--  DECIMAL(x,y)
--    Número com casas decimais. O x é o total de dígitos, o y é quantos são decimais.
--    Ex: DECIMAL(10,2) = até 99999999.99
--
--  CHAR(x)
--    Texto de tamanho fixo. Usado em CNPJ (sempre 14), CPF (sempre 11), CEP (sempre 8).
--
--  VARCHAR(x)
--    Texto de tamanho variável até x caracteres. Usado em nome, descrição etc.
--
--  DATE / DATETIME
--    DATE = só a data (2026-05-18). DATETIME = data e hora (2026-05-18 09:00:00).
--
--  GETDATE()
--    Função do SQL Server que retorna a data e hora atual do servidor.
--
--  CAST(GETDATE() AS DATE)
--    Converte DATETIME pra DATE, descartando a hora. Usado em data_cadastro.
--
--  CONVERT(DATETIME, '...', 120)
--    Converte texto em data usando o formato ISO (AAAA-MM-DD HH:MM).
--    Necessário nos dados de exemplo pra evitar erro de formato regional.
--
--  CONSTRAINT
--    Nome dado a uma regra (FOREIGN KEY, PRIMARY KEY).
--    Serve pra identificar qual regra foi violada quando der erro.
--
--  SCOPE_IDENTITY()
--    Retorna o último id gerado pelo IDENTITY na mesma operação.
--    Usado só em sp_inserir_nota pra saber o id da nota recém criada
--    e conseguir inserir os produtos dela logo em seguida.
--
--  SET NOCOUNT ON
--    Desliga as mensagens "(X linhas afetadas)" dentro das SPs.
--    Sem isso o Python poderia interpretar essas mensagens como resultado de consulta.
--
--  DECLARE @variavel TABLE (...)
--    Cria uma tabela temporária que existe só durante a execução.
--    Usada nos triggers pra guardar os ids afetados temporariamente.
--
--  inserted / deleted
--    Tabelas especiais que existem só dentro de triggers.
--    "inserted" tem as linhas que foram inseridas ou o valor novo do update.
--    "deleted" tem as linhas que foram deletadas ou o valor antigo antes do update.
--
--  ISNULL(valor, substituto)
--    Se o valor for NULL, substitui pelo segundo argumento.
--    Usado nos triggers pra garantir que o total vira 0 e não NULL.
--
--  SUM()
--    Soma todos os valores de uma coluna.
--
--  JOIN
--    Une duas tabelas pelos campos relacionados.
--    Usado nas SPs de listagem pra trazer nomes em vez de só ids.
--
--  ORDER BY ... DESC
--    Ordena o resultado. DESC = do maior pro menor (mais recente primeiro).
--
--  WHERE
--    Filtra os registros. Só retorna ou altera as linhas que atendem a condição.
--
--  ALTER DATABASE ... SET SINGLE_USER WITH ROLLBACK IMMEDIATE
--    Fecha conexões ativas antes de deletar o banco.
--    O DROP DATABASE falha se alguém ainda estiver conectado.
--
-- ============================================================

USE master;  -- banco padrão do SQL Server
GO

IF DB_ID('DistribuiMax') IS NOT NULL   -- se já existir, apaga pra recriar do zero
    DROP DATABASE DistribuiMax;
GO
CREATE DATABASE DistribuiMax;   -- Cria o banco do zero
GO
USE DistribuiMax;   -- Agora entra no nosso banco pra começar a criar as tabelas
GO

-- ============================================================
-- FILIAL 
-- ============================================================
CREATE TABLE FILIAL (
    id_filial      INT IDENTITY(1,1) PRIMARY KEY,
    nome           VARCHAR(100) NOT NULL,
    cnpj           CHAR(14)     NOT NULL UNIQUE,
    telefone       VARCHAR(20)  NULL,
    dt_inauguracao DATE         NOT NULL,
    logradouro     VARCHAR(150) NOT NULL,
    bairro         VARCHAR(100) NOT NULL,
    cep            CHAR(8)      NOT NULL,
    cidade         VARCHAR(80)  NOT NULL,
    estado         CHAR(2)      NOT NULL
);
GO

-- ============================================================
-- FUNCIONARIO
-- ============================================================
CREATE TABLE FUNCIONARIO (
    id_funcionario INT IDENTITY(1,1) PRIMARY KEY,
    id_filial      INT           NOT NULL,
    nome           VARCHAR(100)  NOT NULL,
    cpf            CHAR(11)      NOT NULL UNIQUE,
    cargo          VARCHAR(60)   NOT NULL,
    salario        DECIMAL(10,2) NOT NULL,
    dt_admissao    DATE          NOT NULL,
    dt_demissao    DATE          NULL,
    ativo          BIT           NOT NULL DEFAULT 1,
    CONSTRAINT FK_FUNC_FILIAL FOREIGN KEY (id_filial) REFERENCES FILIAL(id_filial)
);
GO

-- ============================================================
-- CATEGORIA
-- ============================================================
CREATE TABLE CATEGORIA (
    id_categoria INT IDENTITY(1,1) PRIMARY KEY,
    nome         VARCHAR(80)  NOT NULL,
    descricao    VARCHAR(255) NULL
);
GO

-- ============================================================
-- PRODUTO
-- ============================================================
CREATE TABLE PRODUTO (
    id_produto     INT IDENTITY(1,1) PRIMARY KEY,
    id_categoria   INT           NOT NULL,
    codigo_sku     VARCHAR(30)   NOT NULL UNIQUE,
    descricao      VARCHAR(150)  NOT NULL,
    unidade_medida VARCHAR(20)   NOT NULL,
    preco_custo    DECIMAL(10,2) NOT NULL,
    preco_venda    DECIMAL(10,2) NOT NULL,
    peso_kg        DECIMAL(8,3)  NULL,
    ativo          BIT           NOT NULL DEFAULT 1,
    CONSTRAINT FK_PROD_CAT FOREIGN KEY (id_categoria) REFERENCES CATEGORIA(id_categoria)
);
GO

-- ============================================================
-- EMPRESA  (unifica CLIENTE e FORNECEDOR)
-- Uma empresa pode ser cliente, fornecedora ou ambas.
-- ============================================================
CREATE TABLE EMPRESA (
    id_empresa          INT IDENTITY(1,1) PRIMARY KEY,
    razao_social        VARCHAR(120)  NOT NULL,
    cnpj                CHAR(14)      NOT NULL UNIQUE,
    telefone            VARCHAR(20)   NULL,
    email               VARCHAR(100)  NULL,
    contato_responsavel VARCHAR(100)  NULL,
    data_cadastro       DATE          NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    ativo               BIT           NOT NULL DEFAULT 1,
    is_cliente          BIT           NOT NULL DEFAULT 0,
    is_fornecedor       BIT           NOT NULL DEFAULT 0,
    limite_credito      DECIMAL(12,2) NULL DEFAULT 0,
    logradouro          VARCHAR(150)  NOT NULL,
    bairro              VARCHAR(100)  NOT NULL,
    cep                 CHAR(8)       NOT NULL,
    cidade              VARCHAR(80)   NOT NULL,
    estado              CHAR(2)       NOT NULL
);
GO

-- ============================================================
-- FORNECE  
-- ============================================================
CREATE TABLE FORNECE (
    id_empresa         INT           NOT NULL,
    id_produto         INT           NOT NULL,
    preco_negociado    DECIMAL(10,2) NOT NULL,
    prazo_entrega_dias INT           NULL,
    dt_ultima_entrega  DATE          NULL,
    CONSTRAINT PK_FORNECE     PRIMARY KEY (id_empresa, id_produto),
    CONSTRAINT FK_FORN_EMP    FOREIGN KEY (id_empresa) REFERENCES EMPRESA(id_empresa),
    CONSTRAINT FK_FORN_PROD   FOREIGN KEY (id_produto) REFERENCES PRODUTO(id_produto)
);
GO

-- ============================================================
-- PEDIDO
-- ============================================================
CREATE TABLE PEDIDO (
    id_pedido           INT IDENTITY(1,1) PRIMARY KEY,
    id_empresa          INT           NOT NULL,
    id_filial           INT           NOT NULL,
    dt_pedido           DATETIME      NOT NULL DEFAULT GETDATE(),
    dt_prevista_entrega DATE          NULL,
    status              VARCHAR(15)   NOT NULL DEFAULT 'AGUARDANDO',
    observacao          VARCHAR(300)  NULL,
    valor_total         DECIMAL(12,2) NULL,
    CONSTRAINT FK_PED_EMP    FOREIGN KEY (id_empresa) REFERENCES EMPRESA(id_empresa),
    CONSTRAINT FK_PED_FILIAL FOREIGN KEY (id_filial)  REFERENCES FILIAL(id_filial)
);
GO

-- ============================================================
-- ITEM_PEDIDO  (N:M — PEDIDO × PRODUTO)
-- ============================================================
CREATE TABLE ITEM_PEDIDO (
    id_pedido      INT           NOT NULL,
    id_produto     INT           NOT NULL,
    quantidade     INT           NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    desconto_pct   DECIMAL(5,2)  NULL DEFAULT 0,  
    CONSTRAINT PK_ITEM_PED  PRIMARY KEY (id_pedido, id_produto),
    CONSTRAINT FK_ITEM_PED  FOREIGN KEY (id_pedido)  REFERENCES PEDIDO(id_pedido),
    CONSTRAINT FK_ITEM_PROD FOREIGN KEY (id_produto) REFERENCES PRODUTO(id_produto)
);
GO

-- ============================================================
-- NOTA_FISCAL
-- Relação N:1 com PEDIDO — um pedido pode gerar VÁRIAS notas
-- (recebimento parcial, produtos faltantes, etc.)
-- ============================================================
CREATE TABLE NOTA_FISCAL (
    id_nf        INT IDENTITY(1,1) PRIMARY KEY,
    id_pedido    INT          NOT NULL,          -- N:1 portanto SEM UNIQUE
    numero_nf    VARCHAR(20)  NOT NULL UNIQUE,
    serie        CHAR(3)      NOT NULL DEFAULT '001',
    dt_emissao   DATETIME     NOT NULL DEFAULT GETDATE(),
    chave_acesso CHAR(44)     NULL,
    valor_total  DECIMAL(12,2) NULL,
    CONSTRAINT FK_NF_PEDIDO FOREIGN KEY (id_pedido) REFERENCES PEDIDO(id_pedido)
);
GO

-- ============================================================
-- ITEM_NOTA  (N:M — NOTA_FISCAL × PRODUTO)
-- Indica exatamente quais produtos cada nota cobre.
-- ============================================================
CREATE TABLE ITEM_NOTA (
    id_nf          INT           NOT NULL,
    id_produto     INT           NOT NULL,
    quantidade     INT           NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    CONSTRAINT PK_ITEM_NOTA  PRIMARY KEY (id_nf, id_produto),
    CONSTRAINT FK_INOTA_NF   FOREIGN KEY (id_nf)      REFERENCES NOTA_FISCAL(id_nf),
    CONSTRAINT FK_INOTA_PROD FOREIGN KEY (id_produto) REFERENCES PRODUTO(id_produto)
);
GO

-- ============================================================
-- VEICULO
-- ============================================================
CREATE TABLE VEICULO (
    id_veiculo    INT IDENTITY(1,1) PRIMARY KEY,
    id_filial     INT          NOT NULL,
    placa         VARCHAR(8)   NOT NULL UNIQUE,
    modelo        VARCHAR(60)  NOT NULL,
    marca         VARCHAR(40)  NULL,
    ano           SMALLINT     NULL,
    capacidade_kg DECIMAL(8,2) NULL,
    ativo         BIT          NOT NULL DEFAULT 1,
    CONSTRAINT FK_VEI_FILIAL FOREIGN KEY (id_filial) REFERENCES FILIAL(id_filial)
);
GO

-- ============================================================
-- ENTREGA
-- ============================================================
CREATE TABLE ENTREGA (
    id_entrega     INT IDENTITY(1,1) PRIMARY KEY,
    id_pedido      INT          NOT NULL,
    id_funcionario INT          NOT NULL,
    id_veiculo     INT          NOT NULL,
    dt_saida       DATETIME     NOT NULL,
    dt_chegada     DATETIME     NULL,
    status         VARCHAR(15)  NOT NULL DEFAULT 'PENDENTE',
    observacao     VARCHAR(300) NULL,
    CONSTRAINT FK_ENT_PED  FOREIGN KEY (id_pedido)      REFERENCES PEDIDO(id_pedido),
    CONSTRAINT FK_ENT_FUNC FOREIGN KEY (id_funcionario) REFERENCES FUNCIONARIO(id_funcionario),
    CONSTRAINT FK_ENT_VEI  FOREIGN KEY (id_veiculo)     REFERENCES VEICULO(id_veiculo)
);
GO

-- ============================================================
-- ESTOQUE  (N:M — PRODUTO × FILIAL)
-- ============================================================
CREATE TABLE ESTOQUE (
    id_produto     INT      NOT NULL,
    id_filial      INT      NOT NULL,
    quantidade     INT      NOT NULL DEFAULT 0,
    estoque_minimo INT      NOT NULL DEFAULT 0,
    dt_atualizacao DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT PK_ESTOQUE    PRIMARY KEY (id_produto, id_filial),
    CONSTRAINT FK_EST_PROD   FOREIGN KEY (id_produto) REFERENCES PRODUTO(id_produto),
    CONSTRAINT FK_EST_FILIAL FOREIGN KEY (id_filial)  REFERENCES FILIAL(id_filial)
);
GO

-- ============================================================
-- MOVIMENTACAO
-- ============================================================
CREATE TABLE MOVIMENTACAO (
    id_movimentacao INT IDENTITY(1,1) PRIMARY KEY,
    id_produto      INT           NOT NULL,
    id_filial       INT           NOT NULL,
    id_funcionario  INT           NOT NULL,
    tipo            VARCHAR(6)    NOT NULL,
    quantidade      INT           NOT NULL,
    motivo          VARCHAR(150)  NULL,
    dt_movimentacao DATETIME      NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_MOV_PROD  FOREIGN KEY (id_produto)     REFERENCES PRODUTO(id_produto),
    CONSTRAINT FK_MOV_FILIAL FOREIGN KEY (id_filial)     REFERENCES FILIAL(id_filial),
    CONSTRAINT FK_MOV_FUNC  FOREIGN KEY (id_funcionario) REFERENCES FUNCIONARIO(id_funcionario)
);
GO


-- ==================================================
-- TRIGGERS
-- ==================================================


-- ============================================================
-- TRIGGER: Recalcula valor_total do PEDIDO após mudança em ITEM_PEDIDO
-- ============================================================
CREATE OR ALTER TRIGGER trg_valor_pedido
ON ITEM_PEDIDO AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    -- tabela temporária pra guardar os ids dos pedidos afetados
    DECLARE @ids TABLE (id_pedido INT);

    -- captura os pedidos que foram inseridos ou atualizados
    INSERT INTO @ids SELECT id_pedido FROM inserted;

    -- captura também os pedidos que tiveram itens deletados
    INSERT INTO @ids SELECT id_pedido FROM deleted;

    -- recalcula o valor total somando quantidade × preço de todos os itens do pedido
    -- ISNULL para garantir que o NULL se torna 0 
    UPDATE P SET P.valor_total = (
        SELECT ISNULL(SUM(ip.quantidade * ip.preco_unitario), 0)
        FROM ITEM_PEDIDO ip WHERE ip.id_pedido = P.id_pedido
    )
    FROM PEDIDO P INNER JOIN @ids I ON I.id_pedido = P.id_pedido;
END;
GO

-- ============================================================
-- TRIGGER: Recalcula valor_total da NOTA_FISCAL após mudança em ITEM_NOTA
-- ============================================================
CREATE OR ALTER TRIGGER trg_valor_nota
ON ITEM_NOTA AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    -- tabela temporária pra guardar os ids das notas afetadas
    DECLARE @ids TABLE (id_nf INT);

    -- captura as notas que foram inseridas ou atualizadas
    INSERT INTO @ids SELECT id_nf FROM inserted;

    -- captura também as notas que tiveram itens deletados
    INSERT INTO @ids SELECT id_nf FROM deleted;

    -- recalcula o valor total somando quantidade × preço de todos os itens da nota
    -- ISNULL para garantir que o NULL se torna 0
    UPDATE N SET N.valor_total = (
        SELECT ISNULL(SUM(it.quantidade * it.preco_unitario), 0)
        FROM ITEM_NOTA it WHERE it.id_nf = N.id_nf
    )
    FROM NOTA_FISCAL N INNER JOIN @ids I ON I.id_nf = N.id_nf;
END;
GO

-- ============================================================
-- TRIGGER: Atualiza ESTOQUE após MOVIMENTACAO
-- ============================================================
CREATE OR ALTER TRIGGER trg_atualiza_estoque
ON MOVIMENTACAO AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    -- se for entrada ou ajuste, soma a quantidade no estoque
    UPDATE E SET E.quantidade = E.quantidade + I.quantidade, E.dt_atualizacao = GETDATE()
    FROM ESTOQUE E INNER JOIN inserted I ON I.id_produto = E.id_produto AND I.id_filial = E.id_filial
    WHERE I.tipo IN ('ENTRADA','AJUSTE');

    -- se for saída, subtrai a quantidade do estoque
    UPDATE E SET E.quantidade = E.quantidade - I.quantidade, E.dt_atualizacao = GETDATE()
    FROM ESTOQUE E INNER JOIN inserted I ON I.id_produto = E.id_produto AND I.id_filial = E.id_filial
    WHERE I.tipo = 'SAIDA';
END;
GO
-- ===============================================================================================================
-- DADOS DE EXEMPLO   (valores totalmente de exemplo, identados corretamente mas informações totalmente ficticias)
-- ===============================================================================================================

INSERT INTO FILIAL (nome,cnpj,telefone,dt_inauguracao,logradouro,bairro,cep,cidade,estado) VALUES
('DistribuiMax - Vila Velha','12345678000191','(27) 3300-1001','2010-03-15','Av. Getúlio Vargas, 1500','Centro','29100010','Vila Velha','ES'),
('DistribuiMax - Vitória',   '12345678000272','(27) 3300-1002','2012-07-20','Rua das Palmeiras, 320',  'Jardim América','29020050','Vitória','ES'),
('DistribuiMax - Cachoeiro', '12345678000353','(28) 3300-1003','2015-01-10','Av. Brasil, 900',          'Industrial','29300100','Cachoeiro','ES'),
('DistribuiMax - Cariacica', '12345678000434','(27) 3300-1004','2018-05-05','Rua das Acácias, 200',     'Centro','29140010','Cariacica','ES'),
('DistribuiMax - Linhares',  '12345678000515','(27) 3300-1005','2020-09-01','Rua Sete de Setembro, 780','Centro','29500010','Linhares','ES');

INSERT INTO FUNCIONARIO (id_filial,nome,cpf,cargo,salario,dt_admissao) VALUES
(1,'Carlos Eduardo Silva',  '11122233344','Gerente',            8500.00,'2010-03-15'),
(1,'Ana Paula Ferreira',    '22233344455','Motorista',          3200.00,'2011-06-01'),
(2,'Marcos Antônio Costa',  '33344455566','Gerente',            8500.00,'2012-07-20'),
(2,'Juliana Ramos Souza',   '44455566677','Analista de Estoque',4100.00,'2013-02-10'),
(3,'Roberto Lima Neto',     '55566677788','Motorista',          3200.00,'2015-01-10'),
(1,'Fernanda Dias Oliveira','66677788899','Vendedor',           2800.00,'2016-08-15'),
(4,'Paulo Sérgio Andrade',  '77788899900','Motorista',          3200.00,'2018-06-01'),
(5,'Luciana Matos Borges',  '88899900011','Analista de Estoque',4100.00,'2020-09-01');

INSERT INTO CATEGORIA (nome,descricao) VALUES
('Alimentos',         'Produtos alimentícios em geral'),
('Higiene Pessoal',   'Produtos de higiene e cuidados pessoais'),
('Limpeza',           'Produtos de limpeza doméstica e industrial'),
('Bebidas',           'Bebidas alcoólicas e não alcoólicas'),
('Frios e Laticínios','Queijos, frios, leites e derivados');

INSERT INTO PRODUTO (id_categoria,codigo_sku,descricao,unidade_medida,preco_custo,preco_venda,peso_kg) VALUES
(1,'ALI-001','Arroz Tipo 1 5kg',       'PCT', 12.50,18.90,5.000),
(1,'ALI-002','Feijão Carioca 1kg',      'PCT',  5.80, 9.50,1.000),
(1,'ALI-003','Óleo de Soja 900ml',      'UND',  6.20, 9.90,0.900),
(2,'HIG-001','Sabonete Antibacteriano', 'UND',  1.50, 3.20,0.085),
(2,'HIG-002','Shampoo 400ml',           'UND',  7.00,13.50,0.400),
(3,'LIM-001','Detergente 500ml',        'UND',  2.10, 4.50,0.500),
(3,'LIM-002','Água Sanitária 1L',       'UND',  3.00, 5.90,1.100),
(4,'BEB-001','Refrigerante Cola 2L',    'UND',  4.50, 7.80,2.200),
(4,'BEB-002','Suco de Laranja 1L',      'UND',  5.00, 8.50,1.050),
(5,'FRI-001','Queijo Mussarela 500g',   'PCT', 14.00,22.90,0.500);

-- Apenas clientes
INSERT INTO EMPRESA (razao_social,cnpj,telefone,email,is_cliente,is_fornecedor,limite_credito,logradouro,bairro,cep,cidade,estado) VALUES
('Supermercado Central Ltda','11223344000101','(21) 2500-1000','compras@supcentral.com.br', 1,0,50000.00,'Av. Rio Branco, 500',    'Centro',    '20040020','Rio de Janeiro','RJ'),
('Mercado Bom Preço ME',     '22334455000102','(11) 3300-2000','compras@bompreco.com.br',   1,0,20000.00,'Av. Paulista, 1000',     'Bela Vista','01310100','São Paulo',      'SP'),
('Mini Mercado Vitória',     '33445566000103','(27) 3100-3000','compras@minivix.com.br',    1,0,10000.00,'Av. Leitão da Silva, 40','Universitário','29075010','Vitória',     'ES'),
('Rede de Padarias ES Ltda', '44556677000104','(27) 3200-4000','fin@padarias.com.br',       1,0,30000.00,'Rua das Acácias, 200',  'Centro',    '29140010','Cariacica',      'ES');

-- Apenas fornecedores
INSERT INTO EMPRESA (razao_social,cnpj,telefone,email,contato_responsavel,is_cliente,is_fornecedor,logradouro,bairro,cep,cidade,estado) VALUES
('Alimentos Nacionais Ltda',   '98765432000100','(21) 3200-5000','contato@alimnac.com.br',  'Rodrigo Mendes',0,1,'Rua João Pessoa, 55',            'Bairro de Fátima','20050002','Rio de Janeiro','RJ'),
('Higiene & Cia Distribuidora','87654321000200','(11) 3100-4000','vendas@higienecia.com.br','Carla Souza',   0,1,'Av. Faria Lima, 100',             'Pinheiros',      '05426100','São Paulo',     'SP'),
('BebMax Indústria de Bebidas','76543210000300','(27) 3050-2000','pedidos@bebmax.com.br',   'Thiago Alves',  0,1,'Av. Leitão da Silva, 400',        'Universitário',  '29075010','Vitória',       'ES');

-- Cliente E fornecedor ao mesmo tempo
INSERT INTO EMPRESA (razao_social,cnpj,telefone,email,contato_responsavel,is_cliente,is_fornecedor,limite_credito,logradouro,bairro,cep,cidade,estado) VALUES
('Distribuidora Norte ES Ltda','55667788000105','(27) 3400-5000','contato@northes.com.br','Marcos Vinicius',1,1,15000.00,'Rua Sete de Setembro, 780','Centro','29500010','Linhares','ES');

INSERT INTO FORNECE (id_empresa,id_produto,preco_negociado,prazo_entrega_dias,dt_ultima_entrega) VALUES
(5,1,11.00,3,'2026-04-10'),(5,2,5.00,3,'2026-04-10'),(5,3,5.50,5,'2026-03-28'),
(6,4,1.20,7,'2026-04-05'),(6,5,6.50,7,'2026-04-05'),(6,6,1.80,5,'2026-04-01'),(6,7,2.70,5,'2026-04-01'),
(7,8,4.00,2,'2026-04-15'),(7,9,4.50,2,'2026-04-15'),
(8,1,12.00,4,'2026-04-08'),(8,8,4.20,3,'2026-04-08');

INSERT INTO PEDIDO (id_empresa,id_filial,dt_pedido,dt_prevista_entrega,status) VALUES
(1,1,CONVERT(DATETIME,'2026-04-20 09:00',120),'2026-04-23','ENTREGUE'),
(2,2,CONVERT(DATETIME,'2026-04-22 10:30',120),'2026-04-25','APROVADO'),
(3,1,CONVERT(DATETIME,'2026-04-25 14:00',120),'2026-04-28','AGUARDANDO'),
(4,3,CONVERT(DATETIME,'2026-05-01 08:00',120),'2026-05-05','APROVADO'),
(8,4,CONVERT(DATETIME,'2026-05-05 11:00',120),'2026-05-08','AGUARDANDO');

INSERT INTO ITEM_PEDIDO (id_pedido,id_produto,quantidade,preco_unitario,desconto_pct) VALUES
(1,1,100,18.90,0.00),(1,2,50,9.50,0.00),(1,6,200,4.50,5.00),
(2,4,300,3.20,0.00),(2,5,150,13.50,0.00),(2,8,200,7.80,3.00),
(3,3,80,9.90,0.00),(3,7,100,5.90,0.00),
(4,1,60,18.90,2.50),(4,9,80,8.50,0.00),
(5,8,120,7.80,0.00),(5,10,40,22.90,5.00);

-- Pedido 1 gerou 2 notas (recebimento parcial)
INSERT INTO NOTA_FISCAL (id_pedido,numero_nf,serie,dt_emissao) VALUES
(1,'NF-2026-00001','001',CONVERT(DATETIME,'2026-04-20 09:15',120)),
(1,'NF-2026-00002','001',CONVERT(DATETIME,'2026-04-21 08:00',120)),
(2,'NF-2026-00003','001',CONVERT(DATETIME,'2026-04-22 10:45',120));

INSERT INTO ITEM_NOTA (id_nf,id_produto,quantidade,preco_unitario) VALUES
(1,1,100,18.90),(1,2,50,9.50),   -- NF1: arroz + feijão
(2,6,200,4.50),                  -- NF2: detergente (faltou na 1ª entrega)
(3,4,300,3.20),(3,5,150,13.50),(3,8,200,7.80);

INSERT INTO VEICULO (id_filial,placa,modelo,marca,ano,capacidade_kg) VALUES
(1,'QRS1234','Delivery 3/4','Fiat',    2021,4000.00),
(1,'QRS5678','Sprinter',    'Mercedes',2020,3500.00),
(2,'ABC9012','HR',          'Hyundai', 2022,3000.00),
(3,'DEF3456','Delivery 3/4','Fiat',    2019,4000.00),
(4,'GHI7890','Sprinter',    'Mercedes',2023,3500.00);

INSERT INTO ENTREGA (id_pedido,id_funcionario,id_veiculo,dt_saida,dt_chegada,status) VALUES
(1,2,1,CONVERT(DATETIME,'2026-04-23 07:00',120),CONVERT(DATETIME,'2026-04-23 14:30',120),'ENTREGUE'),
(2,3,3,CONVERT(DATETIME,'2026-04-25 07:30',120),NULL,'EM_ROTA');

INSERT INTO ESTOQUE (id_produto,id_filial,quantidade,estoque_minimo) VALUES
(1,1,500,50),(1,2,300,30),(2,1,400,40),(2,2,200,20),
(3,1,350,30),(3,3,150,20),(4,1,800,80),(4,2,600,60),
(5,2,250,25),(5,4,180,20),(6,1,700,70),(6,3,400,40),
(7,1,600,60),(7,2,350,35),(8,1,450,45),(8,4,300,30),
(9,2,200,20),(9,5,150,15),(10,1,12,15),(10,2,8,10);

PRINT 'Banco DistribuiMax criado com sucesso!!!!';
GO



-- ======================================
-- STORED PROCEDURES
-- ======================================



-- ============================================================
-- STORED PROCEDURES — EMPRESA
-- ============================================================

CREATE OR ALTER PROCEDURE sp_inserir_empresa
    -- recebe todos os dados necessários pra cadastrar uma nova empresa
    -- campos com = NULL são opcionais, não precisam ser informados
    @razao_social VARCHAR(120), @cnpj CHAR(14), @telefone VARCHAR(20) = NULL,
    @email VARCHAR(100) = NULL, @contato_responsavel VARCHAR(100) = NULL,
    @is_cliente BIT, @is_fornecedor BIT, @limite_credito DECIMAL(12,2) = 0,
    @logradouro VARCHAR(150), @bairro VARCHAR(100), @cep CHAR(8),
    @cidade VARCHAR(80), @estado CHAR(2)
AS
BEGIN
    SET NOCOUNT ON;
    -- insere a empresa com todos os dados recebidos
    INSERT INTO EMPRESA (razao_social,cnpj,telefone,email,contato_responsavel,
        is_cliente,is_fornecedor,limite_credito,logradouro,bairro,cep,cidade,estado)
    VALUES (@razao_social,@cnpj,@telefone,@email,@contato_responsavel,
        @is_cliente,@is_fornecedor,@limite_credito,@logradouro,@bairro,@cep,@cidade,@estado);
END;
GO




CREATE OR ALTER PROCEDURE sp_atualizar_empresa
    -- recebe o id pra saber qual empresa editar
    -- todos os campos são reescritos, então precisa mandar tudo mesmo que não mudou
    @id_empresa INT, @razao_social VARCHAR(120), @cnpj CHAR(14),
    @telefone VARCHAR(20) = NULL, @email VARCHAR(100) = NULL,
    @contato_responsavel VARCHAR(100) = NULL, @is_cliente BIT, @is_fornecedor BIT,
    @limite_credito DECIMAL(12,2) = 0, @logradouro VARCHAR(150),
    @bairro VARCHAR(100), @cep CHAR(8), @cidade VARCHAR(80), @estado CHAR(2), @ativo BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    -- atualiza todos os campos da empresa de uma vez
    -- o WHERE garante que só a empresa com esse id seja alterada
    UPDATE EMPRESA SET razao_social=@razao_social, cnpj=@cnpj, telefone=@telefone,
        email=@email, contato_responsavel=@contato_responsavel,
        is_cliente=@is_cliente, is_fornecedor=@is_fornecedor,
        limite_credito=@limite_credito, logradouro=@logradouro, bairro=@bairro,
        cep=@cep, cidade=@cidade, estado=@estado, ativo=@ativo
    WHERE id_empresa=@id_empresa;
END;
GO




CREATE OR ALTER PROCEDURE sp_desativar_empresa
    -- recebe só o id da empresa que vai ser desativada
    @id_empresa INT
AS
BEGIN
    SET NOCOUNT ON;
    -- não deleta a empresa, só marca como inativa pra preservar o histórico
    -- assim os pedidos e notas antigas ainda conseguem referenciar ela
    UPDATE EMPRESA SET ativo=0 WHERE id_empresa=@id_empresa;
END;
GO




CREATE OR ALTER PROCEDURE sp_listar_empresas
    -- o parâmetro tipo filtra a listagem
    -- aceita 'cliente', 'fornecedor' ou 'todos' — padrão é todos
    @tipo VARCHAR(12) = 'todos'
AS
BEGIN
    SET NOCOUNT ON;
    -- o WHERE usa OR pra cobrir os três casos possíveis do filtro
    -- retorna ordenado por nome pra facilitar a visualização
    SELECT id_empresa,razao_social,cnpj,telefone,email,contato_responsavel,
           cidade,estado,ativo,is_cliente,is_fornecedor,limite_credito
    FROM EMPRESA
    WHERE (@tipo='cliente'    AND is_cliente=1)
       OR (@tipo='fornecedor' AND is_fornecedor=1)
       OR (@tipo='todos')
    ORDER BY razao_social;
END;
GO




-- ============================================================
-- STORED PROCEDURES — PRODUTO
-- ============================================================

CREATE OR ALTER PROCEDURE sp_inserir_produto
    -- recebe os dados do produto e o id da categoria que ele pertence
    -- peso_kg é opcional, nem todo produto tem peso relevante
    @id_categoria INT, @codigo_sku VARCHAR(30), @descricao VARCHAR(150),
    @unidade_medida VARCHAR(20), @preco_custo DECIMAL(10,2),
    @preco_venda DECIMAL(10,2), @peso_kg DECIMAL(8,3) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO PRODUTO (id_categoria,codigo_sku,descricao,unidade_medida,preco_custo,preco_venda,peso_kg)
    VALUES (@id_categoria,@codigo_sku,@descricao,@unidade_medida,@preco_custo,@preco_venda,@peso_kg);
END;
GO





CREATE OR ALTER PROCEDURE sp_atualizar_produto
    -- recebe o id do produto e todos os campos editáveis
    -- ativo permite reativar um produto que estava desativado
    @id_produto INT, @id_categoria INT, @codigo_sku VARCHAR(30),
    @descricao VARCHAR(150), @unidade_medida VARCHAR(20),
    @preco_custo DECIMAL(10,2), @preco_venda DECIMAL(10,2),
    @peso_kg DECIMAL(8,3) = NULL, @ativo BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    -- atualiza todos os campos do produto de uma vez
    -- o WHERE garante que só o produto com esse id seja alterado
    UPDATE PRODUTO SET id_categoria=@id_categoria, codigo_sku=@codigo_sku,
        descricao=@descricao, unidade_medida=@unidade_medida,
        preco_custo=@preco_custo, preco_venda=@preco_venda,
        peso_kg=@peso_kg, ativo=@ativo
    WHERE id_produto=@id_produto;
END;
GO




CREATE OR ALTER PROCEDURE sp_deletar_produto
    -- recebe só o id do produto a ser deletado
    -- cuidado: só funciona se o produto não tiver itens de pedido vinculados
    @id_produto INT
AS
BEGIN
    SET NOCOUNT ON;
    -- deleta permanentemente, diferente de empresa e funcionário que só desativam
    DELETE FROM PRODUTO WHERE id_produto=@id_produto;
END;
GO





CREATE OR ALTER PROCEDURE sp_listar_produtos
AS
BEGIN
    SET NOCOUNT ON;
    -- traz o nome da categoria via JOIN pra não retornar só o id
    -- ordenado por descrição pra facilitar a busca na tela
    SELECT p.id_produto,p.codigo_sku,p.descricao,p.unidade_medida,
           p.preco_custo,p.preco_venda,p.peso_kg,p.ativo,p.id_categoria,
           c.nome AS categoria
    FROM PRODUTO p JOIN CATEGORIA c ON c.id_categoria=p.id_categoria
    ORDER BY p.descricao;
END;
GO





-- ============================================================
-- STORED PROCEDURES — PEDIDO
-- ============================================================

CREATE OR ALTER PROCEDURE sp_inserir_pedido
    -- recebe o id da empresa cliente e da filial responsável pelo pedido
    -- status e data de entrega são opcionais na criação
    @id_empresa INT, @id_filial INT,
    @dt_prevista_entrega DATE = NULL,
    @status VARCHAR(15) = 'AGUARDANDO',
    @observacao VARCHAR(300) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO PEDIDO (id_empresa,id_filial,dt_prevista_entrega,status,observacao)
    VALUES (@id_empresa,@id_filial,@dt_prevista_entrega,@status,@observacao);
END;
GO





CREATE OR ALTER PROCEDURE sp_atualizar_pedido
    -- só permite editar status, data prevista e observação
    -- cliente e filial não mudam depois que o pedido foi criado
    @id_pedido INT, @status VARCHAR(15),
    @dt_prevista_entrega DATE = NULL, @observacao VARCHAR(300) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE PEDIDO SET status=@status, dt_prevista_entrega=@dt_prevista_entrega,
        observacao=@observacao
    WHERE id_pedido=@id_pedido;
END;
GO





CREATE OR ALTER PROCEDURE sp_deletar_pedido
    -- recebe o id do pedido que vai ser removido
    @id_pedido INT
AS
BEGIN
    SET NOCOUNT ON;
    -- deleta os itens primeiro por causa da chave estrangeira
    -- sem isso o banco bloquearia a exclusão do pedido
    DELETE FROM ITEM_PEDIDO WHERE id_pedido=@id_pedido;
    DELETE FROM PEDIDO       WHERE id_pedido=@id_pedido;
END;
GO






CREATE OR ALTER PROCEDURE sp_listar_pedidos
AS
BEGIN
    SET NOCOUNT ON;
    -- traz o nome do cliente e da filial via JOIN pra não retornar só ids
    -- ordenado do mais recente pro mais antigo
    SELECT p.id_pedido,p.dt_pedido,p.status,p.valor_total,
           p.dt_prevista_entrega,p.observacao,p.id_empresa,p.id_filial,
           e.razao_social AS cliente, f.nome AS filial
    FROM PEDIDO p
    JOIN EMPRESA e ON e.id_empresa=p.id_empresa
    JOIN FILIAL  f ON f.id_filial=p.id_filial
    ORDER BY p.dt_pedido DESC;
END;
GO





-- ============================================================
-- STORED PROCEDURES — NOTA FISCAL
-- ============================================================

CREATE OR ALTER PROCEDURE sp_inserir_nota
    -- recebe o id do pedido que gerou essa nota
    -- um pedido pode chamar essa SP mais de uma vez pra gerar notas parciais
    @id_pedido INT, @numero_nf VARCHAR(20),
    @serie CHAR(3) = '001', @chave_acesso CHAR(44) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO NOTA_FISCAL (id_pedido,numero_nf,serie,chave_acesso)
    VALUES (@id_pedido,@numero_nf,@serie,@chave_acesso);
    -- retorna o id da nota gerada pra conseguir inserir os itens dela em seguida
    -- sem esse retorno a aplicação não saberia em qual nota inserir os produtos
    SELECT SCOPE_IDENTITY() AS id_nf;
END;
GO






CREATE OR ALTER PROCEDURE sp_deletar_nota
    -- recebe o id da nota que vai ser removida
    @id_nf INT
AS
BEGIN
    SET NOCOUNT ON;
    -- deleta os itens primeiro por causa da chave estrangeira
    -- sem isso o banco bloquearia a exclusão da nota
    DELETE FROM ITEM_NOTA   WHERE id_nf=@id_nf;
    DELETE FROM NOTA_FISCAL WHERE id_nf=@id_nf;
END;
GO





CREATE OR ALTER PROCEDURE sp_listar_notas
AS
BEGIN
    SET NOCOUNT ON;
    -- traz o nome do cliente via dois JOINs: nota → pedido → empresa
    -- ordenado da emissão mais recente pra mais antiga
    SELECT n.id_nf,n.numero_nf,n.serie,n.dt_emissao,n.valor_total,
           n.id_pedido, e.razao_social AS cliente
    FROM NOTA_FISCAL n
    JOIN PEDIDO  p ON p.id_pedido=n.id_pedido
    JOIN EMPRESA e ON e.id_empresa=p.id_empresa
    ORDER BY n.dt_emissao DESC;
END;
GO






CREATE OR ALTER PROCEDURE sp_listar_itens_nota
    -- recebe o id da nota e retorna só os produtos que ela cobre
    -- cada nota pode cobrir produtos diferentes do mesmo pedido
    @id_nf INT
AS
BEGIN
    SET NOCOUNT ON;
    -- traz a descrição e o sku do produto via JOIN pra não retornar só o id
    SELECT it.id_nf,it.id_produto,it.quantidade,it.preco_unitario,
           p.descricao AS produto, p.codigo_sku
    FROM ITEM_NOTA it JOIN PRODUTO p ON p.id_produto=it.id_produto
    WHERE it.id_nf=@id_nf;
END;
GO





-- ============================================================
-- STORED PROCEDURES — FUNCIONARIO
-- ============================================================

CREATE OR ALTER PROCEDURE sp_inserir_funcionario
    -- recebe os dados do funcionário e o id da filial onde ele vai trabalhar
    -- dt_admissao é obrigatória pra controle de tempo de casa
    @id_filial INT, @nome VARCHAR(100), @cpf CHAR(11),
    @cargo VARCHAR(60), @salario DECIMAL(10,2), @dt_admissao DATE
AS
BEGIN
    SET NOCOUNT ON;
    -- cpf tem UNIQUE então o banco rejeita duplicado automaticamente
    INSERT INTO FUNCIONARIO (id_filial,nome,cpf,cargo,salario,dt_admissao)
    VALUES (@id_filial,@nome,@cpf,@cargo,@salario,@dt_admissao);
END;
GO







CREATE OR ALTER PROCEDURE sp_atualizar_funcionario
    -- só permite editar nome, cargo, salário e status
    -- cpf e filial não são editáveis por essa SP
    @id_funcionario INT, @nome VARCHAR(100),
    @cargo VARCHAR(60), @salario DECIMAL(10,2), @ativo BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    -- ativo=1 permite reativar um funcionário que tinha sido desativado
    -- o WHERE garante que só o funcionário com esse id seja alterado
    UPDATE FUNCIONARIO SET nome=@nome, cargo=@cargo, salario=@salario, ativo=@ativo
    WHERE id_funcionario=@id_funcionario;
END;
GO






CREATE OR ALTER PROCEDURE sp_desativar_funcionario
    -- recebe só o id do funcionário que vai ser desativado
    @id_funcionario INT
AS
BEGIN
    SET NOCOUNT ON;
    -- não deleta o funcionário, só marca como inativo pra preservar o histórico
    -- entregas e movimentações antigas ainda referenciam ele
    UPDATE FUNCIONARIO SET ativo=0 WHERE id_funcionario=@id_funcionario;
END;
GO





CREATE OR ALTER PROCEDURE sp_listar_funcionarios
AS
BEGIN
    SET NOCOUNT ON;
    -- traz o nome da filial via JOIN pra não retornar só o id
    -- ordenado por nome pra facilitar a busca na tela
    SELECT f.id_funcionario,f.nome,f.cpf,f.cargo,f.salario,
           f.dt_admissao,f.ativo,f.id_filial,fi.nome AS filial
    FROM FUNCIONARIO f JOIN FILIAL fi ON fi.id_filial=f.id_filial
    ORDER BY f.nome;
END;
GO



-- ============================================================
-- STORED PROCEDURES — ESTOQUE E AUXILIARES
-- ============================================================

CREATE OR ALTER PROCEDURE sp_listar_estoque
AS
BEGIN
    SET NOCOUNT ON;
    -- traz produto e filial via JOIN pra não retornar só ids
    -- a aplicação usa estoque_minimo pra destacar produtos com quantidade baixa
    SELECT e.id_produto,e.id_filial,e.quantidade,e.estoque_minimo,
           e.dt_atualizacao, p.descricao AS produto, f.nome AS filial
    FROM ESTOQUE e
    JOIN PRODUTO p ON p.id_produto=e.id_produto
    JOIN FILIAL  f ON f.id_filial=e.id_filial
    ORDER BY p.descricao, f.nome;
END;
GO



CREATE OR ALTER PROCEDURE sp_listar_categorias
AS
BEGIN
    SET NOCOUNT ON;
    -- usada pra popular o dropdown de categorias na tela de produtos
    -- retorna só id e nome pra não carregar dados desnecessários
    SELECT id_categoria, nome FROM CATEGORIA ORDER BY nome;
END;
GO





CREATE OR ALTER PROCEDURE sp_listar_filiais
AS
BEGIN
    SET NOCOUNT ON;
    -- usada pra popular os dropdowns de filial nas telas de pedido e funcionário
    -- retorna só id e nome pra não carregar dados desnecessários
    SELECT id_filial, nome FROM FILIAL ORDER BY nome;
END;
GO

PRINT 'Stored Procedures criadas!';
GO