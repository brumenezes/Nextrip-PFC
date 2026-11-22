import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as Location from 'expo-location';
import { router } from 'expo-router';
import React from 'react';
import { Controller, useForm } from 'react-hook-form';
import { Pressable, StyleSheet, Switch, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { getErrorMessage } from '@/api/errors';
import { useAuth } from '@/auth/AuthProvider';
import { Button, Card, Input, Screen } from '@/components';
import { colors, radii, spacing, typography } from '@/design-system';
import {
  generateItinerarySchema,
  toApiCivilDate,
  type GenerateItineraryForm,
} from '@/features/roteiros/schemas';
import {
  getPreferredCurrency,
  setPreferredCurrency,
  TRAVEL_CURRENCIES,
  type TravelCurrency,
} from '@/features/preferencias/currency-storage';
import { generateItinerary } from '@/features/roteiros/service';
import type { GeneratedItinerary } from '@/features/roteiros/types';
import { formatCurrency } from '@/utils/formatters';

const DURATIONS = [
  { value: 120, label: '2 horas' },
  { value: 240, label: '4 horas' },
  { value: 360, label: '6 horas' },
] as const;

const STOPS = [2, 3, 4] as const;

const OPTIMIZATION_MODES = [
  { value: 'fast', label: 'Mais rápido', weight: 0.2 },
  { value: 'balanced', label: 'Equilibrado', weight: 0.5 },
  { value: 'preferences', label: 'Preferências', weight: 0.8 },
] as const;

type OptimizationMode = typeof OPTIMIZATION_MODES[number]['value'];
type Origin = { latitude: number; longitude: number; label: string };

function hojeCivilBrasileiro() {
  const hoje = new Date();
  const ano = hoje.getFullYear();
  const mes = String(hoje.getMonth() + 1).padStart(2, '0');
  const dia = String(hoje.getDate()).padStart(2, '0');
  return `${dia}/${mes}/${ano}`;
}

function Resultado({ roteiro, currency }: { roteiro: GeneratedItinerary; currency: TravelCurrency }) {
  return (
    <View style={styles.resultado}>
      <View style={styles.successIcon}>
        <Ionicons name="checkmark" size={28} color={colors.white} />
      </View>
      <Text style={styles.resultadoTitulo}>Roteiro criado</Text>
      <Text style={styles.resumo}>
        {roteiro.tempo_total_roteiro} min · {formatCurrency(roteiro.custo_total_estimado, currency)}
      </Text>
      {roteiro.atividades.map((atividade) => (
        <Card key={atividade.poi_id} style={styles.atividade}>
          <Text style={styles.ordem}>{atividade.ordem_sequencia}</Text>
          <View style={styles.atividadeTexto}>
            <Text style={styles.atividadeNome}>{atividade.nome}</Text>
            <Text style={styles.atividadeDetalhe}>
              {atividade.duracao_minutos} min · {formatCurrency(atividade.preco_estimado, currency)}
            </Text>
          </View>
        </Card>
      ))}
      <Button label="Ver meus roteiros" onPress={() => router.replace('/(private)/(tabs)/roteiros')} />
    </View>
  );
}

type ChoiceProps = {
  label: string;
  selected: boolean;
  onPress: () => void;
};

function Choice({ label, selected, onPress }: ChoiceProps) {
  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityState={{ selected }}
      onPress={onPress}
      style={({ pressed }) => [
        styles.choice,
        selected && styles.choiceSelected,
        pressed && styles.pressed,
      ]}
    >
      <Text style={[styles.choiceText, selected && styles.choiceTextSelected]}>{label}</Text>
    </Pressable>
  );
}

export default function NewItineraryScreen() {
  const { userId } = useAuth();
  const queryClient = useQueryClient();
  const [resultado, setResultado] = React.useState<GeneratedItinerary | null>(null);
  const [formMessage, setFormMessage] = React.useState<string | null>(null);
  const [selectedCurrency, setSelectedCurrency] = React.useState<TravelCurrency | null>(null);
  const [optimizationMode, setOptimizationMode] = React.useState<OptimizationMode>('balanced');
  const [origin, setOrigin] = React.useState<Origin | null>(null);
  const [originAddress, setOriginAddress] = React.useState('');
  const [locationAction, setLocationAction] = React.useState<'current' | 'address' | null>(null);
  const [locationError, setLocationError] = React.useState<string | null>(null);
  const [returnToOrigin, setReturnToOrigin] = React.useState(false);
  const [useRoadMatrix, setUseRoadMatrix] = React.useState(true);
  const currencyQuery = useQuery({
    queryKey: ['preferences-currency', userId],
    queryFn: () => getPreferredCurrency(userId!),
    enabled: Boolean(userId),
  });
  const currency = selectedCurrency ?? currencyQuery.data ?? 'BRL';
  const preferenceWeight = OPTIMIZATION_MODES.find((mode) => mode.value === optimizationMode)?.weight ?? 0.5;
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<GenerateItineraryForm>({
    resolver: zodResolver(generateItinerarySchema),
    defaultValues: {
      data_visita: hojeCivilBrasileiro(),
      tempo_disponivel_minutos: 360,
      orcamento_maximo: 150,
      quantidade_paradas: 3,
    },
  });
  const mutation = useMutation({
    mutationFn: generateItinerary,
    onSuccess: async (roteiro) => {
      setResultado(roteiro);
      await queryClient.invalidateQueries({ queryKey: ['itineraries'] });
    },
  });

  async function requestLocationPermission() {
    const permission = await Location.requestForegroundPermissionsAsync();
    if (!permission.granted) {
      throw new Error('Permita o acesso à localização para definir o início do roteiro.');
    }
  }

  async function selectCurrentLocation() {
    setLocationAction('current');
    setLocationError(null);
    try {
      await requestLocationPermission();
      const current = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      setOrigin({
        latitude: current.coords.latitude,
        longitude: current.coords.longitude,
        label: 'Minha localização atual',
      });
    } catch (error) {
      setLocationError(error instanceof Error ? error.message : 'Não foi possível obter sua localização.');
    } finally {
      setLocationAction(null);
    }
  }

  async function selectAddressLocation() {
    if (!originAddress.trim()) {
      setLocationError('Digite um endereço para buscar.');
      return;
    }
    setLocationAction('address');
    setLocationError(null);
    try {
      await requestLocationPermission();
      const [result] = await Location.geocodeAsync(originAddress.trim());
      if (!result) throw new Error('Endereço não encontrado. Tente incluir cidade e estado.');
      setOrigin({ latitude: result.latitude, longitude: result.longitude, label: originAddress.trim() });
    } catch (error) {
      setLocationError(error instanceof Error ? error.message : 'Não foi possível localizar este endereço.');
    } finally {
      setLocationAction(null);
    }
  }

  const submit = handleSubmit(async (values) => {
    setFormMessage(null);
    const dados = generateItinerarySchema.parse(values);
    if (userId) {
      await setPreferredCurrency(userId, currency);
      queryClient.setQueryData(['preferences-currency', userId], currency);
    }
    mutation.mutate({
      ...dados,
      data_visita: toApiCivilDate(dados.data_visita),
      latitude_origem: origin?.latitude,
      longitude_origem: origin?.longitude,
      retornar_origem: Boolean(origin && returnToOrigin),
      peso_preferencias: preferenceWeight,
      usar_matriz_viaria: useRoadMatrix,
      metrica_recomendacao: 'hibrido',
      peso_cosseno: 0.7,
    });
  }, () => setFormMessage('Revise os campos destacados antes de criar o roteiro.'));

  return (
    <Screen scroll contentStyle={styles.screen}>
      <View style={styles.header}>
        <Pressable accessibilityRole="button" accessibilityLabel="Voltar" onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={colors.primary} />
        </Pressable>
        <Text style={styles.title}>Novo roteiro</Text>
        <View style={styles.headerSpacer} />
      </View>

      {resultado ? (
        <Resultado roteiro={resultado} currency={currency} />
      ) : (
        <View style={styles.formFlow}>
          <View style={styles.intro}>
            <View style={styles.introIcon}>
              <Ionicons name="sparkles-outline" size={22} color={colors.actionPressed} />
            </View>
            <View style={styles.introText}>
              <Text style={styles.introTitle}>Planejado para você</Text>
              <Text style={styles.introDescription}>
                Usaremos as preferências do seu perfil para selecionar e organizar as atrações.
              </Text>
            </View>
          </View>

          <Card style={styles.form}>
            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>Como devemos montar seu roteiro?</Text>
              <View style={styles.choiceRow}>
                {OPTIMIZATION_MODES.map((mode) => (
                  <Choice
                    key={mode.value}
                    label={mode.label}
                    selected={optimizationMode === mode.value}
                    onPress={() => setOptimizationMode(mode.value)}
                  />
                ))}
              </View>
              <Text style={styles.fieldHint}>
                {optimizationMode === 'fast'
                  ? 'Reduz deslocamentos e prioriza a rota mais rápida.'
                  : optimizationMode === 'preferences'
                    ? 'Prioriza atrações mais alinhadas ao seu perfil.'
                    : 'Equilibra tempo de deslocamento e suas preferências.'}
              </Text>
            </View>

            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>De onde você vai sair?</Text>
              <Button
                label="Usar minha localização"
                variant="secondary"
                loading={locationAction === 'current'}
                onPress={() => void selectCurrentLocation()}
              />
              <View style={styles.orDivider}>
                <View style={styles.dividerLine} />
                <Text style={styles.orText}>ou informe um endereço</Text>
                <View style={styles.dividerLine} />
              </View>
              <Input
                label="Ponto de partida"
                placeholder="Rua, número, cidade"
                value={originAddress}
                onChangeText={setOriginAddress}
                returnKeyType="search"
                onSubmitEditing={() => void selectAddressLocation()}
              />
              <Button
                label="Buscar endereço"
                variant="secondary"
                loading={locationAction === 'address'}
                onPress={() => void selectAddressLocation()}
              />
              {origin ? (
                <View style={styles.originSelected}>
                  <Ionicons name="location" size={19} color={colors.actionPressed} />
                  <View style={styles.originText}>
                    <Text style={styles.originTitle}>Origem definida</Text>
                    <Text style={styles.originLabel} numberOfLines={2}>{origin.label}</Text>
                  </View>
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel="Remover origem"
                    hitSlop={8}
                    onPress={() => {
                      setOrigin(null);
                      setReturnToOrigin(false);
                    }}
                  >
                    <Ionicons name="close-circle" size={22} color={colors.textSecondary} />
                  </Pressable>
                </View>
              ) : null}
              {locationError ? <Text style={styles.fieldError}>{locationError}</Text> : null}
              <View style={[styles.returnRow, !origin && styles.returnRowDisabled]}>
                <View style={styles.returnText}>
                  <Text style={styles.returnTitle}>Voltar ao ponto de partida</Text>
                  <Text style={styles.returnSubtitle}>Inclui o trajeto de retorno no tempo total.</Text>
                </View>
                <Switch
                  disabled={!origin}
                  value={Boolean(origin && returnToOrigin)}
                  onValueChange={setReturnToOrigin}
                  trackColor={{ false: colors.border, true: colors.action }}
                  thumbColor={colors.white}
                />
              </View>
              <View style={styles.returnRow}>
                <View style={styles.returnText}>
                  <Text style={styles.returnTitle}>Usar rotas pelas ruas</Text>
                  <Text style={styles.returnSubtitle}>
                    Desative se o serviço de rotas estiver indisponível. O cálculo usará distâncias aproximadas.
                  </Text>
                </View>
                <Switch
                  value={useRoadMatrix}
                  onValueChange={setUseRoadMatrix}
                  trackColor={{ false: colors.border, true: colors.action }}
                  thumbColor={colors.white}
                />
              </View>
            </View>

            <Controller
              control={control}
              name="data_visita"
              render={({ field }) => (
                <Input
                  label="Quando será o passeio?"
                  value={String(field.value)}
                  onChangeText={field.onChange}
                  onBlur={field.onBlur}
                  placeholder="DD/MM/AAAA"
                  autoCapitalize="none"
                  error={errors.data_visita?.message}
                  hint="Use o formato dia/mês/ano."
                />
              )}
            />

            <Controller
              control={control}
              name="tempo_disponivel_minutos"
              render={({ field }) => (
                <View style={styles.fieldGroup}>
                  <Text style={styles.fieldLabel}>Quanto tempo você deseja gastar com atrações diariamente?</Text>
                  <View style={styles.choiceRow}>
                    {DURATIONS.map((duration) => (
                      <Choice
                        key={duration.value}
                        label={duration.label}
                        selected={Number(field.value) === duration.value}
                        onPress={() => field.onChange(duration.value)}
                      />
                    ))}
                  </View>
                  {errors.tempo_disponivel_minutos?.message ? (
                    <Text style={styles.fieldError}>{errors.tempo_disponivel_minutos.message}</Text>
                  ) : null}
                </View>
              )}
            />

            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>Quanto pretende gastar em reais?</Text>
              <View style={styles.currencyOptions}>
                {TRAVEL_CURRENCIES.map((option) => {
                  const selected = currency === option.code;
                  return (
                    <Pressable
                      key={option.code}
                      accessibilityRole="radio"
                      accessibilityState={{ selected }}
                      onPress={() => setSelectedCurrency(option.code)}
                      style={({ pressed }) => [
                        styles.currencyOption,
                        selected && styles.currencyOptionSelected,
                        pressed && styles.pressed,
                      ]}
                    >
                      <Text style={[styles.currencySymbol, selected && styles.currencyTextSelected]}>
                        {option.symbol}
                      </Text>
                      <Text numberOfLines={1} style={[styles.currencyLabel, selected && styles.currencyTextSelected]}>
                        {option.label}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
              <Controller
                control={control}
                name="orcamento_maximo"
                render={({ field }) => (
                  <Input
                    label={`Valor em ${TRAVEL_CURRENCIES.find((item) => item.code === currency)?.label ?? currency}`}
                    value={String(field.value)}
                    onChangeText={field.onChange}
                    onBlur={field.onBlur}
                    keyboardType="decimal-pad"
                    placeholder="Ex.: 150,00"
                    hint="A API atualmente interpreta todos os valores em reais."
                    error={errors.orcamento_maximo?.message}
                  />
                )}
              />
            </View>

            <Controller
              control={control}
              name="quantidade_paradas"
              render={({ field }) => (
                <View style={styles.fieldGroup}>
                  <Text style={styles.fieldLabel}>Quantos lugares deseja visitar?</Text>
                  <View style={styles.choiceRow}>
                    {STOPS.map((stops) => (
                      <Choice
                        key={stops}
                        label={`${stops} lugares`}
                        selected={Number(field.value) === stops}
                        onPress={() => field.onChange(stops)}
                      />
                    ))}
                  </View>
                  {errors.quantidade_paradas?.message ? (
                    <Text style={styles.fieldError}>{errors.quantidade_paradas.message}</Text>
                  ) : null}
                </View>
              )}
            />
          </Card>

          {formMessage ? <Text style={styles.error}>{formMessage}</Text> : null}
          {mutation.isError ? (
            <View style={styles.apiError}>
              <Ionicons name="alert-circle-outline" size={20} color={colors.error} />
              <Text style={styles.apiErrorText}>{getErrorMessage(mutation.error)}</Text>
            </View>
          ) : null}
          <Button label="Criar meu roteiro" loading={mutation.isPending} onPress={() => void submit()} />
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { gap: spacing.lg },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  headerSpacer: { width: 24 },
  title: { ...typography.heading, color: colors.primary, textAlign: 'center' },
  formFlow: { width: '100%', gap: spacing.md },
  intro: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    padding: spacing.md,
    borderRadius: radii.lg,
    backgroundColor: '#E5F7F6',
  },
  introIcon: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.md,
    backgroundColor: colors.surface,
  },
  introText: { flex: 1, justifyContent: 'center' },
  introTitle: { ...typography.label, color: colors.primary, textAlign: 'left' },
  introDescription: { ...typography.caption, color: colors.textSecondary, textAlign: 'left' },
  form: { width: '100%', alignItems: 'stretch', gap: spacing.lg },
  fieldGroup: { width: '100%', gap: spacing.sm },
  fieldLabel: { ...typography.label, color: colors.text, textAlign: 'left' },
  fieldHint: { ...typography.caption, color: colors.textSecondary, fontSize: 11, textAlign: 'left' },
  choiceRow: { width: '100%', flexDirection: 'row', gap: spacing.xs },
  choice: {
    flex: 1,
    minWidth: 0,
    minHeight: 52,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.xs,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  choiceSelected: { borderColor: colors.action, backgroundColor: '#E5F7F6' },
  choiceText: {
    ...typography.label,
    color: colors.textSecondary,
    fontSize: 12,
    lineHeight: 18,
    includeFontPadding: false,
    textAlign: 'center',
    textAlignVertical: 'center',
  },
  choiceTextSelected: { color: colors.actionPressed },
  currencyOptions: { width: '100%', flexDirection: 'row', gap: spacing.xs },
  currencyOption: {
    flex: 1,
    minHeight: 68,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xxs,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  currencyOptionSelected: { borderColor: colors.action, backgroundColor: colors.action },
  currencySymbol: { ...typography.title, color: colors.primary, textAlign: 'center' },
  currencyLabel: { ...typography.caption, color: colors.textSecondary, fontSize: 11, textAlign: 'center' },
  currencyTextSelected: { color: colors.white },
  orDivider: { width: '100%', flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  dividerLine: { flex: 1, height: 1, backgroundColor: colors.border },
  orText: { ...typography.caption, color: colors.textSecondary, fontSize: 11, textAlign: 'center' },
  originSelected: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    padding: spacing.sm,
    borderRadius: radii.md,
    backgroundColor: '#E5F7F6',
  },
  originText: { flex: 1, justifyContent: 'center' },
  originTitle: { ...typography.label, color: colors.primary, fontSize: 12, textAlign: 'left' },
  originLabel: { ...typography.caption, color: colors.textSecondary, fontSize: 11, textAlign: 'left' },
  returnRow: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    padding: spacing.sm,
    borderRadius: radii.md,
    backgroundColor: colors.background,
  },
  returnRowDisabled: { opacity: 0.5 },
  returnText: { flex: 1, justifyContent: 'center' },
  returnTitle: { ...typography.label, color: colors.primary, fontSize: 12, textAlign: 'left' },
  returnSubtitle: { ...typography.caption, color: colors.textSecondary, fontSize: 11, textAlign: 'left' },
  pressed: { opacity: 0.75 },
  fieldError: { ...typography.caption, color: colors.error, textAlign: 'center' },
  error: { ...typography.caption, color: colors.error, textAlign: 'center' },
  apiError: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    padding: spacing.sm,
    borderRadius: radii.md,
    backgroundColor: colors.errorSoft,
  },
  apiErrorText: { ...typography.caption, flex: 1, color: colors.error, textAlign: 'left' },
  resultado: { alignItems: 'center', gap: spacing.md },
  successIcon: {
    width: 56,
    height: 56,
    borderRadius: radii.pill,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.action,
  },
  resultadoTitulo: { ...typography.heading, color: colors.primary, textAlign: 'center' },
  resumo: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  atividade: { width: '100%', flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  ordem: {
    ...typography.label,
    color: colors.white,
    backgroundColor: colors.primary,
    width: 32,
    height: 32,
    borderRadius: radii.pill,
    textAlign: 'center',
    textAlignVertical: 'center',
    lineHeight: 32,
  },
  atividadeTexto: { flex: 1, justifyContent: 'center' },
  atividadeNome: { ...typography.title, color: colors.primary, textAlign: 'left' },
  atividadeDetalhe: { ...typography.caption, color: colors.textSecondary, textAlign: 'left' },
});
