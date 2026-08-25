-- =====================================================================
-- CONEXÃO ESPORTE — Row Level Security (RLS) para Supabase
-- =====================================================================
-- ⚠️  NÃO EXECUTE ESTE ARQUIVO NO SERVIDOR POSTGRES AUTOGERENCIADO. ⚠️
-- Estas políticas dependem de `request.jwt.claims`, um valor de sessão que
-- só existe quando as conexões passam pelo PostgREST do Supabase. Numa
-- instalação própria, o backend FastAPI conecta direto via SQLAlchemy e
-- nunca define esse valor — então toda policy abaixo avaliaria para FALSE
-- e, se o papel de conexão do app não for o dono das tabelas, a aplicação
-- ficaria travada (nenhuma linha visível/gravável). O RBAC por polo/turma
-- já é imposto inteiramente pelo backend em app/core/dependencies.py.
-- Este arquivo fica no repositório apenas como referência caso o projeto
-- volte a usar Supabase no futuro.
-- =====================================================================
-- OBSERVAÇÃO IMPORTANTE SOBRE ARQUITETURA:
-- O backend FastAPI já impõe o RBAC por polo/turma via middleware
-- (app/core/dependencies.py). As políticas abaixo são uma CAMADA EXTRA
-- de defesa, úteis se o frontend acessar o Supabase diretamente
-- (supabase-js) ou para garantir o isolamento no nível do banco.
--
-- Elas assumem que o JWT do Supabase carrega os claims:
--   - request.jwt.claims ->> 'perfil'   (MASTER | GESTOR_POLO | PROFESSOR)
--   - request.jwt.claims ->> 'polo_id'
--   - request.jwt.claims ->> 'sub'      (id do usuário)
-- =====================================================================

-- Funções auxiliares para ler os claims do JWT
CREATE OR REPLACE FUNCTION auth_perfil() RETURNS TEXT AS $$
    SELECT current_setting('request.jwt.claims', true)::json ->> 'perfil';
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION auth_polo_id() RETURNS UUID AS $$
    SELECT NULLIF(current_setting('request.jwt.claims', true)::json ->> 'polo_id', '')::UUID;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION auth_user_id() RETURNS UUID AS $$
    SELECT NULLIF(current_setting('request.jwt.claims', true)::json ->> 'sub', '')::UUID;
$$ LANGUAGE sql STABLE;

-- ---------------------------------------------------------------------
-- Habilitar RLS
-- ---------------------------------------------------------------------
ALTER TABLE polos                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios               ENABLE ROW LEVEL SECURITY;
ALTER TABLE turmas                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE beneficiarios          ENABLE ROW LEVEL SECURITY;
ALTER TABLE beneficiario_documentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE frequencias            ENABLE ROW LEVEL SECURITY;
ALTER TABLE relatorios_aula        ENABLE ROW LEVEL SECURITY;
ALTER TABLE modalidades            ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------
-- POLOS
--   MASTER: tudo | GESTOR_POLO: apenas o próprio polo (leitura)
-- ---------------------------------------------------------------------
CREATE POLICY polos_master_all ON polos
    FOR ALL USING (auth_perfil() = 'MASTER') WITH CHECK (auth_perfil() = 'MASTER');

CREATE POLICY polos_gestor_read ON polos
    FOR SELECT USING (auth_perfil() = 'GESTOR_POLO' AND id = auth_polo_id());

-- ---------------------------------------------------------------------
-- MODALIDADES  (leitura para todos autenticados; escrita MASTER/GESTOR)
-- ---------------------------------------------------------------------
CREATE POLICY modalidades_read ON modalidades
    FOR SELECT USING (auth_perfil() IN ('MASTER', 'GESTOR_POLO', 'PROFESSOR'));

CREATE POLICY modalidades_write ON modalidades
    FOR ALL USING (auth_perfil() IN ('MASTER', 'GESTOR_POLO'))
    WITH CHECK (auth_perfil() IN ('MASTER', 'GESTOR_POLO'));

-- ---------------------------------------------------------------------
-- TURMAS
--   MASTER: tudo
--   GESTOR_POLO: turmas do seu polo
--   PROFESSOR: apenas suas turmas (leitura)
-- ---------------------------------------------------------------------
CREATE POLICY turmas_master_all ON turmas
    FOR ALL USING (auth_perfil() = 'MASTER') WITH CHECK (auth_perfil() = 'MASTER');

CREATE POLICY turmas_gestor_all ON turmas
    FOR ALL USING (auth_perfil() = 'GESTOR_POLO' AND polo_id = auth_polo_id())
    WITH CHECK (auth_perfil() = 'GESTOR_POLO' AND polo_id = auth_polo_id());

CREATE POLICY turmas_professor_read ON turmas
    FOR SELECT USING (auth_perfil() = 'PROFESSOR' AND professor_id = auth_user_id());

-- ---------------------------------------------------------------------
-- BENEFICIÁRIOS
--   MASTER: tudo
--   GESTOR_POLO: beneficiários de turmas do seu polo
--   PROFESSOR: beneficiários das suas turmas (leitura)
-- ---------------------------------------------------------------------
CREATE POLICY beneficiarios_master_all ON beneficiarios
    FOR ALL USING (auth_perfil() = 'MASTER') WITH CHECK (auth_perfil() = 'MASTER');

CREATE POLICY beneficiarios_gestor_all ON beneficiarios
    FOR ALL USING (
        auth_perfil() = 'GESTOR_POLO'
        AND (
            polo_id = auth_polo_id()
            OR (polo_id IS NULL AND (turma_id IS NULL OR turma_id IN (
                SELECT id FROM turmas WHERE polo_id = auth_polo_id()
            )))
        )
    )
    WITH CHECK (
        auth_perfil() = 'GESTOR_POLO'
        AND (
            polo_id = auth_polo_id()
            OR (polo_id IS NULL AND (turma_id IS NULL OR turma_id IN (
                SELECT id FROM turmas WHERE polo_id = auth_polo_id()
            )))
        )
    );

CREATE POLICY beneficiarios_professor_read ON beneficiarios
    FOR SELECT USING (
        auth_perfil() = 'PROFESSOR'
        AND turma_id IN (SELECT id FROM turmas WHERE professor_id = auth_user_id())
    );

-- ---------------------------------------------------------------------
-- DOCUMENTOS DE BENEFICIÁRIOS
--   Mesma regra de acesso do beneficiário dono do documento.
--   MASTER: tudo | GESTOR_POLO: documentos de beneficiários do seu polo.
-- ---------------------------------------------------------------------
CREATE POLICY beneficiario_documentos_master_all ON beneficiario_documentos
    FOR ALL USING (auth_perfil() = 'MASTER') WITH CHECK (auth_perfil() = 'MASTER');

CREATE POLICY beneficiario_documentos_gestor_all ON beneficiario_documentos
    FOR ALL USING (
        auth_perfil() = 'GESTOR_POLO'
        AND beneficiario_id IN (
            SELECT id FROM beneficiarios WHERE
                polo_id = auth_polo_id()
                OR (polo_id IS NULL AND (turma_id IS NULL OR turma_id IN (
                    SELECT id FROM turmas WHERE polo_id = auth_polo_id()
                )))
        )
    )
    WITH CHECK (
        auth_perfil() = 'GESTOR_POLO'
        AND beneficiario_id IN (
            SELECT id FROM beneficiarios WHERE
                polo_id = auth_polo_id()
                OR (polo_id IS NULL AND (turma_id IS NULL OR turma_id IN (
                    SELECT id FROM turmas WHERE polo_id = auth_polo_id()
                )))
        )
    );

-- ---------------------------------------------------------------------
-- FREQUÊNCIAS
--   PROFESSOR: pode inserir/ler nas suas turmas
--   GESTOR_POLO: turmas do seu polo | MASTER: tudo
-- ---------------------------------------------------------------------
CREATE POLICY frequencias_master_all ON frequencias
    FOR ALL USING (auth_perfil() = 'MASTER') WITH CHECK (auth_perfil() = 'MASTER');

CREATE POLICY frequencias_gestor_all ON frequencias
    FOR ALL USING (
        auth_perfil() = 'GESTOR_POLO'
        AND turma_id IN (SELECT id FROM turmas WHERE polo_id = auth_polo_id())
    )
    WITH CHECK (
        auth_perfil() = 'GESTOR_POLO'
        AND turma_id IN (SELECT id FROM turmas WHERE polo_id = auth_polo_id())
    );

CREATE POLICY frequencias_professor_all ON frequencias
    FOR ALL USING (
        auth_perfil() = 'PROFESSOR'
        AND turma_id IN (SELECT id FROM turmas WHERE professor_id = auth_user_id())
    )
    WITH CHECK (
        auth_perfil() = 'PROFESSOR'
        AND turma_id IN (SELECT id FROM turmas WHERE professor_id = auth_user_id())
    );

-- ---------------------------------------------------------------------
-- RELATÓRIOS DE AULA  (mesma lógica das frequências)
-- ---------------------------------------------------------------------
CREATE POLICY relatorios_master_all ON relatorios_aula
    FOR ALL USING (auth_perfil() = 'MASTER') WITH CHECK (auth_perfil() = 'MASTER');

CREATE POLICY relatorios_gestor_read ON relatorios_aula
    FOR SELECT USING (
        auth_perfil() = 'GESTOR_POLO'
        AND turma_id IN (SELECT id FROM turmas WHERE polo_id = auth_polo_id())
    );

CREATE POLICY relatorios_professor_all ON relatorios_aula
    FOR ALL USING (
        auth_perfil() = 'PROFESSOR'
        AND turma_id IN (SELECT id FROM turmas WHERE professor_id = auth_user_id())
    )
    WITH CHECK (
        auth_perfil() = 'PROFESSOR'
        AND professor_id = auth_user_id()
        AND turma_id IN (SELECT id FROM turmas WHERE professor_id = auth_user_id())
    );

-- ---------------------------------------------------------------------
-- USUÁRIOS
--   MASTER: tudo | GESTOR_POLO: usuários do seu polo (leitura)
--   Cada usuário pode ler a si mesmo
-- ---------------------------------------------------------------------
CREATE POLICY usuarios_master_all ON usuarios
    FOR ALL USING (auth_perfil() = 'MASTER') WITH CHECK (auth_perfil() = 'MASTER');

CREATE POLICY usuarios_gestor_read ON usuarios
    FOR SELECT USING (auth_perfil() = 'GESTOR_POLO' AND polo_id = auth_polo_id());

CREATE POLICY usuarios_self_read ON usuarios
    FOR SELECT USING (id = auth_user_id());
