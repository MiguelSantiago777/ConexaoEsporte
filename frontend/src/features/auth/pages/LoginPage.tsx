import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { AlertCircleIcon } from "@/components/ui/icons";

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
      <div className="hidden lg:flex lg:w-[46%] relative overflow-hidden bg-brand-dark">
        <div
          className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-brand opacity-60 blur-3xl"
          aria-hidden
        />
        <div
          className="absolute bottom-0 right-0 w-[28rem] h-[28rem] rounded-full bg-accent/30 blur-3xl translate-x-1/3 translate-y-1/4"
          aria-hidden
        />
        <div className="relative z-10 flex flex-col justify-between p-12 text-white w-full">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="Conexão Esporte" className="w-11 h-11 object-contain" />
            <span className="text-xl font-bold tracking-tight">Conexão Esporte</span>
          </div>
          <div className="max-w-sm">
            <h1 className="text-3xl font-bold leading-tight">
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
