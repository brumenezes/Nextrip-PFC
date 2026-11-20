import { ActivityIndicator, Pressable, StyleSheet, Text, type PressableProps } from 'react-native';

import { colors, radii, spacing, typography } from '@/design-system';

type ButtonVariant = 'primary' | 'secondary' | 'ghost';

type ButtonProps = PressableProps & {
  label: string;
  loading?: boolean;
  variant?: ButtonVariant;
};

export function Button({ label, loading = false, variant = 'primary', disabled, style, ...props }: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <Pressable
      accessibilityRole="button"
      disabled={isDisabled}
      style={(state) => [
        styles.base,
        styles[variant],
        state.pressed && !isDisabled && styles.pressed,
        isDisabled && styles.disabled,
        typeof style === 'function' ? style(state) : style,
      ]}
      {...props}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'primary' ? colors.white : colors.action} />
      ) : (
        <Text style={[styles.label, variant !== 'primary' && styles.labelSecondary]}>{label}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 58,
    paddingHorizontal: spacing.lg,
    borderRadius: radii.lg,
  },
  primary: { backgroundColor: colors.action },
  secondary: { backgroundColor: colors.primarySoft, borderWidth: 1, borderColor: colors.border },
  ghost: { backgroundColor: colors.transparent },
  pressed: { opacity: 0.82 },
  disabled: { opacity: 0.5 },
  label: {
    ...typography.label,
    color: colors.white,
    includeFontPadding: false,
    textAlign: 'center',
    textAlignVertical: 'center',
  },
  labelSecondary: { color: colors.primary },
});
