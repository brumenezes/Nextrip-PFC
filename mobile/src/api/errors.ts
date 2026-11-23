export type ValidationIssue = {
  loc?: (string | number)[];
  msg?: string;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly issues: ValidationIssue[] = [],
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function getErrorMessage(error: unknown) {
  if (error instanceof ApiError || error instanceof Error) return error.message;
  return 'Não foi possível concluir a operação.';
}
