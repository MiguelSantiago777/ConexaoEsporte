import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { AlertCircleIcon } from "@/components/ui/icons";

/** Brasão do Conexão Esporte redesenhado só com linhas brancas (sem cor de
 * preenchimento — ver frontend/public/brasao-linhas.png) com uma luz
 * dourada varrendo diagonalmente por cima, recortada exatamente no
 * contorno do brasão via mask-image (o PNG tem fundo transparente e só as
 * linhas do desenho como pixels opacos, então a luz só aparece em cima do
 * traço, nunca no vazio ao redor). */
function BrasaoDeLinhas({ className = "" }: { className?: string }) {
  const mascara = {
    WebkitMaskImage: "url(/brasao-linhas.png)",
    maskImage: "url(/brasao-linhas.png)",
    WebkitMaskSize: "contain",
    maskSize: "contain",
    WebkitMaskRepeat: "no-repeat",
    maskRepeat: "no-repeat",
    WebkitMaskPosition: "center",
    maskPosition: "center",
  };

  return (
    <div className={className} aria-hidden="true">
      <img src="/brasao-linhas.png" alt="" className="absolute inset-0 w-full h-full object-contain opacity-30" />
      <div className="absolute inset-0 w-full h-full animate-luz-varrendo" style={mascara} />
    </div>
  );
}

export function LoginPage() {
  const { entrar } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setCarregando(true);
    try {
      await entrar(email, senha);
      navigate("/");
    } catch (err: any) {
      if (err?.response?.status === 429) {
        setErro("Muitas tentativas seguidas. Aguarde cerca de 1 minuto e tente de novo.");
      } else if (err?.response?.status === 401) {
        setErro("Email ou senha inválidos.");
      } else {
        setErro("Não foi possível conectar ao servidor. Tente novamente em instantes.");
      }
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="min-h-screen flex bg-white">
      {/* Painel de marca — só em telas maiores */}
      <div className="hidden lg:flex lg:w-[46%] relative overflow-hidden bg-brand-dark bg-[radial-gradient(circle_at_20%_0%,rgba(255,255,255,0.08),transparent_45%)]">
        <BrasaoDeLinhas className="absolute inset-0 w-full h-full" />
        <div className="relative z-10 flex flex-col justify-between p-12 text-white w-full">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="Conexão Esporte" className="w-11 h-11 object-contain" />
            <span className="font-display text-xl font-semibold tracking-tight">Conexão Esporte</span>
          </div>
          <div className="max-w-sm">
            <h1 className="font-display text-4xl font-semibold leading-[1.15]">
              Gestão de projetos esportivos, do polo à quadra.
            </h1>
            <p className="mt-4 text-white/70 text-sm leading-relaxed">
              Cadastre polos, modalidades, turmas e beneficiários, acompanhe a frequência e emita
              relatórios de aula — tudo em um só lugar.
            </p>
          </div>
          <p className="text-white/40 text-xs">© {new Date().getFullYear()} Conexão Esporte</p>
        </div>
      </div>

      {/* Formulário */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-10 bg-brand-light lg:bg-white">
        <form onSubmit={handleSubmit} className="w-full max-w-sm animate-fade-in">
          <div className="lg:hidden flex flex-col items-center text-center mb-8">
            <img src="/logo.png" alt="Conexão Esporte" className="w-16 h-16 object-contain mb-2" />
            <h1 className="text-xl font-bold text-brand-dark">Conexão Esporte</h1>
          </div>

          <h2 className="hidden lg:block text-2xl font-bold text-brand-dark">Bem-vindo de volta</h2>
          <p className="hidden lg:block text-sm text-gray-500 mt-1 mb-8">
            Entre com suas credenciais para acessar o sistema.
          </p>

          {erro && (
            <div className="flex items-center gap-2 bg-red-50 text-red-700 text-sm p-3 rounded-lg mb-5 animate-fade-in">
              <AlertCircleIcon className="w-4 h-4 shrink-0" />
              {erro}
            </div>
          )}

          <div className="space-y-4">
            <Input label="Email" type="email" autoComplete="username" value={email}
              onChange={(e) => setEmail(e.target.value)} required />
            <Input label="Senha" type="password" autoComplete="current-password" value={senha}
              onChange={(e) => setSenha(e.target.value)} required />
          </div>

          <Button type="submit" className="w-full mt-6" disabled={carregando}>
            {carregando ? "Entrando…" : "Entrar"}
          </Button>
        </form>
      </div>
    </div>
  );
}
