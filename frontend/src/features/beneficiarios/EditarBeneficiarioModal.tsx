import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Beneficiario, Polo } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useToast } from "@/components/ui/toast/ToastContext";
import { maskCPF, maskTelefone, onlyDigits } from "@/lib/masks";
import { formatarData } from "@/lib/format";
import { TIPOS_RELACAO } from "./constants";

interface Props {
  beneficiario: Beneficiario | null;
  polos: Polo[];
  onClose: () => void;
  onSalvo: () => void;
}

function formInicialDe(b: Beneficiario) {
  const tipoConhecido = b.responsavel_legal_tipo_relacao && TIPOS_RELACAO.includes(b.responsavel_legal_tipo_relacao);
  return {
    nome_completo: b.nome_completo,
    polo_id: b.polo_id,
    responsavel_legal_nome: b.responsavel_legal_nome ?? "",
    responsavel_legal_data_nascimento: b.responsavel_legal_data_nascimento ?? "",
    responsavel_legal_tipo_relacao: tipoConhecido ? b.responsavel_legal_tipo_relacao! : b.responsavel_legal_tipo_relacao ? "Outro" : "",
    responsavel_legal_tipo_relacao_outro: tipoConhecido ? "" : b.responsavel_legal_tipo_relacao ?? "",
    responsavel_legal_telefone_1: b.responsavel_legal_telefone_1 ? maskTelefone(b.responsavel_legal_telefone_1) : "",
    responsavel_legal_telefone_2: b.responsavel_legal_telefone_2 ? maskTelefone(b.responsavel_legal_telefone_2) : "",
    responsavel_legal_email: b.responsavel_legal_email ?? "",
    responsavel_legal_rede_social: b.responsavel_legal_rede_social ?? "",
    endereco: b.endereco ?? "",
    autoriza_whatsapp: b.autoriza_whatsapp,
    observacoes_medicas: b.observacoes_medicas ?? "",
  };
}

export function EditarBeneficiarioModal({ beneficiario, polos, onClose, onSalvo }: Props) {
  const toast = useToast();
  const [form, setForm] = useState(beneficiario ? formInicialDe(beneficiario) : null);
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    setForm(beneficiario ? formInicialDe(beneficiario) : null);
  }, [beneficiario]);

  if (!beneficiario || !form) {
    return null;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form || !beneficiario) return;
    setSalvando(true);
    try {
      const tipoRelacaoFinal =
        form.responsavel_legal_tipo_relacao === "Outro"
          ? form.responsavel_legal_tipo_relacao_outro
          : form.responsavel_legal_tipo_relacao;
      await api.patch(`/beneficiarios/${beneficiario.id}`, {
        nome_completo: form.nome_completo,
        polo_id: form.polo_id,
        responsavel_legal_nome: form.responsavel_legal_nome || null,
        responsavel_legal_data_nascimento: form.responsavel_legal_data_nascimento || null,
        responsavel_legal_tipo_relacao: tipoRelacaoFinal || null,
        responsavel_legal_telefone_1: onlyDigits(form.responsavel_legal_telefone_1) || null,
        responsavel_legal_telefone_2: onlyDigits(form.responsavel_legal_telefone_2) || null,
        responsavel_legal_email: form.responsavel_legal_email || null,
        responsavel_legal_rede_social: form.responsavel_legal_rede_social || null,
        endereco: form.endereco || null,
        autoriza_whatsapp: form.autoriza_whatsapp,
        observacoes_medicas: form.observacoes_medicas || null,
      });
      onSalvo();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao salvar alterações.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Modal open={!!beneficiario} onClose={onClose} title={`Editar — ${beneficiario.nome_completo}`} maxWidth="max-w-2xl">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-2 gap-4 text-sm bg-gray-50 rounded-lg p-3">
          <div>
            <span className="block text-xs text-gray-400">CPF (não editável)</span>
            <span className="font-medium text-gray-700">{maskCPF(beneficiario.documento)}</span>
          </div>
          <div>
            <span className="block text-xs text-gray-400">Nascimento (não editável)</span>
            <span className="font-medium text-gray-700">{formatarData(beneficiario.data_nascimento)}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Nome completo"
            value={form.nome_completo}
            onChange={(e) => setForm({ ...form, nome_completo: e.target.value })}
            required
          />
          <Select label="Polo" value={form.polo_id} onChange={(e) => setForm({ ...form, polo_id: e.target.value })} required>
            {polos.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nome}
              </option>
            ))}
          </Select>
        </div>
        <p className="text-xs text-gray-400 -mt-3">
          Modalidades e turmas são gerenciadas em "Matrículas", na listagem de beneficiários.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Nome do responsável"
            value={form.responsavel_legal_nome}
            onChange={(e) => setForm({ ...form, responsavel_legal_nome: e.target.value })}
          />
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
            value={form.responsavel_legal_email}
            onChange={(e) => setForm({ ...form, responsavel_legal_email: e.target.value })}
          />
          <Input
            label="Rede social"
            value={form.responsavel_legal_rede_social}
            onChange={(e) => setForm({ ...form, responsavel_legal_rede_social: e.target.value })}
          />
          <div className="sm:col-span-2">
            <Input label="Endereço" value={form.endereco} onChange={(e) => setForm({ ...form, endereco: e.target.value })} />
          </div>
          <div className="sm:col-span-2">
            <label className="flex items-center gap-2 cursor-pointer select-none">
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

        <Input
          label="Observações médicas"
          value={form.observacoes_medicas}
          onChange={(e) => setForm({ ...form, observacoes_medicas: e.target.value })}
        />

        <div className="flex gap-3">
          <Button type="submit" disabled={salvando}>
            {salvando ? "Salvando…" : "Salvar alterações"}
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
        </div>
      </form>
    </Modal>
  );
}
