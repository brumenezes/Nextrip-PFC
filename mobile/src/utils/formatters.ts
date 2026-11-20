import type { TravelCurrency } from '@/features/preferencias/currency-storage';

export function formatCurrency(value: number | null, currency: TravelCurrency = 'BRL') {
  if (value === null) return 'Não informado';
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency }).format(value);
}

export function formatCivilDate(value: string) {
  const [year, month, day] = value.split('-');
  return year && month && day ? `${day}/${month}/${year}` : value;
}
