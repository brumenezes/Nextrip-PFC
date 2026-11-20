import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { Link, router } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { StyleSheet, Text, View } from 'react-native';

import { getErrorMessage } from '@/api/errors';
import { sessionStorage } from '@/auth/session-storage';
import { BrandLogo, Button, Input, Screen } from '@/components';
import { colors, spacing, typography } from '@/design-system';
import { registerSchema, type RegisterFormData } from '@/features/usuarios/schemas';
import { createUser } from '@/features/usuarios/service';

export default function RegisterScreen() {
  const { control, handleSubmit, formState: { errors } } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { nome: '', email: '', senha: '', confirmarSenha: '' },
  });
  const mutation = useMutation({
    mutationFn: ({ confirmarSenha: _, ...input }: RegisterFormData) => createUser(input),
    onSuccess: async (user) => {
      await sessionStorage.setKnownDisplayName(user.email, user.nome);
      router.replace({
        pathname: '/(public)/login',
        params: { email: user.email, nome: user.nome },
      });
    },
  });

  return (
    <Screen scroll contentStyle={styles.screen}>
      <BrandLogo size={112} />
      <View style={styles.heading}>
        <Text style={styles.title}>Crie sua conta</Text>
        <Text style={styles.subtitle}>Comece com seus dados básicos. Você poderá definir suas preferências depois.</Text>
      </View>

      <View style={styles.form}>
        <Controller control={control} name="nome" render={({ field: { onBlur, onChange, value } }) => (
          <Input label="Nome" placeholder="Seu nome" autoComplete="name" value={value} onBlur={onBlur} onChangeText={onChange} error={errors.nome?.message} />
        )} />
        <Controller control={control} name="email" render={({ field: { onBlur, onChange, value } }) => (
          <Input label="E-mail" placeholder="voce@exemplo.com" keyboardType="email-address" autoCapitalize="none" autoComplete="email" value={value} onBlur={onBlur} onChangeText={onChange} error={errors.email?.message} />
        )} />
        <Controller control={control} name="senha" render={({ field: { onBlur, onChange, value } }) => (
          <Input label="Senha" placeholder="Mínimo de 8 caracteres" secureTextEntry autoComplete="new-password" value={value} onBlur={onBlur} onChangeText={onChange} error={errors.senha?.message} />
        )} />
        <Controller control={control} name="confirmarSenha" render={({ field: { onBlur, onChange, value } }) => (
          <Input label="Confirmar senha" placeholder="Repita sua senha" secureTextEntry autoComplete="new-password" value={value} onBlur={onBlur} onChangeText={onChange} error={errors.confirmarSenha?.message} />
        )} />
        {mutation.error ? <Text style={styles.apiError}>{getErrorMessage(mutation.error)}</Text> : null}
        <Button label="Criar conta" loading={mutation.isPending} onPress={() => void handleSubmit((data) => mutation.mutate(data))()} />
      </View>

      <Text style={styles.footer}>
        Já tem uma conta?{' '}<Link href="/(public)/login" style={styles.link}>Entrar</Link>
      </Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { flexGrow: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.xl, paddingVertical: spacing.xxl },
  heading: { alignItems: 'center', gap: spacing.sm, maxWidth: 440 },
  title: { ...typography.display, color: colors.primary, textAlign: 'center' },
  subtitle: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  form: { width: '100%', maxWidth: 440, gap: spacing.md },
  apiError: { ...typography.caption, color: colors.error, backgroundColor: colors.errorSoft, padding: spacing.sm, borderRadius: 8, textAlign: 'center' },
  footer: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  link: { color: colors.action, fontFamily: 'Inter_600SemiBold' },
});
