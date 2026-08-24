import { useAuth } from "../AuthContext";
import { Card } from "@/components/ui/Card";

export function DashboardPage() {
  const { usuario } = useAuth();

  const descricaoPorPerfil: Record<string, string> = {
    MASTER: "Você tem acesso total: polos, modalidades, turmas, beneficiários e usuários.",
    GESTOR_POLO: "Você gerencia modalidades, turmas, professores e beneficiários do seu polo.",
    PROFESSOR: "Você registra a frequência dos beneficiários e emite relatórios de aula das suas turmas.",
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Bem-vindo, {usuario?.nome}</h1>
        <p className="text-gray-500">{usuario && descricaoPorPerfil[usuario.perfil]}</p>
      </div>
      <Card title="Seu perfil">
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-gray-500">Perfil de acesso</dt>
            <dd className="font-medium">{usuario?.perfil}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Polo vinculado</dt>
            <dd className="font-medium">{usuario?.polo_id ?? "—"}</dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}
