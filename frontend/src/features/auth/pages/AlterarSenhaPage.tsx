import { FormEvent, useState } from "react";
import { alterarSenha } from "../authService";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { KeyIcon } from "@/components/ui/icons";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";

export function AlterarSenhaPage() {
  const toast = useToast();
  const [senhaAtual, setSenhaAtual] = useState("");
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmarSenha, setConfirmarSenha] = useState("");
  const [salvando, setSalvando] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    if (novaSenha !== confirmarSenha) {
      toast.error("A confirmação não confere com a nova senha.");
      return;
    }
    if (novaSenha.length < 8) {
      toast.error("A nova senha deve ter pelo menos 8 caracteres.");
      return;
    }

    setSalvando(true);
    try {
      await alterarSenha(senhaAtual, novaSenha);
      setSenhaAtual("");
      setNovaSenha("");
      setConfirmarSenha("");
      toast.success("Senha alterada com sucesso.");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao alterar a senha.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Alterar senha" subtitle="Troque a senha usada para acessar o sistema." />
      <Card className="max-w-md animate-fade-in-up" style={staggerStyle(0)}>
        <div className="flex items-center gap-2 mb-5 text-brand">
          <div className="w-9 h-9 rounded-lg bg-brand-light flex items-center justify-center shrink-0">
            <KeyIcon className="w-5 h-5" />
          </div>
          <p className="text-sm text-gray-500">Sua senha atual é necessária para confirmar a troca.</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Senha atual"
            type="password"
            autoComplete="current-password"
            value={senhaAtual}
            onChange={(e) => setSenhaAtual(e.target.value)}
            required
          />
          <Input
            label="Nova senha"
            type="password"
            autoComplete="new-password"
            minLength={8}
            hint="Mínimo de 8 caracteres."
            value={novaSenha}
            onChange={(e) => setNovaSenha(e.target.value)}
            required
          />
          <Input
            label="Confirmar nova senha"
            type="password"
            autoComplete="new-password"
            minLength={8}
            value={confirmarSenha}
            onChange={(e) => setConfirmarSenha(e.target.value)}
            required
          />
          <Button type="submit" disabled={salvando}>
            {salvando ? "Salvando…" : "Alterar senha"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
