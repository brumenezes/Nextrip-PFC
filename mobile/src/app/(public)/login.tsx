import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { Link, router, useLocalSearchParams } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { StyleSheet, Text, View } from 'react-native';

import { getErrorMessage } from '@/api/errors';
import { useAuth } from '@/auth/AuthProvider';
import { sessionStorage } from '@/auth/session-storage';
import { BrandLogo, Button, Card, Input, Screen } from '@/components';
import { colors, spacing, typography } from '@/design-system';
import { loginSchema, type LoginFormData } from '@/features/auth/schemas';
import { login } from '@/features/auth/service';

export default function LoginScreen() {
  const { email: initialEmail, nome: initialName } = useLocalSearchParams<{
    email?: string;
    nome?: string;
  }>();
  const { signIn } = useAuth();
  const { control, handleSubmit, formState: { errors } } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: initialEmail ?? '', senha: '' },
  });
  const mutation = useMutation({
    mutationFn: login,
    onSuccess: async (response, credentials) => {
      const registeredName = initialName?.trim();
      if (registeredName) {
        await sessionStorage.setKnownDisplayName(credentials.email, registeredName);
      }
      const knownName = registeredName
        || await sessionStorage.getKnownDisplayName(credentials.email);
      const firstName = knownName?.split(/\s+/)[0] ?? null;
      await signIn(response.access_token, firstName);
      router.replace('/(private)');
    },
  });

  return (
    <Screen scroll contentStyle={styles.screen}>
      <BrandLogo size={112} />

      <View style={styles.heading}>
        <Text style={styles.title}>Bem-vindo ao Nextrip</Text>
        <Text style={styles.subtitle}>
          {initialEmail
            ? 'Conta criada! Entre com a senha que você acabou de cadastrar.'
            : 'Use seu e-mail e senha para continuar.'}
        </Text>
      </View>

      <Card style={styles.form}>
        <Controller
          control={control}
          name="email"
          render={({ field: { onBlur, onChange, value } }) => (
            <Input
              label="E-mail"
              placeholder="voce@exemplo.com"
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
              returnKeyType="next"
              value={value}
              onBlur={onBlur}
              onChangeText={onChange}
              error={errors.email?.message}
            />
          )}
        />
        <Controller
          control={control}
          name="senha"
          render={({ field: { onBlur, onChange, value } }) => (
            <Input
              label="Senha"
              placeholder="Sua senha"
              secureTextEntry
              autoComplete="current-password"
              returnKeyType="done"
              value={value}
              onBlur={onBlur}
              onChangeText={onChange}
              onSubmitEditing={() => void handleSubmit((data) => mutation.mutate(data))()}
              error={errors.senha?.message}
            />
          )}
        />
        {mutation.error ? <Text style={styles.apiError}>{getErrorMessage(mutation.error)}</Text> : null}
        <Button label="Entrar" loading={mutation.isPending} onPress={() => void handleSubmit((data) => mutation.mutate(data))()} />
      </Card>

      <View style={styles.footer}>
        <Text style={styles.footerQuestion}>Ainda não tem uma conta?</Text>
        <Link href="/(public)/cadastro" style={styles.link}>Criar conta</Link>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { flexGrow: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.lg, paddingVertical: spacing.xl },
  heading: { alignItems: 'center', gap: spacing.sm, maxWidth: 440 },
  title: { ...typography.heading, color: colors.primary, textAlign: 'center' },
  subtitle: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  form: { width: '100%', maxWidth: 440, gap: spacing.md, padding: spacing.xl },
  apiError: { ...typography.caption, color: colors.error, backgroundColor: colors.errorSoft, padding: spacing.sm, borderRadius: 8, textAlign: 'center' },
  footer: { alignItems: 'center', gap: spacing.xxs },
  footerQuestion: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  link: { ...typography.label, color: colors.action, textAlign: 'center' },
});
