import { StatusBar } from 'expo-status-bar';
import { Image, StyleSheet, View } from 'react-native';

import { colors } from '@/design-system';

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
});
