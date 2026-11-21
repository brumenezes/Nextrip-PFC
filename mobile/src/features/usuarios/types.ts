export type CreateUserRequest = {
  nome: string;
  email: string;
  senha: string;
};

export type UserResponse = {
  id: string;
  nome: string;
  email: string;
};

export type ChangePasswordRequest = {
  senha_atual: string;
  nova_senha: string;
};
