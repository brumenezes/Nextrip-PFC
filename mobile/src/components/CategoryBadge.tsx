import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, Text, View, type ViewStyle } from 'react-native';

import { colors, radii, spacing, typography } from '@/design-system';
import { getCategoryPresentation } from '@/features/pontos-interesse/categories';

type CategoryBadgeProps = {
  category: string | null | undefined;
  style?: ViewStyle;
};

export function CategoryBadge({ category, style }: CategoryBadgeProps) {
  const presentation = getCategoryPresentation(category);

  return (
    <View style={[styles.badge, style]}>
      <Ionicons name={presentation.icon} size={15} color={colors.actionPressed} />
      <Text style={styles.label}>{presentation.label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'center',
    gap: spacing.xxs,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: radii.pill,
    backgroundColor: '#E5F7F6',
  },
  label: { ...typography.caption, color: colors.actionPressed },
});
