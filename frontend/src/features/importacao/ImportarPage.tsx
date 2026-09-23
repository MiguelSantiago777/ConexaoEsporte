import { ComponentType, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import {
  AcademicCapIcon,
  BuildingIcon,
  ClipboardIcon,
  StackIcon,
  UsersIcon,
} from "@/components/ui/icons";
import { ImportarPlanilhaModal } from "@/components/import/ImportarPlanilhaModal";

interface EntidadeImportavel {
  recurso: string;
  titulo: string;
  descricao: string;
  icon: ComponentType<{ className?: string }>;
  queryKey: string;
  nomeArquivoModelo: string;
}

const ENTIDADES: EntidadeImportavel[] = [
  {
    recurso: "beneficiarios", titulo: "Beneficiários",
    descricao: "Cadastro de beneficiários e responsáveis legais.",
    icon: ClipboardIcon, queryKey: "beneficiarios",
    nomeArquivoModelo: "modelo-importacao-beneficiarios.xlsx",
  },
  {
    recurso: "turmas", titulo: "Turmas",
    descricao: "Turmas de cada modalidade, por polo.",
    icon: UsersIcon, queryKey: "turmas",
    nomeArquivoModelo: "modelo-importacao-turmas.xlsx",
  },
  {
    recurso: "usuarios", titulo: "Professores / Usuários",
    descricao: "Professores, gestores e demais funcionários.",
    icon: AcademicCapIcon, queryKey: "usuarios",
    nomeArquivoModelo: "modelo-importacao-usuarios.xlsx",
  },
  {
    recurso: "produtos", titulo: "Produtos",
    descricao: "Produtos do Estoque, com quantidade inicial e NCM.",
    icon: StackIcon, queryKey: "produtos",
    nomeArquivoModelo: "modelo-importacao-produtos.xlsx",
  },
  {
    recurso: "polos", titulo: "Polos",
    descricao: "Unidades onde os projetos esportivos são executados.",
    icon: BuildingIcon, queryKey: "polos",
    nomeArquivoModelo: "modelo-importacao-polos.xlsx",
  },
];

/**
 * Ponto único de importação em massa por planilha — exclusivo do MASTER.
 * Escolha a entidade e o mesmo fluxo de sempre roda dentro do modal: baixar
 * modelo → enviar preenchido → prévia (nada é gravado) → confirmar.
 */
export function ImportarPage() {
  const queryClient = useQueryClient();
  const [entidadeAberta, setEntidadeAberta] = useState<EntidadeImportavel | null>(null);

  return (
    <div className="space-y-6">
      <PageHeader title="Importar" subtitle="Cadastre em massa a partir de uma planilha — escolha o que você quer importar." />

      <Card title="O que você quer importar?" className="animate-fade-in-up">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {ENTIDADES.map((entidade) => {
            const Icon = entidade.icon;
            return (
              <button
                key={entidade.recurso}
                type="button"
                onClick={() => setEntidadeAberta(entidade)}
                className="flex items-start gap-3 text-left p-4 rounded-lg border border-slate-300 hover:border-brand hover:bg-brand-light/40 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50"
              >
                <span className="w-10 h-10 rounded-lg bg-brand-light text-brand flex items-center justify-center shrink-0">
                  <Icon className="w-5 h-5" />
                </span>
                <span>
                  <span className="block text-sm font-semibold text-brand-dark">{entidade.titulo}</span>
                  <span className="block text-xs text-slate-500 mt-0.5">{entidade.descricao}</span>
                </span>
              </button>
            );
          })}
        </div>
      </Card>

      <ImportarPlanilhaModal
        aberto={entidadeAberta !== null}
        onFechar={() => setEntidadeAberta(null)}
        recurso={entidadeAberta?.recurso ?? ""}
        titulo={entidadeAberta ? `Importar ${entidadeAberta.titulo.toLowerCase()}` : ""}
        nomeArquivoModelo={entidadeAberta?.nomeArquivoModelo ?? ""}
        onImportado={() => {
          if (entidadeAberta) queryClient.invalidateQueries({ queryKey: [entidadeAberta.queryKey] });
        }}
      />
    </div>
  );
}
