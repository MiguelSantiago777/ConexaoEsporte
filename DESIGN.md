---
# gstack: design-md-format=spec
name: Conexão Esporte
description: Registro oficial de programa social esportivo — navy institucional, serifa de destaque e números tabulares, para transmitir rigor e prestação de contas de verba pública.
colors:
  primary: "#00417d"       # brand — sidebar, títulos de card, foco de inputs
  on-primary: "#ffffff"
  surface: "#ffffff"
  text: "#10233a"          # ink
  text-muted: "#5f6b7a"    # slate-500
  accent: "#fcba27"        # dourado — únicos usos: marca, luz do brasão no login, ícone de página
  success: "#1c7a4b"       # court — "verde de quadra", deliberadamente não o verde genérico
  warning: "#f59e0b"
  error: "#c23b3b"         # danger — vermelho abaixado, convive com dourado/verde sem destoar
typography:
  display:
    fontFamily: Fraunces
    fontWeight: 650
    fontSize: clamp(1.25rem, 1rem + 1vw, 1.75rem)
    letterSpacing: -0.01em
  body:
    fontFamily: Inter
    fontSize: 1rem
    lineHeight: 1.5
  label:
    fontFamily: Inter
    fontSize: 0.75rem
    letterSpacing: 0.025em
  mono:
    fontFamily: "IBM Plex Mono"
    fontFeature: tnum
rounded:
  sm: 8px
  md: 12px
  lg: 12px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.sm}"
  button-primary-hover:
    backgroundColor: "#00325f"
  button-danger:
    backgroundColor: "{colors.error}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.sm}"
  input:
    borderColor: "#c7ced7"
    rounded: "{rounded.sm}"
    focusRing: "{colors.primary}/40"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.md}"
    shadow: sm
  badge:
    rounded: "{rounded.full}"
  nav-link:
    textColor: "{colors.on-primary}/70"
    textColorActive: "{colors.on-primary}"
---

# Conexão Esporte

## Overview

**Creative North Star:** um sistema de registro público — navy institucional e
serifa de destaque fazem o produto parecer um documento oficial que pode ser
auditado, não um app de consumo.

**Product context:** plataforma de gestão de projetos esportivos sociais
(polos, modalidades, turmas e beneficiários), financiados via Termo de
Fomento (convênio público). Uso interno por MASTER, Gestor de Polo,
Professor e Coordenador de Almoxarifado — nunca uso público. A pessoa
atendida é sempre "Beneficiário", nunca "aluno" (regra de nomenclatura do
próprio README).

**Mode per surface:**
- Login: Persuade (uma tela, precisa transmitir confiança em 3 segundos — daí o brasão e a luz dourada)
- Dashboard, Cadastros, Estoque, Relatórios: Operate (uso diário de alta frequência, densidade de dados, uma tarefa atrás da outra)
- Ficha de Execução impressa, Termo de Responsabilidade, Lista de Presença: Read (vira papel/PDF — ver a seção de impressão em `index.css`)

**Reference sites:** gov.br (padrão de confiança institucional brasileira — navy + cards brancos + números grandes em faixa de destaque, a mesma estrutura que o "Desempenho dos Serviços" de gov.br e o header de stats do nosso Dashboard); Linear.app (referência de restrição e precisão — não emprestamos a paleta escura, mas emprestamos a disciplina de "sem decoração, só hierarquia").

**Key characteristics:**
- Sidebar navy cheia de altura, nunca colapsada — a marca está sempre presente
- Títulos em serifa (Fraunces), tudo o mais em Inter — a mudança de fonte é a única pista visual de "isto é um título"
- Números de indicador em mono tabular — parece planilha oficial, os dígitos não "dançam" ao atualizar
- Cards brancos flutuando sobre fundo `brand-light`, nunca aninhados
- Entrada em cascata (stagger) nos cards do dashboard — dá uma sensação de "montagem", não de "carregou tudo de uma vez"

## Colors

**Strategy:** Full palette — brand (navy) domina superfícies estruturais
(sidebar, títulos), accent (dourado) é raro e sempre um marcador de destaque
pontual (nunca um fundo grande), court (verde) e danger (vermelho) são
estritamente semânticos (sucesso/presença vs. erro/destrutivo).

**Light or dark:** só claro. É uma ferramenta de trabalho usada em escritório/
polo esportivo durante o expediente — não há cenário de uso no escuro que
justifique o dobro de manutenção de um tema dark.

**Named rules:**
- `accent` carrega destaque pontual, nunca interação — botões primários usam `brand`, não `accent`. Accent é para o que deve ser notado uma vez (ícone de página, a luz do login), não clicado repetidamente.
- `text-muted` (slate-500) é a única cor de texto secundário — não usar `gray-*` do Tailwind puro (ele quebra a coerência com o matiz azulado de `ink`).
- Neutros (`slate`) derivam do matiz de `ink`, não do cinza neutro padrão do Tailwind — é por isso que têm um leve azul mesmo nos tons claros.
- `CATEGORICAL_PALETTE` (`src/components/ui/charts/palette.ts`) é uma paleta à parte, feita para 4+ fatias de gráfico distinguíveis — **decisão intencional**, não deriva de brand/accent porque 3 tons da marca não bastam para diferenciar fatias com segurança visual. Não "corrigir" isso pra usar brand/accent.

## Typography

Fraunces vem do mundo de identidade editorial/institucional — pesos
variáveis permitem um peso 650 que lê como "sério" sem parecer um cartaz.
Reservada estritamente a h1/h2/h3 (ver `@layer base` em `index.css`); nunca
em botões, labels ou corpo de texto — se Fraunces aparecesse em toda parte
perderia a função de marcar "isto é um título estrutural".

Inter carrega todo o resto: formulários, tabelas, texto de corpo. É a
exceção documentada da lista de fontes batidas — aqui ela nunca é a voz de
destaque (isso é papel da Fraunces), só a voz de UI em uma superfície
Operate de alta densidade, que é exatamente o papel em que Inter é aceitável.

IBM Plex Mono entra só em números de indicador/contador e colunas numéricas
de tabela, sempre com `tabular-nums` — o objetivo é a sensação de "registro
oficial/planilha", e dígitos monoespaçados tabulares não mudam de largura
quando o valor muda (evita o número "pular" na tela).

**Carregamento:** as três fontes vêm do Google Fonts via `@import` em
`index.css` (`Inter:wght@400;500;600;700;800`,
`Fraunces:opsz,wght@9..144,450;9..144,560;9..144,650`,
`IBM+Plex+Mono:wght@500;600`) — pesos exatos aos usados, nada a mais.

## Layout

Sidebar fixa de largura constante (não colapsa para ícones) + área de
conteúdo com `max-w` por página. Densidade alta é esperada e correta — os
usuários são profissionais preenchendo formulários e lendo tabelas o dia
inteiro, não visitantes ocasionais; esconder densidade atrás de progressive
disclosure aqui atrapalharia mais do que ajudaria.

Cards nunca se aninham (nenhum `<Card>` dentro de outro `<Card>`) — hierarquia
vem de espaçamento e do salto de peso entre Fraunces (título) e Inter
(corpo), não de camadas de container.

## Elevation & Depth

Só `shadow-sm` (cards) e `shadow-xl` (modais) — profundidade rasa e
consistente, nunca glow ou halo. `hover:shadow-md` em cards e botões
primários sinaliza interatividade sem exagero.

## Shapes

Dois raios reais no sistema: `sm` (8px, `rounded-lg`) em controles
interativos — botão, input — e `md`/`lg` (12px, `rounded-xl`) em
containers — card, modal. `full` (9999px) só em badges/avatares. Não
inventar um terceiro raio intermediário; o sistema deliberadamente usa só
dois níveis.

## Components

- **button-primary**: `brand` de fundo, branco por cima, hover escurece pra `brand-dark` (#00325f) e ganha `shadow-md`; foco usa `ring-brand/50`.
- **button-secondary**: fundo branco, borda `slate-300`, texto `slate-700` — não `gray-*`.
- **button-danger**: fundo `danger`, hover `danger-dark` — reservado a ações destrutivas (remover, desativar), nunca a ações neutras.
- **input**: borda `slate-300` (via `#c7ced7`), foco com anel `brand/40` + borda `brand`, desabilitado em `slate-100`-equivalente.
- **card**: fundo branco, `rounded-md`, `shadow-sm`, título em `brand-dark` + Fraunces.
- **nav-link** (sidebar): texto branco 70% opaco em repouso, 100% + fundo `brand-dark`/leve quando ativo.

Estados hover/focus-visible/disabled já existem em Button e Input — nenhuma
mudança pedida nesta sessão.

## Do's and Don'ts

**Do:**
- Reservar `accent` (dourado) para destaque pontual — nunca como fundo de área grande ou cor de botão primário.
- Usar `slate-*`/`danger` para qualquer neutro ou vermelho novo — nunca `gray-*`/`red-*` puro do Tailwind.
- Usar Fraunces só em h1/h2/h3 — nunca em botão, label, corpo de texto ou número.
- Números de indicador/tabela sempre em `font-mono` + `tabular-nums`.

**Don't:**
- Barra colorida na borda esquerda de card (`border-left: 3px solid <cor>`) — é um clichê reconhecível de UI genérica; removido do StatTile nesta sessão, não reintroduzir em outro componente.
- Cinza/vermelho padrão do Tailwind (`gray-*`, `red-*`) em componente novo — sempre `slate-*`/`ink`/`danger`.
- Empilhar `<Card>` dentro de `<Card>`.
- Tema escuro — fora de escopo, não há cenário de uso que justifique.

**Débito conhecido (não corrigido nesta sessão, fora do escopo aprovado):**
- `Card.tsx`, `Input.tsx`, `Modal.tsx` e `Badge.tsx` ainda usam `gray-*` do Tailwind em vez de `slate-*` — mesma categoria do que foi corrigido em `Button.tsx`/`StatTile.tsx`, só não incluído nesta rodada.
- `ToastContext.tsx` usa `green-600`/`amber-500`/`red-600` do Tailwind puro nos ícones de toast, em vez de `court`/`warning`/`danger` — `court` existe especificamente para o caso de sucesso e não está sendo usado ali.
- O mapa Leaflet (`PolosMapaCard.tsx`) usa tiles e controles padrão do OpenStreetMap — é o único canto do produto que ainda parece "default"; discutido nesta sessão e deixado de fora por escolha do usuário.

## Motion

- **Approach:** intentional — entrada em cascata, transição de página, nunca decoração gratuita.
- **Easing:** enter `cubic-bezier(0.16, 1, 0.3, 1)` em toda animação de entrada (toast, fade, page, stagger).
- **Duration:** micro 150ms (toast-in) · short 400ms (fade-in) · medium 550ms (page-in, fade-in-up).
- **The one authored moment:** a luz dourada varrendo o brasão de linhas na tela de login (`animate-luz-varrendo`, 2.7s, infinita) — o único momento decorativo puro do sistema, reservado à primeira tela que qualquer usuário vê.

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-09-11 | DESIGN.md criado a partir do sistema já em produção | `/design-consultation` — o codebase já tinha um sistema deliberado (paleta com racional escrito, tipografia com papéis definidos); a sessão documentou o existente em vez de propor do zero |
| 2026-09-11 | Removida a barra dourada da borda esquerda do StatTile | Clichê reconhecível de UI genérica, não usado em nenhum outro componente do sistema |
| 2026-09-11 | Criados tokens `slate` (neutro derivado de `ink`) e `danger` (vermelho abaixado) | Fechar o vazamento de `gray-*`/`red-*` padrão do Tailwind em `Button.tsx` e `StatTile.tsx`; aplicado só nesses dois componentes nesta rodada — ver Débito conhecido |
