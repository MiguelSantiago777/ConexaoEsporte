-- =====================================================================
-- CONEXÃO ESPORTE — Esquema do Banco de Dados (PostgreSQL)
-- =====================================================================
-- Nomenclatura oficial e obrigatória: a pessoa atendida é BENEFICIÁRIO.
-- Em nenhuma hipótese utilizar "aluno".
-- =====================================================================

-- Extensão para gerar UUIDs
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------
-- ENUM de perfis de acesso (RBAC)
-- ---------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'perfil_usuario') THEN
        CREATE TYPE perfil_usuario AS ENUM (
            'MASTER', 'GESTOR_POLO', 'PROFESSOR', 'COORDENADOR_ALMOXARIFADO', 'PERSONALIZADO'
        );
    END IF;
END$$;

-- Coordenador de Almoxarifado: acesso restrito ao Estoque de um único
-- almoxarifado (adicionado depois do lançamento inicial do enum).
ALTER TYPE perfil_usuario ADD VALUE IF NOT EXISTS 'COORDENADOR_ALMOXARIFADO';

-- PERSONALIZADO: perfil dinâmico, cujo acesso vem do Papel vinculado (ver
-- tabela `papeis` mais abaixo) em vez de regras fixas do enum — criado pela
-- Central de Acessos, exclusiva do MASTER.
ALTER TYPE perfil_usuario ADD VALUE IF NOT EXISTS 'PERSONALIZADO';

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_polo') THEN
        CREATE TYPE status_polo AS ENUM ('ATIVO', 'INATIVO');
    END IF;
END$$;

-- ---------------------------------------------------------------------
-- TABELA: polos
-- Cada polo/núcleo é sua própria parceria com o poder público: carrega o
-- Termo de Fomento, CNPJ e representante legal próprios (não existe um
-- cadastro de "Entidade" separado — o polo É a entidade parceira para
-- fins da Ficha Técnica de Execução, Portaria nº 102/2024).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS polos (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome                        VARCHAR(150) NOT NULL,
    codigo                      VARCHAR(20) UNIQUE,  -- código curto de identificação (ex.: "ZN01")
    endereco                    VARCHAR(255),
    horario_funcionamento       VARCHAR(100),  -- ex.: "Seg a Sex, 08h às 18h"
    status                      status_polo NOT NULL DEFAULT 'ATIVO',
    gestor_responsavel_id       UUID,  -- FK adicionada após criar 'usuarios' (referência circular)

    -- Dados da parceria (Termo de Fomento) — próprios deste polo
    processo_sei                VARCHAR(50),
    termo_fomento_numero        VARCHAR(50),
    nome_entidade                VARCHAR(150),  -- razão social da OSC parceira responsável por este polo
    cnpj                         VARCHAR(20),
    representante_legal_nome    VARCHAR(150),
    representante_legal_cpf     VARCHAR(20),
    objeto                       TEXT,
    vigencia_inicio              DATE,
    vigencia_fim                 DATE,
    -- Valores em texto livre (ex.: "R$ 200.000,00") — campos de
    -- preenchimento/impressão do documento oficial, não um livro-caixa.
    valor_pactuado                VARCHAR(50),
    valor_executado               VARCHAR(50),
    parlamentar                  VARCHAR(150),
    emenda                        VARCHAR(100),
    -- Lista de até 2 aditivos: [{"numero": "PRIMEIRO", "objeto": "...", "data_assinatura": "2026-03-01"}, ...]
    termos_aditivos               JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Contato do núcleo para a seção "Identificação dos Núcleos" da Ficha
    responsavel_nome             VARCHAR(150),
    responsavel_email            VARCHAR(150),
    responsavel_telefone         VARCHAR(20),

    -- Dados pessoais do representante legal para o Termo de Responsabilidade
    representante_legal_rg        VARCHAR(20),
    representante_legal_endereco VARCHAR(255),
    representante_legal_bairro   VARCHAR(100),
    representante_legal_cidade   VARCHAR(100),

    -- Coordenadas do endereço, para exibir o polo no mapa do Dashboard.
    latitude                     DOUBLE PRECISION,
    longitude                    DOUBLE PRECISION,

    criado_em                    TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE polos ADD COLUMN IF NOT EXISTS codigo VARCHAR(20) UNIQUE;
ALTER TABLE polos ADD COLUMN IF NOT EXISTS horario_funcionamento VARCHAR(100);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS processo_sei VARCHAR(50);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS termo_fomento_numero VARCHAR(50);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS nome_entidade VARCHAR(150);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS cnpj VARCHAR(20);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS representante_legal_nome VARCHAR(150);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS representante_legal_cpf VARCHAR(20);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS objeto TEXT;
ALTER TABLE polos ADD COLUMN IF NOT EXISTS vigencia_inicio DATE;
ALTER TABLE polos ADD COLUMN IF NOT EXISTS vigencia_fim DATE;
ALTER TABLE polos ADD COLUMN IF NOT EXISTS valor_pactuado VARCHAR(50);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS valor_executado VARCHAR(50);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS parlamentar VARCHAR(150);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS emenda VARCHAR(100);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS termos_aditivos JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE polos ADD COLUMN IF NOT EXISTS responsavel_nome VARCHAR(150);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS responsavel_email VARCHAR(150);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS responsavel_telefone VARCHAR(20);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS representante_legal_rg VARCHAR(20);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS representante_legal_endereco VARCHAR(255);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS representante_legal_bairro VARCHAR(100);
ALTER TABLE polos ADD COLUMN IF NOT EXISTS representante_legal_cidade VARCHAR(100);

-- ---------------------------------------------------------------------
-- TABELA: papeis — níveis de acesso personalizados da Central de Acessos
-- (exclusiva do MASTER): um nome e a lista de módulos do sistema que ele
-- libera pra quem tiver perfil PERSONALIZADO vinculado a ele. Fica antes de
-- `usuarios` porque `usuarios.papel_id` referencia esta tabela.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS papeis (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome            VARCHAR(150) NOT NULL,
    descricao       TEXT,
    modulos         JSONB NOT NULL DEFAULT '[]'::jsonb,
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- TABELA: usuarios (funcionários: MASTER, GESTOR_POLO, PROFESSOR, ...)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome                    VARCHAR(150) NOT NULL,
    email                   VARCHAR(150) NOT NULL UNIQUE,
    senha_hash              VARCHAR(255) NOT NULL,
    perfil                  perfil_usuario NOT NULL,
    polo_id                 UUID REFERENCES polos(id) ON DELETE SET NULL,
    ativo                   BOOLEAN NOT NULL DEFAULT TRUE,
    -- RH do núcleo (Planilha de Núcleos — RH e Beneficiário): telefone e
    -- carga horária semanal do professor/gestor naquele polo.
    telefone                VARCHAR(20),
    carga_horaria_semanal   VARCHAR(20),
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Regra: GESTOR_POLO deve estar vinculado a um polo
    CONSTRAINT chk_gestor_tem_polo
        CHECK (perfil <> 'GESTOR_POLO' OR polo_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_polo  ON usuarios(polo_id);

ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS telefone VARCHAR(20);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS carga_horaria_semanal VARCHAR(20);

-- PERSONALIZADO: acesso definido pelo Papel vinculado, não por regra fixa.
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS papel_id UUID REFERENCES papeis(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_usuarios_papel ON usuarios(papel_id);
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'chk_personalizado_tem_papel'
    ) THEN
        ALTER TABLE usuarios ADD CONSTRAINT chk_personalizado_tem_papel
            CHECK (perfil <> 'PERSONALIZADO' OR papel_id IS NOT NULL);
    END IF;
END$$;

-- FK circular: gestor responsável do polo referencia usuarios
ALTER TABLE polos
    DROP CONSTRAINT IF EXISTS fk_polo_gestor;
ALTER TABLE polos
    ADD CONSTRAINT fk_polo_gestor
    FOREIGN KEY (gestor_responsavel_id) REFERENCES usuarios(id) ON DELETE SET NULL;

-- ---------------------------------------------------------------------
-- TABELA: modalidades
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS modalidades (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome        VARCHAR(100) NOT NULL,
    descricao   TEXT,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- TABELA: turmas
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS turmas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    polo_id         UUID NOT NULL REFERENCES polos(id) ON DELETE CASCADE,
    modalidade_id   UUID NOT NULL REFERENCES modalidades(id) ON DELETE RESTRICT,
    professor_id    UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    horario_inicio  VARCHAR(5) NOT NULL,   -- "HH:MM"
    horario_fim     VARCHAR(5) NOT NULL,   -- "HH:MM"
    dias_semana     VARCHAR(50) NOT NULL,  -- ex.: "SEG,QUA,SEX"
    limite_vagas    INTEGER NOT NULL DEFAULT 20 CHECK (limite_vagas > 0),
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_turmas_polo       ON turmas(polo_id);
CREATE INDEX IF NOT EXISTS idx_turmas_professor  ON turmas(professor_id);
CREATE INDEX IF NOT EXISTS idx_turmas_modalidade ON turmas(modalidade_id);

-- ---------------------------------------------------------------------
-- TABELA: beneficiarios  (nomenclatura oficial — nunca "aluno")
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS beneficiarios (
    id                                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome_completo                       VARCHAR(150) NOT NULL,
    data_nascimento                     DATE NOT NULL,
    documento                           VARCHAR(20) NOT NULL UNIQUE,  -- CPF ou outro documento; sempre exclusivo do próprio beneficiário
    polo_id                             UUID REFERENCES polos(id) ON DELETE SET NULL,
    responsavel_legal_nome              VARCHAR(150),
    responsavel_legal_data_nascimento   DATE,
    responsavel_legal_tipo_relacao      VARCHAR(50),
    responsavel_legal_telefone_1        VARCHAR(20),
    responsavel_legal_telefone_2        VARCHAR(20),
    responsavel_legal_email             VARCHAR(150),
    responsavel_legal_rede_social       VARCHAR(150),
    endereco                            VARCHAR(255),
    autoriza_whatsapp                   BOOLEAN NOT NULL DEFAULT FALSE,
    observacoes_medicas                 TEXT,
    ativo                                BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em                           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_beneficiarios_polo        ON beneficiarios(polo_id);
CREATE INDEX IF NOT EXISTS idx_beneficiarios_documento   ON beneficiarios(documento);

-- Upgrade idempotente para bancos que já rodaram uma versão anterior deste schema
-- (adiciona as colunas novas e remove as que foram substituídas por telefone 1/2).
ALTER TABLE beneficiarios ADD COLUMN IF NOT EXISTS polo_id UUID REFERENCES polos(id) ON DELETE SET NULL;
ALTER TABLE beneficiarios ADD COLUMN IF NOT EXISTS responsavel_legal_data_nascimento DATE;
ALTER TABLE beneficiarios ADD COLUMN IF NOT EXISTS responsavel_legal_tipo_relacao VARCHAR(50);
ALTER TABLE beneficiarios ADD COLUMN IF NOT EXISTS responsavel_legal_telefone_1 VARCHAR(20);
ALTER TABLE beneficiarios ADD COLUMN IF NOT EXISTS responsavel_legal_telefone_2 VARCHAR(20);
ALTER TABLE beneficiarios ADD COLUMN IF NOT EXISTS responsavel_legal_email VARCHAR(150);
ALTER TABLE beneficiarios ADD COLUMN IF NOT EXISTS responsavel_legal_rede_social VARCHAR(150);
ALTER TABLE beneficiarios ADD COLUMN IF NOT EXISTS autoriza_whatsapp BOOLEAN NOT NULL DEFAULT FALSE;
-- Migra o telefone antigo para telefone_1 antes de remover a coluna, se ela ainda existir.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'beneficiarios' AND column_name = 'responsavel_legal_contato') THEN
        UPDATE beneficiarios SET responsavel_legal_telefone_1 = responsavel_legal_contato
            WHERE responsavel_legal_telefone_1 IS NULL;
        ALTER TABLE beneficiarios DROP COLUMN responsavel_legal_contato;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'beneficiarios' AND column_name = 'contato') THEN
        ALTER TABLE beneficiarios DROP COLUMN contato;
    END IF;
END$$;

-- ---------------------------------------------------------------------
-- TABELA: matriculas — vínculo N:N entre beneficiário e turma.
-- Um beneficiário pode estar matriculado em várias turmas/modalidades ao
-- mesmo tempo (ex.: judô e natação); cada matrícula é independente e pode
-- ser encerrada (ativo = FALSE) sem afetar as demais nem apagar o
-- histórico de frequência/relatórios já lançado para ela.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS matriculas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    beneficiario_id UUID NOT NULL REFERENCES beneficiarios(id) ON DELETE CASCADE,
    turma_id        UUID NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_matricula_beneficiario_turma UNIQUE (beneficiario_id, turma_id)
);

CREATE INDEX IF NOT EXISTS idx_matriculas_beneficiario ON matriculas(beneficiario_id);
CREATE INDEX IF NOT EXISTS idx_matriculas_turma        ON matriculas(turma_id);

-- Upgrade idempotente: bancos que já rodaram a versão anterior deste schema
-- tinham beneficiarios.turma_id/modalidade_id (relação 1:1). Migra os
-- vínculos existentes para a nova tabela de matrículas antes de remover as
-- colunas antigas — só executa se elas ainda existirem.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'beneficiarios' AND column_name = 'turma_id') THEN
        INSERT INTO matriculas (beneficiario_id, turma_id, ativo)
        SELECT id, turma_id, ativo FROM beneficiarios
        WHERE turma_id IS NOT NULL
        ON CONFLICT (beneficiario_id, turma_id) DO NOTHING;

        ALTER TABLE beneficiarios DROP COLUMN turma_id;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'beneficiarios' AND column_name = 'modalidade_id') THEN
        ALTER TABLE beneficiarios DROP COLUMN modalidade_id;
    END IF;
END$$;

-- ---------------------------------------------------------------------
-- TABELA: beneficiario_documentos (certidão/RG, identidade do responsável,
-- comprovante de residência, comprovante escolar)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS beneficiario_documentos (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    beneficiario_id   UUID NOT NULL REFERENCES beneficiarios(id) ON DELETE CASCADE,
    tipo              VARCHAR(50) NOT NULL CHECK (tipo IN (
        'foto', 'certidao_nascimento_ou_identidade', 'identidade_responsavel',
        'comprovante_residencia', 'comprovante_escolar'
    )),
    nome_arquivo      VARCHAR(255) NOT NULL,
    caminho_arquivo   VARCHAR(500) NOT NULL,
    content_type      VARCHAR(100),
    tamanho_bytes     INTEGER,
    enviado_por_id    UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_beneficiario_documentos_beneficiario ON beneficiario_documentos(beneficiario_id);

-- ---------------------------------------------------------------------
-- TABELA: frequencias (chamada/presença diária)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS frequencias (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    turma_id            UUID NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
    beneficiario_id     UUID NOT NULL REFERENCES beneficiarios(id) ON DELETE CASCADE,
    data                DATE NOT NULL,
    presente            BOOLEAN NOT NULL DEFAULT FALSE,
    falta_justificada   BOOLEAN NOT NULL DEFAULT FALSE,
    justificativa       TEXT,
    registrado_por_id   UUID NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Um único registro de presença por beneficiário/turma/dia
    CONSTRAINT uq_frequencia_dia UNIQUE (turma_id, beneficiario_id, data)
);

CREATE INDEX IF NOT EXISTS idx_frequencias_turma_data ON frequencias(turma_id, data);
CREATE INDEX IF NOT EXISTS idx_frequencias_benef      ON frequencias(beneficiario_id);

-- ---------------------------------------------------------------------
-- TABELA: impeditivos_aula — dia em que a turma inteira não teve aula
-- (feriado, ponto facultativo etc.), vale para todos os beneficiários.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS impeditivos_aula (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    turma_id        UUID NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
    data            DATE NOT NULL,
    justificativa   TEXT NOT NULL,
    criado_por_id   UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_impeditivo_turma_dia UNIQUE (turma_id, data)
);

CREATE INDEX IF NOT EXISTS idx_impeditivos_turma_data ON impeditivos_aula(turma_id, data);

-- ---------------------------------------------------------------------
-- TABELA: relatorios_aula
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS relatorios_aula (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    turma_id                UUID NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
    professor_id            UUID NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    data                    DATE NOT NULL,
    conteudo_trabalhado     TEXT NOT NULL,
    observacoes             TEXT,
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_relatorios_turma ON relatorios_aula(turma_id);

-- ---------------------------------------------------------------------
-- Campos de Lista de Presença em `turmas` (coordenador/monitor não são
-- necessariamente usuários do sistema — só nomes para impressão no
-- relatório oficial — e periodicidade da turma, ex.: "Semanal").
-- ---------------------------------------------------------------------
ALTER TABLE turmas ADD COLUMN IF NOT EXISTS coordenador_nome VARCHAR(150);
ALTER TABLE turmas ADD COLUMN IF NOT EXISTS monitor_nome     VARCHAR(150);
ALTER TABLE turmas ADD COLUMN IF NOT EXISTS periodicidade    VARCHAR(50);

-- "Excluir" turma é uma desativação (ativo = false), nunca um DELETE físico:
-- turma_id tem ON DELETE CASCADE em frequências, matrículas, impeditivos e
-- evidências — um DELETE de verdade apagaria todo o histórico de chamada.
ALTER TABLE turmas ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT true;

-- A tabela "entidade" (cadastro único de OSC) foi substituída pelos campos
-- de parceria direto em `polos` — cada polo é sua própria entidade
-- parceira. Remove o resquício de bancos que já rodaram a versão anterior.
DROP TABLE IF EXISTS entidade;

-- ---------------------------------------------------------------------
-- TABELA: fichas_execucao — uma por polo e por período/trimestre
-- reportado (Ficha Técnica de Execução da Entidade, Portaria nº
-- 102/2024). Só o MASTER cadastra/edita/exporta.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fichas_execucao (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    polo_id                      UUID REFERENCES polos(id) ON DELETE CASCADE,
    periodo_referencia          VARCHAR(100) NOT NULL,  -- ex.: "1º Trimestre 2026" (uso interno/nome do arquivo)
    data_documento               DATE,

    -- 2 - Valores efetivamente recebidos e executados no período
    valor_recebido_periodo      VARCHAR(50),
    valor_recebido_extenso      VARCHAR(255),
    data_recebimento            DATE,

    -- 1.2 - Ajustes do plano de trabalho
    ajuste_status                VARCHAR(20) NOT NULL DEFAULT 'NAO_SOLICITADO'
        CHECK (ajuste_status IN ('NAO_SOLICITADO', 'APROVADO', 'NAO_APROVADO')),
    ajuste_justificativa        TEXT,

    -- 3 - Análise de valor: 2 metas fixas (Planejamento/Divulgação), até 5 etapas cada.
    -- [{"meta": "META 01 – ...", "etapas": [{"nome": "...", "previsto": "...", "executado": "..."}]}]
    metas                        JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- 4 - Desenvolvimento das atividades: comparativo pactuado x executado,
    -- 15 itens fixos e na mesma ordem do modelo (Núcleo, Modalidades, ...).
    -- [{"pactuado": "...", "executado": "...", "observacoes": "..."}]
    atividades_comparativo      JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- 5 - Execução: checklist de documentação (16 itens fixos do modelo).
    -- [{"documento": "...", "situacao": "Inserido"|"Não Inserido", "observacao": "..."}]
    checklist_documentos        JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- 6 - Inscrição dos beneficiados
    periodo_inscricao_inicio    DATE,
    periodo_inscricao_fim       DATE,
    inscricao_todos_nucleos     BOOLEAN,
    qtd_inscritos                INTEGER,
    observacoes_inscricao       TEXT,

    -- 7 - Identificação do núcleo (nome/endereço/responsável/e-mail/telefone
    -- vêm do próprio polo — aqui só a narrativa do período)
    quantitativo_beneficiados    VARCHAR(50),
    modalidades                  VARCHAR(255),
    periodo_funcionamento       VARCHAR(50),  -- ex.: "MANHA,TARDE"
    descricao_atividades        TEXT,
    dificuldades                 TEXT,

    -- 9 - Impactos do benefício social obtido até o período
    impactos_sociais             TEXT,
    consideracoes_finais        TEXT,

    criado_por_id                UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em                    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fichas_execucao_periodo ON fichas_execucao(periodo_referencia);

-- Upgrade idempotente para bancos que já rodaram a versão anterior deste
-- schema (ficha_execucao com `nucleos` JSONB cobrindo vários polos) — as
-- colunas novas precisam existir antes de criar o índice que usa polo_id.
ALTER TABLE fichas_execucao ADD COLUMN IF NOT EXISTS polo_id UUID REFERENCES polos(id) ON DELETE CASCADE;
ALTER TABLE fichas_execucao ADD COLUMN IF NOT EXISTS quantitativo_beneficiados VARCHAR(50);
ALTER TABLE fichas_execucao ADD COLUMN IF NOT EXISTS modalidades VARCHAR(255);
ALTER TABLE fichas_execucao ADD COLUMN IF NOT EXISTS periodo_funcionamento VARCHAR(50);
ALTER TABLE fichas_execucao ADD COLUMN IF NOT EXISTS descricao_atividades TEXT;
ALTER TABLE fichas_execucao ADD COLUMN IF NOT EXISTS dificuldades TEXT;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'fichas_execucao' AND column_name = 'nucleos') THEN
        ALTER TABLE fichas_execucao DROP COLUMN nucleos;
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_fichas_execucao_polo ON fichas_execucao(polo_id);

-- ---------------------------------------------------------------------
-- TABELA: entregas_materiais — Termo de Entrega de Materiais, um registro
-- por entrega física de materiais/uniformes ao núcleo (MASTER/GESTOR_POLO
-- do próprio polo cadastram e exportam o termo assinável em .docx).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS entregas_materiais (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    polo_id         UUID NOT NULL REFERENCES polos(id) ON DELETE CASCADE,
    data_entrega    DATE,
    coordenador_nome VARCHAR(150),  -- snapshot do responsável do núcleo no momento da entrega
    entregue_por    VARCHAR(150),  -- nome de quem foi fisicamente levar os materiais
    -- [{"descricao": "Bolas de futebol", "quantidade": "10", "produto_id": "..."}, ...]
    -- produto_id é opcional — quando presente, o item veio do catálogo de
    -- Estoque e gerou uma Saída automática (ver movimentos_estoque abaixo).
    itens           JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- Comprovante de recebimento no polo (foto/PDF assinado), anexado depois
    -- que a entrega já foi registrada, via rota própria de upload.
    comprovante_nome_arquivo    VARCHAR(255),
    comprovante_caminho_arquivo VARCHAR(500),
    comprovante_content_type   VARCHAR(100),
    comprovante_tamanho_bytes  INTEGER,
    criado_por_id   UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_entregas_materiais_polo ON entregas_materiais(polo_id);

-- ---------------------------------------------------------------------
-- TABELA: produtos — catálogo central de Estoque (bolas, uniformes,
-- materiais em geral), exclusivo do MASTER. A quantidade disponível nunca
-- fica aqui; é sempre a soma dos movimentos_estoque (ENTRADA - SAÍDA).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS produtos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome            VARCHAR(150) NOT NULL,
    unidade_medida  VARCHAR(30) NOT NULL,
    descricao       TEXT,
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- TABELA: almoxarifados — locais físicos onde o estoque central fica
-- guardado. O saldo de cada Produto é controlado separadamente em cada
-- almoxarifado (ver almoxarifado_id em movimentos_estoque).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS almoxarifados (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome            VARCHAR(150) NOT NULL,
    descricao       TEXT,
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- COORDENADOR_ALMOXARIFADO: acesso restrito ao Estoque de um único
-- almoxarifado, igual GESTOR_POLO é restrito a um único polo. Só pode vir
-- depois da tabela almoxarifados existir (referenciada pela FK).
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS almoxarifado_id UUID REFERENCES almoxarifados(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_usuarios_almoxarifado ON usuarios(almoxarifado_id);
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'chk_coordenador_tem_almoxarifado'
    ) THEN
        ALTER TABLE usuarios ADD CONSTRAINT chk_coordenador_tem_almoxarifado
            CHECK (perfil <> 'COORDENADOR_ALMOXARIFADO' OR almoxarifado_id IS NOT NULL);
    END IF;
END$$;

-- ---------------------------------------------------------------------
-- TABELA: movimentos_estoque — Entrada ou Saída de um Produto, num
-- almoxarifado específico. ENTRADA é lançada manualmente na tela de
-- Estoque (com nota fiscal/comprovante em anexo); SAÍDA nasce
-- automaticamente quando um item de uma Entrega de Materiais referencia o
-- produto (entrega_material_id rastreia a origem), escolhendo de qual
-- almoxarifado a saída sai.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movimentos_estoque (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    produto_id          UUID NOT NULL REFERENCES produtos(id) ON DELETE RESTRICT,
    almoxarifado_id     UUID NOT NULL REFERENCES almoxarifados(id) ON DELETE RESTRICT,
    tipo                VARCHAR(10) NOT NULL CHECK (tipo IN ('ENTRADA', 'SAIDA')),
    quantidade          INTEGER NOT NULL CHECK (quantidade > 0),
    data                DATE NOT NULL,
    observacao          TEXT,
    entregue_por        VARCHAR(150),  -- quem trouxe o material até o estoque (fornecedor, transportadora etc.)
    recebido_por        VARCHAR(150),  -- quem recebeu e conferiu no estoque central
    nome_arquivo        VARCHAR(255),
    caminho_arquivo     VARCHAR(500),
    content_type        VARCHAR(100),
    tamanho_bytes       INTEGER,
    entrega_material_id UUID REFERENCES entregas_materiais(id) ON DELETE SET NULL,
    criado_por_id       UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_movimentos_estoque_produto ON movimentos_estoque(produto_id);
CREATE INDEX IF NOT EXISTS idx_movimentos_estoque_almoxarifado ON movimentos_estoque(almoxarifado_id);
CREATE INDEX IF NOT EXISTS idx_movimentos_estoque_entrega ON movimentos_estoque(entrega_material_id);

-- ---------------------------------------------------------------------
-- TABELA: chamada_evidencias — fotos anexadas pelo professor a uma chamada
-- (turma + data), comprovando que a aula realmente aconteceu.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chamada_evidencias (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    turma_id        UUID NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
    data            DATE NOT NULL,
    nome_arquivo    VARCHAR(255) NOT NULL,
    caminho_arquivo VARCHAR(500) NOT NULL,
    content_type    VARCHAR(100),
    tamanho_bytes   INTEGER,
    enviado_por_id  UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chamada_evidencias_turma_data ON chamada_evidencias(turma_id, data);

-- ---------------------------------------------------------------------
-- TABELA: usuario_documentos — anexos do cadastro de professor (foto,
-- documentos e contrato). Mesmo esquema de armazenamento dos demais
-- anexos do sistema (beneficiario_documentos).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuario_documentos (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id        UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo              VARCHAR(20) NOT NULL CHECK (tipo IN ('FOTO', 'DOCUMENTO', 'CONTRATO')),
    nome_arquivo      VARCHAR(255) NOT NULL,
    caminho_arquivo   VARCHAR(500) NOT NULL,
    content_type      VARCHAR(100),
    tamanho_bytes     INTEGER,
    enviado_por_id    UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_usuario_documentos_usuario ON usuario_documentos(usuario_id);

-- ---------------------------------------------------------------------
-- TABELA: anexos_gerais — repositório livre de documentos por polo (não
-- ligados a um professor/beneficiário específico), para MASTER e
-- GESTOR_POLO anexarem qualquer arquivo útil (apólices, contratos de
-- aluguel, atas, etc.).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS anexos_gerais (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    polo_id           UUID NOT NULL REFERENCES polos(id) ON DELETE CASCADE,
    titulo            VARCHAR(150) NOT NULL,
    nome_arquivo      VARCHAR(255) NOT NULL,
    caminho_arquivo   VARCHAR(500) NOT NULL,
    content_type      VARCHAR(100),
    tamanho_bytes     INTEGER,
    enviado_por_id    UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_anexos_gerais_polo ON anexos_gerais(polo_id);

-- ---------------------------------------------------------------------
-- TABELA: configuracao_geral — registro único (singleton) com dados
-- globais do projeto/convênio, exibidos no rodapé de todos os relatórios
-- exportados. Não é por polo (cada polo já tem seu próprio Termo de
-- Fomento em `polos`) — é um dado só, da entidade como um todo.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS configuracao_geral (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome_projeto          VARCHAR(200),
    numero_convenio       VARCHAR(100),
    data_inicio_projeto   DATE,
    data_fim_projeto      DATE,
    atualizado_por_id     UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    atualizado_em         TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE configuracao_geral ADD COLUMN IF NOT EXISTS nome_projeto VARCHAR(200);
