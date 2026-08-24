import { api, tokenStorage } from "@/lib/api";
import type { TokenResponse, UsuarioLogado } from "@/types";

export async function login(email: string, senha: string): Promise<UsuarioLogado> {
  // O backend usa OAuth2PasswordRequestForm: campos 'username' e 'password'.
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", senha);

  const { data } = await api.post<TokenResponse>("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  tokenStorage.set(data.access_token, data.refresh_token);

  const me = await api.get<UsuarioLogado>("/auth/me");
  return me.data;
}

export function logout() {
  tokenStorage.clear();
}

export async function fetchMe(): Promise<UsuarioLogado> {
  const { data } = await api.get<UsuarioLogado>("/auth/me");
  return data;
}
