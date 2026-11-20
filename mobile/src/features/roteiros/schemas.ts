import { z } from 'zod';

const dataCivil = /^\d{4}-\d{2}-\d{2}$/;

export const generateItinerarySchema = z.object({
  data_visita: z.string().regex(dataCivil, 'Use o formato AAAA-MM-DD'),
  tempo_disponivel_minutos: z.coerce
    .number<number>('Informe o tempo disponível')
    .int('Use minutos inteiros')
    .min(30, 'Informe pelo menos 30 minutos')
    .max(1440, 'O limite é de 1.440 minutos'),
  orcamento_maximo: z.coerce
    .number<number>('Informe o orçamento')
    .min(0, 'O orçamento não pode ser negativo'),
  quantidade_paradas: z.coerce
    .number<number>('Informe a quantidade')
    .int('Use um número inteiro')
    .min(1, 'Escolha pelo menos uma parada')
    .max(19, 'O limite é de 19 paradas'),
});

export type GenerateItineraryForm = z.input<typeof generateItinerarySchema>;
