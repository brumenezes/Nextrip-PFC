import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { getErrorMessage } from '@/api/errors';
import { useAuth } from '@/auth/AuthProvider';
import { Button, Card, CategoryBadge, FeedbackState, Loading, Screen } from '@/components';
import { colors, radii, spacing, typography } from '@/design-system';
import { ProfileQuestionnaire } from '@/features/preferencias/ProfileQuestionnaire';
import { getPreferredCurrency } from '@/features/preferencias/currency-storage';
import { getExchangeRates } from '@/features/preferencias/exchange-rates';
import { getPreferences } from '@/features/preferencias/service';
import { formatBrlInCurrency } from '@/utils/formatters';

export default function ProfileScreen() {
  const { userId, displayName, fullName, email, signOut } = useAuth();
  const [editing, setEditing] = useState(false);
  useFocusEffect(useCallback(() => {
    setEditing(false);
  }, []));
  const preferencesQuery = useQuery({
    queryKey: ['preferences', userId],
    queryFn: () => getPreferences(userId!),
    enabled: Boolean(userId),
  });
  const currencyQuery = useQuery({
    queryKey: ['preferences-currency', userId],
    queryFn: () => getPreferredCurrency(userId!),
    enabled: Boolean(userId),
  });
  const exchangeRatesQuery = useQuery({
    queryKey: ['exchange-rates', 'BRL'],
    queryFn: getExchangeRates,
    staleTime: 6 * 60 * 60 * 1000,
    retry: 1,
  });

  if (!userId) {
    return (
      <Screen contentStyle={styles.centered}>
        <FeedbackState
          icon="alert-circle-outline"
          title="Identidade indisponível"
          message="O token desta sessão não contém um identificador de usuário válido."
          actionLabel="Entrar novamente"
          onAction={() => void signOut()}
        />
      </Screen>
    );
  }

  if (preferencesQuery.isLoading) {
    return <Screen><Loading message="Carregando seu perfil…" /></Screen>;
  }

  if (preferencesQuery.isError) {
    return (
      <Screen contentStyle={styles.centered}>
        <FeedbackState
          icon="cloud-offline-outline"
          title="Não foi possível carregar seu perfil"
          message={getErrorMessage(preferencesQuery.error)}
          actionLabel="Tentar novamente"
          onAction={() => void preferencesQuery.refetch()}
        />
      </Screen>
    );
  }

  const preferences = preferencesQuery.data;

  if (editing && preferences) {
    return (
      <ProfileQuestionnaire
        preferences={preferences}
        onCancel={() => setEditing(false)}
        onCompleted={() => setEditing(false)}
      />
    );
  }

  return (
    <Screen scroll contentStyle={styles.screen}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Ionicons name="person" size={34} color={colors.white} />
        </View>
        <Text style={styles.title}>Seu perfil</Text>
        <Text style={styles.profileName}>{fullName ?? displayName ?? 'Viajante Nextrip'}</Text>
        {email ? <Text style={styles.profileEmail}>{email}</Text> : null}
        <Text style={styles.subtitle}>
          Suas escolhas ajudam o Nextrip a criar experiências mais alinhadas com você.
        </Text>
      </View>

      <Card style={styles.accountCard}>
        <View style={styles.accountRow}>
          <View style={styles.accountIcon}>
            <Ionicons name="mail-outline" size={21} color={colors.secondary} />
          </View>
          <View style={styles.cardText}>
            <Text style={styles.cardLabel}>Conta</Text>
            <Text style={styles.accountValue}>{email ?? 'E-mail indisponível nesta sessão'}</Text>
          </View>
        </View>
        <View style={styles.accountDivider} />
        <View style={styles.accountRow}>
          <View style={styles.accountIcon}>
            <Ionicons name="language-outline" size={21} color={colors.actionPressed} />
          </View>
          <View style={styles.cardText}>
            <Text style={styles.cardLabel}>Moeda preferida</Text>
            <Text style={styles.accountValue}>{currencyQuery.data ?? 'BRL'}</Text>
          </View>
        </View>
      </Card>

      <Card style={styles.budgetCard}>
        <View style={styles.cardIcon}>
          <Ionicons name="wallet-outline" size={24} color={colors.actionPressed} />
        </View>
        <View style={styles.cardText}>
          <Text style={styles.cardLabel}>Orçamento diário</Text>
          <Text style={styles.budgetValue}>
            {formatBrlInCurrency(
              preferences?.orcamento_maximo ?? null,
              currencyQuery.data ?? 'BRL',
              exchangeRatesQuery.data,
            )}
          </Text>
        </View>
      </Card>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Interesses de viagem</Text>
        <Card style={styles.interestsCard}>
          <View style={styles.interests}>
            {preferences?.interesses.map((interest) => (
              <CategoryBadge key={interest} category={interest} />
            ))}
          </View>
        </Card>
      </View>

      <View style={styles.actions}>
        <Button
          label="Editar dados"
          variant="secondary"
          onPress={() => router.push('/(private)/editar-dados')}
        />
        <Button
          label="Refazer questionário"
          variant="secondary"
          onPress={() => setEditing(true)}
        />
        <Button
          label="Trocar senha"
          variant="secondary"
          onPress={() => router.push('/(private)/trocar-senha')}
        />
        <Button
          label="Ver atividade da API"
          variant="secondary"
          onPress={() => router.push('/(private)/diagnostico-api')}
        />
        <Button label="Sair da conta" variant="ghost" onPress={() => void signOut()} />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { alignItems: 'stretch', gap: spacing.lg, paddingBottom: spacing.xl },
  centered: { justifyContent: 'center' },
  header: { alignItems: 'center', gap: spacing.xs, paddingVertical: spacing.sm },
  avatar: {
    width: 72,
    height: 72,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.pill,
    backgroundColor: colors.primary,
    marginBottom: spacing.xs,
  },
  title: { ...typography.heading, color: colors.primary, textAlign: 'center' },
  profileName: { ...typography.title, color: colors.primary, textAlign: 'center' },
  profileEmail: { ...typography.caption, color: colors.textSecondary, textAlign: 'center' },
  subtitle: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  budgetCard: {
    width: '100%',
    minHeight: 104,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-start',
  },
  accountCard: { width: '100%', alignItems: 'stretch' },
  accountRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  accountIcon: {
    width: 42,
    height: 42,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.md,
    backgroundColor: colors.primarySoft,
  },
  accountDivider: { width: '100%', height: 1, backgroundColor: colors.border },
  accountValue: { ...typography.label, color: colors.primary, textAlign: 'left' },
  cardIcon: {
    width: 52,
    height: 52,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.pill,
    backgroundColor: '#E5F7F6',
  },
  cardText: { flex: 1, alignItems: 'flex-start' },
  cardLabel: { ...typography.caption, color: colors.textSecondary, textAlign: 'left' },
  budgetValue: { ...typography.title, color: colors.primary, textAlign: 'left' },
  section: { gap: spacing.sm },
  sectionTitle: { ...typography.title, color: colors.primary, textAlign: 'left' },
  interestsCard: { width: '100%', alignItems: 'stretch' },
  interests: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: spacing.xs },
  actions: { gap: spacing.xs, marginTop: spacing.sm },
});
