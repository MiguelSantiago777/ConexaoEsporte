import { ComponentType, useEffect, useState } from "react";
import { Outlet, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/AuthContext";
import type { Perfil } from "@/types";
import {
  AcademicCapIcon,
  ArchiveIcon,
  BoxIcon,
  BuildingIcon,
  CalendarCheckIcon,
  ChartPieIcon,
  ClipboardIcon,
  CloseIcon,
  DocumentTextIcon,
  HomeIcon,
  KeyIcon,
  LogoutIcon,
  MenuIcon,
  PaperclipIcon,
  SettingsIcon,
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
  { label: "Fichas de Execução", to: "/fichas-execucao", perfis: ["MASTER"], icon: ArchiveIcon },
  { label: "Modalidades", to: "/modalidades", perfis: ["MASTER", "GESTOR_POLO"], icon: TrophyIcon },
  { label: "Turmas", to: "/turmas", perfis: ["MASTER", "GESTOR_POLO"], icon: UsersIcon },
  { label: "Beneficiários", to: "/beneficiarios", perfis: ["MASTER", "GESTOR_POLO"], icon: ClipboardIcon },
  { label: "Professores", to: "/professores", perfis: ["MASTER", "GESTOR_POLO"], icon: AcademicCapIcon },
  { label: "Entregas de Materiais", to: "/entregas-materiais", perfis: ["MASTER", "GESTOR_POLO"], icon: BoxIcon },
  { label: "Relatórios", to: "/relatorios-gerenciais", perfis: ["MASTER", "GESTOR_POLO"], icon: ChartPieIcon },
  { label: "Anexos Gerais", to: "/anexos-gerais", perfis: ["MASTER", "GESTOR_POLO"], icon: PaperclipIcon },
  { label: "Configurações", to: "/configuracoes", perfis: ["MASTER"], icon: SettingsIcon },
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
  const [menuAberto, setMenuAberto] = useState(false);

  const itensVisiveis = MENU.filter((i) => usuario && i.perfis.includes(usuario.perfil));

  function handleSair() {
    sair();
    navigate("/login");
  }

  // Fecha o menu mobile (off-canvas) automaticamente ao trocar de rota —
  // senão ele ficaria aberto por cima da tela seguinte.
  useEffect(() => {
    setMenuAberto(false);
  }, [location.pathname]);

  // Trava o scroll do body enquanto o menu mobile está aberto — sem isso, a
  // página por trás do menu ainda rola durante o arrasto (o corpo não tem
  // altura travada em 100vh, só min-height), e junto com o recolhimento da
  // barra de endereço do navegador no celular isso faz o menu (position:
  // fixed) parecer "descolar" da tela em vez de ficar parado por cima.
  // Restaura a posição de rolagem exata ao fechar.
  useEffect(() => {
    if (!menuAberto) return;
    const scrollY = window.scrollY;
    const { style } = document.body;
    const original = { overflow: style.overflow, position: style.position, top: style.top, width: style.width };
    style.overflow = "hidden";
    style.position = "fixed";
    style.top = `-${scrollY}px`;
    style.width = "100%";
    return () => {
      style.overflow = original.overflow;
      style.position = original.position;
      style.top = original.top;
      style.width = original.width;
      window.scrollTo(0, scrollY);
    };
  }, [menuAberto]);

  return (
    <div className="min-h-screen lg:flex print:block">
      {menuAberto && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-[1px] lg:hidden print:hidden"
          onClick={() => setMenuAberto(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-brand-dark bg-[radial-gradient(circle_at_18%_0%,rgba(255,255,255,0.07),transparent_45%)] text-white flex flex-col shrink-0 print:hidden transition-transform duration-200 ease-out lg:static lg:translate-x-0 ${
          menuAberto ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="p-5 flex items-center gap-3 border-b border-white/10">
          <img src="/logo.png" alt="Conexão Esporte" className="w-10 h-10 object-contain shrink-0" />
          <span className="font-display text-lg font-semibold tracking-tight leading-tight flex-1">Conexão Esporte</span>
          <button
            type="button"
            onClick={() => setMenuAberto(false)}
            aria-label="Fechar menu"
            className="lg:hidden w-8 h-8 flex items-center justify-center rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors shrink-0"
          >
            <CloseIcon />
          </button>
        </div>
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto overscroll-contain">
          {itensVisiveis.map((i) => {
            const Icon = i.icon;
            return (
              <NavLink
                key={i.to}
                to={i.to}
                end={i.to === "/"}
                className={({ isActive }) =>
                  `group flex items-center gap-2.5 pl-[10px] pr-3 py-2.5 lg:py-2 rounded-r-lg border-l-2 text-sm transition-all duration-150 ${
                    isActive
                      ? "border-accent bg-white/[0.08] text-white font-semibold"
                      : "border-transparent text-white/75 hover:bg-white/10 hover:text-white"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      className={`w-[18px] h-[18px] shrink-0 transition-colors ${
                        isActive ? "text-accent" : "text-white/60 group-hover:text-white"
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

      <div className="flex-1 flex flex-col min-w-0">
        <header className="lg:hidden sticky top-0 z-30 flex items-center gap-3 px-4 py-3 bg-brand-dark text-white print:hidden">
          <button
            type="button"
            onClick={() => setMenuAberto(true)}
            aria-label="Abrir menu"
            className="w-9 h-9 -ml-1.5 flex items-center justify-center rounded-lg text-white/85 hover:text-white hover:bg-white/10 transition-colors shrink-0"
          >
            <MenuIcon className="w-5 h-5" />
          </button>
          <img src="/logo.png" alt="Conexão Esporte" className="w-7 h-7 object-contain shrink-0" />
          <span className="font-display text-base font-semibold tracking-tight truncate">Conexão Esporte</span>
        </header>

        <main className="flex-1 overflow-auto print:overflow-visible">
          {/* key={pathname} força o React a remontar este container a cada troca
              de rota, o que reinicia a animação de entrada (senão ela só tocaria
              uma vez, no primeiro carregamento). */}
          <div key={location.pathname} className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 print:p-10 print:max-w-none animate-page-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
