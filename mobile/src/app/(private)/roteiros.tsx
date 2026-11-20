import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';
import { FlatList, StyleSheet, Text, View } from 'react-native';

import { getErrorMessage } from '@/api/errors';
import { Button, Card, FeedbackState, Loading, Screen } from '@/components';
import { colors, radii, spacing, typography } from '@/design-system';
import { listItineraries } from '@/features/roteiros/service';
import type { ItinerarySummary } from '@/features/roteiros/types';
import { formatCivilDate, formatCurrency } from '@/utils/formatters';

function ItineraryCard({ itinerary }: { itinerary: ItinerarySummary }) {
  return (
    <Card style={styles.card}>
      <View style={styles.iconContainer}>
        <Ionicons name="map-outline" size={24} color={colors.secondary} />
      </View>
      <Text style={styles.cardTitle}>{formatCivilDate(itinerary.data_inicio)}</Text>
      <Text style={styles.dateRange}>
        {itinerary.data_inicio === itinerary.data_fim
          ? 'Roteiro de um dia'
          : `Até ${formatCivilDate(itinerary.data_fim)}`}
      </Text>
      <Text style={styles.cost}>{formatCurrency(itinerary.custo_total_estimado)}</Text>
    </Card>
  );
}

export default function ItinerariesScreen() {
  const query = useQuery({ queryKey: ['itineraries'], queryFn: listItineraries });

  if (query.isLoading) return <Screen><Loading message="Carregando roteiros…" /></Screen>;

  return (
    <Screen contentStyle={styles.screen}>
      <Text style={styles.title}>Roteiros</Text>
      <Button label="Criar novo roteiro" onPress={() => router.push('/(private)/novo-roteiro')} />
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
          renderItem={({ item }) => <ItineraryCard itinerary={item} />}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
        />
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { gap: spacing.lg, paddingBottom: 0 },
  title: { ...typography.heading, color: colors.primary, textAlign: 'center' },
  list: { gap: spacing.md, paddingBottom: spacing.xl },
  card: { width: '100%' },
  iconContainer: {
    width: 48,
    height: 48,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primarySoft,
    borderRadius: radii.pill,
  },
  cardTitle: { ...typography.title, color: colors.primary, textAlign: 'center' },
  dateRange: { ...typography.caption, color: colors.textSecondary, textAlign: 'center' },
  cost: { ...typography.label, color: colors.action, textAlign: 'center' },
});
