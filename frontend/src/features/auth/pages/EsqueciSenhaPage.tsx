import { FormEvent, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { solicitarRedefinicaoSenha } from "../authService";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { AlertCircleIcon, CheckCircleIcon } from "@/components/ui/icons";

export function EsqueciSenhaPage() {
  const [email, setEmail] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [enviado, setEnviado] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await solicitarRedefinicaoSenha(email);
      // O backend sempre responde 204, exista ou não o email cadastrado —
      // a tela mantém essa mesma ambiguidade de propósito, pra não revelar
      // quais emails têm conta no sistema.
      setEnviado(true);
    } catch (err: unknown) {
      const status = axios.isAxiosError(err) ? err.response?.status : undefined;
      setErro(
        status === 429
          ? "Muitas tentativas seguidas. Aguarde cerca de 1 minuto e tente de novo."
          : "Não foi possível conectar ao servidor. Tente novamente em instantes.",
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-brand-light">
      <div className="w-full max-w-sm animate-fade-in">
        <div className="flex flex-col items-center text-center mb-8">
          <img src="/logo.png" alt="Conexão Esporte" className="w-14 h-14 object-contain mb-2" />
          <h1 className="font-display text-2xl font-bold text-brand-dark">Esqueci minha senha</h1>
          <p className="text-sm text-slate-500 mt-1">
            Informe seu email de acesso e enviaremos um link para redefinir sua senha.
          </p>
        </div>

        <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm">
          {enviado ? (
            <div className="text-center space-y-4 animate-fade-in">
              <div className="w-12 h-12 rounded-full bg-court/10 text-court flex items-center justify-center mx-auto">
                <CheckCircleIcon className="w-6 h-6" />
              </div>
              <p className="text-sm text-ink">
                Se <strong>{email}</strong> estiver cadastrado no sistema, você vai receber um email com o
                link de redefinição em instantes. Confira também a caixa de spam.
              </p>
              <Link to="/login" className="inline-block text-sm text-brand hover:underline">
                Voltar para o login
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {erro && (
                <div className="flex items-center gap-2 bg-red-50 text-danger text-sm p-3 rounded-lg animate-fade-in">
                  <AlertCircleIcon className="w-4 h-4 shrink-0" />
                  {erro}
                </div>
              )}
              <Input label="Email" type="email" autoComplete="username" value={email}
                onChange={(e) => setEmail(e.target.value)} required />
              <Button type="submit" className="w-full" disabled={enviando}>
                {enviando ? "Enviando…" : "Enviar link de redefinição"}
              </Button>
              <Link to="/login" className="block text-center text-sm text-brand hover:underline">
                Voltar para o login
              </Link>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
