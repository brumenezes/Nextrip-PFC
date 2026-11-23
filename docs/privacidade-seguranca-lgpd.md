# Privacidade e segurança LGPD

## Escopo atual

O NexTrip aplica privacidade desde a concepção ao cadastro, autenticação, preferências e roteiros. Esta documentação é uma base técnica para o protótipo e não substitui avaliação jurídica, relatório de impacto ou políticas organizacionais.

## Dados e finalidades

- Nome e e-mail: identificação, autenticação e comunicação relacionada à conta.
- Hash de senha: autenticação; a senha em texto aberto não é persistida.
- Preferências e orçamento: personalização dos roteiros.
- Origem informada: cálculo do roteiro durante a requisição; não é persistida no modelo atual.
- Roteiros: entrega do serviço e histórico solicitado pelo usuário.
- Versão e instante dos aceites: comprovação do texto apresentado no cadastro.

## Controles implementados

- Senhas protegidas com Argon2 e JWT com expiração.
- Autorização por titular nas preferências e nos roteiros.
- Token mantido em armazenamento seguro no Android e iOS.
- Normalização de nome e e-mail e respostas sem hash de senha.
- Aceites separados e obrigatórios para Termos e Aviso de Privacidade.
- Registro versionado dos aceites em UTC.
- Cabeçalhos contra cache de dados de conta, MIME sniffing, framing e vazamento de referência.
- CORS restrito às origens configuradas.
- Edição autenticada dos dados da própria conta.

## Pendências antes de produção

- Identificar formalmente controlador, operador, encarregado/canal e dados de contato.
- Definir prazos de retenção e implementar exportação, revogação e eliminação da conta.
- Criar trilha de auditoria sem registrar tokens, senhas ou localização precisa.
- Aplicar limitação de tentativas no login, monitoramento e resposta a incidentes.
- Usar HTTPS, segredos gerenciados, backups criptografados e rotação de chaves.
- Avaliar fornecedores, licenças, transferências internacionais e contratos.
- Revisar Termos e Aviso de Privacidade por responsável jurídico.
- Executar análise de riscos e, quando aplicável, relatório de impacto.

