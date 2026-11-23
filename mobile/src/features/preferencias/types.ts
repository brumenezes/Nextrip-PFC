export type Preferences = {
  id: string;
  usuario_id: string;
  orcamento_maximo: number;
  interesses: string[];
};

export type PreferencesInput = {
  orcamento_maximo: number;
  interesses: string[];
};
