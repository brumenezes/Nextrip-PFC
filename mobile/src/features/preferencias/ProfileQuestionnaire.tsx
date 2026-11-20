import { Ionicons } from '@expo/vector-icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { getErrorMessage } from '@/api/errors';
import { useAuth } from '@/auth/AuthProvider';
import { BrandLogo, Button, Card, Input, Screen } from '@/components';
import { colors, radii, spacing, typography } from '@/design-system';
import { TRAVEL_INTERESTS } from '@/features/pontos-interesse/categories';

import {
  getPreferredCurrency,
  setPreferredCurrency,
  TRAVEL_CURRENCIES,
  type TravelCurrency,
} from './currency-storage';
import { createPreferences, updatePreferences } from './service';
import type { Preferences } from './types';

type ProfileQuestionnaireProps = {
  preferences: Preferences | null;
  onCancel?: () => void;
  onCompleted?: () => void;
};

export function ProfileQuestionnaire({
  preferences,
  onCancel,
  onCompleted,
}: ProfileQuestionnaireProps) {
  const { userId, signOut } = useAuth();
  const queryClient = useQueryClient();
  const [step, setStep] = useState(0);
  const [selectedInterests, setSelectedInterests] = useState<string[]>(
    () => preferences?.interesses ?? [],
  );
  const [budget, setBudget] = useState(
    () => preferences ? String(preferences.orcamento_maximo) : '',
  );
  const [selectedCurrency, setSelectedCurrency] = useState<TravelCurrency | null>(null);
  const currencyQuery = useQuery({
    queryKey: ['preferences-currency', userId],
    queryFn: () => getPreferredCurrency(userId!),
    enabled: Boolean(userId),
  });
  const currency = selectedCurrency ?? currencyQuery.data ?? 'BRL';
  const normalizedBudget = useMemo(() => Number(budget.replace(',', '.')), [budget]);
  const validBudget = budget.trim().length > 0
    && Number.isFinite(normalizedBudget)
    && normalizedBudget >= 0;
  const editing = preferences !== null;

  const mutation = useMutation({
    mutationFn: async () => {
      if (!userId) throw new Error('Não foi possível identificar sua conta.');
      const input = {
        orcamento_maximo: normalizedBudget,
        interesses: selectedInterests,
      };
      const savedPreferences = editing
        ? updatePreferences(userId, input)
        : createPreferences(userId, input);
      const result = await savedPreferences;
      await setPreferredCurrency(userId, currency);
      return result;
    },
    onSuccess: (savedPreferences) => {
      queryClient.setQueryData(['preferences', userId], savedPreferences);
      queryClient.setQueryData(['preferences-currency', userId], currency);
      onCompleted?.();
    },
  });

  function toggleInterest(value: string) {
    setSelectedInterests((current) =>
      current.includes(value)
        ? current.filter((interest) => interest !== value)
        : [...current, value],
    );
  }

  return (
    <Screen scroll contentStyle={styles.screen}>
      <View style={styles.topBar}>
        {step > 0 || onCancel ? (
          <Pressable
            accessibilityLabel="Voltar"
            accessibilityRole="button"
            hitSlop={12}
            onPress={() => (step > 0 ? setStep(0) : onCancel?.())}
            style={styles.iconButton}
          >
            <Ionicons name="arrow-back" size={22} color={colors.primary} />
          </Pressable>
        ) : (
          <View style={styles.iconButtonPlaceholder} />
        )}
        <BrandLogo size={54} />
        {!editing ? (
          <Pressable
            accessibilityLabel="Sair"
            accessibilityRole="button"
            hitSlop={12}
            onPress={() => void signOut()}
            style={styles.iconButton}
          >
            <Ionicons name="log-out-outline" size={22} color={colors.primary} />
          </Pressable>
        ) : (
          <View style={styles.iconButtonPlaceholder} />
        )}
      </View>

      <View style={styles.progress}>
        {[0, 1].map((item) => (
          <View key={item} style={[styles.progressItem, item <= step && styles.progressItemActive]} />
        ))}
      </View>

      {step === 0 ? (
        <View style={styles.content}>
          <View style={styles.heading}>
            <Text style={styles.eyebrow}>Seu perfil de viagem</Text>
            <Text style={styles.title}>Quais tipos de atrações mais te interessam?</Text>
            <Text style={styles.subtitle}>
              Escolha uma ou mais experiências para personalizar seus roteiros.
            </Text>
          </View>

          <View style={styles.interestsGrid}>
            {TRAVEL_INTERESTS.map((interest) => {
              const selected = selectedInterests.includes(interest.value);
              return (
                <Pressable
                  key={interest.value}
                  accessibilityRole="checkbox"
                  accessibilityState={{ checked: selected }}
                  onPress={() => toggleInterest(interest.value)}
                  style={({ pressed }) => [
                    styles.interestCard,
                    selected && styles.interestCardSelected,
                    pressed && styles.pressed,
                  ]}
                >
                  <View style={[styles.interestIcon, selected && styles.interestIconSelected]}>
                    <Ionicons
                      name={interest.icon}
                      size={25}
                      color={selected ? colors.white : colors.primary}
                    />
                  </View>
                  <Text style={[styles.interestLabel, selected && styles.interestLabelSelected]}>
                    {interest.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <Button
            label="Continuar"
            disabled={selectedInterests.length === 0}
            onPress={() => setStep(1)}
          />
        </View>
      ) : (
        <View style={styles.content}>
          <View style={styles.heading}>
            <Text style={styles.title}>Qual é o seu orçamento habitual?</Text>
            <Text style={styles.subtitle}>
              Use uma estimativa para um dia de passeio. Você poderá alterar depois.
            </Text>
          </View>

          <Card style={styles.budgetCard}>
            <View style={styles.budgetIcon}>
              <Ionicons name="wallet-outline" size={28} color={colors.actionPressed} />
            </View>
            <View style={styles.currencySection}>
              <Text style={styles.currencyTitle}>Escolha a moeda</Text>
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
                      <Text
                        numberOfLines={1}
                        style={[styles.currencyLabel, selected && styles.currencyTextSelected]}
                      >
                        {option.label}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
            </View>
            <Input
              label="Valor diário"
              placeholder="Ex.: 250,00"
              keyboardType="decimal-pad"
              value={budget}
              onChangeText={setBudget}
              error={budget.length > 0 && !validBudget ? 'Informe um valor válido.' : undefined}
            />
          </Card>

          {mutation.isError ? <Text style={styles.error}>{getErrorMessage(mutation.error)}</Text> : null}
          <Button
            label={editing ? 'Atualizar perfil' : 'Concluir meu perfil'}
            loading={mutation.isPending}
            disabled={!validBudget}
            onPress={() => mutation.mutate()}
          />
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { flexGrow: 1, gap: spacing.lg, paddingBottom: spacing.xl },
  topBar: { width: '100%', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  iconButton: {
    width: 42,
    height: 42,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  iconButtonPlaceholder: { width: 42, height: 42 },
  progress: { flexDirection: 'row', gap: spacing.xs, alignSelf: 'center' },
  progressItem: { width: 44, height: 5, borderRadius: radii.pill, backgroundColor: colors.border },
  progressItemActive: { backgroundColor: colors.action },
  content: { width: '100%', gap: spacing.lg },
  heading: { alignItems: 'center', gap: spacing.xs },
  eyebrow: { ...typography.label, color: colors.action, textAlign: 'center' },
  title: { ...typography.heading, color: colors.primary, textAlign: 'center' },
  subtitle: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  interestsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  interestCard: {
    width: '48%',
    height: 116,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    padding: spacing.md,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  interestCardSelected: { borderColor: colors.action, backgroundColor: '#F0FBFA' },
  interestIcon: {
    width: 48,
    height: 48,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.pill,
    backgroundColor: colors.primarySoft,
  },
  interestIconSelected: { backgroundColor: colors.action },
  interestLabel: { ...typography.label, color: colors.primary, textAlign: 'center' },
  interestLabelSelected: { color: colors.actionPressed },
  pressed: { opacity: 0.76 },
  budgetCard: { width: '100%', padding: spacing.xl },
  budgetIcon: {
    width: 58,
    height: 58,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.pill,
    backgroundColor: '#E5F7F6',
  },
  currencySection: { width: '100%', gap: spacing.sm },
  currencyTitle: { ...typography.label, color: colors.primary, textAlign: 'center' },
  currencyOptions: { width: '100%', flexDirection: 'row', gap: spacing.xs },
  currencyOption: {
    flex: 1,
    minHeight: 72,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xxs,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  currencyOptionSelected: { borderColor: colors.action, backgroundColor: colors.action },
  currencySymbol: { ...typography.title, color: colors.primary },
  currencyLabel: { ...typography.caption, color: colors.textSecondary, fontSize: 11 },
  currencyTextSelected: { color: colors.white },
  error: { ...typography.caption, color: colors.error, textAlign: 'center' },
});
