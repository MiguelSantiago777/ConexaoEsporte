import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import type { Perfil, UsuarioLogado } from "@/types";
import { fetchMe, login as loginService, logout as logoutService } from "./authService";
import { tokenStorage } from "@/lib/api";

interface AuthContextValue {
  usuario: UsuarioLogado | null;
  carregando: boolean;
  entrar: (email: string, senha: string) => Promise<void>;
  sair: () => void;
  temPerfil: (...perfis: Perfil[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<UsuarioLogado | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    async function init() {
      if (tokenStorage.getAccess()) {
        try {
          setUsuario(await fetchMe());
        } catch {
          tokenStorage.clear();
        }
      }
      setCarregando(false);
    }
    init();
  }, []);

  async function entrar(email: string, senha: string) {
    const u = await loginService(email, senha);
    setUsuario(u);
  }

  function sair() {
    logoutService();
    setUsuario(null);
  }

  function temPerfil(...perfis: Perfil[]) {
    return !!usuario && perfis.includes(usuario.perfil);
  }

  return (
    <AuthContext.Provider value={{ usuario, carregando, entrar, sair, temPerfil }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de <AuthProvider>");
  return ctx;
}
