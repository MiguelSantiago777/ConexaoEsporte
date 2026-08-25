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
        CREATE TYPE perfil_usuario AS ENUM ('MASTER', 'GESTOR_POLO', 'PROFESSOR');
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_polo') THEN
        CREATE TYPE status_polo AS ENUM ('ATIVO', 'INATIVO');
    END IF;
END$$;

-- ---------------------------------------------------------------------
-- TABELA: polos
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS polos (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome                    VARCHAR(150) NOT NULL,
    codigo                  VARCHAR(20) UNIQUE,  -- código curto de identificação (ex.: "ZN01")
    endereco                VARCHAR(255),
    horario_funcionamento   VARCHAR(100),  -- ex.: "Seg a Sex, 08h às 18h"
    status                  status_polo NOT NULL DEFAULT 'ATIVO',
    gestor_responsavel_id   UUID,  -- FK adicionada após criar 'usuarios' (referência circular)
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE polos ADD COLUMN IF NOT EXISTS codigo VARCHAR(20) UNIQUE;
ALTER TABLE polos ADD COLUMN IF NOT EXISTS horario_funcionamento VARCHAR(100);

-- ---------------------------------------------------------------------
-- TABELA: usuarios (funcionários: MASTER, GESTOR_POLO, PROFESSOR)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome        VARCHAR(150) NOT NULL,
    email       VARCHAR(150) NOT NULL UNIQUE,
    senha_hash  VARCHAR(255) NOT NULL,
    perfil      perfil_usuario NOT NULL,
    polo_id     UUID REFERENCES polos(id) ON DELETE SET NULL,
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Regra: GESTOR_POLO deve estar vinculado a um polo
    CONSTRAINT chk_gestor_tem_polo
        CHECK (perfil <> 'GESTOR_POLO' OR polo_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_polo  ON usuarios(polo_id);

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
        'certidao_nascimento_ou_identidade', 'identidade_responsavel',
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
    registrado_por_id   UUID NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Um único registro de presença por beneficiário/turma/dia
    CONSTRAINT uq_frequencia_dia UNIQUE (turma_id, beneficiario_id, data)
);

CREATE INDEX IF NOT EXISTS idx_frequencias_turma_data ON frequencias(turma_id, data);
CREATE INDEX IF NOT EXISTS idx_frequencias_benef      ON frequencias(beneficiario_id);

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
