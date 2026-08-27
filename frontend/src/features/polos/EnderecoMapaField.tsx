import { useState } from "react";
import { Input } from "@/components/ui/Input";
import { CheckCircleIcon } from "@/components/ui/icons";
import { useToast } from "@/components/ui/toast/ToastContext";
import { buscarEndereco, buscarEnderecoPorCep } from "@/lib/geocoding";
import { maskCEP } from "@/lib/masks";

interface Props {
  onEnderecoChange: (endereco: string) => void;
  latitude: number | null;
  longitude: number | null;
  onChange: (latitude: number | null, longitude: number | null) => void;
}

/**
 * Localiza o polo a partir do CEP — busca automática assim que os 8 dígitos
 * são preenchidos, e preenche o campo Endereço junto. O pino em si só
 * aparece no Mapa de Polos do Dashboard — aqui só confirma que a
 * localização foi salva.
 */
export function EnderecoMapaField({ onEnderecoChange, latitude, longitude, onChange }: Props) {
  const toast = useToast();
  const [cep, setCep] = useState("");
  const [buscandoCep, setBuscandoCep] = useState(false);

  async function localizarNoMapa(enderecoParaBuscar: string) {
    const resultado = await buscarEndereco(enderecoParaBuscar);
    if (!resultado) return false;
    onChange(resultado.latitude, resultado.longitude);
    return true;
  }

  async function handleCepChange(valor: string) {
    const mascarado = maskCEP(valor);
    setCep(mascarado);
    if (mascarado.replace(/\D/g, "").length !== 8) return;

    setBuscandoCep(true);
    try {
      const resultado = await buscarEnderecoPorCep(mascarado);
      if (!resultado) {
        toast.error("CEP não encontrado.");
        return;
      }
      onEnderecoChange(resultado.endereco);
      const localizado = await localizarNoMapa(resultado.endereco);
      toast[localizado ? "success" : "error"](
        localizado
          ? "Localização encontrada pelo CEP — já vai aparecer no Mapa de Polos do Dashboard."
          : "CEP encontrado, mas não foi possível localizar no mapa. Ajuste o endereço e tente \"Buscar pelo endereço\"."
      );
    } catch {
      toast.error("Não foi possível consultar o CEP agora.");
    } finally {
      setBuscandoCep(false);
    }
  }

  return (
    <div className="sm:col-span-2 space-y-2">
      <span className="block text-sm font-medium text-gray-700">Localização no mapa</span>
      <div className="max-w-[220px]">
        <Input
          label="CEP"
          placeholder="00000-000"
          value={cep}
          onChange={(e) => handleCepChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") e.preventDefault();
          }}
          maxLength={9}
          hint={buscandoCep ? "Localizando…" : "Localiza automaticamente ao completar."}
        />
      </div>
      {latitude !== null && longitude !== null && (
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <CheckCircleIcon className="w-4 h-4 text-accent-dark shrink-0" />
          <span>Localização definida — aparece no Mapa de Polos do Dashboard.</span>
          <button type="button" onClick={() => onChange(null, null)} className="text-gray-400 hover:text-red-600 underline">
            remover
          </button>
        </div>
      )}
    </div>
  );
}
