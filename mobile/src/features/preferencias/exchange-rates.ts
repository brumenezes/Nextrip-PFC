import type { TravelCurrency } from './currency-storage';

const EXCHANGE_API_URL = 'https://api.frankfurter.dev/v2/rates?base=BRL&quotes=EUR,GBP,USD';

type ExchangeRateRow = {
  quote: string;
  rate: number;
};

export type ExchangeRates = {
  base: 'BRL';
  rates: Record<TravelCurrency, number>;
};

export async function getExchangeRates(): Promise<ExchangeRates> {
  const response = await fetch(EXCHANGE_API_URL);
  if (!response.ok) throw new Error('Não foi possível consultar as cotações agora.');

  const rows = await response.json() as ExchangeRateRow[];
  const rates: Record<TravelCurrency, number> = { BRL: 1, EUR: 0, GBP: 0, USD: 0 };
  for (const row of rows) {
    const quote = row.quote.toUpperCase() as TravelCurrency;
    if (quote in rates && Number.isFinite(row.rate) && row.rate > 0) {
      rates[quote] = row.rate;
    }
  }

  if (!rates.EUR || !rates.GBP || !rates.USD) {
    throw new Error('A resposta de cotações veio incompleta.');
  }

  return { base: 'BRL', rates };
}

export function convertCurrency(
  value: number,
  from: TravelCurrency,
  to: TravelCurrency,
  exchangeRates?: ExchangeRates,
) {
  if (from === to || value === 0) return value;
  if (!exchangeRates) throw new Error('A cotação da moeda ainda não está disponível.');

  const valueInBrl = from === 'BRL' ? value : value / exchangeRates.rates[from];
  return to === 'BRL' ? valueInBrl : valueInBrl * exchangeRates.rates[to];
}

export function formatRateToBrl(currency: TravelCurrency, exchangeRates?: ExchangeRates) {
  if (currency === 'BRL') return 'Valores enviados diretamente em reais.';
  if (!exchangeRates) return 'Consultando cotação…';
  const brl = convertCurrency(1, currency, 'BRL', exchangeRates);
  return `1 ${currency} = ${new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(brl)}`;
}
