import type { FichaChamada } from "@/types";
import { DetalhesFichaPresenca } from "./DetalhesFichaPresenca";
import { STATUS_ESTILO, dataBR, diaCurto } from "./statusChamada";

const BARRA_COR: Record<string, string> = {
  presenca: "bg-emerald-500",
  falta: "bg-red-500",
  falta_justificada: "bg-blue-500",
  impeditivo: "bg-amber-400",
  sem_marcacao: "bg-gray-300",
};

const BARRA_LABEL: Record<string, string> = {
  presenca: "Presença",
  falta: "Falta",
  falta_justificada: "Falta Justificada",
  impeditivo: "Impeditivo",
  sem_marcacao: "Sem marcação",
};

/**
 * Documento impresso da Ficha de Chamada mensal — no padrão visual de
 * referência do cliente: cabeçalho com dados da turma, legenda, tabela com
 * ícone colorido por dia/beneficiário, impeditivos do mês e barra de
 * resumo geral. Usado tanto pelo Professor (própria turma) quanto pela
 * Central de Relatórios (MASTER/GESTOR_POLO, qualquer turma).
 */
export function FichaChamadaImpressao({ ficha }: { ficha: FichaChamada }) {
  const chaves = ["presenca", "falta", "falta_justificada", "impeditivo", "sem_marcacao"] as const;
  const total = ficha.resumo.total || 1;

  return (
    <div className="bg-white rounded-xl p-8 shadow-sm">
      <div className="flex items-start justify-between gap-4 mb-4 pb-4 border-b-4 border-brand">
        <img src="/logo.png" alt="Conexão Esporte" className="w-10 h-10 object-contain" />
        <div className="text-right text-xs text-gray-500">
          <div className="font-semibold text-brand-dark">Conexão Esporte</div>
          <div>Ficha gerada pelo sistema</div>
          <div>{new Date().toLocaleDateString("pt-BR")}</div>
        </div>
      </div>

      <h1 className="text-lg font-bold text-brand-dark uppercase tracking-wide mb-1">
        Ficha de Chamada <span className="font-normal text-sm text-gray-500 normal-case">(com marcações)</span>
      </h1>

      <div className="mb-4">
        <h2 className="text-sm font-bold text-brand-dark mb-2">Detalhes da ficha de presença</h2>
        <DetalhesFichaPresenca ficha={ficha} />
        <div className="mt-3 inline-block bg-brand-light text-brand-dark font-bold text-sm px-3 py-1.5 rounded-lg">
          {ficha.linhas.length} beneficiário{ficha.linhas.length === 1 ? "" : "s"} ativo{ficha.linhas.length === 1 ? "" : "s"}
        </div>
      </div>

      <div className="flex flex-wrap gap-4 items-center text-xs bg-gray-50 rounded-lg px-4 py-2 mb-4">
        <span className="font-semibold text-gray-500">Legenda:</span>
        {(Object.keys(STATUS_ESTILO) as (keyof typeof STATUS_ESTILO)[]).map((k) => (
          <span key={k} className={`flex items-center gap-1 ${STATUS_ESTILO[k].className}`}>
            {STATUS_ESTILO[k].icon} <span className="text-gray-600">{STATUS_ESTILO[k].titulo}</span>
          </span>
        ))}
      </div>

      {ficha.linhas.length === 0 || ficha.datas.length === 0 ? (
        <p className="text-sm text-gray-500">Sem beneficiários ativos ou sem aulas previstas neste mês.</p>
      ) : (
        <div className="overflow-x-auto -mx-2">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left uppercase tracking-wide text-gray-400 bg-gray-50">
                <th className="py-1.5 px-2">Nº</th>
                <th className="px-2">Beneficiário</th>
                <th className="px-2">Idade</th>
                <th className="px-2">Freq.</th>
                {ficha.datas.map((d) => <th key={d} className="px-1 text-center">{diaCurto(d)}</th>)}
              </tr>
            </thead>
            <tbody>
              {ficha.linhas.map((linha, i) => (
                <tr key={linha.beneficiario_id} className="border-t border-gray-100">
                  <td className="py-1.5 px-2 text-gray-400">{i + 1}</td>
                  <td className="px-2 font-medium text-gray-800 whitespace-nowrap">{linha.nome}</td>
                  <td className="px-2 text-gray-500">{linha.idade ?? "—"}</td>
                  <td className="px-2 font-semibold text-brand-dark">{linha.frequencia_pct}%</td>
                  {ficha.datas.map((d) => {
                    const estilo = STATUS_ESTILO[linha.status_por_data[d]];
                    return (
                      <td key={d} className={`px-1 text-center ${estilo.className}`}>
                        <span className="inline-flex">{estilo.icon}</span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {ficha.impeditivos.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">
            Impeditivos de aula ({ficha.impeditivos.length})
          </h3>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left uppercase tracking-wide text-gray-400 bg-gray-50">
                <th className="py-1.5 px-2">Data</th>
                <th className="px-2">Justificativa</th>
              </tr>
            </thead>
            <tbody>
              {ficha.impeditivos.map((imp) => (
                <tr key={imp.id} className="border-t border-gray-100">
                  <td className="py-1.5 px-2 text-gray-600">{dataBR(imp.data)}</td>
                  <td className="px-2 text-gray-600">{imp.justificativa}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {ficha.justificativas.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">
            Justificativas de falta ({ficha.justificativas.length})
          </h3>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left uppercase tracking-wide text-gray-400 bg-gray-50">
                <th className="py-1.5 px-2">Beneficiário</th>
                <th className="px-2">Data</th>
                <th className="px-2">Justificativa</th>
              </tr>
            </thead>
            <tbody>
              {ficha.justificativas.map((j, i) => (
                <tr key={`${j.beneficiario_id}-${j.data}-${i}`} className="border-t border-gray-100">
                  <td className="py-1.5 px-2 text-gray-800 font-medium whitespace-nowrap">{j.beneficiario_nome}</td>
                  <td className="px-2 text-gray-600">{dataBR(j.data)}</td>
                  <td className="px-2 text-gray-600">{j.justificativa}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-6">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">Resumo geral de marcações</h3>
        <div className="flex w-full h-5 rounded overflow-hidden">
          {chaves.map((k) => {
            const valor = ficha.resumo[k];
            const pct = (100 * valor) / total;
            if (pct <= 0) return null;
            return <div key={k} className={BARRA_COR[k]} style={{ width: `${pct}%` }} title={`${BARRA_LABEL[k]}: ${pct.toFixed(1)}%`} />;
          })}
        </div>
        <div className="flex flex-wrap gap-x-6 gap-y-1 mt-2 text-xs text-gray-600">
          {chaves.map((k) => {
            const valor = ficha.resumo[k];
            const pct = (100 * valor) / total;
            return (
              <span key={k} className="flex items-center gap-1.5">
                <span className={`w-2.5 h-2.5 rounded-sm ${BARRA_COR[k]}`} />
                {BARRA_LABEL[k]}: {pct.toFixed(1)}% ({valor})
              </span>
            );
          })}
        </div>
      </div>

      <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-8 text-sm">
        <div>
          <div className="border-t border-gray-400 pt-1">
            <div className="font-medium text-gray-700">Visto do Professor</div>
            <div className="text-gray-500">{ficha.professor_nome ?? ""}</div>
          </div>
        </div>
        <div>
          <div className="border-t border-gray-400 pt-1">
            <div className="font-medium text-gray-700">Visto do Responsável</div>
            <div className="text-gray-500">Coordenação / Direção</div>
          </div>
        </div>
      </div>
    </div>
  );
}
