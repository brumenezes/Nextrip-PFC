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
