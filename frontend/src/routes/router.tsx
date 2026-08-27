import { createBrowserRouter } from "react-router-dom";
import { ProtectedRoute } from "./ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { DashboardPage } from "@/features/auth/pages/DashboardPage";
import { AlterarSenhaPage } from "@/features/auth/pages/AlterarSenhaPage";
import { PolosPage } from "@/features/polos/PolosPage";
import { ModalidadesPage } from "@/features/modalidades/ModalidadesPage";
import { TurmasPage } from "@/features/turmas/TurmasPage";
import { BeneficiariosPage } from "@/features/beneficiarios/BeneficiariosPage";
import { ProfessoresPage } from "@/features/professores/ProfessoresPage";
import { AutorizacaoImagemPage } from "@/features/beneficiarios/AutorizacaoImagemPage";
import { FrequenciaPage } from "@/features/frequencia/FrequenciaPage";
import { RelatoriosPage } from "@/features/relatorios/RelatoriosPage";
import { FichasExecucaoPage } from "@/features/fichas-execucao/FichasExecucaoPage";
import { FichaExecucaoDetalhePage } from "@/features/fichas-execucao/FichaExecucaoDetalhePage";
import { EntregasMateriaisPage } from "@/features/entregas-materiais/EntregasMateriaisPage";
import { RelatoriosGerenciaisPage } from "@/features/relatorios-gerenciais/RelatoriosGerenciaisPage";

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
          { path: "/alterar-senha", element: <AlterarSenhaPage /> },
          // MASTER: polos
          {
            element: <ProtectedRoute perfisPermitidos={["MASTER"]} />,
            children: [
              { path: "/polos", element: <PolosPage /> },
              { path: "/fichas-execucao", element: <FichasExecucaoPage /> },
              { path: "/fichas-execucao/:id", element: <FichaExecucaoDetalhePage /> },
            ],
          },
          // MASTER + GESTOR_POLO
          {
            element: <ProtectedRoute perfisPermitidos={["MASTER", "GESTOR_POLO"]} />,
            children: [
              { path: "/modalidades", element: <ModalidadesPage /> },
              { path: "/turmas", element: <TurmasPage /> },
              { path: "/beneficiarios", element: <BeneficiariosPage /> },
              { path: "/beneficiarios/:id/autorizacao-imagem", element: <AutorizacaoImagemPage /> },
              { path: "/professores", element: <ProfessoresPage /> },
              { path: "/entregas-materiais", element: <EntregasMateriaisPage /> },
              { path: "/relatorios-gerenciais", element: <RelatoriosGerenciaisPage /> },
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
