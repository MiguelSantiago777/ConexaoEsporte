import { createBrowserRouter } from "react-router-dom";
import { ProtectedRoute } from "./ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { DashboardPage } from "@/features/auth/pages/DashboardPage";
import { PolosPage } from "@/features/polos/PolosPage";
import { ModalidadesPage } from "@/features/modalidades/ModalidadesPage";
import { TurmasPage } from "@/features/turmas/TurmasPage";
import { BeneficiariosPage } from "@/features/beneficiarios/BeneficiariosPage";
import { FrequenciaPage } from "@/features/frequencia/FrequenciaPage";
import { RelatoriosPage } from "@/features/relatorios/RelatoriosPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/sem-acesso", element: <div className="p-8">Você não tem acesso a esta área.</div> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: "/", element: <DashboardPage /> },
          // MASTER: polos
          {
            element: <ProtectedRoute perfisPermitidos={["MASTER"]} />,
            children: [{ path: "/polos", element: <PolosPage /> }],
          },
          // MASTER + GESTOR_POLO
          {
            element: <ProtectedRoute perfisPermitidos={["MASTER", "GESTOR_POLO"]} />,
            children: [
              { path: "/modalidades", element: <ModalidadesPage /> },
              { path: "/turmas", element: <TurmasPage /> },
              { path: "/beneficiarios", element: <BeneficiariosPage /> },
            ],
          },
          // PROFESSOR
          {
            element: <ProtectedRoute perfisPermitidos={["PROFESSOR"]} />,
            children: [
              { path: "/frequencia", element: <FrequenciaPage /> },
              { path: "/relatorios", element: <RelatoriosPage /> },
            ],
          },
        ],
      },
    ],
  },
]);
