import { useEffect, useRef, useState } from "react";
import { pinoPolo } from "@/lib/leafletSetup";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import html2canvas from "html2canvas";
import type { Polo } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";

const TILE_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const TILE_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';


const CENTRO_RJ: [number, number] = [-22.25, -42.66];
const ZOOM_CARD = 7;
const ZOOM_MODAL = 8;


function ForcarCentro({ centro, zoom }: { centro: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
    map.setView(centro, zoom);

  }, [map]);
  return null;
}

function PinsDoMapa({ polos }: { polos: Polo[] }) {
  return (
    <>
      {polos.map((p) => (
        <Marker key={p.id} position={[p.latitude!, p.longitude!]} icon={pinoPolo}>
          <Popup>
            <strong>{p.nome}</strong>
            {p.endereco && <div>{p.endereco}</div>}
          </Popup>
        </Marker>
      ))}
    </>
  );
}


export function PolosMapaCard({ polos }: { polos: Polo[] }) {
  const toast = useToast();
  const [expandido, setExpandido] = useState(false);
  const [exportando, setExportando] = useState(false);
  const modalMapaRef = useRef<HTMLDivElement>(null);

  const comCoordenadas = polos.filter(
    (p): p is Polo & { latitude: number; longitude: number } => p.latitude !== null && p.longitude !== null
  );

  async function exportarImagem() {
    setExportando(true);
    const jaEstavaExpandido = expandido;
    try {
      if (!jaEstavaExpandido) {
        setExpandido(true);

        await new Promise((r) => setTimeout(r, 900));
      }
      if (!modalMapaRef.current) {
        toast.error("Não foi possível gerar a imagem do mapa.");
        return;
      }
      const canvas = await html2canvas(modalMapaRef.current, { useCORS: true });
      canvas.toBlob((blob) => {
        if (!blob) {
          toast.error("Não foi possível gerar a imagem do mapa.");
          return;
        }
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "mapa-de-polos.png";
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      });
    } catch {
      toast.error("Não foi possível gerar a imagem do mapa. Tente novamente.");
    } finally {
      setExportando(false);
      if (!jaEstavaExpandido) setExpandido(false);
    }
  }

  return (
    <>
      <Card
        title="Mapa de Polos"
        actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => setExpandido(true)}>Expandir</Button>
            <Button variant="secondary" onClick={exportarImagem} disabled={exportando}>
              {exportando ? "Gerando…" : "Exportar imagem"}
            </Button>
          </div>
        }
        className="animate-fade-in-up"
        style={staggerStyle(7)}
      >
        <div className="h-72 rounded-lg overflow-hidden">
          <MapContainer center={CENTRO_RJ} zoom={ZOOM_CARD} style={{ height: "100%", width: "100%" }}>
            <ForcarCentro centro={CENTRO_RJ} zoom={ZOOM_CARD} />
            <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} />
            <PinsDoMapa polos={comCoordenadas} />
          </MapContainer>
        </div>
      </Card>

      <Modal open={expandido} onClose={() => setExpandido(false)} title="Mapa de Polos" maxWidth="max-w-4xl">
        <div ref={modalMapaRef} className="h-[70vh] rounded-lg overflow-hidden">
          <MapContainer center={CENTRO_RJ} zoom={ZOOM_MODAL} style={{ height: "100%", width: "100%" }}>
            <ForcarCentro centro={CENTRO_RJ} zoom={ZOOM_MODAL} />
            <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} />
            <PinsDoMapa polos={comCoordenadas} />
          </MapContainer>
        </div>
      </Modal>
    </>
  );
}
