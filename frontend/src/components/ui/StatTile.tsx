import { useEffect, useRef, useState } from "react";
import { staggerStyle } from "@/lib/animation";

interface Props {
  label: string;
  value: string | number;
  sublabel?: string;
  /** Posição no grid — anima em cascata (cada tile atrasa um pouco mais). */
  staggerIndex?: number;
  /** Versão menor e de largura fixa (usada na Central de Relatórios) — o
   * Dashboard mantém o tile grande, esticado pelo grid. */
  compact?: boolean;
}

/** Conta de 0 até o número embutido em `value` (ex.: "40%", "143") em
 * ~1,8s, com desaceleração no final, preservando prefixo/sufixo não
 * numérico. Quando `value` não tem parte numérica, exibe como veio, sem
 * animação. */
function useValorContado(value: string | number, duracaoMs = 1800) {
  const texto = String(value);
  const partes = texto.match(/^(\D*)(\d+)(\D*)$/);
  const [exibido, setExibido] = useState(partes ? partes[1] + "0" + partes[3] : texto);
  const primeiraRenderizacao = useRef(true);

  useEffect(() => {
    if (!partes) {
      setExibido(texto);
      return;
    }
    const [, prefixo, digitos, sufixo] = partes;
    const alvo = Number(digitos);

    // Sem animação na primeiríssima pintura (evita um "flash" de 0 antes do
    // efeito rodar) — parte de 0 só depois que o valor final já existe.
    if (primeiraRenderizacao.current) {
      primeiraRenderizacao.current = false;
    }

    let frame: number;
    const inicio = performance.now();
    function passo(agora: number) {
      const t = Math.min(1, (agora - inicio) / duracaoMs);
      const suavizado = 1 - Math.pow(1 - t, 3);
      setExibido(prefixo + Math.round(alvo * suavizado) + sufixo);
      if (t < 1) frame = requestAnimationFrame(passo);
    }
    frame = requestAnimationFrame(passo);
    return () => cancelAnimationFrame(frame);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [texto]);

  return exibido;
}

export function StatTile({ label, value, sublabel, staggerIndex, compact }: Props) {
  const valorContado = useValorContado(value);

  return (
    <div
      className={`relative bg-white rounded-xl overflow-hidden shadow-sm transition-shadow duration-200 hover:shadow-md ${
        compact ? "p-4 w-full sm:w-[190px]" : "p-6"
      } ${staggerIndex !== undefined ? "animate-fade-in-up" : ""}`}
      style={staggerIndex !== undefined ? staggerStyle(staggerIndex) : undefined}
    >
      <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-accent" />
      <div className={`font-medium text-gray-500 uppercase tracking-wide ${compact ? "text-[0.7rem]" : "text-xs"}`}>{label}</div>
      <div
        className={`font-mono tabular-nums leading-none font-semibold text-ink ${
          compact ? "text-xl mt-1.5" : "text-[1.75rem] mt-2.5"
        }`}
      >
        {valorContado}
      </div>
      {sublabel && <div className={`text-xs text-gray-400 ${compact ? "mt-1.5" : "mt-2"}`}>{sublabel}</div>}
    </div>
  );
}
