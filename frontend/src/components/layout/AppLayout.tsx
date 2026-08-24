import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/AuthContext";
import type { Perfil } from "@/types";

interface ItemMenu {
  label: string;
  to: string;
  perfis: Perfil[];
}

const MENU: ItemMenu[] = [
  { label: "Dashboard", to: "/", perfis: ["MASTER", "GESTOR_POLO", "PROFESSOR"] },
  { label: "Polos", to: "/polos", perfis: ["MASTER"] },
  { label: "Modalidades", to: "/modalidades", perfis: ["MASTER", "GESTOR_POLO"] },
  { label: "Turmas", to: "/turmas", perfis: ["MASTER", "GESTOR_POLO"] },
  { label: "Beneficiários", to: "/beneficiarios", perfis: ["MASTER", "GESTOR_POLO"] },
  { label: "Frequência", to: "/frequencia", perfis: ["PROFESSOR"] },
  { label: "Relatórios de Aula", to: "/relatorios", perfis: ["PROFESSOR"] },
];

export function AppLayout() {
  const { usuario, sair } = useAuth();
  const navigate = useNavigate();

  const itensVisiveis = MENU.filter((i) => usuario && i.perfis.includes(usuario.perfil));

  function handleSair() {
    sair();
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-brand-dark text-white flex flex-col">
        <div className="p-5 text-xl font-bold border-b border-white/10">Conexão Esporte</div>
        <nav className="flex-1 p-3 space-y-1">
          {itensVisiveis.map((i) => (
            <NavLink
              key={i.to}
              to={i.to}
              end={i.to === "/"}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-md text-sm ${
                  isActive ? "bg-white/20 font-semibold" : "hover:bg-white/10"
                }`
              }
            >
              {i.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-white/10 text-sm">
          <div className="font-medium">{usuario?.nome}</div>
          <div className="text-white/60 text-xs mb-2">{usuario?.perfil}</div>
          <button onClick={handleSair} className="text-white/80 hover:text-white underline text-xs">
            Sair
          </button>
        </div>
      </aside>
      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
