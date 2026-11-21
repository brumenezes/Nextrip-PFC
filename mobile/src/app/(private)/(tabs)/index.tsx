import type { ComponentProps } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { getErrorMessage } from '@/api/errors';
import { useAuth } from '@/auth/AuthProvider';
import {
  AppLoading,
  BrandLogo,
  Card,
  CategoryBadge,
  FeedbackState,
  Screen,
} from '@/components';
import { colors, radii, spacing, typography } from '@/design-system';
import { getCategoryPresentation } from '@/features/pontos-interesse/categories';
import { listPointsOfInterest } from '@/features/pontos-interesse/service';
import { ProfileQuestionnaire } from '@/features/preferencias/ProfileQuestionnaire';
import { getPreferredCurrency } from '@/features/preferencias/currency-storage';
import { getPreferences } from '@/features/preferencias/service';
import { formatCurrency } from '@/utils/formatters';

type IconName = ComponentProps<typeof Ionicons>['name'];

type QuickActionProps = {
  icon: IconName;
  label: string;
  color: string;
  onPress: () => void;
};

function QuickAction({ icon, label, color, onPress }: QuickActionProps) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.quickAction, pressed && styles.pressed]}
    >
      <View style={[styles.quickIcon, { backgroundColor: color }]}>
        <Ionicons name={icon} size={20} color={colors.white} />
      </View>
      <Text numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.75} style={styles.quickLabel}>
        {label}
      </Text>
    </Pressable>
  );
}

export default function HomeScreen() {
  const { userId, displayName } = useAuth();
  const preferencesQuery = useQuery({
    queryKey: ['preferences', userId],
    queryFn: () => getPreferences(userId!),
    enabled: Boolean(userId),
  });
  const pointsQuery = useQuery({
    queryKey: ['points-of-interest'],
    queryFn: listPointsOfInterest,
  });
  const currencyQuery = useQuery({
    queryKey: ['preferences-currency', userId],
    queryFn: () => getPreferredCurrency(userId!),
    enabled: Boolean(userId),
  });
  const featuredPoints = pointsQuery.data?.slice(0, 3) ?? [];

  if (preferencesQuery.isLoading) return <AppLoading />;

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

  if (userId && preferencesQuery.data === null) {
    return <ProfileQuestionnaire preferences={null} />;
  }

  return (
    <Screen scroll contentStyle={styles.screen}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.greeting}>
            {displayName ? `Olá, ${displayName}` : 'Olá!'}
          </Text>
          <Text style={styles.headerSubtitle}>O que vamos descobrir hoje?</Text>
        </View>
      </View>

      <View style={styles.quickActions}>
        <QuickAction
          icon="compass-outline"
          label="Explorar"
          color={colors.secondary}
          onPress={() => router.navigate('/(private)/(tabs)/explorar')}
        />
        <QuickAction
          icon="map-outline"
          label="Novo roteiro"
          color={colors.action}
          onPress={() => router.push('/(private)/novo-roteiro')}
        />
        <QuickAction
          icon="calendar-outline"
          label="Roteiros"
          color={colors.accent}
          onPress={() => router.navigate('/(private)/(tabs)/roteiros')}
        />
      </View>

      <Card style={styles.hero}>
        <View style={styles.heroText}>
          <Text style={styles.heroEyebrow}>Nextrip</Text>
          <Text style={styles.heroTitle}>Seu próximo passeio começa aqui.</Text>
          <Text style={styles.heroSubtitle}>
            Descubra lugares incríveis e viva experiências feitas para você.
          </Text>
        </View>
        <BrandLogo size={76} style={styles.heroLogo} />
      </Card>

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Seu perfil de viagem</Text>
          <Pressable onPress={() => router.navigate('/(private)/(tabs)/perfil')} hitSlop={8}>
            <Text style={styles.sectionLink}>Ver perfil</Text>
          </Pressable>
        </View>
        <Card style={styles.profileCard}>
          <View style={styles.profileSummary}>
            <View style={styles.profileIcon}>
              <Ionicons name="wallet-outline" size={22} color={colors.actionPressed} />
            </View>
            <View style={styles.profileText}>
              <Text style={styles.profileCaption}>Orçamento diário</Text>
              <Text style={styles.profileValue}>
                {formatCurrency(
                  preferencesQuery.data?.orcamento_maximo ?? null,
                  currencyQuery.data ?? 'BRL',
                )}
              </Text>
            </View>
          </View>
          <View style={styles.interestList}>
            {preferencesQuery.data?.interesses.map((interest) => (
              <CategoryBadge key={interest} category={interest} />
            ))}
          </View>
        </Card>
      </View>

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>Lugares para explorar</Text>
            {pointsQuery.data ? (
              <Text style={styles.sectionCaption}>{pointsQuery.data.length} lugares disponíveis</Text>
            ) : null}
          </View>
          <Pressable onPress={() => router.navigate('/(private)/(tabs)/explorar')} hitSlop={8}>
            <Text style={styles.sectionLink}>Ver todos</Text>
          </Pressable>
        </View>

        {featuredPoints.length > 0 ? (
          <View style={styles.places}>
            {featuredPoints.map((point) => {
              const category = getCategoryPresentation(point.categoria);

              return (
                <Pressable
                  key={point.id}
                  onPress={() => router.navigate('/(private)/(tabs)/explorar')}
                  style={({ pressed }) => [styles.placeCard, pressed && styles.pressed]}
                >
                  <View style={styles.placeIcon}>
                    <Ionicons name={category.icon} size={20} color={colors.accent} />
                  </View>
                  <View style={styles.placeText}>
                    <Text style={styles.placeName} numberOfLines={2}>{point.nome}</Text>
                    <Text style={styles.placeDetail}>
                      {category.label} · {point.duracao_minutos === null
                        ? 'Duração não informada'
                        : `${point.duracao_minutos} min`}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={18} color={colors.textSecondary} />
                </Pressable>
              );
            })}
          </View>
        ) : (
          <Card style={styles.emptyCard}>
            <Ionicons name="compass-outline" size={26} color={colors.secondary} />
            <Text style={styles.emptyText}>
              {pointsQuery.isLoading
                ? 'Carregando lugares…'
                : pointsQuery.isError
                  ? 'Não foi possível carregar os lugares agora.'
                  : 'Os lugares cadastrados aparecerão aqui.'}
            </Text>
          </Card>
        )}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { gap: spacing.lg, paddingBottom: spacing.xl },
  centered: { justifyContent: 'center' },
  header: { alignItems: 'flex-start' },
  headerText: { flex: 1, gap: spacing.xxs },
  greeting: { ...typography.heading, color: colors.primary },
  headerSubtitle: { ...typography.body, color: colors.textSecondary },
  quickActions: { flexDirection: 'row', gap: spacing.sm },
  quickAction: {
    flex: 1,
    height: 88,
    minWidth: 0,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.xs,
    paddingVertical: spacing.sm,
    borderRadius: radii.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  quickIcon: {
    width: 34,
    height: 34,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.md,
  },
  quickLabel: {
    ...typography.label,
    width: '100%',
    color: colors.primary,
    fontSize: 12,
    lineHeight: 18,
    includeFontPadding: false,
    textAlign: 'center',
    textAlignVertical: 'center',
  },
  pressed: { opacity: 0.72 },
  hero: {
    width: '100%',
    minHeight: 170,
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: colors.primary,
    borderColor: colors.primary,
    overflow: 'hidden',
  },
  heroText: { flex: 1, alignItems: 'flex-start', gap: spacing.xs },
  heroEyebrow: { ...typography.label, color: colors.action },
  heroTitle: { ...typography.title, color: colors.white, textAlign: 'left' },
  heroSubtitle: { ...typography.caption, color: '#DCE8F4', textAlign: 'left' },
  heroLogo: { opacity: 0.92 },
  section: { width: '100%', gap: spacing.sm },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: spacing.sm },
  sectionTitle: { ...typography.title, color: colors.primary },
  sectionCaption: { ...typography.caption, color: colors.textSecondary },
  sectionLink: { ...typography.label, color: colors.actionPressed },
  profileCard: { width: '100%', alignItems: 'stretch' },
  profileSummary: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  profileIcon: {
    width: 46,
    height: 46,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.pill,
    backgroundColor: '#E5F7F6',
  },
  profileText: { flex: 1 },
  profileCaption: { ...typography.caption, color: colors.textSecondary, textAlign: 'left' },
  profileValue: { ...typography.title, color: colors.primary, textAlign: 'left' },
  interestList: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: spacing.xs },
  places: { gap: spacing.sm },
  placeCard: {
    minHeight: 78,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    padding: spacing.md,
    borderRadius: radii.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  placeIcon: {
    width: 42,
    height: 42,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.pill,
    backgroundColor: '#FFF5E8',
  },
  placeText: { flex: 1 },
  placeName: { ...typography.label, color: colors.primary, textAlign: 'left' },
  placeDetail: { ...typography.caption, color: colors.textSecondary, textAlign: 'left' },
  emptyCard: { width: '100%', minHeight: 110 },
  emptyText: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
});
