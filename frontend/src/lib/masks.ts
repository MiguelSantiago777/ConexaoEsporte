export function maskCPF(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  return digits
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
}

export function maskTelefone(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  if (digits.length <= 10) {
    return digits.replace(/(\d{2})(\d)/, "($1) $2").replace(/(\d{4})(\d{1,4})$/, "$1-$2");
  }
  return digits.replace(/(\d{2})(\d)/, "($1) $2").replace(/(\d{5})(\d{1,4})$/, "$1-$2");
}

export function maskCEP(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 8);
  return digits.replace(/(\d{5})(\d)/, "$1-$2");
}

export function onlyDigits(value: string): string {
  return value.replace(/\D/g, "");
}

// Mascaramento LGPD para uso em relatórios de uso externo — mantém só o
// primeiro e o último nome, escondendo os do meio.
export function mascararNomeLGPD(nome: string): string {
  const partes = nome.trim().split(/\s+/);
  if (partes.length <= 2) return nome;
  const meio = partes.slice(1, -1).map((p) => "*".repeat(p.length));
  return [partes[0], ...meio, partes[partes.length - 1]].join(" ");
}

// Mascaramento LGPD do CPF — mantém só os 3 primeiros dígitos.
export function mascararCPFLGPD(cpf: string): string {
  const digits = onlyDigits(cpf).padEnd(11, "0").slice(0, 11);
  return `${digits.slice(0, 3)}.***.***-**`;
}
