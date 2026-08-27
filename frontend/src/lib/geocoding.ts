// Geocodificação de endereço via Nominatim (OpenStreetMap) — serviço público
// e gratuito, sem chave de API. Chamado só sob ação explícita do usuário
// (botão "Buscar endereço"), nunca a cada tecla, respeitando o limite de uso
// justo do serviço (~1 requisição por segundo).
export interface ResultadoGeocodificacao {
  latitude: number;
  longitude: number;
  enderecoEncontrado: string;
}

export async function buscarEndereco(endereco: string): Promise<ResultadoGeocodificacao | null> {
  const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(endereco)}`;
  const resp = await fetch(url, { headers: { "Accept-Language": "pt-BR" } });
  if (!resp.ok) throw new Error("Erro ao consultar o serviço de geocodificação.");
  const resultados: { lat: string; lon: string; display_name: string }[] = await resp.json();
  if (resultados.length === 0) return null;
  return {
    latitude: Number(resultados[0].lat),
    longitude: Number(resultados[0].lon),
    enderecoEncontrado: resultados[0].display_name,
  };
}

// CEP é um identificador preciso e de tamanho fixo (8 dígitos) — mais
// confiável pra localizar no mapa do que buscar um endereço digitado à mão
// (o Nominatim erra bastante com endereços brasileiros incompletos/abreviados).
// ViaCEP (gratuito, sem chave) traduz o CEP num endereço estruturado, que aí
// sim vai pro Nominatim pra virar coordenadas.
export interface EnderecoPorCep {
  endereco: string;
  cidade: string;
  uf: string;
}

export async function buscarEnderecoPorCep(cep: string): Promise<EnderecoPorCep | null> {
  const digits = cep.replace(/\D/g, "");
  const resp = await fetch(`https://viacep.com.br/ws/${digits}/json/`);
  if (!resp.ok) throw new Error("Erro ao consultar o CEP.");
  const dados = await resp.json();
  if (dados.erro) return null;
  const cepFormatado = digits.replace(/(\d{5})(\d{3})/, "$1-$2");
  const endereco = [dados.logradouro, dados.bairro, `${dados.localidade} - ${dados.uf}`, cepFormatado]
    .filter(Boolean)
    .join(", ");
  return { endereco, cidade: dados.localidade, uf: dados.uf };
}
