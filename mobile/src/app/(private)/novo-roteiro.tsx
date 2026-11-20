import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import React from 'react';
import { Controller, useForm } from 'react-hook-form';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { getErrorMessage } from '@/api/errors';
import { Button, Card, Input, Screen } from '@/components';
import { colors, radii, spacing, typography } from '@/design-system';
import {
  generateItinerarySchema,
  type GenerateItineraryForm,
} from '@/features/roteiros/schemas';
import { generateItinerary } from '@/features/roteiros/service';
import type { GeneratedItinerary } from '@/features/roteiros/types';
import { formatCurrency } from '@/utils/formatters';

const DURATIONS = [
  { value: 120, label: '2 horas' },
  { value: 240, label: '4 horas' },
  { value: 360, label: '6 horas' },
] as const;

const STOPS = [2, 3, 4] as const;

function hojeCivil() {
  const hoje = new Date();
  const ano = hoje.getFullYear();
  const mes = String(hoje.getMonth() + 1).padStart(2, '0');
  const dia = String(hoje.getDate()).padStart(2, '0');
  return `${ano}-${mes}-${dia}`;
}

function Resultado({ roteiro }: { roteiro: GeneratedItinerary }) {
  return (
    <View style={styles.resultado}>
      <View style={styles.successIcon}>
        <Ionicons name="checkmark" size={28} color={colors.white} />
      </View>
      <Text style={styles.resultadoTitulo}>Roteiro criado</Text>
      <Text style={styles.resumo}>
        {roteiro.tempo_total_roteiro} min · {formatCurrency(roteiro.custo_total_estimado)}
      </Text>
      {roteiro.atividades.map((atividade) => (
        <Card key={atividade.poi_id} style={styles.atividade}>
          <Text style={styles.ordem}>{atividade.ordem_sequencia}</Text>
          <View style={styles.atividadeTexto}>
            <Text style={styles.atividadeNome}>{atividade.nome}</Text>
            <Text style={styles.atividadeDetalhe}>
              {atividade.duracao_minutos} min · {formatCurrency(atividade.preco_estimado)}
            </Text>
          </View>
        </Card>
      ))}
      <Button label="Ver meus roteiros" onPress={() => router.replace('/(private)/roteiros')} />
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
  const queryClient = useQueryClient();
  const [resultado, setResultado] = React.useState<GeneratedItinerary | null>(null);
  const [formMessage, setFormMessage] = React.useState<string | null>(null);
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<GenerateItineraryForm>({
    resolver: zodResolver(generateItinerarySchema),
    defaultValues: {
      data_visita: hojeCivil(),
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

  const submit = handleSubmit((values) => {
    setFormMessage(null);
    const dados = generateItinerarySchema.parse(values);
    mutation.mutate({
      ...dados,
      peso_preferencias: 0.8,
      usar_matriz_viaria: true,
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
        <Resultado roteiro={resultado} />
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
            <Controller
              control={control}
              name="data_visita"
              render={({ field }) => (
                <Input
                  label="Quando será o passeio?"
                  value={String(field.value)}
                  onChangeText={field.onChange}
                  onBlur={field.onBlur}
                  placeholder="AAAA-MM-DD"
                  autoCapitalize="none"
                  error={errors.data_visita?.message}
                  hint="Use o formato ano-mês-dia."
                />
              )}
            />

            <Controller
              control={control}
              name="tempo_disponivel_minutos"
              render={({ field }) => (
                <View style={styles.fieldGroup}>
                  <Text style={styles.fieldLabel}>Quanto tempo você tem?</Text>
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

            <Controller
              control={control}
              name="orcamento_maximo"
              render={({ field }) => (
                <Input
                  label="Quanto pretende gastar?"
                  value={String(field.value)}
                  onChangeText={field.onChange}
                  onBlur={field.onBlur}
                  keyboardType="decimal-pad"
                  placeholder="Ex.: 150,00"
                  hint="Valor máximo para as atrações do roteiro."
                  error={errors.orcamento_maximo?.message}
                />
              )}
            />

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
