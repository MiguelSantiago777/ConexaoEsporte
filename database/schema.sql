-- =====================================================================
-- CONEXÃO ESPORTE — Esquema do Banco de Dados (Supabase / PostgreSQL)
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
    endereco                VARCHAR(255),
    status                  status_polo NOT NULL DEFAULT 'ATIVO',
    gestor_responsavel_id   UUID,  -- FK adicionada após criar 'usuarios' (referência circular)
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT now()
);

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
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome_completo               VARCHAR(150) NOT NULL,
    data_nascimento             DATE NOT NULL,
    documento                   VARCHAR(20) NOT NULL UNIQUE,  -- CPF ou outro documento
    responsavel_legal_nome      VARCHAR(150),
    responsavel_legal_contato   VARCHAR(50),
    contato                     VARCHAR(50),
    endereco                    VARCHAR(255),
    turma_id                    UUID REFERENCES turmas(id) ON DELETE SET NULL,
    observacoes_medicas         TEXT,
    ativo                       BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em                   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_beneficiarios_turma     ON beneficiarios(turma_id);
CREATE INDEX IF NOT EXISTS idx_beneficiarios_documento ON beneficiarios(documento);

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
