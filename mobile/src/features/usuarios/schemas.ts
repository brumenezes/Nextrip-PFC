import { z } from 'zod';

export const registerSchema = z
  .object({
    nome: z.string().trim().min(2, 'Use pelo menos 2 caracteres.').max(150, 'Use no máximo 150 caracteres.'),
    email: z.email('Informe um e-mail válido.'),
    senha: z.string().min(8, 'A senha deve ter pelo menos 8 caracteres.'),
    confirmarSenha: z.string().min(1, 'Confirme sua senha.'),
  })
  .refine((data) => data.senha === data.confirmarSenha, {
    message: 'As senhas não coincidem.',
    path: ['confirmarSenha'],
  });

export type RegisterFormData = z.infer<typeof registerSchema>;

export const changePasswordSchema = z
  .object({
    senha_atual: z.string().min(1, 'Informe sua senha atual.'),
    nova_senha: z.string().min(8, 'A nova senha deve ter pelo menos 8 caracteres.'),
    confirmar_senha: z.string().min(1, 'Confirme a nova senha.'),
  })
  .refine((data) => data.nova_senha === data.confirmar_senha, {
    message: 'As senhas não coincidem.',
    path: ['confirmar_senha'],
  })
  .refine((data) => data.nova_senha !== data.senha_atual, {
    message: 'A nova senha deve ser diferente da senha atual.',
    path: ['nova_senha'],
  });

export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;
