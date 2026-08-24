import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/features/auth/AuthContext";
import type { Perfil } from "@/types";

interface Props {
  perfisPermitidos?: Perfil[];
}

/**
 * Guarda de rota: exige autenticação e, opcionalmente, um dos perfis dados.
 * Espelha o RBAC do backend — mas a autorização real é sempre validada no servidor.
 */
export function ProtectedRoute({ perfisPermitidos }: Props) {
  const { usuario, carregando } = useAuth();

  if (carregando) {
    return <div className="p-8 text-center text-gray-500">Carregando…</div>;
  }
  if (!usuario) {
    return <Navigate to="/login" replace />;
  }
  if (perfisPermitidos && !perfisPermitidos.includes(usuario.perfil)) {
    return <Navigate to="/sem-acesso" replace />;
  }
  return <Outlet />;
}
