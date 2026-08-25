import { CSSProperties } from "react";

/**
 * Estilo para a entrada em cascata (classe `animate-fade-in-up` do
 * index.css): cada elemento atrasa um pouco mais que o anterior conforme o
 * índice. Use na sequência em que os elementos aparecem na tela.
 *
 * Ex.: <Card className="animate-fade-in-up" style={staggerStyle(0)}> ...
 */
export function staggerStyle(index: number): CSSProperties {
  return { "--stagger-index": index } as CSSProperties;
}
