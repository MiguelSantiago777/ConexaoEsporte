import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface DocumentoComTipo {
  id: string;
  tipo: string;
  criado_em: string | null;
}

function iniciais(nome: string) {
  const partes = nome.trim().split(/\s+/).filter(Boolean);
  if (partes.length === 0) return "?";
  const letras = partes.length > 1 ? [partes[0][0], partes[partes.length - 1][0]] : [partes[0][0]];
  return letras.join("").toUpperCase();
}

/**
 * Avatar circular com a foto do professor/beneficiário (busca o anexo mais
 * recente do tipo indicado) ou, na ausência de foto, as iniciais do nome —
 * mesmo padrão de miniatura autenticada usado pelas evidências de chamada
 * (`EvidenciaThumb`, em FrequenciaPage).
 */
export function Avatar({
  nome,
  documentosUrl,
  arquivoUrlBase,
  tipoFoto,
  size = 32,
}: {
  nome: string;
  documentosUrl: string;
  arquivoUrlBase: string;
  tipoFoto: string;
  size?: number;
}) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelado = false;
    api
      .get<DocumentoComTipo[]>(documentosUrl)
      .then((r) => {
        const fotos = r.data
          .filter((d) => d.tipo === tipoFoto)
          .sort((a, b) => (b.criado_em ?? "").localeCompare(a.criado_em ?? ""));
        const foto = fotos[0];
        if (!foto || cancelado) return null;
        return api.get(`${arquivoUrlBase}/${foto.id}/arquivo`, { responseType: "blob" });
      })
      .then((r) => {
        if (!r || cancelado) return;
        objectUrl = window.URL.createObjectURL(r.data);
        setSrc(objectUrl);
      })
      .catch(() => {});
    return () => {
      cancelado = true;
      if (objectUrl) window.URL.revokeObjectURL(objectUrl);
    };
  }, [documentosUrl, arquivoUrlBase, tipoFoto]);

  const estilo = { width: size, height: size, fontSize: Math.round(size * 0.4) };

  if (src) {
    return (
      <img
        src={src}
        alt={nome}
        className="rounded-full object-cover shrink-0 border border-gray-200"
        style={estilo}
      />
    );
  }
  return (
    <span
      className="rounded-full bg-brand-light text-brand-dark font-semibold flex items-center justify-center shrink-0"
      style={estilo}
      title={nome}
    >
      {iniciais(nome)}
    </span>
  );
}
