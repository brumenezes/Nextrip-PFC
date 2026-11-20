export type ItinerarySummary = {
  id: string;
  data_inicio: string;
  data_fim: string;
  custo_total_estimado: number | null;
};

export type GenerateItineraryInput = {
  data_visita: string;
  tempo_disponivel_minutos: number;
  orcamento_maximo: number;
  quantidade_paradas: number;
  peso_preferencias?: number;
  usar_matriz_viaria?: boolean;
  metrica_recomendacao?: 'cosseno' | 'hibrido';
  peso_cosseno?: number;
  latitude_origem?: number;
  longitude_origem?: number;
};

export type ItineraryActivity = {
  poi_id: string;
  nome: string;
  categoria: string | null;
  ordem_sequencia: number;
  preco_estimado: number;
  duracao_minutos: number;
  tempo_deslocamento_previsto: number;
  distancia_deslocamento_metros: number;
};

export type GeneratedItinerary = {
  roteiro_id: string;
  data_visita: string;
  tempo_disponivel_minutos: number;
  tempo_total_visitas: number;
  orcamento_maximo: number;
  custo_total_estimado: number;
  tempo_total_deslocamentos: number;
  tempo_total_roteiro: number;
  atividades: ItineraryActivity[];
};
