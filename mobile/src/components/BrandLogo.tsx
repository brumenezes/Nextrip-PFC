import { Image, StyleSheet, type ImageStyle, type StyleProp } from 'react-native';

import { radii } from '@/design-system';

type BrandLogoProps = {
  size?: number;
  style?: StyleProp<ImageStyle>;
};

export function BrandLogo({ size = 128, style }: BrandLogoProps) {
  return (
    <Image
      accessibilityLabel="Logo Nextrip"
      resizeMode="cover"
      source={require('../../assets/nextrip-logo.png')}
      style={[styles.logo, { width: size, height: size }, style]}
    />
  );
}

const styles = StyleSheet.create({
  logo: { borderRadius: radii.lg },
});
