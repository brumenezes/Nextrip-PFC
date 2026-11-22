import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { Linking, Platform, Pressable, StyleSheet, Text, View } from 'react-native';

import { AttractionMap, Button, Card, CategoryBadge, FeedbackState, Loading, Screen } from '@/components';
import { useAuth } from '@/auth/AuthProvider';
import { colors, radii, spacing, typography } from '@/design-system';
import { getCategoryPresentation } from '@/features/pontos-interesse/categories';
import { getPointOfInterest } from '@/features/pontos-interesse/service';
import { getPreferredCurrency } from '@/features/preferencias/currency-storage';
import { getExchangeRates } from '@/features/preferencias/exchange-rates';
import { formatBrlInCurrency } from '@/utils/formatters';

export default function AttractionDetailsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { userId } = useAuth();
  const query = useQuery({
    queryKey: ['point-of-interest', id],
    queryFn: () => getPointOfInterest(id!),
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

  async function openMap() {
    if (!query.data) return;
    const { latitude, longitude, nome } = query.data;
    const encodedName = encodeURIComponent(nome);
    const url = Platform.select({
      ios: `http://maps.apple.com/?ll=${latitude},${longitude}&q=${encodedName}`,
      android: `geo:${latitude},${longitude}?q=${latitude},${longitude}(${encodedName})`,
      default: `https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=17/${latitude}/${longitude}`,
    });
    await Linking.openURL(url);
  }

  if (query.isLoading) return <Screen><Loading message="Carregando atração…" /></Screen>;

  if (query.isError || !query.data) {
    return (
      <Screen contentStyle={styles.centered}>
        <FeedbackState
          icon="alert-circle-outline"
          title="Não foi possível abrir esta atração"
          message="Tente novamente ou volte para a lista de lugares."
          actionLabel="Voltar"
          onAction={() => router.back()}
        />
      </Screen>
    );
  }

  const point = query.data;
  const category = getCategoryPresentation(point.categoria);
  const currency = currencyQuery.data ?? 'BRL';
  const admissionPrice = point.preco_estimado === 0
    ? 'Entrada gratuita'
    : formatBrlInCurrency(point.preco_estimado, currency, exchangeRatesQuery.data);

  return (
    <Screen scroll contentStyle={styles.screen}>
      <View style={styles.topBar}>
        <Pressable accessibilityRole="button" accessibilityLabel="Voltar" onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={22} color={colors.primary} />
        </Pressable>
        <Text style={styles.topTitle}>Detalhes</Text>
        <View style={styles.backPlaceholder} />
      </View>

      <View style={styles.heroIcon}>
        <Ionicons name={category.icon} size={42} color={colors.primary} />
      </View>
      <View style={styles.heading}>
        <Text style={styles.title}>{point.nome}</Text>
        <CategoryBadge category={point.categoria} />
      </View>

      <View style={styles.metrics}>
        <Card style={styles.metricCard}>
          <Ionicons name="ticket-outline" size={22} color={colors.actionPressed} />
          <Text style={styles.metricValue}>{admissionPrice}</Text>
        </Card>
        <Card style={styles.metricCard}>
          <Ionicons name="time-outline" size={22} color={colors.secondary} />
          <Text style={styles.metricValue}>
            {point.duracao_minutos === null ? 'Não informada' : `${point.duracao_minutos} min`}
          </Text>
        </Card>
      </View>

      <Card style={styles.locationCard}>
        <AttractionMap
          latitude={point.latitude}
          longitude={point.longitude}
          title={point.nome}
          description={category.label}
        />
        <View style={styles.locationHeader}>
          <Ionicons name="location-outline" size={24} color={colors.accent} />
          <View style={styles.locationText}>
            <Text style={styles.locationTitle}>Localização</Text>
            <Text style={styles.coordinates}>{point.latitude.toFixed(5)}, {point.longitude.toFixed(5)}</Text>
          </View>
        </View>
        <Button label="Abrir no mapa" variant="secondary" onPress={() => void openMap()} />
      </Card>

      {point.avaliacao_media !== null ? (
        <Card style={styles.ratingCard}>
          <Ionicons name="star" size={24} color={colors.accent} />
          <Text style={styles.ratingValue}>{point.avaliacao_media.toFixed(1)}</Text>
          <Text style={styles.ratingLabel}>Avaliação informada pela API</Text>
        </Card>
      ) : null}
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
  heroIcon: {
    width: 88,
    height: 88,
    alignSelf: 'center',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.lg,
    backgroundColor: colors.primarySoft,
  },
  heading: { alignItems: 'center', gap: spacing.sm },
  title: { ...typography.heading, color: colors.primary, textAlign: 'center' },
  metrics: { flexDirection: 'row', gap: spacing.sm },
  metricCard: { flex: 1, minHeight: 112, justifyContent: 'center', padding: spacing.md },
  metricValue: { ...typography.label, color: colors.primary, textAlign: 'center' },
  locationCard: { width: '100%', alignItems: 'stretch' },
  locationHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  locationText: { flex: 1, justifyContent: 'center' },
  locationTitle: { ...typography.label, color: colors.primary, textAlign: 'left' },
  coordinates: { ...typography.caption, color: colors.textSecondary, textAlign: 'left' },
  ratingCard: { width: '100%', flexDirection: 'row', justifyContent: 'center' },
  ratingValue: { ...typography.title, color: colors.primary },
  ratingLabel: { ...typography.caption, color: colors.textSecondary },
});
