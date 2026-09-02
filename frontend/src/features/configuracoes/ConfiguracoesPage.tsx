import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { InformacoesGeraisTab } from "./InformacoesGeraisTab";

export function ConfiguracoesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Configurações"
        subtitle="Dados gerais do projeto/convênio, exibidos no rodapé de todos os relatórios exportados."
      />
      <Card className="animate-fade-in-up">
        <InformacoesGeraisTab />
      </Card>
    </div>
  );
}
