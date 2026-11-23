export const colors = {
  background: '#F5F8FC',
  surface: '#FFFFFF',
  primary: '#173B66',
  primaryPressed: '#102D50',
  primarySoft: '#EAF1F8',
  action: '#18B7B0',
  actionPressed: '#10938E',
  secondary: '#69B9ED',
  accent: '#FFB65C',
  text: '#173B66',
  textSecondary: '#64748B',
  navigation: '#303840',
  navigationActive: '#46515B',
  border: '#D9E4EF',
  error: '#B42318',
  errorSoft: '#FEECEB',
  disabled: '#94A3B8',
  white: '#FFFFFF',
  transparent: 'transparent',
} as const;

export const spacing = {
  xxs: 4,
  xs: 8,
  sm: 12,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const;

export const radii = {
  sm: 8,
  md: 14,
  lg: 22,
  pill: 999,
} as const;

export const typography = {
  display: { fontFamily: 'Inter_700Bold', fontSize: 36, lineHeight: 44 },
  heading: { fontFamily: 'Inter_700Bold', fontSize: 24, lineHeight: 32 },
  title: { fontFamily: 'Inter_600SemiBold', fontSize: 18, lineHeight: 26 },
  body: { fontFamily: 'Inter_400Regular', fontSize: 16, lineHeight: 24 },
  label: { fontFamily: 'Inter_600SemiBold', fontSize: 14, lineHeight: 20 },
  caption: { fontFamily: 'Inter_400Regular', fontSize: 13, lineHeight: 18 },
} as const;
