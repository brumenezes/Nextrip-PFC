export type PointOfInterest = {
  id: string;
  nome: string;
  categoria: string | null;
  latitude: number;
  longitude: number;
  preco_estimado: number | null;
  duracao_minutos: number | null;
  avaliacao_media: number | null;
  osm_id: number | null;
  google_place_id: string | null;
};
