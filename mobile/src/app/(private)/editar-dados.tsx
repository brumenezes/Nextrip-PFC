import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { router } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { getErrorMessage } from '@/api/errors';
import { useAuth } from '@/auth/AuthProvider';
import { Button, Card, Input, Screen } from '@/components';
import { colors, radii, spacing, typography } from '@/design-system';
import { updateUserSchema, type UpdateUserFormData } from '@/features/usuarios/schemas';
import { updateCurrentUser } from '@/features/usuarios/service';

export default function EditUserScreen() {
  const { token, fullName, email, signIn } = useAuth();
  const { control, handleSubmit, formState: { errors } } = useForm<UpdateUserFormData>({
    resolver: zodResolver(updateUserSchema),
    defaultValues: { nome: fullName ?? '', email: email ?? '' },
  });
  const mutation = useMutation({
    mutationFn: updateCurrentUser,
    onSuccess: async (user) => {
      if (token) {
        await signIn(token, {
          displayName: user.nome.trim().split(/\s+/)[0] ?? null,
          fullName: user.nome,
          email: user.email,
        });
      }
      router.back();
    },
  });

  return (
    <Screen scroll contentStyle={styles.screen}>
      <View style={styles.topBar}>
        <Pressable accessibilityLabel="Voltar" onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={22} color={colors.primary} />
        </Pressable>
        <Text style={styles.title}>Editar dados</Text>
        <View style={styles.placeholder} />
      </View>
      <Text style={styles.subtitle}>Atualize apenas os dados necessários para sua conta.</Text>
      <Card style={styles.form}>
        <Controller control={control} name="nome" render={({ field }) => (
          <Input
            label="Nome"
            autoComplete="name"
            value={field.value}
            onBlur={field.onBlur}
            onChangeText={field.onChange}
            error={errors.nome?.message}
          />
        )} />
        <Controller control={control} name="email" render={({ field }) => (
          <Input
            label="E-mail"
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            value={field.value}
            onBlur={field.onBlur}
            onChangeText={field.onChange}
            error={errors.email?.message}
          />
        )} />
      </Card>
      {mutation.isError ? <Text style={styles.error}>{getErrorMessage(mutation.error)}</Text> : null}
      <Button
        label="Salvar alterações"
        loading={mutation.isPending}
        onPress={() => void handleSubmit((data) => mutation.mutate(data))()}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { gap: spacing.lg, paddingBottom: spacing.xl },
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
  title: { ...typography.title, color: colors.primary },
  subtitle: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  form: { width: '100%', alignItems: 'stretch', gap: spacing.md },
  error: { ...typography.caption, color: colors.error, textAlign: 'center' },
});

