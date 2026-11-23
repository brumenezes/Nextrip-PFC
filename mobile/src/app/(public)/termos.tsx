import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Card, Screen } from '@/components';
import { colors, radii, spacing, typography } from '@/design-system';
import { TERMS_SECTIONS, TERMS_VERSION } from '@/legal/terms';

export default function TermsScreen() {
  return (
    <Screen scroll contentStyle={styles.screen}>
      <View style={styles.topBar}>
        <Pressable accessibilityLabel="Voltar" onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={22} color={colors.primary} />
        </Pressable>
        <Text style={styles.topTitle}>Termos e privacidade</Text>
        <View style={styles.placeholder} />
      </View>
      <Text style={styles.version}>Versão {TERMS_VERSION}</Text>
      {TERMS_SECTIONS.map((section) => (
        <Card key={section.title} style={styles.section}>
          <Text style={styles.title}>{section.title}</Text>
          {section.paragraphs.map((paragraph) => (
            <Text key={paragraph} style={styles.paragraph}>{paragraph}</Text>
          ))}
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { gap: spacing.md, paddingBottom: spacing.xl },
  topBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  backButton: {
    width: 42,
    height: 42,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  placeholder: { width: 42 },
  topTitle: { ...typography.title, color: colors.primary },
  version: { ...typography.caption, color: colors.textSecondary, textAlign: 'center' },
  section: { width: '100%', alignItems: 'stretch', gap: spacing.sm },
  title: { ...typography.title, color: colors.primary, textAlign: 'left' },
  paragraph: { ...typography.body, color: colors.textSecondary, textAlign: 'left' },
});

