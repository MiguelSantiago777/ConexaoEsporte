/**
 * Extrai uma mensagem de erro segura (sempre string) de uma resposta de
 * erro da API. Quando o FastAPI rejeita a requisição por validação (422),
 * `detail` não vem como texto — vem como uma lista de objetos do Pydantic
 * ({type, loc, msg, input, ctx}). Passar esse objeto direto pro toast
 * derruba a tela inteira (React não sabe renderizar um objeto como filho,
 * e como o app não tem error boundary, o erro sobe até o topo e a tela
 * fica em branco). Esta função sempre devolve texto legível, nunca o
 * objeto cru.
 */
function ehRegistro(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === "object" && valor !== null;
}

export function mensagemErroApi(err: unknown, fallback: string): string {
  const response = ehRegistro(err) ? err.response : undefined;
  const data = ehRegistro(response) ? response.data : undefined;
  const detail = ehRegistro(data) ? data.detail : undefined;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    const mensagens = detail
      .map((item) => (typeof item === "string" ? item : typeof item?.msg === "string" ? item.msg : null))
      .filter((m): m is string => !!m);
    return mensagens.length > 0 ? mensagens.join("; ") : fallback;
  }

  if (ehRegistro(detail) && typeof detail.msg === "string") {
    return detail.msg;
  }

  return fallback;
}
