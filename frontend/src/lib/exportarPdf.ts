import html2canvas from "html2canvas";
import jsPDF from "jspdf";

/**
 * Gera um arquivo .pdf de verdade a partir de um elemento do DOM (captura
 * como imagem via html2canvas e monta um PDF paginado em A4 com jsPDF) e
 * dispara o download direto — nada de abrir o diálogo de impressão do
 * navegador. O diálogo de "Imprimir" (window.print()) depende de como cada
 * navegador decide renderizar o CSS de impressão (animações, quebras de
 * página, cabeçalho/rodapé) e isso variava demais entre navegadores,
 * gerando PDFs com pedaços cortados ou faltando.
 */
export async function exportarPdf(elemento: HTMLElement, nomeArquivo: string) {
  // Containers com rolagem horizontal (tabelas largas) só mostram o que
  // cabe no viewport visível — sem isso, colunas de tabelas largas (ex.: a
  // grade da Ficha de Chamada, com uma coluna por dia do mês) saem cortadas
  // da captura. Neutraliza a rolagem só durante a captura e desfaz depois.
  const scrollaveis = Array.from(elemento.querySelectorAll<HTMLElement>(".overflow-x-auto"));
  const estiloOriginalOverflow = scrollaveis.map((el) => el.style.overflow);
  scrollaveis.forEach((el) => { el.style.overflow = "visible"; });

  // As classes de animação de entrada partem de opacity:0 e só chegam a
  // opacity:1 depois do tempo real da animação passar — o html2canvas clona
  // o DOM pra capturar, e nesse clone a animação não necessariamente já
  // rodou, saindo com o conteúdo semitransparente/apagado no PDF. Força
  // tudo pro estado final visível só durante a captura.
  const SELETOR_ANIMACAO = ".animate-fade-in-up, .animate-fade-in, .animate-page-in";
  const animados = Array.from(elemento.querySelectorAll<HTMLElement>(SELETOR_ANIMACAO));
  if (elemento.matches(SELETOR_ANIMACAO)) animados.push(elemento);
  const estiloOriginalAnimacao = animados.map((el) => ({
    opacity: el.style.opacity, animation: el.style.animation, transform: el.style.transform,
  }));
  animados.forEach((el) => {
    el.style.opacity = "1";
    el.style.animation = "none";
    el.style.transform = "none";
  });

  let canvas: HTMLCanvasElement;
  try {
    canvas = await html2canvas(elemento, { scale: 2, useCORS: true, backgroundColor: "#ffffff" });
  } finally {
    scrollaveis.forEach((el, i) => { el.style.overflow = estiloOriginalOverflow[i]; });
    animados.forEach((el, i) => {
      el.style.opacity = estiloOriginalAnimacao[i].opacity;
      el.style.animation = estiloOriginalAnimacao[i].animation;
      el.style.transform = estiloOriginalAnimacao[i].transform;
    });
  }

  const imgData = canvas.toDataURL("image/png");

  const pdf = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const imgWidth = pageWidth;
  const imgHeight = (canvas.height * imgWidth) / canvas.width;

  let heightLeft = imgHeight;
  let position = 0;

  pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
  heightLeft -= pageHeight;

  while (heightLeft > 0) {
    position -= pageHeight;
    pdf.addPage();
    pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;
  }

  pdf.save(nomeArquivo);
}
