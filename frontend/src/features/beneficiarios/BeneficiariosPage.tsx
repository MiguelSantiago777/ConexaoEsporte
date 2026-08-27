import { FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Beneficiario, Modalidade, Polo, Turma } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";
import { FileInput } from "@/components/ui/FileInput";
import { PencilIcon, TrashIcon, TrophyIcon } from "@/components/ui/icons";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { maskCPF, maskTelefone, onlyDigits } from "@/lib/masks";
import { formatarData } from "@/lib/format";
import { TIPOS_RELACAO } from "./constants";
import { DocumentosModal } from "./DocumentosModal";
import { EditarBeneficiarioModal } from "./EditarBeneficiarioModal";
import { MatriculasModal } from "./MatriculasModal";

const FORM_INICIAL = {
  nome_completo: "",
  data_nascimento: "",
  documento: "",
  polo_id: "",
  modalidade_id: "",
  turma_id: "",
  responsavel_legal_nome: "",
  responsavel_legal_data_nascimento: "",
  responsavel_legal_tipo_relacao: "",
  responsavel_legal_tipo_relacao_outro: "",
  responsavel_legal_telefone_1: "",
  responsavel_legal_telefone_2: "",
  responsavel_legal_email: "",
  responsavel_legal_rede_social: "",
  endereco: "",
  autoriza_whatsapp: false,
  observacoes_medicas: "",
};

type CampoDocumento =
  | "certidao_nascimento_ou_identidade"
  | "identidade_responsavel"
  | "comprovante_residencia"
  | "comprovante_escolar";

const DOCUMENTOS_CONFIG: { campo: CampoDocumento; label: string }[] = [
  { campo: "certidao_nascimento_ou_identidade", label: "Certidão de nascimento ou identidade do beneficiário" },
  { campo: "identidade_responsavel", label: "Identidade do responsável" },
  { campo: "comprovante_residencia", label: "Comprovante de residência" },
  { campo: "comprovante_escolar", label: "Comprovante escolar" },
];

const ARQUIVOS_INICIAL: Record<CampoDocumento, File | null> = {
  certidao_nascimento_ou_identidade: null,
  identidade_responsavel: null,
  comprovante_residencia: null,
  comprovante_escolar: null,
};

/**
 * Página de cadastro e listagem de BENEFICIÁRIOS.
 * Nomenclatura oficial e obrigatória — nunca "aluno".
 *
 * Modalidade/turma não fazem parte do cadastro em si — um beneficiário pode
 * estar matriculado em várias ao mesmo tempo (ex.: judô e natação), então
 * isso é gerenciado à parte pelo MatriculasModal.
 */
export function BeneficiariosPage() {
  const toast = useToast();
  const queryClient = useQueryClient();

  const { data: beneficiarios = [], isLoading: carregando } = useQuery({
    queryKey: ["beneficiarios"],
    queryFn: () => api.get<Beneficiario[]>("/beneficiarios").then((r) => r.data),
  });
  const { data: turmas = [] } = useQuery({
    queryKey: ["turmas"],
    queryFn: () => api.get<Turma[]>("/turmas").then((r) => r.data),
  });
  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });
  const { data: modalidades = [] } = useQuery({
    queryKey: ["modalidades"],
    queryFn: () => api.get<Modalidade[]>("/modalidades").then((r) => r.data),
  });

  const [enviando, setEnviando] = useState(false);
  const [form, setForm] = useState(FORM_INICIAL);
  const [arquivos, setArquivos] = useState<Record<CampoDocumento, File | null>>(ARQUIVOS_INICIAL);
  const [filtroNome, setFiltroNome] = useState("");
  const [filtroPolo, setFiltroPolo] = useState("");
  const [beneficiarioDocumentos, setBeneficiarioDocumentos] = useState<Beneficiario | null>(null);
  const [beneficiarioEditando, setBeneficiarioEditando] = useState<Beneficiario | null>(null);
  const [beneficiarioMatriculas, setBeneficiarioMatriculas] = useState<Beneficiario | null>(null);

  function poloNome(id: string | null) {
    return polos.find((p) => p.id === id)?.nome ?? "—";
  }

  const turmasDoFormulario = useMemo(
    () => turmas.filter((t) => t.polo_id === form.polo_id && t.modalidade_id === form.modalidade_id),
    [turmas, form.polo_id, form.modalidade_id]
  );

  const beneficiariosFiltrados = useMemo(
    () =>
      beneficiarios.filter((b) => {
        if (!b.ativo) return false;
        const nomeOk = !filtroNome || b.nome_completo.toLowerCase().includes(filtroNome.toLowerCase());
        const poloOk = !filtroPolo || b.polo_id === filtroPolo;
        return nomeOk && poloOk;
      }),
    [beneficiarios, filtroNome, filtroPolo]
  );

  const removerMutation = useMutation({
    mutationFn: (b: Beneficiario) => api.patch(`/beneficiarios/${b.id}`, { ativo: false }),
    onSuccess: () => {
      toast.success("Beneficiário removido.");
      queryClient.invalidateQueries({ queryKey: ["beneficiarios"] });
    },
    onError: (err: any) => {
      toast.error(mensagemErroApi(err, "Erro ao remover beneficiário."));
    },
  });

  function excluirBeneficiario(b: Beneficiario) {
    if (!window.confirm(`Remover ${b.nome_completo} da lista de beneficiários?`)) return;
    removerMutation.mutate(b);
  }

  async function enviarDocumentos(beneficiarioId: string) {
    const selecionados = (Object.entries(arquivos) as [CampoDocumento, File | null][]).filter(([, f]) => f);
    if (selecionados.length === 0) return;
    const dados = new FormData();
    selecionados.forEach(([campo, arquivo]) => dados.append(campo, arquivo as File));
    try {
      // Não define Content-Type manualmente: o navegador precisa gerar o boundary do multipart.
      await api.post(`/beneficiarios/${beneficiarioId}/documentos`, dados);
    } catch {
      toast.warning(
        "Beneficiário cadastrado, mas não foi possível enviar os documentos agora. Anexe novamente mais tarde."
      );
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form.modalidade_id || !form.turma_id) {
      toast.error("Selecione a modalidade e a turma do beneficiário.");
      return;
    }
    setEnviando(true);
    try {
      const { responsavel_legal_tipo_relacao_outro, modalidade_id, turma_id, ...dadosForm } = form;
      const tipoRelacaoFinal =
        form.responsavel_legal_tipo_relacao === "Outro"
          ? responsavel_legal_tipo_relacao_outro
          : form.responsavel_legal_tipo_relacao;
      const { data: criado } = await api.post<Beneficiario>("/beneficiarios", {
        ...dadosForm,
        documento: onlyDigits(form.documento),
        responsavel_legal_telefone_1: onlyDigits(form.responsavel_legal_telefone_1) || null,
        responsavel_legal_telefone_2: onlyDigits(form.responsavel_legal_telefone_2) || null,
        responsavel_legal_nome: form.responsavel_legal_nome || null,
        responsavel_legal_data_nascimento: form.responsavel_legal_data_nascimento || null,
        responsavel_legal_tipo_relacao: tipoRelacaoFinal || null,
        responsavel_legal_email: form.responsavel_legal_email || null,
        responsavel_legal_rede_social: form.responsavel_legal_rede_social || null,
        endereco: form.endereco || null,
        observacoes_medicas: form.observacoes_medicas || null,
      });
      await enviarDocumentos(criado.id);
      try {
        await api.post(`/beneficiarios/${criado.id}/matriculas`, { turma_id });
        toast.success("Beneficiário cadastrado e matriculado com sucesso.");
      } catch (err: any) {
        toast.error(
          `Beneficiário cadastrado, mas houve um problema ao matricular na turma: ${
            mensagemErroApi(err, "erro desconhecido")
          }. Você pode tentar novamente pelo ícone de troféu na lista.`
        );
      }
      setForm(FORM_INICIAL);
      setArquivos(ARQUIVOS_INICIAL);
      queryClient.invalidateQueries({ queryKey: ["beneficiarios"] });
      queryClient.invalidateQueries({ queryKey: ["turmas"] });
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao cadastrar beneficiário."));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Beneficiários" subtitle="Cadastro de beneficiários e seus responsáveis legais." />

      <Card title="Cadastrar beneficiário" className="animate-fade-in-up" style={staggerStyle(0)}>
        <form onSubmit={handleSubmit} className="space-y-6">
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-brand/70 mb-3">Dados do beneficiário</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2">
                <Input
                  label="Nome completo"
                  value={form.nome_completo}
                  onChange={(e) => setForm({ ...form, nome_completo: e.target.value })}
                  required
                />
              </div>
              <Input
                label="Data de nascimento"
                type="date"
                value={form.data_nascimento}
                onChange={(e) => setForm({ ...form, data_nascimento: e.target.value })}
                required
              />
              <Input
                label="CPF"
                placeholder="000.000.000-00"
                inputMode="numeric"
                value={form.documento}
                onChange={(e) => setForm({ ...form, documento: maskCPF(e.target.value) })}
                maxLength={14}
                required
                hint="Sempre exclusivo do próprio beneficiário — mesmo entre irmãos."
              />
              <Select
                label="Polo"
                value={form.polo_id}
                onChange={(e) => setForm({ ...form, polo_id: e.target.value, modalidade_id: "", turma_id: "" })}
                required
              >
                <option value="">— Selecione —</option>
                {polos.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nome}
                  </option>
                ))}
              </Select>
              <Select
                label="Modalidade"
                value={form.modalidade_id}
                onChange={(e) => setForm({ ...form, modalidade_id: e.target.value, turma_id: "" })}
                disabled={!form.polo_id}
                required
              >
                <option value="">— Selecione —</option>
                {modalidades.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.nome}
                  </option>
                ))}
              </Select>
              <Select
                label="Turma"
                value={form.turma_id}
                onChange={(e) => setForm({ ...form, turma_id: e.target.value })}
                disabled={!form.modalidade_id}
                required
              >
                <option value="">— Selecione —</option>
                {turmasDoFormulario.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.horario_inicio}–{t.horario_fim} ({t.dias_semana.join(", ")}) — {t.vagas_ocupadas}/{t.limite_vagas} vagas
                  </option>
                ))}
              </Select>
            </div>
            <p className="text-xs text-gray-400 mt-3">
              Essa é a matrícula inicial do beneficiário. Para matricular em outras modalidades/turmas ao mesmo
              tempo, use o ícone de troféu na lista depois do cadastro.
            </p>
          </section>

          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-brand/70 mb-3">Responsável legal</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="lg:col-span-2">
                <Input
                  label="Nome do responsável"
                  value={form.responsavel_legal_nome}
                  onChange={(e) => setForm({ ...form, responsavel_legal_nome: e.target.value })}
                />
              </div>
              <Input
                label="Nascimento do responsável"
                type="date"
                value={form.responsavel_legal_data_nascimento}
                onChange={(e) => setForm({ ...form, responsavel_legal_data_nascimento: e.target.value })}
              />
              <Select
                label="Tipo de relação"
                value={form.responsavel_legal_tipo_relacao}
                onChange={(e) => setForm({ ...form, responsavel_legal_tipo_relacao: e.target.value })}
              >
                <option value="">— Selecione —</option>
                {TIPOS_RELACAO.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </Select>
              {form.responsavel_legal_tipo_relacao === "Outro" && (
                <Input
                  label="Especifique o grau de parentesco"
                  value={form.responsavel_legal_tipo_relacao_outro}
                  onChange={(e) => setForm({ ...form, responsavel_legal_tipo_relacao_outro: e.target.value })}
                  required
                />
              )}
              <Input
                label="Telefone de contato 1"
                placeholder="(00) 00000-0000"
                inputMode="numeric"
                value={form.responsavel_legal_telefone_1}
                onChange={(e) => setForm({ ...form, responsavel_legal_telefone_1: maskTelefone(e.target.value) })}
                maxLength={15}
              />
              <Input
                label="Telefone de contato 2"
                placeholder="(00) 00000-0000"
                inputMode="numeric"
                value={form.responsavel_legal_telefone_2}
                onChange={(e) => setForm({ ...form, responsavel_legal_telefone_2: maskTelefone(e.target.value) })}
                maxLength={15}
              />
              <Input
                label="Email"
                type="email"
                placeholder="nome@exemplo.com"
                value={form.responsavel_legal_email}
                onChange={(e) => setForm({ ...form, responsavel_legal_email: e.target.value })}
              />
              <Input
                label="Rede social"
                placeholder="@usuario ou link do perfil"
                value={form.responsavel_legal_rede_social}
                onChange={(e) => setForm({ ...form, responsavel_legal_rede_social: e.target.value })}
              />
              <div className="lg:col-span-2">
                <Input
                  label="Endereço"
                  value={form.endereco}
                  onChange={(e) => setForm({ ...form, endereco: e.target.value })}
                />
              </div>
              <div className="lg:col-span-2 flex items-end">
                <label className="flex items-center gap-2 cursor-pointer select-none pb-2">
                  <input
                    type="checkbox"
                    className="w-5 h-5 accent-[#fcba27] rounded"
                    checked={form.autoriza_whatsapp}
                    onChange={(e) => setForm({ ...form, autoriza_whatsapp: e.target.checked })}
                  />
                  <span className="text-sm text-gray-700">Autorizo o envio de mensagens via WhatsApp</span>
                </label>
              </div>
            </div>
          </section>

          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-brand/70 mb-3">Documentos anexos</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {DOCUMENTOS_CONFIG.map(({ campo, label }) => (
                <FileInput
                  key={campo}
                  label={label}
                  accept="image/*,application/pdf"
                  file={arquivos[campo]}
                  onChange={(file) => setArquivos({ ...arquivos, [campo]: file })}
                />
              ))}
            </div>
          </section>

          <section>
            <Input
              label="Observações médicas"
              value={form.observacoes_medicas}
              onChange={(e) => setForm({ ...form, observacoes_medicas: e.target.value })}
            />
          </section>

          <div>
            <Button type="submit" disabled={enviando}>
              {enviando ? "Cadastrando…" : "Cadastrar beneficiário"}
            </Button>
          </div>
        </form>
      </Card>

      <Card
        title="Beneficiários cadastrados"
        subtitle={filtroNome || filtroPolo ? `${beneficiariosFiltrados.length} de ${beneficiarios.length}` : undefined}
        actions={<Badge variant="accent">{beneficiariosFiltrados.length}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(1)}
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <Input
            label="Buscar por nome"
            placeholder="Nome do beneficiário"
            value={filtroNome}
            onChange={(e) => setFiltroNome(e.target.value)}
          />
          <Select label="Filtrar por polo" value={filtroPolo} onChange={(e) => setFiltroPolo(e.target.value)}>
            <option value="">Todos os polos</option>
            {polos.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nome}
              </option>
            ))}
          </Select>
        </div>
        {carregando ? (
          <Spinner label="Carregando beneficiários…" />
        ) : beneficiariosFiltrados.length === 0 ? (
          <EmptyState
            message={
              beneficiarios.length === 0
                ? "Nenhum beneficiário cadastrado ainda."
                : "Nenhum beneficiário encontrado com esses filtros."
            }
          />
        ) : (
          <div className="overflow-x-auto -mx-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                  <th className="py-2.5 px-6">Nome</th>
                  <th className="px-3">CPF</th>
                  <th className="px-3">Nascimento</th>
                  <th className="px-3">Polo</th>
                  <th className="px-3">Responsável</th>
                  <th className="px-3">Contato</th>
                  <th className="px-3 text-right pr-6">Ações</th>
                </tr>
              </thead>
              <tbody>
                {beneficiariosFiltrados.map((b) => (
                  <tr key={b.id} className="border-t border-gray-100 hover:bg-brand-light/60 transition-colors">
                    <td className="py-2.5 px-6 font-medium text-gray-800">
                      <button
                        type="button"
                        onClick={() => setBeneficiarioDocumentos(b)}
                        title="Ver documentos anexados"
                        className="text-left hover:text-brand hover:underline"
                      >
                        {b.nome_completo}
                      </button>
                    </td>
                    <td className="px-3 text-gray-600">{maskCPF(b.documento)}</td>
                    <td className="px-3 text-gray-600">{formatarData(b.data_nascimento)}</td>
                    <td className="px-3 text-gray-600">
                      <span className="block truncate max-w-[110px]" title={poloNome(b.polo_id)}>
                        {poloNome(b.polo_id)}
                      </span>
                    </td>
                    <td className="px-3 text-gray-600">{b.responsavel_legal_nome ?? "—"}</td>
                    <td className="px-3 text-gray-600">
                      {b.responsavel_legal_telefone_1 ? maskTelefone(b.responsavel_legal_telefone_1) : "—"}
                    </td>
                    <td className="px-3 text-right pr-6">
                      <div className="flex items-center justify-end gap-3">
                        <Link
                          to={`/beneficiarios/${b.id}/autorizacao-imagem`}
                          className="text-brand text-xs font-medium hover:underline whitespace-nowrap"
                        >
                          Autorização de imagem
                        </Link>
                        <button
                          type="button"
                          title="Matrículas (modalidades/turmas)"
                          onClick={() => setBeneficiarioMatriculas(b)}
                          className="text-gray-400 hover:text-brand transition-colors"
                        >
                          <TrophyIcon className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          title="Editar"
                          onClick={() => setBeneficiarioEditando(b)}
                          className="text-gray-400 hover:text-brand transition-colors"
                        >
                          <PencilIcon />
                        </button>
                        <button
                          type="button"
                          title="Remover"
                          onClick={() => excluirBeneficiario(b)}
                          className="text-gray-400 hover:text-red-600 transition-colors"
                        >
                          <TrashIcon />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <DocumentosModal beneficiario={beneficiarioDocumentos} onClose={() => setBeneficiarioDocumentos(null)} />
      <EditarBeneficiarioModal
        beneficiario={beneficiarioEditando}
        polos={polos}
        onClose={() => setBeneficiarioEditando(null)}
        onSalvo={() => {
          setBeneficiarioEditando(null);
          toast.success("Alterações salvas.");
          queryClient.invalidateQueries({ queryKey: ["beneficiarios"] });
        }}
      />
      <MatriculasModal
        beneficiario={beneficiarioMatriculas}
        turmas={turmas}
        modalidades={modalidades}
        polos={polos}
        onClose={() => setBeneficiarioMatriculas(null)}
        onAlterado={() => {
          queryClient.invalidateQueries({ queryKey: ["beneficiarios"] });
          queryClient.invalidateQueries({ queryKey: ["turmas"] });
        }}
      />
    </div>
  );
}
