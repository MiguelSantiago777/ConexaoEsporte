// Leaflet CSS + correção do ícone padrão do marcador — o bundler (Vite) não
// resolve os caminhos relativos que o Leaflet espera por padrão. Importar
// este módulo (por efeito colateral) uma vez antes de qualquer <MapContainer>.
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

// Pino customizado nas cores da marca (em vez do pino azul/branco padrão do
// Leaflet, com sombra "3D") — usado em todo Marker de polo no mapa.
const PIN_SVG = `
<svg width="28" height="38" viewBox="0 0 28 38" xmlns="http://www.w3.org/2000/svg">
  <path d="M14 0C6.268 0 0 6.268 0 14c0 10.5 14 24 14 24s14-13.5 14-24C28 6.268 21.732 0 14 0z" fill="#00417d"/>
  <circle cx="14" cy="14" r="6" fill="#fcba27"/>
</svg>`;

export const pinoPolo = L.divIcon({
  html: PIN_SVG,
  className: "",
  iconSize: [28, 38],
  iconAnchor: [14, 38],
  popupAnchor: [0, -34],
});
