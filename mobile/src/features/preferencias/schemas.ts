import { z } from 'zod';

export const preferencesSchema = z.object({
  orcamentoMaximo: z
    .string()
    .trim()
    .min(1, 'Informe um orçamento.')
    .refine((value) => {
      const number = Number(value.replace(',', '.'));
      return Number.isFinite(number) && number >= 0;
    }, 'Informe um valor maior ou igual a zero.'),
  interesses: z.string(),
});

export type PreferencesFormData = z.infer<typeof preferencesSchema>;

export function toPreferencesInput(data: PreferencesFormData) {
  const interests = data.interesses
    .split(',')
    .map((interest) => interest.trim())
    .filter((interest, index, items) => interest.length > 0 && items.indexOf(interest) === index);

  return {
    orcamento_maximo: Number(data.orcamentoMaximo.replace(',', '.')),
    interesses: interests,
  };
}
