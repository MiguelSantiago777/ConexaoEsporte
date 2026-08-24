-- =====================================================================
-- CONEXÃO ESPORTE — Dados iniciais (seed) para desenvolvimento
-- =====================================================================
-- As senhas abaixo são hashes bcrypt da senha em texto: "senha123"
-- (gere seus próprios hashes em produção via backend/scripts).
--
-- Hash bcrypt REAL e VÁLIDO de "senha123" (gerado no setup):
--   $2b$12$5nNHyNZAKvbcBG71cVsi.OOO8YQQY9Tbna9O/667CPn4O8EdcJyNe
-- (Exemplo — substitua por hashes reais gerados no seu ambiente.)
-- =====================================================================

-- MASTER
INSERT INTO usuarios (id, nome, email, senha_hash, perfil, polo_id, ativo)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'Administrador Master',
    'master@conexaoesporte.org',
    '$2b$12$5nNHyNZAKvbcBG71cVsi.OOO8YQQY9Tbna9O/667CPn4O8EdcJyNe',
    'MASTER', NULL, TRUE
) ON CONFLICT (email) DO NOTHING;

-- POLO
INSERT INTO polos (id, nome, endereco, status)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    'Polo Zona Norte',
    'Rua das Palmeiras, 100 - Zona Norte',
    'ATIVO'
) ON CONFLICT DO NOTHING;

-- GESTOR DE POLO (vinculado ao Polo Zona Norte)
INSERT INTO usuarios (id, nome, email, senha_hash, perfil, polo_id, ativo)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    'Gestor Zona Norte',
    'gestor.zn@conexaoesporte.org',
    '$2b$12$5nNHyNZAKvbcBG71cVsi.OOO8YQQY9Tbna9O/667CPn4O8EdcJyNe',
    'GESTOR_POLO', '22222222-2222-2222-2222-222222222222', TRUE
) ON CONFLICT (email) DO NOTHING;

-- Vincular o gestor como responsável do polo
UPDATE polos SET gestor_responsavel_id = '33333333-3333-3333-3333-333333333333'
WHERE id = '22222222-2222-2222-2222-222222222222';

-- PROFESSOR (do Polo Zona Norte)
INSERT INTO usuarios (id, nome, email, senha_hash, perfil, polo_id, ativo)
VALUES (
    '44444444-4444-4444-4444-444444444444',
    'Professor João',
    'prof.joao@conexaoesporte.org',
    '$2b$12$5nNHyNZAKvbcBG71cVsi.OOO8YQQY9Tbna9O/667CPn4O8EdcJyNe',
    'PROFESSOR', '22222222-2222-2222-2222-222222222222', TRUE
) ON CONFLICT (email) DO NOTHING;

-- MODALIDADES
INSERT INTO modalidades (id, nome, descricao) VALUES
    ('55555555-5555-5555-5555-555555555555', 'Futebol', 'Futebol de campo e society'),
    ('66666666-6666-6666-6666-666666666666', 'Judô', 'Arte marcial e defesa pessoal'),
    ('77777777-7777-7777-7777-777777777777', 'Basquete', 'Basquetebol')
ON CONFLICT DO NOTHING;

-- TURMA (Polo Zona Norte + Judô + Professor João)
INSERT INTO turmas (id, polo_id, modalidade_id, professor_id, horario_inicio, horario_fim, dias_semana, limite_vagas)
VALUES (
    '88888888-8888-8888-8888-888888888888',
    '22222222-2222-2222-2222-222222222222',
    '66666666-6666-6666-6666-666666666666',
    '44444444-4444-4444-4444-444444444444',
    '14:00', '15:30', 'SEG,QUA,SEX', 20
) ON CONFLICT DO NOTHING;

-- BENEFICIÁRIO de exemplo
INSERT INTO beneficiarios (
    id, nome_completo, data_nascimento, documento,
    responsavel_legal_nome, responsavel_legal_contato, turma_id
) VALUES (
    '99999999-9999-9999-9999-999999999999',
    'Maria Beneficiária da Silva',
    '2014-05-20',
    '123.456.789-00',
    'Ana da Silva (mãe)',
    '(21) 99999-0000',
    '88888888-8888-8888-8888-888888888888'
) ON CONFLICT (documento) DO NOTHING;
