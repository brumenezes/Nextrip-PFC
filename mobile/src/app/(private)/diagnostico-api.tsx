import { Ionicons } from '@expo/vector-icons';
import { useMutation } from '@tanstack/react-query';
import { router } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { clearApiActivities, useApiActivities } from '@/api/activity';
import { apiRequest } from '@/api/client';
import { Button, Card, Screen } from '@/components';
import { colors, radii, spacing, typography } from '@/design-system';

type HealthResponse = { status: string; servico: string };

export default function ApiDiagnosticsScreen() {
  const activities = useApiActivities();
  const healthMutation = useMutation({
    mutationFn: () => apiRequest<HealthResponse>('/health'),
  });

  return (
    <Screen scroll contentStyle={styles.screen}>
      <View style={styles.topBar}>
        <Pressable accessibilityRole="button" accessibilityLabel="Voltar" onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={22} color={colors.primary} />
        </Pressable>
        <Text style={styles.topTitle}>Atividade da API</Text>
        <View style={styles.backPlaceholder} />
      </View>

      <Card style={styles.statusCard}>
        <View style={[styles.statusIcon, healthMutation.isSuccess && styles.statusIconSuccess]}>
          <Ionicons
            name={healthMutation.isSuccess ? 'checkmark' : 'server-outline'}
            size={26}
            color={healthMutation.isSuccess ? colors.white : colors.primary}
          />
        </View>
        <Text style={styles.statusTitle}>
          {healthMutation.isSuccess ? 'Backend respondendo' : 'Teste a conexão com o backend'}
        </Text>
        {healthMutation.data ? (
          <Text style={styles.statusText}>{healthMutation.data.servico} · {healthMutation.data.status}</Text>
        ) : null}
        <Button label="Testar backend" loading={healthMutation.isPending} onPress={() => healthMutation.mutate()} />
      </Card>

      <View style={styles.sectionHeader}>
        <View>
          <Text style={styles.sectionTitle}>Requisições recentes</Text>
          <Text style={styles.sectionCaption}>Cada integração usada pelo app aparece aqui.</Text>
        </View>
        {activities.length > 0 ? (
          <Pressable onPress={clearApiActivities} hitSlop={10}>
            <Text style={styles.clearText}>Limpar</Text>
          </Pressable>
        ) : null}
      </View>

      {activities.length === 0 ? (
        <Card style={styles.emptyCard}>
          <Ionicons name="pulse-outline" size={28} color={colors.secondary} />
          <Text style={styles.emptyText}>Use o aplicativo ou teste o backend para acompanhar as chamadas.</Text>
        </Card>
      ) : (
        <View style={styles.activityList}>
          {activities.map((activity) => (
            <Card key={activity.id} style={styles.activityCard}>
              <View style={[styles.activityDot, activity.ok ? styles.dotSuccess : styles.dotError]} />
              <View style={styles.activityContent}>
                <Text style={styles.activityPath} numberOfLines={1}>{activity.method} {activity.path}</Text>
                <Text style={styles.activityMeta}>
                  {activity.status || 'Rede'} · {activity.durationMs} ms · {new Date(activity.timestamp).toLocaleTimeString('pt-BR')}
                </Text>
              </View>
              <Ionicons
                name={activity.ok ? 'checkmark-circle-outline' : 'alert-circle-outline'}
                size={21}
                color={activity.ok ? colors.actionPressed : colors.error}
              />
            </Card>
          ))}
        </View>
      )}
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
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  backPlaceholder: { width: 42 },
  topTitle: { ...typography.title, color: colors.primary, textAlign: 'center' },
  statusCard: { width: '100%' },
  statusIcon: {
    width: 58,
    height: 58,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.lg,
    backgroundColor: colors.primarySoft,
  },
  statusIconSuccess: { backgroundColor: colors.action },
  statusTitle: { ...typography.title, color: colors.primary, textAlign: 'center' },
  statusText: { ...typography.caption, color: colors.textSecondary, textAlign: 'center' },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: spacing.sm },
  sectionTitle: { ...typography.title, color: colors.primary, textAlign: 'left' },
  sectionCaption: { ...typography.caption, color: colors.textSecondary, textAlign: 'left' },
  clearText: { ...typography.label, color: colors.actionPressed },
  emptyCard: { width: '100%', minHeight: 120, justifyContent: 'center' },
  emptyText: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  activityList: { gap: spacing.sm },
  activityCard: { width: '100%', flexDirection: 'row', alignItems: 'center', padding: spacing.md },
  activityDot: { width: 8, height: 8, borderRadius: radii.pill },
  dotSuccess: { backgroundColor: colors.action },
  dotError: { backgroundColor: colors.error },
  activityContent: { flex: 1, justifyContent: 'center' },
  activityPath: { ...typography.label, color: colors.primary, textAlign: 'left' },
  activityMeta: { ...typography.caption, color: colors.textSecondary, textAlign: 'left' },
});
