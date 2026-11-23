# Relatório de alterações, justificativas e testes

Atualizado em: 21/11/2026

## 1. Objetivo

Este relatório separa o trabalho por responsabilidade para facilitar revisão, criação de commits e Pull Requests.

Status utilizados:

- **Implementado:** código presente na branch local `codex-frontend` ou no working tree atual.
- **Testado:** há evidência de teste automatizado ou build executado.
- **Teste parcial:** apenas testes direcionados ou validação manual foram executados.
- **Pendente:** ainda não foi incorporado ou validado.

## 2. Visão das branches do repositório principal

| Branch | Responsabilidade | Situação em relação a `develop` |
|---|---|---|
| `main` | Versão estável | Está atrás de `develop` |
| `develop` | Integração das entregas | Contém Database inicial e Backend API consolidados |
| `feature/backend-api` | FastAPI, autenticação, preferências, POIs e roteiros | Conteúdo incorporado a `develop` por squash |
| `feature/database` | PostgreSQL, PostGIS, modelos e migrations | Base incorporada; o fix mais recente ainda difere de `develop` |
| `feature/arquitetura-pocs` | Recomendação, OR-Tools, matriz viária e personalização | Não deve ser mesclada integralmente; possui estrutura antiga e conteúdo exclusivo |
| `codex-frontend` | Frontend mobile e integrações necessárias ao protótipo | Branch do fork `jmauch99`, baseada em `develop` |

## 3. Bloco A — POCs e planejamento de roteiros

### 3.1 O que foi alterado

- integração da recomendação por afinidade ao planejador atual;
- suporte às métricas `cosseno` e `hibrido`;
- peso configurável entre afinidade e deslocamento;
- matriz viária utilizada na otimização;
- origem geográfica opcional;
- quantidade configurável de paradas;
- opção de retornar ao ponto de partida;
- inclusão do tempo de retorno no total de deslocamentos;
- exclusão de POIs incompletos ou com nomes genéricos antes da otimização.

Arquivos diretamente alterados no working tree atual:

- `backend/app/schemas/roteiro.py`;
- `backend/app/routers/roteiros.py`;
- `backend/app/services/planejador_roteiros.py`;
- `backend/app/services/qualidade_pois.py`.

Serviços de POC já presentes na branch:

- `backend/app/services/pocs/recomendacao.py`;
- `backend/app/services/pocs/otimizacao.py`;
- `backend/app/services/pocs/matriz_deslocamentos.py`.

### 3.2 Por que foi alterado

O backend original gerava roteiros, mas o protótipo precisava demonstrar as três POCs dentro do fluxo real da API:

1. recomendar atrações compatíveis com o perfil;
2. reduzir deslocamentos com otimização de rota;
3. equilibrar afinidade, tempo, orçamento e quantidade de paradas.

A opção de retorno foi adicionada porque o usuário pode precisar considerar a volta ao ponto inicial no limite total do passeio.

### 3.3 Como foi testado

Em 21/11/2026 foram executados:

```text
tests/test_poc_matriz_deslocamentos.py
tests/test_poc_otimizacao.py
tests/test_poc_recomendacao.py
tests/test_qualidade_pois.py
tests/test_alterar_senha_api.py
tests/test_roteiros_api.py::test_gerar_roteiro_inclui_retorno_ao_ponto_de_partida
```

Resultado conjunto:

```text
25 passed in 6.14s
```

Também foi feita anteriormente uma validação manual de geração real com origem e retorno, confirmando a inclusão do trecho de volta no tempo total.

### 3.4 Status e lacunas

**Status: implementado e testado.**

Os algoritmos, filtros e o comportamento HTTP de `retornar_origem=true` possuem cobertura automatizada. O teste confirma que o retorno aumenta o deslocamento total e que o tempo total continua consistente com visitas mais deslocamentos.

## 4. Bloco B — API e conta do usuário

### 4.1 O que foi alterado

- criado `PUT /usuarios/me/senha`;
- validação da senha atual;
- rejeição de nova senha igual à atual;
- hash da nova senha antes da persistência;
- retorno `204 No Content` no sucesso;
- registro das requisições da API no diagnóstico do aplicativo;
- filtragem de nomes de POIs sem valor descritivo, como `Abertura`, `Entrada`, `Saída` e `Sem nome`.

Arquivos:

- `backend/app/routers/usuarios.py`;
- `backend/app/schemas/usuario.py`;
- `backend/app/routers/pontos_interesse.py`;
- `backend/app/services/qualidade_pois.py`;
- `backend/tests/test_alterar_senha_api.py`;
- `backend/tests/test_qualidade_pois.py`.

### 4.2 Por que foi alterado

- o perfil mobile precisava oferecer troca de senha funcional;
- nomes genéricos vindos de fontes externas não representam atrações úteis;
- o protótipo precisava demonstrar quando cada ação realmente chama o backend.

### 4.3 Como foi testado

Os testes direcionados de senha e qualidade de POIs fazem parte dos 25 testes aprovados.

Casos cobertos:

- alteração de senha com sucesso;
- senha atual incorreta;
- nova senha abaixo do tamanho mínimo;
- rejeição de nomes genéricos;
- preservação de nomes descritivos.

### 4.4 Status e lacunas

**Status: implementado e testado nos casos direcionados.**

Ainda faltam no backend:

- `GET /usuarios/me`;
- atualização de nome/e-mail;
- refresh token;
- recuperação de senha;
- moeda no contrato da API.

Esses itens estão detalhados em `PENDENCIAS_BACKEND.md`.

## 5. Bloco C — Database

### 5.1 O que foi alterado por nós

Nenhuma migration, tabela ou modelo de banco foi alterado nesta etapa.

As mudanças atuais utilizam campos e relacionamentos já existentes. A troca de senha atualiza `senha_hash`, que já fazia parte do modelo de usuário.

### 5.2 Alteração existente na branch remota

A branch `upstream/feature/database` possui o commit:

```text
1bd27ca fix(database): protege tabelas internas do PostGIS no Alembic
```

O arquivo `backend/migrations/env.py` dessa branch difere de `upstream/develop`.

### 5.3 Por que essa alteração existe

O objetivo do fix é impedir que tabelas internas gerenciadas pela extensão PostGIS sejam tratadas pelo Alembic como tabelas comuns da aplicação.

### 5.4 Como foi testado

**Status: pendente de validação na nossa branch.**

O commit remoto ainda não foi incorporado por nós. Antes de trazê-lo, deve-se executar:

- geração de migration de verificação;
- upgrade em banco vazio;
- upgrade em banco existente;
- teste de integração PostgreSQL/PostGIS;
- confirmação de que o Alembic não tenta remover tabelas internas do PostGIS.

Não deve ser marcado como testado apenas por existir na feature branch.

## 6. Bloco D — Frontend mobile

### 6.1 Estrutura e design system

#### Alterações

- Expo, TypeScript e Expo Router;
- separação por features;
- cliente HTTP centralizado;
- TanStack Query;
- React Hook Form e Zod;
- armazenamento seguro no mobile;
- tokens de cores, tipografia, espaçamento e raios;
- componentes reutilizáveis de tela, botão, input, card, feedback e loading;
- identidade visual Nextrip;
- splash animada com rota e avião.

#### Justificativa

Criar uma base reutilizável, consistente e compatível com Android, iOS e Web, sem concentrar regras de negócio nas telas.

### 6.2 Autenticação e onboarding

#### Alterações

- cadastro integrado à API;
- login integrado à API;
- logout;
- proteção de rotas públicas e privadas;
- questionário obrigatório de preferências no primeiro acesso;
- interesses, orçamento e moeda preferida;
- troca de senha;
- fluxo único splash → login, sem redirecionamentos concorrentes.

#### Justificativa

Garantir que o usuário tenha um perfil antes da geração personalizada e impedir sobreposição ou piscar de telas durante autenticação.

### 6.3 Home e navegação

#### Alterações

- saudação com nome;
- atalhos para Explorar, Novo roteiro e Roteiros;
- resumo das preferências;
- destaques de atrações reais;
- menu inferior com Início, Explorar, Roteiros e Perfil;
- correções de safe area, cantos, alinhamento e textos cortados.

#### Justificativa

Transformar a antiga tela vazia em uma home funcional, com acesso direto aos fluxos principais.

### 6.4 Atrações e mapas

#### Alterações

- listagem real de POIs;
- categorias com ícones e gramática normalizada;
- preço, duração e avaliação quando fornecidos pela API;
- tela de detalhe;
- mapa nativo em iOS/Android;
- fallback compatível com Web;
- abertura no aplicativo de mapas do aparelho.

#### Justificativa

Permitir explorar dados reais sem inventar descrição, imagem ou endereço inexistentes no contrato.

### 6.5 Roteiros

#### Alterações

- formulário com data em `DD/MM/AAAA`;
- tempo diário;
- orçamento e moeda;
- quantidade de atrações;
- origem por GPS ou endereço;
- retorno opcional à origem;
- modos Mais rápido, Equilibrado e Preferências;
- geração real pela API;
- resultado imediato;
- lista de roteiros persistidos;
- detalhe com ordem, custo, duração, deslocamento e distância;
- acesso ao detalhe de cada atração.

#### Justificativa

Expor as POCs como uma experiência de produto compreensível, sem apresentar parâmetros acadêmicos ou técnicos diretamente ao usuário comum.

### 6.6 Diagnóstico da API

#### Alterações

- histórico de método, rota, status e duração das requisições;
- teste do endpoint `/health`;
- tela acessível pelo perfil.

#### Justificativa

Facilitar a demonstração do backend funcionando e o diagnóstico de falhas de rede no protótipo.

### 6.7 Como foi testado

Executado em 21/11/2026:

```text
npm run typecheck
npm run lint
npm run doctor
npx expo export --platform all
```

Resultado:

- TypeScript: aprovado;
- ESLint/Expo lint: aprovado;
- Expo Doctor: 20/20 verificações aprovadas;
- bundle Web: aprovado;
- bundle iOS: aprovado;
- bundle Android: aprovado.

Também validado durante a integração:

- API e PostgreSQL via `/health` e `/health/db`: respostas `ok`;
- fluxo manual no iPhone via Expo Go.

### 6.8 Status e lacunas

**Status: funcional, com validação estática e bundles aprovados.**

Ainda não existem:

- testes unitários de componentes;
- testes de integração do frontend;
- testes E2E automatizados;
- mapa com a rota completa e polyline;
- personalização do ranking da Home/Explorar por endpoint próprio;
- contrato real de moedas;
- testes sistemáticos de acessibilidade e múltiplos tamanhos de tela.

## 7. Bloco E — Documentação

### 7.1 Arquivos

- `ANALISE_TECNICA_FRONTEND.md`: análise original dos contratos e arquitetura;
- `PENDENCIAS_BACKEND.md`: evoluções necessárias para completar o produto;
- `RELATORIO_ALTERACOES_E_TESTES.md`: separação desta entrega por responsabilidade.

### 7.2 Por que foi alterado

Permitir que responsáveis por frontend, backend, database e POCs revisem apenas o que pertence à sua área e saibam quais afirmações possuem evidência de teste.

### 7.3 Como foi testado

- conferência dos caminhos e contratos contra o código atual;
- `git diff --check` sem erro no documento de pendências;
- nenhum segredo ou `.env` foi incluído.

## 8. Resultado da suíte completa do backend

A primeira execução dentro do sandbox ficou parada ao criar o `socketpair` interno utilizado pelo `TestClient` do FastAPI no Windows. O diagnóstico com `faulthandler` mostrou que a restrição era do ambiente de execução, não um deadlock do código.

A suíte foi então executada fora dessa restrição:

```text
154 passed, 1 warning in 24.59s
```

O aviso é uma depreciação do uso de `httpx` pelo `starlette.testclient`. Ele não causa falha hoje, mas a compatibilidade indicada pela versão do Starlette deve ser tratada em uma atualização de dependências separada.

## 9. Divisão recomendada para commits e revisão

### Commit 1 — Planejamento e POCs

```text
feat(roteiros): integra retorno à origem e qualidade de POIs
```

Responsável principal pela revisão: arquitetura/POCs e backend.

### Commit 2 — Conta e senha

```text
feat(usuarios): adiciona alteração autenticada de senha
```

Responsável principal pela revisão: backend.

### Commit 3 — Aplicativo mobile

```text
feat(mobile): entrega protótipo funcional integrado à API
```

Responsável principal pela revisão: frontend.

### Commit 4 — Documentação

```text
docs: registra pendências do backend e evidências de teste
```

Responsáveis pela revisão: equipe completa.

### Database

O fix de `feature/database` deve entrar em commit ou Pull Request separado, depois de validado. Ele não deve ser misturado ao commit do frontend.

## 10. Condições antes do Pull Request

1. revisar o fix de Alembic da branch Database;
2. revisar o aviso de compatibilidade entre Starlette TestClient e HTTPX;
3. revisar o diff para garantir que `.env`, logs e artefatos não sejam versionados;
4. abrir PR para `develop`, nunca diretamente para `main`.
