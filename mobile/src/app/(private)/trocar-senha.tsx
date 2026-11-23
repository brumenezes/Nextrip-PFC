import { zodResolver } from '@hookform/resolvers/zod';
import { Ionicons } from '@expo/vector-icons';
import { useMutation } from '@tanstack/react-query';
import { router } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { getErrorMessage } from '@/api/errors';
import { useAuth } from '@/auth/AuthProvider';
import { Button, Card, Input, Screen } from '@/components';
import { colors, radii, spacing, typography } from '@/design-system';
import { changePasswordSchema, type ChangePasswordFormData } from '@/features/usuarios/schemas';
import { changePassword } from '@/features/usuarios/service';

export default function ChangePasswordScreen() {
  const { signOut } = useAuth();
  const { control, handleSubmit, formState: { errors } } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: { senha_atual: '', nova_senha: '', confirmar_senha: '' },
  });
  const mutation = useMutation({
    mutationFn: ({ confirmar_senha: _, ...input }: ChangePasswordFormData) => changePassword(input),
  });

  if (mutation.isSuccess) {
    return (
      <Screen contentStyle={styles.successScreen}>
        <View style={styles.successIcon}>
          <Ionicons name="checkmark" size={34} color={colors.white} />
        </View>
        <Text style={styles.title}>Senha atualizada</Text>
        <Text style={styles.subtitle}>Entre novamente usando sua nova senha.</Text>
        <Button label="Ir para o login" onPress={() => void signOut()} />
      </Screen>
    );
  }

  return (
    <Screen scroll contentStyle={styles.screen}>
      <View style={styles.topBar}>
        <Pressable accessibilityRole="button" accessibilityLabel="Voltar" onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={22} color={colors.primary} />
        </Pressable>
        <Text style={styles.topTitle}>Segurança</Text>
        <View style={styles.backPlaceholder} />
      </View>

      <View style={styles.heading}>
        <View style={styles.lockIcon}>
          <Ionicons name="lock-closed-outline" size={30} color={colors.actionPressed} />
        </View>
        <Text style={styles.title}>Trocar senha</Text>
        <Text style={styles.subtitle}>Use pelo menos 8 caracteres para proteger sua conta.</Text>
      </View>

      <Card style={styles.form}>
        <Controller control={control} name="senha_atual" render={({ field }) => (
          <Input label="Senha atual" secureTextEntry autoComplete="current-password" value={field.value} onChangeText={field.onChange} onBlur={field.onBlur} error={errors.senha_atual?.message} />
        )} />
        <Controller control={control} name="nova_senha" render={({ field }) => (
          <Input label="Nova senha" secureTextEntry autoComplete="new-password" value={field.value} onChangeText={field.onChange} onBlur={field.onBlur} error={errors.nova_senha?.message} />
        )} />
        <Controller control={control} name="confirmar_senha" render={({ field }) => (
          <Input label="Confirmar nova senha" secureTextEntry autoComplete="new-password" value={field.value} onChangeText={field.onChange} onBlur={field.onBlur} error={errors.confirmar_senha?.message} />
        )} />
      </Card>

      {mutation.isError ? <Text style={styles.error}>{getErrorMessage(mutation.error)}</Text> : null}
      <Button
        label="Atualizar senha"
        loading={mutation.isPending}
        onPress={() => void handleSubmit((data) => mutation.mutate(data))()}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { gap: spacing.lg, paddingBottom: spacing.xl },
  successScreen: { justifyContent: 'center', alignItems: 'center', gap: spacing.md },
  topBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  backButton: {
    width: 42,
    height: 42,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  backPlaceholder: { width: 42 },
  topTitle: { ...typography.title, color: colors.primary, textAlign: 'center' },
  heading: { alignItems: 'center', gap: spacing.sm },
  lockIcon: {
    width: 64,
    height: 64,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.lg,
    backgroundColor: '#E5F7F6',
  },
  successIcon: {
    width: 68,
    height: 68,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.pill,
    backgroundColor: colors.action,
  },
  title: { ...typography.heading, color: colors.primary, textAlign: 'center' },
  subtitle: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  form: { width: '100%', alignItems: 'stretch' },
  error: { ...typography.caption, color: colors.error, textAlign: 'center' },
});
