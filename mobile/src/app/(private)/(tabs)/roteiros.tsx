import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';

import { getErrorMessage } from '@/api/errors';
import { useAuth } from '@/auth/AuthProvider';
import { Button, Card, FeedbackState, Loading, Screen } from '@/components';
import { colors, radii, spacing, typography } from '@/design-system';
import { getPreferredCurrency, type TravelCurrency } from '@/features/preferencias/currency-storage';
import { listItineraries } from '@/features/roteiros/service';
import type { ItinerarySummary } from '@/features/roteiros/types';
import { formatCivilDate, formatCurrency } from '@/utils/formatters';

function ItineraryCard({ itinerary, currency }: { itinerary: ItinerarySummary; currency: TravelCurrency }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`Abrir roteiro de ${formatCivilDate(itinerary.data_inicio)}`}
      onPress={() => router.push({ pathname: '/(private)/roteiros/[id]', params: { id: itinerary.id } })}
      style={({ pressed }) => [styles.cardPressable, pressed && styles.pressed]}
    >
      <Card style={styles.card}>
        <View style={styles.iconContainer}>
          <Ionicons name="map-outline" size={24} color={colors.primary} />
        </View>
        <View style={styles.cardContent}>
          <Text style={styles.cardEyebrow}>ROTEIRO PLANEJADO</Text>
          <Text style={styles.cardTitle}>{formatCivilDate(itinerary.data_inicio)}</Text>
          <Text style={styles.dateRange}>
            {itinerary.data_inicio === itinerary.data_fim
              ? 'Passeio de um dia'
              : `Até ${formatCivilDate(itinerary.data_fim)}`}
          </Text>
          <Text style={styles.cost}>{formatCurrency(itinerary.custo_total_estimado, currency)}</Text>
        </View>
        <View style={styles.chevron}>
          <Ionicons name="chevron-forward" size={20} color={colors.actionPressed} />
        </View>
      </Card>
    </Pressable>
  );
}

export default function ItinerariesScreen() {
  const { userId } = useAuth();
  const query = useQuery({ queryKey: ['itineraries'], queryFn: listItineraries });
  const currencyQuery = useQuery({
    queryKey: ['preferences-currency', userId],
    queryFn: () => getPreferredCurrency(userId!),
    enabled: Boolean(userId),
  });
  const currency = currencyQuery.data ?? 'BRL';

  if (query.isLoading) return <Screen><Loading message="Carregando roteiros…" /></Screen>;

  return (
    <Screen contentStyle={styles.screen}>
      <View style={styles.header}>
        <Text style={styles.title}>Seus roteiros</Text>
        <Text style={styles.subtitle}>Reveja cada parada ou planeje sua próxima experiência.</Text>
      </View>
      <View style={styles.newRouteCard}>
        <View style={styles.newRouteIcon}>
          <Ionicons name="sparkles-outline" size={24} color={colors.white} />
        </View>
        <View style={styles.newRouteText}>
          <Text style={styles.newRouteTitle}>Pronto para um novo passeio?</Text>
          <Text style={styles.newRouteSubtitle}>Crie um roteiro adaptado ao seu perfil.</Text>
        </View>
        <Button label="Criar" onPress={() => router.push('/(private)/novo-roteiro')} style={styles.newRouteButton} />
      </View>
      {query.isError ? (
        <FeedbackState
          icon="cloud-offline-outline"
          title="Não foi possível carregar seus roteiros"
          message={getErrorMessage(query.error)}
          actionLabel="Tentar novamente"
          onAction={() => void query.refetch()}
        />
      ) : query.data?.length === 0 ? (
        <FeedbackState
          icon="map-outline"
          title="Nenhum roteiro salvo"
          message="Seus roteiros gerados aparecerão aqui."
        />
      ) : (
        <FlatList
          data={query.data}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <ItineraryCard itinerary={item} currency={currency} />}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
        />
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { gap: spacing.lg, paddingBottom: 0 },
  header: { alignItems: 'center', gap: spacing.xs },
  title: { ...typography.heading, color: colors.primary, textAlign: 'center' },
  subtitle: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  list: { gap: spacing.md, paddingBottom: spacing.xl },
  newRouteCard: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    padding: spacing.md,
    borderRadius: radii.lg,
    backgroundColor: colors.primary,
  },
  newRouteIcon: {
    width: 46,
    height: 46,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.md,
    backgroundColor: colors.action,
  },
  newRouteText: { flex: 1, justifyContent: 'center' },
  newRouteTitle: { ...typography.label, color: colors.white, textAlign: 'left' },
  newRouteSubtitle: { ...typography.caption, color: '#DCE8F4', textAlign: 'left' },
  newRouteButton: { width: 78, minHeight: 44, paddingHorizontal: spacing.sm, borderRadius: radii.md },
  cardPressable: { width: '100%', borderRadius: radii.lg },
  pressed: { opacity: 0.72 },
  card: { width: '100%', flexDirection: 'row', alignItems: 'center', padding: spacing.md },
  iconContainer: {
    width: 52,
    height: 52,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primarySoft,
    borderRadius: radii.md,
  },
  cardContent: { flex: 1, alignItems: 'flex-start', justifyContent: 'center' },
  cardEyebrow: { ...typography.caption, color: colors.actionPressed, fontSize: 10, textAlign: 'left' },
  cardTitle: { ...typography.title, color: colors.primary, textAlign: 'left' },
  dateRange: { ...typography.caption, color: colors.textSecondary, textAlign: 'left' },
  cost: { ...typography.label, color: colors.actionPressed, textAlign: 'left' },
  chevron: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.pill,
    backgroundColor: '#E5F7F6',
  },
});
