import { z } from 'zod';

const dataBrasileira = /^(\d{2})\/(\d{2})\/(\d{4})$/;

function isValidBrazilianDate(value: string) {
  const match = dataBrasileira.exec(value);
  if (!match) return false;
  const [, dayText, monthText, yearText] = match;
  const day = Number(dayText);
  const month = Number(monthText);
  const year = Number(yearText);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year
    && date.getUTCMonth() === month - 1
    && date.getUTCDate() === day;
}

export function toApiCivilDate(value: string) {
  const [day, month, year] = value.split('/');
  return `${year}-${month}-${day}`;
}

export const generateItinerarySchema = z.object({
  data_visita: z.string()
    .regex(dataBrasileira, 'Use o formato DD/MM/AAAA')
    .refine(isValidBrazilianDate, 'Informe uma data válida'),
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
