import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { FlatList, Linking, Pressable, StyleSheet, Text, View } from 'react-native';

import { getErrorMessage } from '@/api/errors';
import { Card, CategoryBadge, FeedbackState, Loading, Screen } from '@/components';
import { colors, radii, spacing, typography } from '@/design-system';
import { listPointsOfInterest } from '@/features/pontos-interesse/service';
import type { PointOfInterest } from '@/features/pontos-interesse/types';
import { getCategoryPresentation } from '@/features/pontos-interesse/categories';
import { formatCurrency } from '@/utils/formatters';

function PointCard({ point }: { point: PointOfInterest }) {
  const category = getCategoryPresentation(point.categoria);

  return (
    <Card style={styles.card}>
      <View style={styles.iconContainer}>
        <Ionicons name={category.icon} size={24} color={colors.primary} />
      </View>
      <Text style={styles.cardTitle}>{point.nome}</Text>
      <CategoryBadge category={point.categoria} />
      <View style={styles.metadata}>
        <Text style={styles.metadataText}>{formatCurrency(point.preco_estimado)}</Text>
        <Text style={styles.separator}>•</Text>
        <Text style={styles.metadataText}>
          {point.duracao_minutos === null ? 'Duração não informada' : `${point.duracao_minutos} min`}
        </Text>
      </View>
      {point.avaliacao_media !== null ? (
        <View style={styles.rating}>
          <Ionicons name="star" size={16} color={colors.accent} />
          <Text style={styles.metadataText}>{point.avaliacao_media.toFixed(1)}</Text>
        </View>
      ) : null}
    </Card>
  );
}

export default function ExploreScreen() {
  const query = useQuery({ queryKey: ['points-of-interest'], queryFn: listPointsOfInterest });

  if (query.isLoading) return <Screen><Loading message="Buscando lugares…" /></Screen>;

  return (
    <Screen contentStyle={styles.screen}>
      <Text style={styles.title}>Explorar</Text>
      {query.isError ? (
        <FeedbackState
          icon="cloud-offline-outline"
          title="Não foi possível buscar os lugares"
          message={getErrorMessage(query.error)}
          actionLabel="Tentar novamente"
          onAction={() => void query.refetch()}
        />
      ) : query.data?.length === 0 ? (
        <FeedbackState
          icon="compass-outline"
          title="Nenhum lugar disponível"
          message="Ainda não há pontos de interesse cadastrados na API."
        />
      ) : (
        <FlatList
          data={query.data}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <PointCard point={item} />}
          ListFooterComponent={
            <Pressable
              accessibilityRole="link"
              onPress={() => void Linking.openURL('https://www.openstreetmap.org/copyright')}
            >
              <Text style={styles.attribution}>© OpenStreetMap contributors</Text>
            </Pressable>
          }
          contentContainerStyle={styles.list}
          style={styles.listView}
          showsVerticalScrollIndicator={false}
        />
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { gap: spacing.lg, paddingBottom: 0 },
  title: {
    ...typography.heading,
    color: colors.primary,
    textAlign: 'center',
    lineHeight: 34,
    includeFontPadding: false,
  },
  list: { gap: spacing.md, paddingBottom: spacing.xl },
  listView: { flex: 1 },
  card: { width: '100%' },
  iconContainer: {
    width: 46,
    height: 46,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primarySoft,
    borderRadius: radii.pill,
  },
  cardTitle: { ...typography.title, color: colors.primary, textAlign: 'center' },
  metadata: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: spacing.xs },
  metadataText: { ...typography.caption, color: colors.textSecondary, textAlign: 'center' },
  separator: { ...typography.caption, color: colors.border },
  rating: { flexDirection: 'row', alignItems: 'center', gap: spacing.xxs },
  attribution: {
    ...typography.caption,
    color: colors.textSecondary,
    textAlign: 'center',
    paddingTop: spacing.md,
  },
});
