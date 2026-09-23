import { CSSProperties, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { LocalizarPoloResposta, Polo } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/toast/ToastContext";

interface Resumo {
  localizados: number;
  aproximados: string[];
  naoEncontrados: string[];
}

/** Aparece só quando existe polo sem latitude/longitude (e portanto fora do
 * mapa do Dashboard) — ex.: importados em massa com um endereço que a busca
 * não reconheceu. O botão busca a coordenada pelo endereço de cada um, um
 * por vez (o serviço de mapas aceita ~1 busca por segundo). */
export function PolosForaDoMapaCard({ style }: { style?: CSSProperties }) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const { data: todos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });
  const foraDoMapa = todos.filter((p) => p.latitude === null || p.longitude === null);

  const [progresso, setProgresso] = useState<{ atual: number; total: number } | null>(null);
  const [resumo, setResumo] = useState<Resumo | null>(null);

  async function localizarTodos() {
    const fila = foraDoMapa;
    const parcial: Resumo = { localizados: 0, aproximados: [], naoEncontrados: [] };
    setResumo(null);
    for (let i = 0; i < fila.length; i++) {
      setProgresso({ atual: i + 1, total: fila.length });
      try {
        const { data } = await api.post<LocalizarPoloResposta>(`/polos/${fila[i].id}/localizar`);
        if (data.situacao === "localizado") parcial.localizados++;
        else if (data.situacao === "aproximado") parcial.aproximados.push(fila[i].nome);
        else parcial.naoEncontrados.push(fila[i].nome);
      } catch {
        parcial.naoEncontrados.push(fila[i].nome);
      }
    }
    setProgresso(null);
    setResumo(parcial);
    queryClient.invalidateQueries({ queryKey: ["polos"] });
    const achados = parcial.localizados + parcial.aproximados.length;
    toast.success(`${achados} de ${fila.length} polo(s) colocado(s) no mapa.`);
  }

  if (foraDoMapa.length === 0 && !resumo) return null;

  return (
    <Card title="Polos fora do mapa" className="animate-fade-in-up" style={style}>
      {foraDoMapa.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-gray-600">
            {foraDoMapa.length === 1 ? "1 polo está sem localização" : `${foraDoMapa.length} polos estão sem localização`} e
            não aparece{foraDoMapa.length === 1 ? "" : "m"} no mapa do Dashboard:{" "}
            <span className="text-gray-800">{foraDoMapa.map((p) => p.nome).join(", ")}</span>.
          </p>
          <Button onClick={localizarTodos} disabled={!!progresso}>
            {progresso ? `Localizando ${progresso.atual} de ${progresso.total}…` : "Localizar no mapa pelo endereço"}
          </Button>
        </div>
      )}
      {resumo && (
        <div className={`text-sm space-y-1 ${foraDoMapa.length > 0 ? "mt-4" : ""}`}>
          {resumo.localizados > 0 && <p className="text-gray-700">✓ {resumo.localizados} localizado(s) pelo endereço.</p>}
          {resumo.aproximados.length > 0 && (
            <p className="text-accent-dark">
              Localização aproximada (pelo bairro/cidade): {resumo.aproximados.join(", ")}. Se quiser o pino exato,
              edite o polo e ajuste no mapa.
            </p>
          )}
          {resumo.naoEncontrados.length > 0 && (
            <p className="text-red-600">
              Não encontrados: {resumo.naoEncontrados.join(", ")}. Edite o polo e confira o endereço (rua, número, bairro e
              cidade) ou marque o ponto no mapa.
            </p>
          )}
        </div>
      )}
    </Card>
  );
}
