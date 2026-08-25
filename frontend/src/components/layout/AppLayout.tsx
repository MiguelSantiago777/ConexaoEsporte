import { ComponentType } from "react";
import { Outlet, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/AuthContext";
import type { Perfil } from "@/types";
import {
  AcademicCapIcon,
  BuildingIcon,
  CalendarCheckIcon,
  ClipboardIcon,
  DocumentTextIcon,
  HomeIcon,
  KeyIcon,
  LogoutIcon,
  TrophyIcon,
  UsersIcon,
} from "@/components/ui/icons";

interface ItemMenu {
  label: string;
  to: string;
  perfis: Perfil[];
  icon: ComponentType<{ className?: string }>;
}

const MENU: ItemMenu[] = [
  { label: "Dashboard", to: "/", perfis: ["MASTER", "GESTOR_POLO", "PROFESSOR"], icon: HomeIcon },
  { label: "Polos", to: "/polos", perfis: ["MASTER"], icon: BuildingIcon },
  { label: "Modalidades", to: "/modalidades", perfis: ["MASTER", "GESTOR_POLO"], icon: TrophyIcon },
  { label: "Turmas", to: "/turmas", perfis: ["MASTER", "GESTOR_POLO"], icon: UsersIcon },
  { label: "Beneficiários", to: "/beneficiarios", perfis: ["MASTER", "GESTOR_POLO"], icon: ClipboardIcon },
  { label: "Professores", to: "/professores", perfis: ["MASTER", "GESTOR_POLO"], icon: AcademicCapIcon },
  { label: "Frequência", to: "/frequencia", perfis: ["PROFESSOR"], icon: CalendarCheckIcon },
  { label: "Relatórios de Aula", to: "/relatorios", perfis: ["PROFESSOR"], icon: DocumentTextIcon },
];

const PERFIL_LABEL: Record<Perfil, string> = {
  MASTER: "Master",
  GESTOR_POLO: "Gestor de polo",
  PROFESSOR: "Professor",
};

function iniciais(nome?: string) {
  if (!nome) return "?";
  const partes = nome.trim().split(/\s+/);
  return ((partes[0]?.[0] ?? "") + (partes[partes.length - 1]?.[0] ?? "")).toUpperCase();
}

export function AppLayout() {
  const { usuario, sair } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const itensVisiveis = MENU.filter((i) => usuario && i.perfis.includes(usuario.perfil));

  function handleSair() {
    sair();
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex print:block">
      <aside className="w-64 bg-brand-dark text-white flex flex-col shrink-0 print:hidden">
        <div className="p-5 flex items-center gap-3 border-b border-white/10">
          <img src="/logo.png" alt="Conexão Esporte" className="w-10 h-10 object-contain shrink-0" />
          <span className="text-lg font-bold tracking-tight leading-tight">Conexão Esporte</span>
        </div>
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          {itensVisiveis.map((i) => {
            const Icon = i.icon;
            return (
              <NavLink
                key={i.to}
                to={i.to}
                end={i.to === "/"}
                className={({ isActive }) =>
                  `group flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all duration-150 ${
                    isActive
                      ? "bg-white text-brand-dark font-semibold shadow-sm"
                      : "text-white/75 hover:bg-white/10 hover:text-white"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      className={`w-[18px] h-[18px] shrink-0 transition-colors ${
                        isActive ? "text-accent-dark" : "text-white/60 group-hover:text-white"
                      }`}
                    />
                    <span className="truncate">{i.label}</span>
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>
        <div className="p-4 border-t border-white/10 flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-accent text-brand-dark flex items-center justify-center text-sm font-bold shrink-0">
            {iniciais(usuario?.nome)}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-medium truncate">{usuario?.nome}</div>
            <div className="text-white/60 text-xs">{usuario && PERFIL_LABEL[usuario.perfil]}</div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <NavLink
              to="/alterar-senha"
              title="Alterar senha"
              className="w-8 h-8 flex items-center justify-center rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            >
              <KeyIcon className="w-4 h-4" />
            </NavLink>
            <button
              onClick={handleSair}
              title="Sair"
              className="w-8 h-8 flex items-center justify-center rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            >
              <LogoutIcon />
            </button>
          </div>
        </div>
      </aside>
      <main className="flex-1 overflow-auto print:overflow-visible">
        {/* key={pathname} força o React a remontar este container a cada troca
            de rota, o que reinicia a animação de entrada (senão ela só tocaria
            uma vez, no primeiro carregamento). */}
        <div key={location.pathname} className="max-w-6xl mx-auto p-8 print:p-0 print:max-w-none animate-page-in">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
