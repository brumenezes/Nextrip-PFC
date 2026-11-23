type JwtPayload = {
  sub?: unknown;
};

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function getUserIdFromToken(token: string | null) {
  if (!token) return null;

  try {
    const payloadPart = token.split('.')[1];
    if (!payloadPart) return null;

    const base64 = payloadPart.replace(/-/g, '+').replace(/_/g, '/');
    const paddedBase64 = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=');
    const payload = JSON.parse(atob(paddedBase64)) as JwtPayload;

    return typeof payload.sub === 'string' && UUID_PATTERN.test(payload.sub) ? payload.sub : null;
  } catch {
    return null;
  }
}
