import type { ComponentProps } from 'react';
import { Ionicons } from '@expo/vector-icons';

type IconName = ComponentProps<typeof Ionicons>['name'];

export type CategoryPresentation = {
  label: string;
  icon: IconName;
};

const categories: Record<string, CategoryPresentation> = {
  atracao: { label: 'Atração', icon: 'sparkles-outline' },
  compras: { label: 'Compras', icon: 'bag-handle-outline' },
  cultura: { label: 'Cultura', icon: 'color-palette-outline' },
  galeria: { label: 'Galeria', icon: 'images-outline' },
  gastronomia: { label: 'Gastronomia', icon: 'restaurant-outline' },
  historia: { label: 'História', icon: 'time-outline' },
  mirante: { label: 'Mirante', icon: 'telescope-outline' },
  museu: { label: 'Museu', icon: 'business-outline' },
  natureza: { label: 'Natureza', icon: 'leaf-outline' },
  parque: { label: 'Parque', icon: 'trail-sign-outline' },
  vida_noturna: { label: 'Vida noturna', icon: 'moon-outline' },
};

const aliases: Record<string, string> = {
  atracoes: 'atracao',
  galerias: 'galeria',
  museus: 'museu',
  parques: 'parque',
};

export function normalizeCategory(value: string | null | undefined) {
  return (value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLocaleLowerCase('pt-BR')
    .replace(/[\s-]+/g, '_');
}

export function getCategoryPresentation(value: string | null | undefined): CategoryPresentation {
  const normalized = normalizeCategory(value);
  const key = aliases[normalized] ?? normalized;
  if (categories[key]) return categories[key];

  const fallback = key
    .replace(/_/g, ' ')
    .replace(/^./, (letter) => letter.toLocaleUpperCase('pt-BR'));
  return {
    label: fallback || 'Sem categoria',
    icon: 'location-outline',
  };
}

export const TRAVEL_INTERESTS = [
  { value: 'Museu', ...categories.museu },
  { value: 'Parque', ...categories.parque },
  { value: 'Cultura', ...categories.cultura },
  { value: 'História', ...categories.historia },
  { value: 'Gastronomia', ...categories.gastronomia },
  { value: 'Natureza', ...categories.natureza },
  { value: 'Mirante', ...categories.mirante },
  { value: 'Galeria', ...categories.galeria },
  { value: 'Compras', ...categories.compras },
  { value: 'Vida noturna', ...categories.vida_noturna },
] as const;
