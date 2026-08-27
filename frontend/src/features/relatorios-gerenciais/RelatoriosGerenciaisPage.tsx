import { useState } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { useAuth } from "@/features/auth/AuthContext";
import { RelatorioGeralPage } from "./RelatorioGeralPage";
import { RelatorioPoloPage } from "./RelatorioPoloPage";
import { RelatorioBeneficiariosPage } from "./RelatorioBeneficiariosPage";
import { RelatorioProfessoresPage } from "./RelatorioProfessoresPage";
import { RelatorioEntregasPage } from "./RelatorioEntregasPage";
import { RelatorioFichaChamadaPage } from "./RelatorioFichaChamadaPage";

type Aba = "geral" | "polo" | "beneficiarios" | "professores" | "entregas" | "chamada";

export function RelatoriosGerenciaisPage() {
  const { temPerfil } = useAuth();
  const ehMaster = temPerfil("MASTER");
  const [aba, setAba] = useState<Aba>(ehMaster ? "geral" : "polo");

  const abas: { id: Aba; label: string }[] = [
    ...(ehMaster ? [{ id: "geral" as const, label: "Relatório Geral" }] : []),
    { id: "polo", label: "Relatório do Polo" },
    { id: "beneficiarios", label: "Ficha Cadastral — Beneficiários" },
    { id: "professores", label: "Ficha Cadastral — Professores" },
    { id: "entregas", label: "Entrega de Materiais" },
    { id: "chamada", label: "Ficha de Chamada" },
  ];

  return (
    <div className="space-y-6">
      <div className="print:hidden">
        <PageHeader title="Relatórios" subtitle="Relatórios gerenciais, fichas cadastrais e documentos prontos para impressão." />
      </div>

      <div className="print:hidden flex flex-wrap gap-2 border-b border-gray-200 pb-px">
        {abas.map((a) => (
          <button
            key={a.id}
            type="button"
            onClick={() => setAba(a.id)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
              aba === a.id
                ? "border-brand text-brand-dark bg-white"
                : "border-transparent text-gray-500 hover:text-brand-dark hover:bg-gray-50"
            }`}
          >
            {a.label}
          </button>
        ))}
      </div>

      {aba === "geral" && ehMaster && <RelatorioGeralPage />}
      {aba === "polo" && <RelatorioPoloPage />}
      {aba === "beneficiarios" && <RelatorioBeneficiariosPage />}
      {aba === "professores" && <RelatorioProfessoresPage />}
      {aba === "entregas" && <RelatorioEntregasPage />}
      {aba === "chamada" && <RelatorioFichaChamadaPage />}
    </div>
  );
}
