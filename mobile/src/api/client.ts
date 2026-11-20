import { env } from '@/config/env';

import { ApiError, type ValidationIssue } from './errors';

const REQUEST_TIMEOUT_MS = 15_000;

let accessToken: string | null = null;
let unauthorizedHandler: (() => void) | null = null;

export function configureApiSession(options: { token: string | null; onUnauthorized?: () => void }) {
  accessToken = options.token;
  unauthorizedHandler = options.onUnauthorized ?? null;
}

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown;
  authenticated?: boolean;
};

type ErrorPayload = {
  detail?: string | ValidationIssue[];
};

async function parseResponse(response: Response) {
  const text = await response.text();
  if (!text) return undefined;

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const headers = new Headers(options.headers);

  headers.set('Accept', 'application/json');
  if (options.body !== undefined) headers.set('Content-Type', 'application/json');
  if (options.authenticated) {
    if (!accessToken) throw new ApiError('Sessão não autenticada.', 401);
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  try {
    const response = await fetch(`${env.apiUrl}${path}`, {
      ...options,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      headers,
      signal: controller.signal,
    });
    const payload = await parseResponse(response);

    if (!response.ok) {
      const detail = (payload as ErrorPayload | undefined)?.detail;
      const issues = Array.isArray(detail) ? detail : [];
      const message =
        typeof detail === 'string'
          ? detail
          : issues[0]?.msg ?? `A API respondeu com o status ${response.status}.`;

      if (response.status === 401 && options.authenticated) unauthorizedHandler?.();
      throw new ApiError(message, response.status, issues);
    }

    return payload as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiError('A API demorou para responder. Tente novamente.', 408);
    }
    throw new ApiError('Não foi possível conectar à API. Verifique sua rede e a URL configurada.', 0);
  } finally {
    clearTimeout(timeout);
  }
}
