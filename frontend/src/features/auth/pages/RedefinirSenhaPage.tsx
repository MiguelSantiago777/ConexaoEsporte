import { FormEvent, useState } from "react";
import axios from "axios";
import { Link, useSearchParams } from "react-router-dom";
import { redefinirSenha } from "../authService";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { AlertCircleIcon, CheckCircleIcon } from "@/components/ui/icons";

export function RedefinirSenhaPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const [novaSenha, setNovaSenha] = useState("");
  const [confirmarSenha, setConfirmarSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);
  const [redefinida, setRedefinida] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);

    if (novaSenha !== confirmarSenha) {
      setErro("A confirmação não confere com a nova senha.");
      return;
    }
    if (novaSenha.length < 8) {
      setErro("A nova senha deve ter pelo menos 8 caracteres.");
      return;
    }

    setSalvando(true);
    try {
      await redefinirSenha(token!, novaSenha);
      setRedefinida(true);
    } catch (err: unknown) {
      const status = axios.isAxiosError(err) ? err.response?.status : undefined;
      if (status === 400) {
        setErro("Este link é inválido ou já expirou. Solicite um novo.");
      } else if (status === 429) {
        setErro("Muitas tentativas seguidas. Aguarde cerca de 1 minuto e tente de novo.");
      } else {
        setErro("Não foi possível conectar ao servidor. Tente novamente em instantes.");
      }
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-brand-light">
      <div className="w-full max-w-sm animate-fade-in">
        <div className="flex flex-col items-center text-center mb-8">
          <img src="/logo.png" alt="Conexão Esporte" className="w-14 h-14 object-contain mb-2" />
          <h1 className="font-display text-2xl font-bold text-brand-dark">Redefinir senha</h1>
          <p className="text-sm text-slate-500 mt-1">Escolha uma nova senha para acessar o sistema.</p>
        </div>

        <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm">
          {!token ? (
            <div className="text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-red-50 text-danger flex items-center justify-center mx-auto">
                <AlertCircleIcon className="w-6 h-6" />
              </div>
              <p className="text-sm text-ink">
                Este link de redefinição está incompleto ou inválido.
              </p>
              <Link to="/esqueci-senha" className="inline-block text-sm text-brand hover:underline">
                Solicitar um novo link
              </Link>
            </div>
          ) : redefinida ? (
            <div className="text-center space-y-4 animate-fade-in">
              <div className="w-12 h-12 rounded-full bg-court/10 text-court flex items-center justify-center mx-auto">
                <CheckCircleIcon className="w-6 h-6" />
              </div>
              <p className="text-sm text-ink">Sua senha foi redefinida com sucesso.</p>
              <Link to="/login">
                <Button className="w-full">Ir para o login</Button>
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
              <Input
                label="Nova senha" type="password" autoComplete="new-password" minLength={8}
                hint="Mínimo de 8 caracteres." value={novaSenha}
                onChange={(e) => setNovaSenha(e.target.value)} required
              />
              <Input
                label="Confirmar nova senha" type="password" autoComplete="new-password" minLength={8}
                value={confirmarSenha} onChange={(e) => setConfirmarSenha(e.target.value)} required
              />
              <Button type="submit" className="w-full" disabled={salvando}>
                {salvando ? "Salvando…" : "Redefinir senha"}
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
