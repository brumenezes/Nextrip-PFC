# Análise técnica do backend e preparação do frontend NexTrip

## 1. Objetivo e escopo

Este documento descreve o contrato atualmente implementado na branch `develop` do projeto NexTrip-PFC e propõe uma arquitetura para o futuro frontend mobile. A análise foi feita a partir do código FastAPI, modelos SQLAlchemy, schemas Pydantic, migrações Alembic, serviços, testes, Docker e workflows existentes.

O diretório `mobile/` ainda não possui uma aplicação: contém somente `.gitkeep`. Nenhum código do backend foi alterado e este documento não inicia a implementação do frontend.

## 2. Visão geral da solução

- API REST: Python 3.11, FastAPI 0.163.1 e Pydantic 2.14.3.
- Persistência: PostgreSQL 16, SQLAlchemy 2.1.9 e Alembic.
- Recursos geográficos: PostGIS/GeoAlchemy2.
- Vetores: pgvector, com embeddings de dimensão 384 previstos no modelo.
- Segurança: senhas Argon2 e access token JWT HS256.
- Testes: Pytest, TestClient/FastAPI, mocks e testes reais de integração com PostgreSQL/PostGIS.
- Infraestrutura local: Docker Compose expõe o PostgreSQL na porta `5433`.
- Frontend previsto pela documentação e pelos workflows: React Native com Node.js 20.

## 3. Convenções gerais da API

- URL local padrão: `http://127.0.0.1:8000`.
- Corpos de entrada e saída: JSON, salvo o cabeçalho de autenticação.
- Datas: strings ISO `YYYY-MM-DD`.
- IDs: UUID serializados como strings.
- Erros explícitos do FastAPI: `{ "detail": "mensagem" }`.
- Erros de validação Pydantic/FastAPI: HTTP `422`, normalmente com `{ "detail": [{ "type", "loc", "msg", "input", ... }] }`.
- Autenticação protegida: `Authorization: Bearer <access_token>`.
- Não há versionamento na URL (por exemplo, `/v1`).
- Não há paginação, envelope padrão de resposta, timestamps, refresh token ou endpoint de logout.

## 4. Mapa completo de rotas

| Método | Caminho | Protegida | Entrada | Resposta de sucesso |
|---|---|---:|---|---|
| GET | `/` | Não | — | `200` mensagem de boas-vindas |
| GET | `/health` | Não | — | `200` estado do serviço |
| GET | `/health/db` | Não | — | `200` estado do PostgreSQL |
| POST | `/usuarios` | Não | `UsuarioCreate` | `201 UsuarioResponse` |
| POST | `/auth/login` | Não | `LoginRequest` | `200 TokenResponse` |
| POST | `/usuarios/{usuario_id}/preferencias` | Sim | UUID no path + `PreferenciasCreate` | `201 PreferenciasResponse` |
| GET | `/usuarios/{usuario_id}/preferencias` | Sim | UUID no path | `200 PreferenciasResponse` |
| PUT | `/usuarios/{usuario_id}/preferencias` | Sim | UUID no path + `PreferenciasCreate` | `200 PreferenciasResponse` |
| POST | `/pontos-interesse` | Não | `PontoInteresseCreate` | `201 PontoInteresseResponse` |
| GET | `/pontos-interesse` | Não | — | `200 PontoInteresseResponse[]` |
| GET | `/pontos-interesse/{poi_id}` | Não | UUID no path | `200 PontoInteresseResponse` |
| POST | `/roteiros/gerar` | Sim | `GerarRoteiroRequest` | `201 GerarRoteiroResponse` |
| GET | `/roteiros` | Sim | — | `200 RoteiroResumoResponse[]` |
| GET | `/roteiros/{roteiro_id}` | Sim | UUID no path | `200 RoteiroDetalhadoResponse` |

Não existem endpoints de edição/exclusão de usuário, recuperação de senha, perfil do usuário atual, edição/exclusão de POI, exclusão de preferências, atualização/exclusão de roteiro ou alteração do status de uma atividade.

## 5. Contratos detalhados da API

### 5.1 Infraestrutura e saúde

#### `GET /`

Resposta `200`:

```json
{ "mensagem": "Bem-vindo à API do NexTrip!" }
```

#### `GET /health`

Resposta `200`:

```json
{ "status": "ok", "servico": "NexTrip Backend" }
```

#### `GET /health/db`

Executa `SELECT 1` no banco.

Resposta `200`:

```json
{ "status": "ok", "banco": "PostgreSQL", "conexao": "ativa" }
```

Erro `503`:

```json
{ "detail": "Banco de dados indisponível" }
```

### 5.2 Usuários

#### `POST /usuarios`

Não requer autenticação.

Entrada `UsuarioCreate`:

```json
{
  "nome": "Maria Silva",
  "email": "maria@example.com",
  "senha": "senha123"
}
```

Validações:

- `nome`: obrigatório, entre 2 e 150 caracteres;
- `email`: obrigatório e com formato de e-mail válido;
- `senha`: obrigatória e mínimo de 8 caracteres; não há regra adicional de complexidade.

Resposta `201 UsuarioResponse`:

```json
{
  "id": "uuid",
  "nome": "Maria Silva",
  "email": "maria@example.com"
}
```

A senha nunca é devolvida. Ela é persistida como hash Argon2.

Erros relevantes:

- `409`: `E-mail já cadastrado`;
- `422`: corpo inválido.

### 5.3 Autenticação

#### `POST /auth/login`

Entrada `LoginRequest`:

```json
{ "email": "maria@example.com", "senha": "senha123" }
```

- `email` precisa ter formato válido;
- `senha` é uma string obrigatória, mas o schema de login não define tamanho mínimo.

Resposta `200 TokenResponse`:

```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

Erro `401`, tanto para usuário inexistente quanto para senha incorreta:

```json
{ "detail": "E-mail ou senha inválidos" }
```

O erro inclui `WWW-Authenticate: Bearer`.

### 5.4 Preferências

Todas as três rotas exigem JWT e só permitem que o usuário autenticado acesse o `usuario_id` igual ao `sub` do token.

Entrada `PreferenciasCreate`, usada integralmente tanto no POST quanto no PUT:

```json
{
  "orcamento_maximo": 250.0,
  "interesses": ["Museu", "Parque"]
}
```

Validações:

- `orcamento_maximo`: obrigatório e maior ou igual a zero;
- `interesses`: lista de strings, opcional no JSON e assumida como `[]` quando omitida;
- não há enumeração, limite de itens, tamanho mínimo/máximo ou normalização no momento da gravação.

Resposta `PreferenciasResponse`:

```json
{
  "id": "uuid",
  "usuario_id": "uuid",
  "orcamento_maximo": 250.0,
  "interesses": ["Museu", "Parque"]
}
```

#### `POST /usuarios/{usuario_id}/preferencias`

- `201`: cria a única preferência esperada para o usuário;
- `401`: token ausente, inválido, expirado, com `sub` inválido ou referente a usuário inexistente;
- `403`: usuário autenticado tenta operar sobre outro UUID;
- `404`: `Usuário não encontrado` (na prática, depois da autorização, tende a ser inalcançável para token válido referente a usuário existente);
- `409`: `Preferências já cadastradas para este usuário`;
- `422`: UUID ou corpo inválido.

#### `GET /usuarios/{usuario_id}/preferencias`

- `200`: objeto de preferências;
- `401`/`403`: conforme autenticação e propriedade;
- `404`: `Preferências não encontradas`.

#### `PUT /usuarios/{usuario_id}/preferencias`

Substitui `orcamento_maximo` e `interesses`; não é atualização parcial.

- `200`: preferências atualizadas;
- `404`: `Preferências não encontradas`;
- demais erros de autenticação, propriedade e validação iguais aos anteriores.

### 5.5 Pontos de interesse (POIs)

As rotas atuais de POI são públicas, inclusive a criação.

Entrada `PontoInteresseCreate`:

```json
{
  "nome": "Museu de Arte",
  "categoria": "Museu",
  "latitude": -23.5505,
  "longitude": -46.6333,
  "preco_estimado": 30.0,
  "duracao_minutos": 90,
  "avaliacao_media": 4.7,
  "osm_id": 123456,
  "google_place_id": "place-id"
}
```

Validações:

- `nome`: obrigatório, 1 a 255 caracteres; é salvo com espaços externos removidos;
- `categoria`: string opcional;
- `latitude`: obrigatória, entre -90 e 90;
- `longitude`: obrigatória, entre -180 e 180;
- `preco_estimado`: opcional, maior ou igual a zero;
- `duracao_minutos`: opcional, inteiro maior que zero;
- `avaliacao_media`: opcional, entre 0 e 5;
- `osm_id` e `google_place_id`: opcionais.

Resposta `PontoInteresseResponse` possui os mesmos campos públicos e acrescenta `id`. Não expõe `horarios_funcionamento`, embeddings nem dados brutos OSM existentes no modelo de banco.

#### `POST /pontos-interesse`

Considera duplicado um POI cujo nome, após `trim` e conversão para minúsculas, seja igual e cuja localização esteja em um raio PostGIS de até 10 metros.

- `201`: POI criado;
- `409`: `Este ponto de interesse já está cadastrado no sistema`;
- `422`: corpo inválido.

#### `GET /pontos-interesse`

Retorna uma lista simples, sem paginação, filtros ou ordenação explícita. Lista vazia é `200 []`.

#### `GET /pontos-interesse/{poi_id}`

- `200`: POI encontrado;
- `404`: `Ponto de interesse não encontrado`;
- `422`: UUID inválido.

### 5.6 Roteiros

Todas as rotas de roteiro exigem JWT. Elas sempre usam o usuário derivado do token; nenhum `usuario_id` é recebido no corpo.

#### `POST /roteiros/gerar`

Gera e persiste um roteiro de exatamente um dia.

Entrada `GerarRoteiroRequest`:

```json
{
  "data_visita": "2026-12-01",
  "tempo_disponivel_minutos": 480,
  "orcamento_maximo": 200.0
}
```

Validações:

- `data_visita`: data ISO obrigatória; não há regra que impeça data passada;
- `tempo_disponivel_minutos`: inteiro obrigatório maior que zero;
- `orcamento_maximo`: número obrigatório maior ou igual a zero.

Resposta `201 GerarRoteiroResponse`:

```json
{
  "roteiro_id": "uuid",
  "data_visita": "2026-12-01",
  "tempo_disponivel_minutos": 480,
  "tempo_total_visitas": 240,
  "orcamento_maximo": 200.0,
  "custo_total_estimado": 90.0,
  "tempo_total_deslocamentos": 25,
  "tempo_total_roteiro": 265,
  "atividades": [
    {
      "poi_id": "uuid",
      "nome": "Museu de Arte",
      "categoria": "Museu",
      "ordem_sequencia": 1,
      "preco_estimado": 30.0,
      "duracao_minutos": 90,
      "tempo_deslocamento_previsto": 0,
      "distancia_deslocamento_metros": 0.0
    }
  ]
}
```

Erros relevantes:

- `401`: falha de autenticação;
- `404`: `Nenhum ponto turístico cadastrado`;
- `422`: `Nenhuma atração atende ao orçamento e tempo disponíveis` ou validação de entrada;
- `500`: `Erro ao salvar o roteiro no banco de dados`.

#### `GET /roteiros`

Retorna apenas os roteiros do usuário autenticado, ordenados por `data_inicio` decrescente.

Resposta `200 RoteiroResumoResponse[]`:

```json
[
  {
    "id": "uuid",
    "data_inicio": "2026-12-01",
    "data_fim": "2026-12-01",
    "custo_total_estimado": 90.0
  }
]
```

Sem resultados: `200 []`.

#### `GET /roteiros/{roteiro_id}`

Busca o ID já restringindo pelo usuário autenticado. Um roteiro inexistente e um roteiro de outro usuário produzem a mesma resposta, evitando revelar sua existência.

Resposta `200 RoteiroDetalhadoResponse`:

```json
{
  "id": "uuid",
  "data_inicio": "2026-12-01",
  "data_fim": "2026-12-01",
  "custo_total_estimado": 90.0,
  "dias": [
    {
      "data_referencia": "2026-12-01",
      "tempo_disponivel_minutos": 480,
      "atividades": [
        {
          "poi_id": "uuid",
          "nome": "Museu de Arte",
          "categoria": "Museu",
          "ordem_sequencia": 1,
          "preco_estimado": 30.0,
          "duracao_minutos": 90,
          "tempo_deslocamento_previsto": 0,
          "distancia_deslocamento_metros": 0.0
        }
      ]
    }
  ]
}
```

- `404`: `Roteiro não encontrado`;
- `422`: UUID inválido.

## 6. Autenticação e autorização JWT

### 6.1 Fluxo implementado

1. O usuário é criado em `POST /usuarios`.
2. O login valida e-mail e senha em `POST /auth/login`.
3. A senha é comparada com o hash Argon2 persistido.
4. A API emite JWT HS256 com apenas `sub` (UUID do usuário em string) e `exp`.
5. A validade padrão é 60 minutos (`JWT_EXPIRE_MINUTES`).
6. Rotas protegidas usam `HTTPBearer` e consultam o usuário no banco em toda requisição.

### 6.2 Respostas de autenticação

- Sem cabeçalho: `401 Token de autenticação não informado`;
- token inválido ou expirado: `401 Token inválido ou expirado`;
- `sub` que não é UUID: `401 Identificação inválida no token`;
- UUID válido, mas usuário inexistente: `401 Usuário não encontrado`;
- preferências de outro usuário: `403 Você não tem permissão para acessar estas preferências`;
- roteiro de outro usuário: `404 Roteiro não encontrado`.

### 6.3 Implicações para o frontend

- O token deve ser armazenado em armazenamento seguro do dispositivo, nunca em código-fonte ou armazenamento simples sem necessidade.
- Toda resposta `401` deve limpar a sessão local e encaminhar ao login; não há refresh token.
- O frontend precisa do UUID para montar as rotas de preferências, mas o login devolve somente o JWT. O cadastro devolve o UUID, porém logins posteriores não. Não existe `/usuarios/me`.
- Decodificar localmente o `sub` do JWT pode funcionar como solução provisória, mas cria acoplamento ao conteúdo interno do token e não substitui validação. O contrato ideal deveria expor a identidade autenticada em uma resposta ou endpoint próprio antes da implementação definitiva.
- Não existe revogação ou logout no servidor; logout é apenas descarte local do token.

## 7. Modelo de dados e relacionamentos

### 7.1 `usuario`

| Campo | Tipo | Regra |
|---|---|---|
| `id` | UUID | PK, gerado pela aplicação |
| `nome` | string | obrigatório |
| `email` | string | obrigatório e único |
| `senha_hash` | string | obrigatório |

Relacionamentos: 1:1 lógico com `preferencias` e 1:N com `roteiro`.

### 7.2 `preferencias`

| Campo | Tipo | Regra |
|---|---|---|
| `id` | UUID | PK |
| `usuario_id` | UUID | FK para `usuario`, obrigatório |
| `orcamento_maximo` | float | anulável no banco |
| `perfil_embedding` | vector(384) | anulável, ainda não usado pela API |
| `interesses` | JSONB | anulável |

O ORM declara `uselist=False`, e o endpoint impede uma segunda linha por consulta prévia. Entretanto, a migração não cria `UNIQUE(usuario_id)`, portanto a cardinalidade 1:1 não é garantida pelo banco em caso de concorrência ou escrita externa.

### 7.3 `ponto_de_interesse`

| Campo | Tipo | Regra/uso atual |
|---|---|---|
| `id` | UUID | PK |
| `osm_id` | bigint | opcional |
| `google_place_id` | string | opcional |
| `nome` | string | obrigatório |
| `categoria` | string | opcional |
| `localizacao` | geography POINT, SRID 4326 | obrigatório; índice GiST |
| `preco_estimado` | float | opcional |
| `duracao_minutos` | int | opcional |
| `horarios_funcionamento` | JSONB | opcional, não exposto pela API |
| `avaliacao_media` | float | opcional |
| `descricao_embedding` | vector(384) | opcional, ainda não usado |
| `dados_brutos_osm` | JSONB | opcional, não exposto |

Relacionamento 1:N com `visita_atividade`.

### 7.4 `roteiro`

| Campo | Tipo | Regra |
|---|---|---|
| `id` | UUID | PK |
| `usuario_id` | UUID | FK para `usuario`, obrigatório |
| `data_inicio` | date | obrigatório |
| `data_fim` | date | obrigatório |
| `custo_total_estimado` | float | opcional |

Relacionamentos: N:1 com usuário e 1:N com dias. O ORM aplica `delete-orphan` entre roteiro e dias, mas não há endpoint de exclusão.

### 7.5 `roteiro_dia`

| Campo | Tipo | Regra |
|---|---|---|
| `id` | UUID | PK |
| `roteiro_id` | UUID | FK para `roteiro`, obrigatório |
| `data_referencia` | date | obrigatório |
| `tempo_disponivel_minutos` | int | obrigatório |

Relacionamento 1:N com atividades, também com cascade ORM `delete-orphan`.

### 7.6 `visita_atividade`

| Campo | Tipo | Regra |
|---|---|---|
| `id` | UUID | PK |
| `roteiro_dia_id` | UUID | FK, obrigatório |
| `poi_id` | UUID | FK, obrigatório |
| `ordem_sequencia` | int | obrigatório |
| `horario_inicio` / `horario_fim` | time | opcionais, não preenchidos atualmente |
| `tempo_deslocamento_previsto` | int | opcional, minutos |
| `distancia_deslocamento_metros` | float | opcional |
| `status` | string | obrigatório; geração usa `Planejado` |

Não há timestamps de criação/atualização, soft delete ou regras `ON DELETE` declaradas nas FKs das migrações.

## 8. Regras de negócio

### 8.1 Preferências

- Cada usuário deve ter no máximo um conjunto de preferências pela regra da aplicação.
- Apenas o próprio usuário pode criar, ler e substituir suas preferências.
- Interesses são strings livres.
- Durante a geração, apenas `interesses` é lido das preferências salvas.
- O `orcamento_maximo` salvo nas preferências não é usado pelo gerador; o limite efetivo é recebido em cada `POST /roteiros/gerar`.
- Se não existirem preferências, a geração continua com interesses vazios.

### 8.2 Seleção de pontos de interesse

O algoritmo atual é guloso e determinístico conforme a ordem resultante da classificação:

1. Descarta POIs sem preço ou duração, com preço negativo ou duração não positiva.
2. Normaliza interesses e categorias com remoção de espaços externos e `casefold`.
3. Ordena primeiro por correspondência exata da categoria com algum interesse e depois por avaliação média, ambos em ordem decrescente.
4. Percorre os POIs nessa ordem.
5. Para cada candidato, soma preço, duração e o deslocamento desde o último POI já selecionado.
6. Inclui o candidato somente se os totais continuarem dentro do orçamento e do tempo.

Consequências:

- Não é uma otimização global de custo, tempo ou distância; uma escolha inicial pode impedir uma combinação posterior melhor.
- Interesses têm prioridade total sobre avaliação, mas a correspondência é somente categoria exata.
- Embeddings de perfil/descrição ainda não participam da recomendação.
- Horários de funcionamento, localização inicial do usuário, trânsito, modo de transporte e horário da visita não são considerados.
- Se faltarem coordenadas no dicionário, o deslocamento daquele par é tratado como zero.

### 8.3 Distância e deslocamento

- A distância entre atrações usa Haversine, com raio terrestre de 6.371.000 m.
- O tempo usa velocidade média fixa de 30 km/h.
- O resultado em minutos é arredondado; qualquer deslocamento positivo tem no mínimo 1 minuto.
- A primeira atividade recebe distância e deslocamento zero.
- Não há deslocamento da origem do usuário até a primeira atração nem da última atração até um destino final.

### 8.4 Persistência do roteiro

- A geração cria um `Roteiro` com início e fim iguais a `data_visita`.
- Cria exatamente um `RoteiroDia`.
- Cria uma `VisitaAtividade` por POI selecionado, em sequência iniciando em 1 e status `Planejado`.
- Um erro durante o commit causa rollback e HTTP 500.
- A consulta detalhada ordena dias por data e atividades por sequência.
- Se o POI de uma atividade não for encontrado, a atividade é silenciosamente omitida da resposta detalhada.

## 9. Execução e configuração do backend

### 9.1 Variáveis e arquivos

Na raiz, `.env` é consumido pelo Docker e explicitamente pelo módulo JWT:

```dotenv
POSTGRES_USER=nextrip_user
POSTGRES_PASSWORD=<senha>
POSTGRES_DB=nextrip_db
JWT_SECRET_KEY=<segredo-forte>
JWT_EXPIRE_MINUTES=60
```

Em `backend/.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://nextrip_user:<senha>@localhost:5433/nextrip_db
TEST_DATABASE_URL=postgresql+psycopg://nextrip_user:<senha>@localhost:5433/nextrip_test_db
CORS_ORIGINS=http://localhost:3000,http://localhost:8081,http://localhost:19006
```

Ponto de atenção: os arquivos `.env.example` versionados não documentam `JWT_SECRET_KEY` nem `JWT_EXPIRE_MINUTES`. Além disso, `auth.py` procura explicitamente o `.env` da raiz, enquanto `database.py` usa `load_dotenv()` dependente do contexto de execução. Sem `JWT_SECRET_KEY`, a importação da aplicação falha.

### 9.2 Inicialização local

Na raiz:

```powershell
Copy-Item .env.example .env
# completar senha e variáveis JWT
docker compose up -d --build
```

O container `nextrip_db` expõe PostgreSQL `5432` como `localhost:5433`; `infra/init.sql` habilita `postgis` e `vector` na primeira inicialização do volume.

No diretório `backend`:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Documentação em execução:

- Swagger: `http://127.0.0.1:8000/docs`;
- OpenAPI: `http://127.0.0.1:8000/openapi.json`.

Para dispositivo físico na mesma rede:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0
```

O aplicativo usa `http://IP_DO_COMPUTADOR:8000`; firewall e permissões de HTTP do Android/iOS podem precisar de ajuste.

### 9.3 Banco de testes

O projeto espera `nextrip_test_db`, separado do banco principal. Ele deve ser criado, receber as extensões PostGIS/pgvector e as migrações via:

```powershell
.\venv\Scripts\python.exe -m alembic -c alembic_test.ini upgrade head
.\venv\Scripts\python.exe -m pytest tests/ -q --cov=app --cov-report=term-missing
```

## 10. Requisitos de integração frontend-backend

### 10.1 Configuração de rede

O frontend deve ter uma variável de ambiente única para a base URL:

| Ambiente | Base URL típica |
|---|---|
| Web no mesmo computador | `http://127.0.0.1:8000` |
| Android Emulator | `http://10.0.2.2:8000` |
| iOS Simulator | `http://localhost:8000` |
| Dispositivo físico | `http://<IPv4-do-computador>:8000` |

CORS importa para builds web; os defaults aceitam portas 3000, 8081 e 19006. Apps nativos não seguem CORS do navegador, mas ainda dependem de conectividade e política de transporte seguro.

### 10.2 Cliente HTTP

O cliente deve:

- enviar e aceitar JSON;
- anexar automaticamente `Authorization: Bearer ...` apenas nas rotas protegidas;
- distinguir `401`, `403`, `404`, `409`, `422`, `500` e `503`;
- converter o formato de erro do FastAPI em mensagens de interface;
- aplicar timeout e representar estados de carregamento, vazio, offline e repetição;
- evitar retry automático em POSTs que criam recursos, pois não há chave de idempotência;
- tratar valores monetários como números recebidos da API, formatando-os em reais somente na apresentação;
- manter datas no formato civil `YYYY-MM-DD`, evitando conversões UTC que mudem o dia.

### 10.3 Lacunas contratuais a resolver antes ou durante o protótipo

1. **Identidade após login:** falta `usuario_id` no login ou endpoint `/me`; é bloqueador para uma integração limpa das preferências.
2. **Sessão:** não há refresh token; após cerca de 60 minutos o usuário precisa autenticar novamente.
3. **Cadastro de POIs:** é público. A interface deve decidir se essa função é administrativa; o backend hoje não impõe papel.
4. **Preferência versus geração:** esclarecer na UX que o orçamento da geração é informado novamente e prevalece; o orçamento salvo é atualmente ignorado pelo algoritmo.
5. **Categorias:** não há catálogo/enum endpoint. Chips de interesses mantidos apenas no frontend podem divergir dos textos de `categoria` existentes.
6. **Detalhe do POI:** a API não entrega descrição, imagem, endereço ou horário de funcionamento, limitando cards e telas de detalhe.
7. **Mapas e rotas:** a API devolve coordenadas somente nos endpoints de POI, mas as atividades do roteiro não incluem latitude/longitude. Exibir o roteiro em mapa exigiria cruzamento com a lista/detalhes de POI ou evolução do contrato.
8. **Sem mutações de roteiro:** a UI não pode reordenar, excluir, concluir ou editar atividades via API atual.
9. **Sem paginação:** listas grandes de POIs/roteiros deverão ser tratadas com cautela.
10. **Ambiente:** os exemplos de `.env` precisam ser alinhados com as variáveis JWT para execução reproduzível.

## 11. Testes e funcionalidades comprovadas

### 11.1 Cobertura funcional existente

Os testes existentes verificam:

- criação de usuário, hash de senha, resposta sem senha e conflito de e-mail;
- validações de nome, e-mail e tamanho mínimo de senha;
- login válido, senha incorreta e usuário inexistente;
- geração, validação, expiração e assinatura de JWT;
- bloqueio por ausência de token, token inválido, `sub` inválido e usuário inexistente;
- autorização de preferências por propriedade do usuário;
- criação, conflito, consulta e atualização de preferências;
- rejeição de orçamento negativo;
- criação, duplicidade geográfica, listagem e consulta de POIs;
- validações de coordenadas, preço, duração e avaliação;
- seleção de atrações por orçamento, tempo, interesses e avaliação;
- descarte de POIs incompletos e consideração do deslocamento;
- Haversine e estimativa de minutos, inclusive entradas inválidas;
- geração, persistência, listagem e detalhe de roteiros;
- listas vazias, ausência de POIs, nenhuma atração compatível e falha no commit;
- isolamento de roteiros entre usuários;
- deslocamento por atividade e totais;
- persistência real de usuários, preferências, POIs, roteiros e atividades no PostgreSQL;
- cálculo geográfico real pelo PostGIS.

### 11.2 Natureza dos testes

- Testes de schema e serviços são unitários.
- Testes de rotas usam `TestClient` com dependências substituídas e objetos simulados.
- `test_integracao_postgresql.py` usa o banco configurado em `TEST_DATABASE_URL` e valida recursos específicos do PostgreSQL/PostGIS.
- Não há testes end-to-end com frontend, testes de carga, testes de acessibilidade, testes de contrato gerado para TypeScript ou testes de segurança de papéis administrativos.
- Os workflows CI atuais são placeholders: a instalação de dependências e a execução real do Pytest estão comentadas, portanto um pull request não executa automaticamente a suíte conforme o YAML atual.

## 12. Proposta de arquitetura para o frontend

### 12.1 Stack sugerida

- React Native com Expo e TypeScript;
- Expo Router para navegação baseada em arquivos;
- TanStack Query para estado remoto, cache, loading, erro e invalidação;
- React Hook Form + Zod para formulários e validação equivalente à API;
- Expo SecureStore para o token em plataformas nativas;
- cliente HTTP centralizado com `fetch` ou Axios;
- Jest + React Native Testing Library; Maestro ou Detox para fluxos essenciais quando o protótipo estabilizar.

Expo favorece a velocidade do protótipo e mantém a opção de executar uma versão web. A escolha final deve considerar qualquer requisito nativo ainda não documentado.

### 12.2 Organização por domínio

```text
mobile/
  app/                    # rotas e layouts do Expo Router
    (public)/
      login.tsx
      cadastro.tsx
    (private)/
      _layout.tsx
      index.tsx
      preferencias.tsx
      gerar-roteiro.tsx
      roteiros/
        index.tsx
        [id].tsx
      pontos-interesse/
        index.tsx
        [id].tsx
  src/
    api/
      client.ts           # base URL, JSON, token e normalização de erros
      generated/          # opcional: tipos/cliente gerados do OpenAPI
    auth/
      AuthProvider.tsx
      session-storage.ts
    features/
      auth/
      usuarios/
      preferencias/
      pontos-interesse/
      roteiros/
    components/           # componentes visuais reutilizáveis
    design-system/        # tokens, tema, tipografia e espaçamento
    hooks/
    utils/
    config/
    types/
```

Cada feature deve conter seus componentes, hooks de query/mutation, schemas de formulário e adaptadores. Tipos de transporte da API não devem ser misturados com modelos de apresentação quando houver transformação.

### 12.3 Camadas e responsabilidades

1. **Configuração:** resolve `API_BASE_URL` por ambiente.
2. **Transporte:** serializa JSON, injeta token, aplica timeout e converte erros.
3. **Contrato:** tipos TypeScript derivados do OpenAPI ou mantidos e testados contra ele.
4. **Estado remoto:** TanStack Query para POIs, preferências e roteiros.
5. **Sessão:** provider mínimo para token, identidade e restauração segura.
6. **Apresentação:** telas mobile-first sem conhecer detalhes de HTTP.

Evitar uma store global para dados que já pertencem ao servidor. Estado global deve se limitar principalmente à sessão e preferências puramente visuais.

### 12.4 Fluxo inicial de telas compatível com a API atual

1. Cadastro → guarda o UUID retornado → login.
2. Login → guarda token; provisoriamente obtém UUID do `sub` ou usa o UUID conhecido do cadastro, até o contrato de identidade ser resolvido.
3. Onboarding/preferências → GET; se 404, POST; se existente, PUT.
4. Home → atalhos para gerar roteiro, roteiros salvos e POIs.
5. Gerar roteiro → data, duração e orçamento → resultado recém-gerado.
6. Roteiros → lista do usuário → detalhe por ID.
7. POIs → listagem e detalhe simples conforme campos disponíveis.

Não se deve desenhar como funcional qualquer edição de roteiro, mapa completo, favorito, avaliação, imagem, endereço, horário ou recuperação de senha enquanto não houver contrato correspondente ou dados mockados explicitamente identificados como protótipo.

### 12.5 Estratégia de erros na interface

| Status | Comportamento recomendado |
|---|---|
| 401 | Encerrar sessão local e abrir login, preservando intenção de navegação quando seguro |
| 403 | Mensagem de acesso negado, sem repetir automaticamente |
| 404 | Estado vazio/contextual; na geração, explicar ausência de POIs |
| 409 | Erro de campo/estado já existente (e-mail, preferências, POI) |
| 422 | Mapear validação para campos; tratar a incompatibilidade do gerador como estado de negócio |
| 500 | Mensagem genérica e opção de tentar novamente com cautela |
| 503 | Indicar indisponibilidade temporária do serviço/banco |

Há dois significados diferentes para `422`: validação estrutural e “nenhuma atração compatível”. O adaptador deve observar `detail` como string versus lista.

## 13. Decisões recomendadas antes de implementar

1. Confirmar React Native + Expo como base do protótipo.
2. Definir o fluxo oficial para descobrir a identidade do usuário após login.
3. Definir uma taxonomia compartilhada de categorias/interesses.
4. Decidir se cadastro de POI pertence ao app comum ou a uma interface administrativa futura.
5. Definir quais lacunas visuais serão mockadas e sinalizadas no protótipo.
6. Alinhar se o orçamento salvo deve preencher apenas o formulário ou ser aplicado automaticamente pelo backend.
7. Decidir se o protótipo precisa de mapa; o contrato atual exige consultas adicionais para obter coordenadas das atividades.
8. Fixar ambientes e variáveis de URL para emulador, dispositivo físico e web.
9. Gerar e versionar tipos TypeScript a partir de `/openapi.json` quando o contrato estiver estabilizado.

## 14. Conclusão

O backend já suporta o núcleo de um protótipo: cadastro, login, preferências, catálogo de POIs, geração personalizada simples e histórico de roteiros. A separação de usuários em preferências e roteiros está implementada e testada. A principal preparação necessária para o frontend é tratar explicitamente as limitações do contrato atual — sobretudo identidade após login, ausência de refresh, orçamento duplicado, categorias livres e poucos dados de apresentação dos POIs — para que a interface não prometa comportamentos que a API ainda não oferece.
