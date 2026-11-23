import { Platform, StyleSheet, Text, TextInput, View, type TextInputProps } from 'react-native';

import { colors, radii, spacing, typography } from '@/design-system';

type InputProps = TextInputProps & {
  label: string;
  error?: string;
  hint?: string;
};

export function Input({ label, error, hint, style, ...props }: InputProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        placeholderTextColor={colors.disabled}
        style={[styles.input, error && styles.inputError, style]}
        accessibilityLabel={label}
        {...props}
      />
      {error ? <Text style={styles.error}>{error}</Text> : hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.xs, width: '100%' },
  label: { ...typography.label, color: colors.text, textAlign: 'left' },
  input: {
    ...typography.body,
    fontSize: 15,
    lineHeight: 20,
    height: 54,
    paddingHorizontal: spacing.md,
    paddingTop: Platform.OS === 'ios' ? 13 : 0,
    paddingBottom: Platform.OS === 'ios' ? 17 : 0,
    color: colors.text,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    textAlign: 'left',
    textAlignVertical: 'center',
    includeFontPadding: false,
  },
  inputError: { borderColor: colors.error },
  error: { ...typography.caption, color: colors.error, textAlign: 'center' },
  hint: { ...typography.caption, color: colors.textSecondary, textAlign: 'center' },
});
