import { StatusBar } from 'expo-status-bar';
import { Image, StyleSheet, Text, View } from 'react-native';

import { colors, spacing, typography } from '@/design-system';

export function AppLoading() {
  return (
    <View style={styles.container} accessibilityLabel="Nextrip">
      <StatusBar style="light" />
      <Image
        accessibilityIgnoresInvertColors
        resizeMode="cover"
        source={require('../../assets/nextrip-logo.png')}
        style={styles.logo}
      />
      <Text style={styles.brandName}>nextrip</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
  },
  logo: { width: 164, height: 164, borderRadius: 28 },
  brandName: {
    ...typography.heading,
    marginTop: spacing.md,
    minHeight: 44,
    paddingBottom: spacing.xs,
    lineHeight: 38,
    color: colors.white,
    letterSpacing: 1.5,
    textAlign: 'center',
  },
});
