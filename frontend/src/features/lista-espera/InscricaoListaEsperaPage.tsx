import { FormEvent, ReactNode, useState } from "react";
import axios from "axios";
import { useQuery } from "@tanstack/react-query";
import { buscarOpcoesPublicas, inscreverNaListaEspera } from "./listaEsperaService";
import { CANAIS_COMO_CONHECEU } from "./constants";
import { TAMANHOS_CALCADO, TAMANHOS_CAMISA } from "@/features/beneficiarios/constants";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Spinner } from "@/components/ui/Spinner";
import { AlertCircleIcon, CheckCircleIcon } from "@/components/ui/icons";
import { maskCPF, maskTelefone } from "@/lib/masks";

const IDADE_MINIMA_PROJETO = 6;
const IDADE_MAXIMA_PROJETO = 17;

const FORM_INICIAL = {
  nome_completo: "", data_nascimento: "", documento: "", nome_responsavel: "", documento_responsavel: "",
  telefone_whatsapp: "", email: "", bairro: "", cidade: "", modalidade_id: "", polo_id: "",
  como_conheceu: "", como_conheceu_outro: "", tamanho_camisa: "", tamanho_calcado: "",
};

/** Fundo navy com o brasão de linhas brancas ao fundo — mesmo painel de
 * marca do login, sem a luz dourada varrendo (reservada à primeira tela
 * que qualquer usuário vê, ver DESIGN.md, seção Motion). Envolve a página
 * inteira, com o card branco flutuando por cima. */
function FundoNavyComBrasao({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen p-6 relative overflow-hidden bg-brand-dark bg-[radial-gradient(circle_at_20%_0%,rgba(255,255,255,0.08),transparent_45%)] flex items-start justify-center">
      <img
        src="/brasao-linhas.png" alt="" aria-hidden="true"
        className="absolute inset-0 w-full h-full object-contain opacity-[0.06] scale-150 pointer-events-none select-none"
      />
      <div className="relative z-10 w-full max-w-2xl mt-10">{children}</div>
    </div>
  );
}

function calcularIdade(dataNascimento: string): number | null {
  if (!dataNascimento) return null;
  const nascimento = new Date(dataNascimento + "T00:00:00");
  if (Number.isNaN(nascimento.getTime())) return null;
  const hoje = new Date();
  let anos = hoje.getFullYear() - nascimento.getFullYear();
  const aindaNaoFezAniversario =
    hoje.getMonth() < nascimento.getMonth() ||
    (hoje.getMonth() === nascimento.getMonth() && hoje.getDate() < nascimento.getDate());
  if (aindaNaoFezAniversario) anos -= 1;
  return anos;
}

function formatarISO(data: Date): string {
  return data.toISOString().slice(0, 10);
}

/** Limites do campo de data de nascimento: a pessoa mais nova permitida
 * acabou de completar a idade mínima hoje; a mais velha ainda não completou
 * a idade máxima + 1. */
function limitesDataNascimento(hoje: Date) {
  const dataMaisRecentePermitida = new Date(hoje.getFullYear() - IDADE_MINIMA_PROJETO, hoje.getMonth(), hoje.getDate());
  const dataMaisAntigaPermitida = new Date(
    hoje.getFullYear() - IDADE_MAXIMA_PROJETO - 1, hoje.getMonth(), hoje.getDate() + 1,
  );
  return { min: formatarISO(dataMaisAntigaPermitida), max: formatarISO(dataMaisRecentePermitida) };
}

export function InscricaoListaEsperaPage() {
  const [form, setForm] = useState(FORM_INICIAL);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [enviado, setEnviado] = useState(false);

  const { data: opcoes, isLoading: carregandoOpcoes } = useQuery({
    queryKey: ["lista-espera-opcoes"],
    queryFn: buscarOpcoesPublicas,
  });

  const idade = calcularIdade(form.data_nascimento);
  const eMenorDeIdade = idade !== null && idade < 18;
  const { min: dataMinima, max: dataMaxima } = limitesDataNascimento(new Date());

  function campo<K extends keyof typeof FORM_INICIAL>(chave: K) {
    return (valor: string) => setForm((f) => ({ ...f, [chave]: valor }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);

    if (idade !== null && (idade < IDADE_MINIMA_PROJETO || idade > IDADE_MAXIMA_PROJETO)) {
      setErro(`O projeto atende participantes de ${IDADE_MINIMA_PROJETO} a ${IDADE_MAXIMA_PROJETO} anos.`);
      return;
    }

    if (eMenorDeIdade && (!form.nome_responsavel.trim() || !form.documento_responsavel.trim())) {
      setErro("Como o participante é menor de idade, o nome e o CPF do responsável são obrigatórios.");
      return;
    }

    setEnviando(true);
    try {
      await inscreverNaListaEspera({
        nome_completo: form.nome_completo,
        data_nascimento: form.data_nascimento,
        documento: form.documento,
        nome_responsavel: eMenorDeIdade ? form.nome_responsavel : null,
        documento_responsavel: eMenorDeIdade ? form.documento_responsavel : null,
        telefone_whatsapp: form.telefone_whatsapp,
        email: form.email,
        bairro: form.bairro || null,
        cidade: form.cidade || null,
        modalidade_id: form.modalidade_id,
        polo_id: form.polo_id,
        como_conheceu: form.como_conheceu === "Outro" ? form.como_conheceu_outro || null : form.como_conheceu || null,
        tamanho_camisa: form.tamanho_camisa || null,
        tamanho_calcado: form.tamanho_calcado || null,
      });
      setEnviado(true);
    } catch (err: unknown) {
      const status = axios.isAxiosError(err) ? err.response?.status : undefined;
      if (status === 429) {
        setErro("Muitas tentativas seguidas. Aguarde cerca de 1 minuto e tente de novo.");
      } else if (status === 400) {
        setErro("Não foi possível enviar a inscrição. Confira os dados e tente novamente.");
      } else {
        setErro("Não foi possível conectar ao servidor. Tente novamente em instantes.");
      }
    } finally {
      setEnviando(false);
    }
  }

  if (enviado) {
    return (
      <FundoNavyComBrasao>
        <div className="flex flex-col items-center text-center mb-6">
          <img src="/logo.png" alt="Conexão Esporte" className="w-20 h-20 object-contain mb-2" />
          <h1 className="font-display text-2xl font-bold text-white">Lista de espera</h1>
        </div>
        <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm text-center space-y-4 animate-fade-in">
          <div className="w-12 h-12 rounded-full bg-court/10 text-court flex items-center justify-center mx-auto">
            <CheckCircleIcon className="w-6 h-6" />
          </div>
          <h2 className="font-display text-xl font-bold text-brand-dark">Inscrição recebida!</h2>
          <p className="text-sm text-ink">
            Enviamos um email de confirmação para <strong>{form.email}</strong>. A equipe do polo vai analisar a
            disponibilidade de vagas e entrar em contato em breve.
          </p>
        </div>
      </FundoNavyComBrasao>
    );
  }

  return (
    <FundoNavyComBrasao>
      <div className="flex flex-col items-center text-center mb-6">
        <img src="/logo.png" alt="Conexão Esporte" className="w-20 h-20 object-contain mb-2" />
        <h1 className="font-display text-2xl font-bold text-white">Lista de espera</h1>
        <p className="text-sm text-white/70 mt-1">
          Preencha os dados abaixo pra entrar na lista de espera de uma modalidade no Conexão Esporte.
        </p>
      </div>

      <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm">
        {erro && (
          <div className="flex items-center gap-2 bg-red-50 text-danger text-sm p-3 rounded-lg mb-5 animate-fade-in">
            <AlertCircleIcon className="w-4 h-4 shrink-0" />
            {erro}
          </div>
        )}

        {carregandoOpcoes ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Nome completo do participante" value={form.nome_completo}
              onChange={(e) => campo("nome_completo")(e.target.value)} required
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input
                label="Data de nascimento" type="date" value={form.data_nascimento} min={dataMinima} max={dataMaxima}
                hint={`Atendemos de ${IDADE_MINIMA_PROJETO} a ${IDADE_MAXIMA_PROJETO} anos.`}
                onChange={(e) => campo("data_nascimento")(e.target.value)} required
              />
              <Input
                label="CPF" value={form.documento} inputMode="numeric"
                onChange={(e) => campo("documento")(maskCPF(e.target.value))} required
              />
            </div>
            {eMenorDeIdade && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 animate-fade-in">
                <Input
                  label="Nome do responsável" value={form.nome_responsavel}
                  onChange={(e) => campo("nome_responsavel")(e.target.value)} required
                />
                <Input
                  label="CPF do responsável" value={form.documento_responsavel} inputMode="numeric"
                  onChange={(e) => campo("documento_responsavel")(maskCPF(e.target.value))} required
                />
              </div>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input
                label="WhatsApp" value={form.telefone_whatsapp} inputMode="tel"
                onChange={(e) => campo("telefone_whatsapp")(maskTelefone(e.target.value))} required
              />
              <Input
                label="Email" type="email" value={form.email}
                onChange={(e) => campo("email")(e.target.value)} required
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input
                label="Bairro" value={form.bairro} onChange={(e) => campo("bairro")(e.target.value)}
              />
              <Input
                label="Cidade" value={form.cidade} onChange={(e) => campo("cidade")(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Select
                label="Modalidade de interesse" value={form.modalidade_id}
                onChange={(e) => campo("modalidade_id")(e.target.value)} required
              >
                <option value="">Selecione</option>
                {opcoes?.modalidades.map((m) => (
                  <option key={m.id} value={m.id}>{m.nome}</option>
                ))}
              </Select>
              <Select
                label="Polo de interesse" value={form.polo_id}
                onChange={(e) => campo("polo_id")(e.target.value)} required
              >
                <option value="">Selecione</option>
                {opcoes?.polos.map((p) => (
                  <option key={p.id} value={p.id}>{p.nome}</option>
                ))}
              </Select>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Select
                label="Tamanho da camisa" value={form.tamanho_camisa}
                onChange={(e) => campo("tamanho_camisa")(e.target.value)} required
              >
                <option value="">Selecione</option>
                {TAMANHOS_CAMISA.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </Select>
              <Select
                label="Tamanho do calçado" value={form.tamanho_calcado}
                onChange={(e) => campo("tamanho_calcado")(e.target.value)} required
              >
                <option value="">Selecione</option>
                {TAMANHOS_CALCADO.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </Select>
            </div>
            <Select
              label="Como conheceu o projeto?" value={form.como_conheceu}
              onChange={(e) => campo("como_conheceu")(e.target.value)}
            >
              <option value="">Selecione</option>
              {CANAIS_COMO_CONHECEU.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </Select>
            {form.como_conheceu === "Outro" && (
              <Input
                label="Qual?" value={form.como_conheceu_outro}
                onChange={(e) => campo("como_conheceu_outro")(e.target.value)}
              />
            )}

            <Button type="submit" className="w-full" disabled={enviando}>
              {enviando ? "Enviando…" : "Enviar inscrição"}
            </Button>
          </form>
        )}
      </div>
    </FundoNavyComBrasao>
  );
}
