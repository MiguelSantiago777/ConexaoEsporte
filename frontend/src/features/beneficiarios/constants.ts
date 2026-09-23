export const TIPOS_RELACAO = ["Mãe", "Pai", "Avó", "Avô", "Tio(a)", "Irmão(ã)", "Tutor(a) legal", "Outro"];

// Mesma lista/faixa validada no backend (app/domain/beneficiario/entities.py).
export const TAMANHOS_CAMISA = ["4", "6", "8", "10", "12", "14", "16", "PP", "P", "M", "G", "GG", "XG", "XGG"];
export const TAMANHOS_CALCADO = Array.from({ length: 46 - 20 + 1 }, (_, i) => String(20 + i));
