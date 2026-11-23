import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, Text, View } from 'react-native';

import { colors, radii, spacing, typography } from '@/design-system';

import type { AttractionMapProps } from './AttractionMap.types';

export type { AttractionMapProps } from './AttractionMap.types';

export function AttractionMap({ latitude, longitude }: AttractionMapProps) {
  return (
    <View style={styles.container}>
      <View style={styles.icon}>
        <Ionicons name="map-outline" size={30} color={colors.primary} />
      </View>
      <Text style={styles.title}>Mapa disponível no aplicativo mobile</Text>
      <Text style={styles.coordinates}>{latitude.toFixed(5)}, {longitude.toFixed(5)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    height: 220,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    borderRadius: radii.lg,
    backgroundColor: colors.primarySoft,
    overflow: 'hidden',
  },
  icon: {
    width: 54,
    height: 54,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.lg,
    backgroundColor: colors.surface,
  },
  title: { ...typography.label, color: colors.primary, textAlign: 'center' },
  coordinates: { ...typography.caption, color: colors.textSecondary, textAlign: 'center' },
});
