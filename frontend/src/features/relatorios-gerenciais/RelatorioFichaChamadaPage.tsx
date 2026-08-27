import { useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { FichaChamada, Modalidade, Polo, Turma } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { staggerStyle } from "@/lib/animation";
import { useAuth } from "@/features/auth/AuthContext";
import { useToast } from "@/components/ui/toast/ToastContext";
import { exportarPdf } from "@/lib/exportarPdf";
import { exportarXlsxMultiplasAbas } from "@/lib/exportarXlsx";
import { FichaChamadaImpressao } from "@/features/frequencia/FichaChamadaImpressao";
import { fichaChamadaParaAbas } from "@/features/frequencia/statusChamada";

const MES_ATUAL = new Date().getMonth() + 1;
const ANO_ATUAL = new Date().getFullYear();

/** Ficha de Chamada mensal de qualquer turma — acesso gerencial (MASTER/GESTOR_POLO). */
export function RelatorioFichaChamadaPage() {
  const { usuario, temPerfil } = useAuth();
  const ehMaster = temPerfil("MASTER");
  const toast = useToast();
  const [exportando, setExportando] = useState(false);
  const [exportandoXlsx, setExportandoXlsx] = useState(false);
  const conteudoRef = useRef<HTMLDivElement>(null);

  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
    enabled: ehMaster,
  });
  const { data: turmas = [] } = useQuery({
    queryKey: ["turmas"],
    queryFn: () => api.get<Turma[]>("/turmas").then((r) => r.data),
  });
  const { data: modalidades = [] } = useQuery({
    queryKey: ["modalidades"],
    queryFn: () => api.get<Modalidade[]>("/modalidades").then((r) => r.data),
  });

  const [poloId, setPoloId] = useState(usuario?.polo_id ?? "");
  const [turmaId, setTurmaId] = useState("");
  const [mes, setMes] = useState(MES_ATUAL);
  const [ano, setAno] = useState(ANO_ATUAL);

  const turmasDoPolo = useMemo(
    () => turmas.filter((t) => !poloId || t.polo_id === poloId),
    [turmas, poloId]
  );

  function rotuloTurma(t: Turma) {
    const modalidade = modalidades.find((m) => m.id === t.modalidade_id)?.nome ?? "—";
    return `${modalidade} — ${t.horario_inicio}–${t.horario_fim} (${t.dias_semana.join(",")})`;
  }

  const { data: ficha, isLoading: carregando } = useQuery<FichaChamada>({
    queryKey: ["frequencias", "ficha-chamada", turmaId, mes, ano],
    queryFn: () =>
      api
        .get<FichaChamada>("/frequencias/ficha-chamada", { params: { turma_id: turmaId, mes, ano } })
        .then((r) => r.data),
    enabled: !!turmaId,
  });

  async function baixarPdf() {
    if (!conteudoRef.current) return;
    setExportando(true);
    try {
      await exportarPdf(conteudoRef.current, "ficha-de-chamada.pdf");
    } catch {
      toast.error("Não foi possível gerar o PDF. Tente novamente.");
    } finally {
      setExportando(false);
    }
  }

  async function baixarXlsx() {
    if (!ficha) return;
    setExportandoXlsx(true);
    try {
      await exportarXlsxMultiplasAbas(fichaChamadaParaAbas(ficha), "ficha-de-chamada.xlsx");
    } catch {
      toast.error("Não foi possível gerar o Excel. Tente novamente.");
    } finally {
      setExportandoXlsx(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card className="animate-fade-in-up" style={staggerStyle(0)}>
        <div className="flex flex-col sm:flex-row gap-4 sm:items-end flex-wrap">
          {ehMaster && (
            <div className="sm:w-56">
              <Select
                label="Polo"
                value={poloId}
                onChange={(e) => { setPoloId(e.target.value); setTurmaId(""); }}
              >
                <option value="">Todos os polos</option>
                {polos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
              </Select>
            </div>
          )}
          <div className="flex-1 sm:min-w-64">
            <Select label="Turma" value={turmaId} onChange={(e) => setTurmaId(e.target.value)}>
              <option value="">— Selecione —</option>
              {turmasDoPolo.map((t) => <option key={t.id} value={t.id}>{rotuloTurma(t)}</option>)}
            </Select>
          </div>
          <div className="sm:w-28">
            <Input label="Mês" type="number" min={1} max={12} value={mes} onChange={(e) => setMes(Number(e.target.value))} />
          </div>
          <div className="sm:w-28">
            <Input label="Ano" type="number" min={2000} max={2100} value={ano} onChange={(e) => setAno(Number(e.target.value))} />
          </div>
          {ficha && (
            <>
              <Button variant="secondary" onClick={baixarXlsx} disabled={exportandoXlsx}>
                {exportandoXlsx ? "Gerando…" : "Baixar Excel"}
              </Button>
              <Button variant="secondary" onClick={baixarPdf} disabled={exportando}>
                {exportando ? "Gerando…" : "Baixar PDF"}
              </Button>
            </>
          )}
        </div>
      </Card>

      {!turmaId && (
        <Card><EmptyState message="Selecione uma turma para gerar a Ficha de Chamada." /></Card>
      )}
      {turmaId && carregando && <Spinner label="Carregando ficha de chamada…" />}
      {turmaId && !carregando && ficha && (
        <div ref={conteudoRef}>
          <FichaChamadaImpressao ficha={ficha} />
        </div>
      )}
    </div>
  );
}
