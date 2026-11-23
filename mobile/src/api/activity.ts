import { useSyncExternalStore } from 'react';

export type ApiActivity = {
  id: number;
  method: string;
  path: string;
  status: number;
  ok: boolean;
  durationMs: number;
  timestamp: number;
};

let activities: ApiActivity[] = [];
let nextId = 1;
const listeners = new Set<() => void>();

export function recordApiActivity(activity: Omit<ApiActivity, 'id' | 'timestamp'>) {
  activities = [
    { ...activity, id: nextId++, timestamp: Date.now() },
    ...activities,
  ].slice(0, 50);
  listeners.forEach((listener) => listener());
}

export function clearApiActivities() {
  activities = [];
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useApiActivities() {
  return useSyncExternalStore(subscribe, () => activities, () => activities);
}
