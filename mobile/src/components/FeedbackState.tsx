import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, Text } from 'react-native';

import { colors, spacing, typography } from '@/design-system';

import { Button } from './Button';
import { Card } from './Card';

type FeedbackStateProps = {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
};

export function FeedbackState({ icon, title, message, actionLabel, onAction }: FeedbackStateProps) {
  return (
    <Card style={styles.card}>
      <Ionicons name={icon} size={36} color={colors.secondary} />
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.message}>{message}</Text>
      {actionLabel && onAction ? <Button label={actionLabel} variant="secondary" onPress={onAction} /> : null}
    </Card>
  );
}

const styles = StyleSheet.create({
  card: { width: '100%', paddingVertical: spacing.xl },
  title: { ...typography.title, color: colors.primary, textAlign: 'center' },
  message: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
});
