import { Ionicons } from '@expo/vector-icons';
import { Redirect, Tabs } from 'expo-router';
import { Platform, StyleSheet, Text, View } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';
import { AppLoading } from '@/components';
import { colors, radii, spacing } from '@/design-system';

const icons = {
  index: ['home-outline', 'home'] as const,
  explorar: ['compass-outline', 'compass'] as const,
  roteiros: ['map-outline', 'map'] as const,
  perfil: ['person-outline', 'person'] as const,
};

const labels = {
  index: 'Início',
  explorar: 'Explorar',
  roteiros: 'Roteiros',
  perfil: 'Perfil',
} as const;

export default function TabsLayout() {
  const { token, isRestoring } = useAuth();

  if (isRestoring) return <AppLoading />;
  if (!token) return <Redirect href="/(public)/login" />;

  return (
    <Tabs
      screenOptions={({ route }) => {
        const routeIcons = icons[route.name as keyof typeof icons] ?? icons.index;
        const routeLabel = labels[route.name as keyof typeof labels] ?? '';

        return {
          headerShown: false,
          tabBarActiveTintColor: colors.white,
          tabBarInactiveTintColor: colors.white,
          tabBarActiveBackgroundColor: colors.transparent,
          tabBarLabelPosition: 'below-icon' as const,
          tabBarLabel: ({ focused }) => (
            <Text numberOfLines={1} style={[styles.label, focused && styles.labelActive]}>
              {routeLabel}
            </Text>
          ),
          tabBarStyle: {
            backgroundColor: colors.navigation,
            borderTopWidth: 0,
            height: Platform.OS === 'ios' ? 84 : 76,
            marginHorizontal: spacing.sm,
            marginBottom: spacing.xs,
            borderRadius: radii.lg,
            overflow: 'hidden' as const,
            paddingTop: spacing.xs,
            paddingBottom: Platform.OS === 'ios' ? spacing.sm : spacing.xs,
          },
          tabBarItemStyle: {
            paddingVertical: 2,
          },
          tabBarHideOnKeyboard: true,
          tabBarIcon: ({ focused }) => (
            <View style={[styles.iconHighlight, focused && styles.iconHighlightActive]}>
              <Ionicons
                name={routeIcons[focused ? 1 : 0]}
                color={colors.white}
                size={22}
              />
            </View>
          ),
        };
      }}
    >
      <Tabs.Screen name="index" options={{ title: 'Início' }} />
      <Tabs.Screen name="explorar" options={{ title: 'Explorar' }} />
      <Tabs.Screen name="roteiros" options={{ title: 'Roteiros' }} />
      <Tabs.Screen name="perfil" options={{ title: 'Perfil' }} />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  iconHighlight: {
    width: 42,
    height: 34,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.md,
  },
  iconHighlightActive: {
    backgroundColor: colors.action,
  },
  label: {
    maxWidth: 72,
    fontFamily: 'Inter_500Medium',
    fontSize: 11,
    lineHeight: 16,
    color: colors.white,
    includeFontPadding: false,
    textAlign: 'center',
  },
  labelActive: {
    fontFamily: 'Inter_600SemiBold',
  },
});
