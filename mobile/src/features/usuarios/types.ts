export type CreateUserRequest = {
  nome: string;
  email: string;
  senha: string;
  aceita_termos: boolean;
  aceita_privacidade: boolean;
};

export type UserResponse = {
  id: string;
  nome: string;
  email: string;
  termos_versao?: string;
  termos_aceitos_em?: string | null;
  privacidade_versao?: string;
  privacidade_aceita_em?: string | null;
};

export type UpdateUserRequest = {
  nome: string;
  email: string;
};

export type ChangePasswordRequest = {
  senha_atual: string;
  nova_senha: string;
};
