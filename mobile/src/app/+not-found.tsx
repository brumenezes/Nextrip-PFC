import { router } from 'expo-router';
import { StyleSheet, Text } from 'react-native';

import { Button, Screen } from '@/components';
import { colors, spacing, typography } from '@/design-system';

export default function NotFoundScreen() {
  return (
    <Screen contentStyle={styles.content}>
      <Text style={styles.title}>Página não encontrada</Text>
      <Text style={styles.description}>O caminho solicitado não existe no aplicativo.</Text>
      <Button label="Voltar ao início" onPress={() => router.replace('/')} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: { justifyContent: 'center', gap: spacing.md },
  title: { ...typography.heading, color: colors.text },
  description: { ...typography.body, color: colors.textSecondary, marginBottom: spacing.sm },
});
