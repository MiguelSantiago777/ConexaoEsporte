import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../AuthContext";
import { api } from "@/lib/api";
import type { Beneficiario, Modalidade, Polo, Turma } from "@/types";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatTile } from "@/components/ui/StatTile";
import { Spinner } from "@/components/ui/Spinner";
import { DonutChart } from "@/components/ui/charts/DonutChart";
import { BarList } from "@/components/ui/charts/BarList";
import { CATEGORICAL_PALETTE, COR_OUTROS } from "@/components/ui/charts/palette";
import { staggerStyle } from "@/lib/animation";
import { PolosMapaCard } from "./PolosMapaCard";
import { RelatorioEstoquePage } from "@/features/relatorios-gerenciais/RelatorioEstoquePage";

const MAX_TURMAS_NO_GRAFICO = 8;
const MAX_FATIAS_MODALIDADE = 4;

const descricaoPorPerfil: Record<string, string> = {
  MASTER: "Você tem acesso total: polos, modalidades, turmas, beneficiários e usuários.",
  GESTOR_POLO: "Você gerencia modalidades, turmas, professores e beneficiários do seu polo.",
  PROFESSOR: "Você registra a frequência dos beneficiários e emite relatórios de aula das suas turmas.",
  COORDENADOR_ALMOXARIFADO: "Você registra a Entrada de produtos e acompanha o relatório do seu almoxarifado.",
};

export function DashboardPage() {
  const { usuario } = useAuth();
  const mostrarRelatorio = usuario?.perfil === "MASTER" || usuario?.perfil === "GESTOR_POLO";
  const mostrarEstoque = usuario?.perfil === "COORDENADOR_ALMOXARIFADO";

  const { data: turmas = [], isLoading: carregandoTurmas } = useQuery({
    queryKey: ["turmas"],
    queryFn: () => api.get<Turma[]>("/turmas").then((r) => r.data),
    enabled: mostrarRelatorio,
  });
  const { data: beneficiarios = [], isLoading: carregandoBeneficiarios } = useQuery({
    queryKey: ["beneficiarios"],
    queryFn: () => api.get<Beneficiario[]>("/beneficiarios").then((r) => r.data),
    enabled: mostrarRelatorio,
  });
  const { data: modalidades = [] } = useQuery({
    queryKey: ["modalidades"],
    queryFn: () => api.get<Modalidade[]>("/modalidades").then((r) => r.data),
    enabled: mostrarRelatorio,
  });
  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
    enabled: mostrarRelatorio,
  });
  const carregando = mostrarRelatorio && (carregandoTurmas || carregandoBeneficiarios);

  const beneficiariosAtivos = useMemo(() => beneficiarios.filter((b) => b.ativo), [beneficiarios]);

  const vagasOcupadas = turmas.reduce((acc, t) => acc + t.vagas_ocupadas, 0);
  const vagasTotais = turmas.reduce((acc, t) => acc + t.limite_vagas, 0);
  const ocupacaoMedia = vagasTotais > 0 ? Math.round((vagasOcupadas / vagasTotais) * 100) : 0;
  const percWhatsapp = beneficiariosAtivos.length
    ? Math.round((beneficiariosAtivos.filter((b) => b.autoriza_whatsapp).length / beneficiariosAtivos.length) * 100)
    : 0;

  // Contagem por matrícula (via turma.vagas_ocupadas, já calculado no servidor) —
  // um beneficiário em 2 modalidades ao mesmo tempo conta uma vez em cada uma,
  // o que é o comportamento correto.
  const porModalidade = useMemo(() => {
    const contagem = new Map<string, number>();
    for (const t of turmas) {
      const nome = modalidades.find((m) => m.id === t.modalidade_id)?.nome ?? "Sem modalidade";
      contagem.set(nome, (contagem.get(nome) ?? 0) + t.vagas_ocupadas);
    }
    const ordenado = [...contagem.entries()]
      .filter(([, value]) => value > 0)
      .sort((a, b) => b[1] - a[1])
      .map(([label, value]) => ({ label, value }));
    const principais = ordenado.slice(0, MAX_FATIAS_MODALIDADE);
    const resto = ordenado.slice(MAX_FATIAS_MODALIDADE).reduce((acc, i) => acc + i.value, 0);
    const fatias = principais.map((item, i) => ({ ...item, color: CATEGORICAL_PALETTE[i] }));
    if (resto > 0) fatias.push({ label: "Outras modalidades", value: resto, color: COR_OUTROS });
    return fatias;
  }, [turmas, modalidades]);

  const porTurma = useMemo(() => {
    return turmas
      .filter((t) => t.vagas_ocupadas > 0)
      .map((t) => {
        const modalidade = modalidades.find((m) => m.id === t.modalidade_id)?.nome ?? "—";
        const polo = usuario?.perfil === "MASTER" ? polos.find((p) => p.id === t.polo_id)?.nome ?? "" : "";
        const label = [polo, modalidade, `${t.horario_inicio}-${t.horario_fim}`].filter(Boolean).join(" · ");
        return { label, value: t.vagas_ocupadas };
      })
      .sort((a, b) => b.value - a.value);
  }, [turmas, modalidades, polos, usuario]);

  const turmasExibidas = porTurma.slice(0, MAX_TURMAS_NO_GRAFICO);
  const turmasOcultas = porTurma.length - turmasExibidas.length;

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Bem-vindo, ${usuario?.nome}`}
        subtitle={usuario ? descricaoPorPerfil[usuario.perfil] : undefined}
      />

      <Card title="Seu perfil" className="animate-fade-in-up" style={staggerStyle(0)}>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-gray-500">Perfil de acesso</dt>
            <dd className="font-medium text-gray-800 mt-0.5">{usuario?.perfil}</dd>
          </div>
          <div>
            <dt className="text-gray-500">{mostrarEstoque ? "Almoxarifado vinculado" : "Polo vinculado"}</dt>
            <dd className="font-medium text-gray-800 mt-0.5">
              {mostrarEstoque
                ? usuario?.almoxarifado_nome ?? "—"
                : usuario?.polo_id ? usuario.polo_codigo ?? usuario.polo_nome ?? "—" : "—"}
            </dd>
          </div>
        </dl>
      </Card>

      {mostrarRelatorio && carregando && (
        <Card>
          <Spinner label="Carregando indicadores…" />
        </Card>
      )}

      {mostrarEstoque && <RelatorioEstoquePage />}

      {mostrarRelatorio && !carregando && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
            <StatTile label="Beneficiários ativos" value={beneficiariosAtivos.length} staggerIndex={1} />
            <StatTile label="Turmas" value={turmas.length} staggerIndex={2} />
            <StatTile
              label="Ocupação média de vagas"
              value={`${ocupacaoMedia}%`}
              sublabel={`${vagasOcupadas}/${vagasTotais} vagas`}
              staggerIndex={3}
            />
            <StatTile
              label="Autorizam WhatsApp"
              value={`${percWhatsapp}%`}
              sublabel={`dos beneficiários ativos`}
              staggerIndex={4}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Beneficiários por modalidade" className="animate-fade-in-up" style={staggerStyle(5)}>
              <DonutChart data={porModalidade} />
            </Card>
            <Card
              title="Beneficiários por turma"
              subtitle={turmasOcultas > 0 ? `mostrando as ${MAX_TURMAS_NO_GRAFICO} maiores de ${porTurma.length}` : undefined}
              className="animate-fade-in-up"
              style={staggerStyle(6)}
            >
              <BarList data={turmasExibidas} />
            </Card>
          </div>

          <PolosMapaCard polos={polos} />
        </>
      )}
    </div>
  );
}
