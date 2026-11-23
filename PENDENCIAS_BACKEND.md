# Pendências do backend para completar o frontend Nextrip

Atualizado em: 21/11/2026

## 1. Objetivo

Este documento registra as evoluções de backend necessárias para transformar o frontend mobile atual em um produto completo, mantendo os contratos existentes compatíveis sempre que possível.

As rotas e campos descritos como **proposta** ainda não fazem parte da API. Eles devem ser discutidos, implementados, documentados no OpenAPI e cobertos por testes antes de serem consumidos pelo aplicativo.

## 2. O que já está disponível

O frontend já consegue consumir:

- cadastro e login;
- alteração de senha autenticada;
- criação, consulta e atualização de preferências;
- listagem e detalhe de pontos de interesse;
- geração otimizada e personalizada de roteiro;
- origem opcional e retorno ao ponto inicial;
- listagem e detalhe de roteiros salvos;
- parâmetros das POCs de recomendação, otimização e personalização;
- endpoints de saúde da API e do banco.

Esses recursos não devem ser recriados em novos endpoints sem necessidade.

## 3. Prioridade crítica

### 3.1 Identidade do usuário autenticado

#### Problema

O login devolve somente `access_token` e `token_type`. O frontend extrai o UUID do `sub` do JWT e mantém nome e e-mail localmente. Isso não funciona de forma confiável em outro aparelho ou depois da remoção dos dados do aplicativo.

#### Proposta

Adicionar:

```http
GET /usuarios/me
Authorization: Bearer <token>
```

Resposta sugerida:

```json
{
  "id": "uuid",
  "nome": "Nome completo",
  "email": "usuario@exemplo.com"
}
```

Opcionalmente, o login também pode devolver um objeto `usuario`, mas o endpoint `/usuarios/me` continua necessário para restaurar e atualizar a identidade da sessão.

#### Critérios de aceite

- somente o próprio usuário pode consultar os dados;
- resposta nunca contém senha ou hash;
- endpoint exige JWT válido;
- existem testes para token ausente, inválido, expirado e usuário inexistente.

### 3.2 Moeda e orçamento

#### Problema

O frontend oferece BRL, USD, EUR e GBP, mas a API recebe somente um número em `orcamento_maximo`. Não há código da moeda nem conversão. Assim, `150 EUR` e `150 BRL` são indistinguíveis para o algoritmo.

#### Decisão necessária

Escolher uma das estratégias:

1. API opera apenas em BRL e o frontend converte antes do envio; ou
2. API recebe a moeda, converte para uma moeda-base e registra a cotação utilizada.

A segunda opção é mais auditável.

Campos sugeridos para preferências e geração:

```json
{
  "orcamento_maximo": 150.0,
  "moeda": "EUR"
}
```

Valores aceitos inicialmente:

```text
BRL, USD, EUR, GBP
```

Se houver conversão no backend, a resposta do roteiro deve informar:

- moeda original;
- moeda-base;
- cotação utilizada;
- data/hora da cotação;
- custo total nas duas moedas.

### 3.3 Dados completos do ponto de interesse

#### Problema

O contrato atual não possui informações suficientes para uma tela completa de atração.

#### Campos desejados

- descrição;
- endereço formatado;
- cidade, estado e país;
- imagens com URL, autoria e licença;
- site oficial;
- telefone;
- horário de funcionamento;
- acessibilidade;
- origem dos dados;
- data da última atualização;
- preço com moeda;
- quantidade de avaliações, quando disponível.

Esses campos podem ser adicionados de forma opcional ao detalhe do POI para preservar compatibilidade.

#### Imagens

Não armazenar imagens grandes diretamente no PostgreSQL. Armazenar arquivos em um serviço de objetos/CDN e persistir apenas metadados e URLs.

É necessário verificar licenças e regras de atribuição de OpenStreetMap, Wikimedia, Google Places ou qualquer outra fonte utilizada.

### 3.4 Coordenadas e geometria do roteiro

#### Problema

As atividades do roteiro não retornam latitude e longitude. O frontend precisa fazer consultas adicionais de POIs e ainda não recebe o traçado real entre as paradas.

#### Evolução mínima

Adicionar em cada atividade:

```json
{
  "latitude": -23.5505,
  "longitude": -46.6333
}
```

#### Evolução recomendada

O detalhe do roteiro também pode devolver:

- coordenadas da origem;
- indicação de retorno à origem;
- sequência completa de coordenadas;
- polyline codificada ou GeoJSON do trajeto;
- distância e duração por trecho;
- provedor que calculou a matriz ou rota;
- data/hora do cálculo.

Isso permitirá desenhar o roteiro completo no mapa sem reconstruir a rota no dispositivo.

## 4. Prioridade alta

### 4.1 Ranking personalizado para Home e Explorar

#### Problema

A POC de recomendação participa da geração do roteiro, mas não existe um endpoint para apresentar atrações ordenadas pelo perfil do usuário.

#### Proposta

Adicionar uma consulta autenticada de recomendações, por exemplo:

```http
GET /pontos-interesse/recomendados?limite=10&metrica=hibrido
```

A resposta deve manter os campos normais do POI e pode acrescentar:

```json
{
  "score_afinidade": 0.87,
  "motivos": ["História", "Cultura"]
}
```

O campo de motivos deve ser derivado de dados reais, e não de texto inventado pelo frontend.

### 4.2 Explicabilidade da geração do roteiro

Para demonstrar claramente as três POCs, a resposta de geração ou detalhe pode informar:

- modo/peso de personalização utilizado;
- métrica de recomendação;
- afinidade de cada atração;
- tempo economizado em relação à ordem de referência;
- distância total;
- tempo total de visitas e deslocamentos;
- provedor da matriz viária;
- avisos de aproximação ou fallback.

Esses dados são especialmente importantes para a demonstração acadêmica do protótipo.

### 4.3 Busca, filtros, ordenação e paginação de POIs

O endpoint de listagem deve evoluir antes que o catálogo cresça.

Parâmetros sugeridos:

- `busca`;
- `categoria`;
- `preco_maximo`;
- `duracao_maxima`;
- `avaliacao_minima`;
- latitude, longitude e raio;
- `ordenar_por`;
- `pagina` e `tamanho_pagina` ou paginação por cursor.

A resposta paginada deve informar total e próximo cursor/página.

### 4.4 Catálogo compartilhado de categorias

#### Problema

As categorias e ícones são mapeados manualmente no frontend. Novos textos vindos do banco podem ficar sem apresentação adequada.

#### Proposta

Definir uma taxonomia canônica no backend e expor um catálogo, por exemplo:

```http
GET /categorias-pontos-interesse
```

Cada categoria deve ter um identificador estável e um nome de exibição. Ícones podem continuar sendo responsabilidade do frontend, associados ao identificador estável.

### 4.5 Atualização do perfil

Adicionar uma operação autenticada para editar os dados permitidos, por exemplo:

```http
PATCH /usuarios/me
```

Campos inicialmente editáveis:

- nome;
- e-mail, caso exista um fluxo seguro de confirmação.

Alteração de e-mail deve tratar duplicidade e, idealmente, exigir confirmação.

## 5. Sessão e segurança

### 5.1 Renovação de sessão

Atualmente há apenas access token. Para manter o usuário autenticado com segurança, definir:

- refresh token com rotação;
- expiração e revogação;
- endpoint de renovação;
- logout/revogação da sessão;
- política para múltiplos dispositivos.

Se não houver refresh token, o comportamento oficial deve permanecer: token expirado encerra a sessão e exige novo login.

### 5.2 Recuperação de senha

Ainda falta um fluxo completo de “Esqueci minha senha”:

1. solicitação por e-mail;
2. token temporário, de uso único e com expiração curta;
3. redefinição da senha;
4. invalidação do token;
5. resposta que não revele se determinado e-mail está cadastrado.

### 5.3 Administração dos POIs

O cadastro de ponto de interesse não deve permanecer público em produção.

Definir:

- papéis/permissões administrativas;
- autenticação para criar ou alterar POIs;
- trilha de auditoria;
- validação da fonte dos dados;
- proteção contra duplicidade e abuso.

## 6. Funcionalidades futuras

Dependem de decisão de produto e não bloqueiam o protótipo atual:

- favoritos;
- avaliações realizadas pelos usuários;
- histórico de atrações visitadas;
- edição, exclusão e reordenação manual de roteiros;
- compartilhamento de roteiro;
- notificações e lembretes;
- roteiros com vários dias configuráveis;
- reservas ou compra de ingressos;
- funcionamento offline e sincronização posterior.

Cada item precisa de contrato, autorização e testes próprios. O frontend não deve simular essas funções como reais antes disso.

## 7. Qualidade, integração e observabilidade

### 7.1 Contrato OpenAPI

- manter exemplos de request e response no OpenAPI;
- documentar erros por status;
- gerar tipos TypeScript quando os contratos estabilizarem;
- adicionar teste de compatibilidade entre OpenAPI e cliente mobile.

### 7.2 Erros

Padronizar respostas de erro com código estável, mensagem e identificador de correlação, sem expor detalhes internos.

Exemplo:

```json
{
  "code": "ROTEIRO_INVIAVEL",
  "detail": "Nenhuma combinação atende aos limites informados.",
  "request_id": "uuid"
}
```

### 7.3 Dados externos

Para importar e manter POIs de várias cidades, criar um processo separado e idempotente de ingestão que:

- registre a fonte e a licença;
- normalize categorias;
- elimine duplicidades;
- descarte nomes genéricos ou inválidos;
- atualize dados sem criar novos registros desnecessários;
- produza relatório de inclusão, atualização e rejeição;
- respeite limites e termos dos provedores.

### 7.4 Testes necessários

Para cada nova evolução:

- teste unitário de schema e serviço;
- teste de autorização;
- teste de rota FastAPI;
- teste de persistência PostgreSQL/PostGIS quando aplicável;
- teste para respostas vazias, dados incompletos e falhas externas;
- atualização dos contratos usados pelo frontend.

## 8. Ordem recomendada de implementação

1. `GET /usuarios/me`.
2. Definição e persistência de moeda.
3. Coordenadas nas atividades e geometria do roteiro.
4. Dados enriquecidos e imagens de POIs.
5. Recomendações personalizadas para Home/Explorar.
6. Busca, filtros, categorias e paginação.
7. Atualização de perfil.
8. Refresh token e recuperação de senha.
9. Recursos futuros de favoritos, avaliações e edição de roteiro.

## 9. Definition of Done para integração

Uma evolução de backend está pronta para o mobile quando:

- contrato foi acordado antes da implementação;
- migration necessária foi criada e testada;
- endpoint está documentado no OpenAPI;
- autenticação e autorização foram testadas;
- erros esperados foram documentados;
- testes automatizados passam no CI;
- `.env.example` foi atualizado sem incluir segredos;
- o frontend recebeu exemplo real de request e response;
- compatibilidade com os contratos existentes foi preservada ou a mudança foi versionada.
