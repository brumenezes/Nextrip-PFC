import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';
import { Card, CategoryBadge, FeedbackState, Loading, Screen } from '@/components';
import { colors, radii, spacing, typography } from '@/design-system';
import { getPreferredCurrency } from '@/features/preferencias/currency-storage';
import { getExchangeRates } from '@/features/preferencias/exchange-rates';
import { getItinerary } from '@/features/roteiros/service';
import type { ItineraryActivity } from '@/features/roteiros/types';
import { formatBrlInCurrency, formatCivilDate } from '@/utils/formatters';

function formatDistance(meters: number) {
  if (meters < 1000) return `${Math.round(meters)} m`;
  return `${(meters / 1000).toFixed(1).replace('.', ',')} km`;
}

function ActivityItem({ activity, isLast }: { activity: ItineraryActivity; isLast: boolean }) {
  return (
    <View style={styles.timelineRow}>
      <View style={styles.timelineRail}>
        <View style={styles.orderCircle}>
          <Text style={styles.orderText}>{activity.ordem_sequencia}</Text>
        </View>
        {!isLast ? <View style={styles.timelineLine} /> : null}
      </View>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`Abrir detalhes de ${activity.nome}`}
        onPress={() => router.push({ pathname: '/(private)/atracoes/[id]', params: { id: activity.poi_id } })}
        style={({ pressed }) => [styles.activityPressable, pressed && styles.pressed]}
      >
        <Card style={styles.activityCard}>
          <View style={styles.activityHeader}>
            <View style={styles.activityText}>
              <Text style={styles.activityName}>{activity.nome}</Text>
              <CategoryBadge category={activity.categoria} />
            </View>
            <Ionicons name="chevron-forward" size={18} color={colors.actionPressed} />
          </View>
          <View style={styles.activityMeta}>
            <View style={styles.metaItem}>
              <Ionicons name="time-outline" size={16} color={colors.secondary} />
              <Text style={styles.metaText}>{activity.duracao_minutos} min</Text>
            </View>
            <View style={styles.metaItem}>
              <Ionicons name="walk-outline" size={16} color={colors.accent} />
              <Text style={styles.metaText}>{activity.tempo_deslocamento_previsto} min</Text>
            </View>
            <View style={styles.metaItem}>
              <Ionicons name="navigate-outline" size={16} color={colors.actionPressed} />
              <Text style={styles.metaText}>{formatDistance(activity.distancia_deslocamento_metros)}</Text>
            </View>
          </View>
        </Card>
      </Pressable>
    </View>
  );
}

export default function ItineraryDetailsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { userId } = useAuth();
  const query = useQuery({
    queryKey: ['itinerary', id],
    queryFn: () => getItinerary(id!),
    enabled: Boolean(id),
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

  if (query.isLoading) return <Screen><Loading message="Carregando roteiro…" /></Screen>;

  if (query.isError || !query.data) {
    return (
      <Screen contentStyle={styles.centered}>
        <FeedbackState
          icon="map-outline"
          title="Não foi possível abrir este roteiro"
          message="Tente novamente ou volte para seus roteiros."
          actionLabel="Voltar"
          onAction={() => router.back()}
        />
      </Screen>
    );
  }

  const itinerary = query.data;
  const activities = itinerary.dias.flatMap((day) => day.atividades);
  const visitMinutes = activities.reduce((total, activity) => total + activity.duracao_minutos, 0);
  const travelMinutes = activities.reduce((total, activity) => total + activity.tempo_deslocamento_previsto, 0);
  const currency = currencyQuery.data ?? 'BRL';

  return (
    <Screen scroll contentStyle={styles.screen}>
      <View style={styles.topBar}>
        <Pressable accessibilityRole="button" accessibilityLabel="Voltar" onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={22} color={colors.primary} />
        </Pressable>
        <Text style={styles.topTitle}>Seu roteiro</Text>
        <View style={styles.backPlaceholder} />
      </View>

      <View style={styles.heading}>
        <Text style={styles.date}>{formatCivilDate(itinerary.data_inicio)}</Text>
        <Text style={styles.subtitle}>{activities.length} atrações organizadas para o seu dia</Text>
      </View>

      <View style={styles.summaryGrid}>
        <Card style={styles.summaryCard}>
          <Ionicons name="ticket-outline" size={22} color={colors.actionPressed} />
          <Text style={styles.summaryValue}>
            {formatBrlInCurrency(itinerary.custo_total_estimado, currency, exchangeRatesQuery.data)}
          </Text>
          <Text style={styles.summaryLabel}>Custo estimado</Text>
        </Card>
        <Card style={styles.summaryCard}>
          <Ionicons name="time-outline" size={22} color={colors.secondary} />
          <Text style={styles.summaryValue}>{visitMinutes + travelMinutes} min</Text>
          <Text style={styles.summaryLabel}>Tempo total</Text>
        </Card>
      </View>

      <View style={styles.sectionHeading}>
        <Text style={styles.sectionTitle}>Paradas do roteiro</Text>
        <Text style={styles.sectionCaption}>Na ordem recomendada</Text>
      </View>

      <View style={styles.timeline}>
        {activities.map((activity, index) => (
          <ActivityItem
            key={`${activity.poi_id}-${activity.ordem_sequencia}`}
            activity={activity}
            isLast={index === activities.length - 1}
          />
        ))}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { gap: spacing.lg, paddingBottom: spacing.xl },
  centered: { justifyContent: 'center' },
  topBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  backButton: {
    width: 42,
    height: 42,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  backPlaceholder: { width: 42 },
  topTitle: { ...typography.title, color: colors.primary, textAlign: 'center' },
  heading: { alignItems: 'center', gap: spacing.xs },
  date: { ...typography.heading, color: colors.primary, textAlign: 'center' },
  subtitle: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  summaryGrid: { flexDirection: 'row', gap: spacing.sm },
  summaryCard: { flex: 1, minHeight: 126, justifyContent: 'center', padding: spacing.md },
  summaryValue: { ...typography.label, color: colors.primary, textAlign: 'center' },
  summaryLabel: { ...typography.caption, color: colors.textSecondary, textAlign: 'center' },
  sectionHeading: { gap: spacing.xxs },
  sectionTitle: { ...typography.title, color: colors.primary, textAlign: 'left' },
  sectionCaption: { ...typography.caption, color: colors.textSecondary, textAlign: 'left' },
  timeline: { width: '100%' },
  timelineRow: { flexDirection: 'row', alignItems: 'stretch' },
  timelineRail: { width: 42, alignItems: 'center' },
  orderCircle: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.pill,
    backgroundColor: colors.primary,
  },
  orderText: { ...typography.label, color: colors.white, textAlign: 'center' },
  timelineLine: { width: 2, flex: 1, minHeight: spacing.lg, backgroundColor: colors.border },
  activityPressable: { flex: 1, marginBottom: spacing.md, borderRadius: radii.lg },
  pressed: { opacity: 0.72 },
  activityCard: { width: '100%', alignItems: 'stretch', padding: spacing.md },
  activityHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  activityText: { flex: 1, alignItems: 'flex-start', gap: spacing.xs },
  activityName: { ...typography.label, color: colors.primary, textAlign: 'left' },
  activityMeta: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.xxs },
  metaText: { ...typography.caption, color: colors.textSecondary },
});
