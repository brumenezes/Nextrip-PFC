export type LoginRequest = {
  email: string;
  senha: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: 'bearer';
};
