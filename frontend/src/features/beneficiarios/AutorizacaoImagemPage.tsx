import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "@/lib/api";
import type { Beneficiario } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import { staggerStyle } from "@/lib/animation";
import { maskCPF } from "@/lib/masks";
import { formatarData } from "@/lib/format";

function hoje() {
  return new Date().toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" });
}

/**
 * Gera um termo de autorização de uso de imagem pré-preenchido com os dados do
 * beneficiário e do responsável, pronto para impressão/exportação em PDF pelo
 * navegador (Ctrl+P → Salvar como PDF) e envio ao responsável para assinatura.
 */
export function AutorizacaoImagemPage() {
  const { id } = useParams<{ id: string }>();
  const [beneficiario, setBeneficiario] = useState<Beneficiario | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [documentoResponsavel, setDocumentoResponsavel] = useState("");
  const [cidade, setCidade] = useState("");

  useEffect(() => {
    api.get<Beneficiario[]>("/beneficiarios").then((r) => {
      setBeneficiario(r.data.find((b) => b.id === id) ?? null);
      setCarregando(false);
    });
  }, [id]);

  if (carregando) {
    return <Spinner label="Carregando…" />;
  }

  if (!beneficiario) {
    return (
      <div className="space-y-4">
        <PageHeader title="Autorização de uso de imagem" />
        <Card>
          <p className="text-gray-500">Beneficiário não encontrado.</p>
          <Link to="/beneficiarios" className="text-brand text-sm font-medium hover:underline">
            ← Voltar para beneficiários
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="print:hidden">
        <PageHeader
          title="Autorização de uso de imagem"
          subtitle={`Termo pré-preenchido para ${beneficiario.nome_completo}.`}
        />
      </div>

      <Card className="print:hidden animate-fade-in-up" style={staggerStyle(0)}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="CPF ou RG do responsável (para o documento)"
            value={documentoResponsavel}
            onChange={(e) => setDocumentoResponsavel(e.target.value)}
            placeholder="Número do documento"
          />
          <Input label="Cidade" value={cidade} onChange={(e) => setCidade(e.target.value)} placeholder="Cidade onde o termo é assinado" />
        </div>
        <div className="mt-4 flex gap-3">
          <Button onClick={() => window.print()}>Baixar / imprimir documento</Button>
          <Link to="/beneficiarios">
            <Button variant="secondary" type="button">Voltar</Button>
          </Link>
        </div>
        <p className="text-xs text-gray-400 mt-3">
          Este documento é gerado para assinatura manual (impressa ou digitalizada) do responsável — não envolve
          nenhuma integração eletrônica externa.
        </p>
      </Card>

      <div
        className="bg-white rounded-xl shadow-sm border border-gray-200/80 p-10 print:shadow-none print:border-0 print:rounded-none print:p-0 max-w-2xl mx-auto leading-relaxed text-sm text-gray-800 animate-fade-in-up"
        style={staggerStyle(1)}
      >
        <div className="flex items-center gap-3 mb-8">
          <img src="/logo.png" alt="Conexão Esporte" className="w-12 h-12 object-contain" />
          <div>
            <div className="font-bold text-brand-dark">Conexão Esporte</div>
            <div className="text-xs text-gray-500">Gestão de projetos esportivos</div>
          </div>
        </div>

        <h1 className="text-center font-bold text-base uppercase tracking-wide mb-8">
          Termo de Autorização de Uso de Imagem
        </h1>

        <p className="mb-4">
          Eu, <strong>{beneficiario.responsavel_legal_nome || "________________________________"}</strong>, portador(a)
          do documento de identidade/CPF nº <strong>{documentoResponsavel || "________________"}</strong>, na condição
          de <strong>{beneficiario.responsavel_legal_tipo_relacao || "responsável legal"}</strong> de{" "}
          <strong>{beneficiario.nome_completo}</strong>, nascido(a) em{" "}
          <strong>{formatarData(beneficiario.data_nascimento)}</strong>, portador(a) do CPF nº{" "}
          <strong>{maskCPF(beneficiario.documento)}</strong>, inscrito(a) no projeto esportivo Conexão Esporte,
          declaro estar ciente e <strong>AUTORIZO</strong> o uso da imagem do(a) beneficiário(a) acima identificado(a),
          captada em fotografias e vídeos durante as atividades do projeto, para fins de divulgação institucional,
          educacional e promocional do Conexão Esporte, em redes sociais, site oficial, materiais impressos e demais
          meios de comunicação, sem finalidade comercial e sem qualquer ônus para as partes.
        </p>

        <p className="mb-8">
          Esta autorização é válida por prazo indeterminado, podendo ser revogada a qualquer momento mediante
          solicitação por escrito.
        </p>

        <p className="mb-16">
          {cidade || "________________________"}, {hoje()}.
        </p>

        <div className="text-center">
          <div className="border-t border-gray-400 w-72 mx-auto mb-1" />
          <div>Assinatura do responsável legal</div>
          <div className="text-gray-500">{beneficiario.responsavel_legal_nome || ""}</div>
        </div>
      </div>
    </div>
  );
}
