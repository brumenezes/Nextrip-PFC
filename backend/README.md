# NexTrip — Backend

API REST desenvolvida em Python com FastAPI para o aplicativo NexTrip, um sistema de recomendação e geração de roteiros turísticos personalizados.

O backend é responsável pelo gerenciamento de usuários, autenticação, preferências, pontos de interesse e roteiros turísticos.

## 1. Tecnologias utilizadas

- Python e FastAPI — desenvolvimento da API REST.
- PostgreSQL — banco de dados relacional.
- PostGIS — armazenamento e consultas geográficas.
- pgvector — armazenamento de vetores para funcionalidades de recomendação.
- SQLAlchemy — mapeamento objeto-relacional (ORM).
- Alembic — controle de versões e migrações do banco de dados.
- Docker Compose — execução do PostgreSQL em contêiner.
- JWT — autenticação de usuários.
- Pytest — testes automatizados.

## 2. Pré-requisitos

Para executar o backend localmente, é necessário instalar:

- Python compatível com as dependências do projeto.
- Docker Desktop com Docker Compose.
- Git.
- Visual Studio Code ou outro editor de código.

## 3. Configuração do ambiente

### 3.1. Clonar o repositório

```powershell
git clone https://github.com/brumenezes/Nextrip-PFC.git
cd Nextrip-PFC
```

**Importante:** enquanto o Pull Request do backend não for integrado à branch `develop`, os arquivos da API estarão disponíveis na branch `feature/backend-api`.

Para acessá-los:

```powershell
git switch feature/backend-api
```

### 3.2. Configurar o Docker

Na raiz do repositório, copie o arquivo `.env.example` para `.env`:

```powershell
Copy-Item .env.example .env
```

Abra o arquivo `.env` e substitua `SUBSTITUA_PELA_SENHA` por uma senha local.

Não compartilhe nem versione esse arquivo.

### 3.3. Iniciar o PostgreSQL

Ainda na raiz do repositório, execute:

```powershell
docker compose up -d --build
```

O PostgreSQL será disponibilizado na porta `5433` do computador.

O banco principal será chamado `nextrip_db`.

As extensões PostGIS e pgvector serão habilitadas pelo script `infra/init.sql` na primeira inicialização do volume de dados.

### 3.4. Configurar o backend

Entre na pasta do backend:

```powershell
cd backend
```

Crie o ambiente virtual:

```powershell
python -m venv venv
```

Instale as dependências:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copie o arquivo de exemplo:

```powershell
Copy-Item .env.example .env
```

Abra `backend/.env` e substitua os marcadores de senha pela mesma senha configurada para o PostgreSQL.

As variáveis são:

- `DATABASE_URL`: conexão com o banco principal.
- `TEST_DATABASE_URL`: conexão com o banco de testes.
- `CORS_ORIGINS`: origens autorizadas para aplicações web durante o desenvolvimento.

O arquivo `.env` contém configurações locais e não deve ser enviado ao GitHub.

## 4. Preparação do banco de dados

### 4.1. Criar as tabelas do banco principal

Com o PostgreSQL em execução e o arquivo `backend/.env` configurado, execute o seguinte comando dentro da pasta `backend`:

```powershell
.\venv\Scripts\python.exe -m alembic upgrade head
```

O Alembic aplicará as migrações existentes e criará as tabelas necessárias para o NexTrip.

### 4.2. Criar o banco de testes

O projeto utiliza um banco separado para os testes de integração, chamado `nextrip_test_db`.

Na primeira configuração do ambiente, execute:

```powershell
docker exec nextrip_db psql -U nextrip_user -d nextrip_db -c "CREATE DATABASE nextrip_test_db;"
```

Esse comando deve ser executado apenas se o banco ainda não existir.

Em seguida, habilite as extensões necessárias no banco de testes:

```powershell
docker exec nextrip_db psql -U nextrip_user -d nextrip_test_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

```powershell
docker exec nextrip_db psql -U nextrip_user -d nextrip_test_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Depois, dentro da pasta `backend`, aplique as migrações do banco de testes:

```powershell
.\venv\Scripts\python.exe -m alembic -c alembic_test.ini upgrade head
```

**Atenção:** nunca configure `TEST_DATABASE_URL` para apontar para o banco principal `nextrip_db`.

## 5. Executar a API

Dentro da pasta `backend`, execute:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

A API estará disponível em:

- API local: http://127.0.0.1:8000
- Documentação Swagger: http://127.0.0.1:8000/docs
- Documentação OpenAPI: http://127.0.0.1:8000/openapi.json

Para verificar se o serviço está funcionando, acesse:

```text
GET http://127.0.0.1:8000/health
```

Para verificar a conexão com o PostgreSQL:

```text
GET http://127.0.0.1:8000/health/db
```

## 6. Executar os testes automatizados

Com o ambiente configurado, os bancos preparados e as dependências instaladas, execute dentro de `backend`:

```powershell
.\venv\Scripts\python.exe -m pytest tests/ -q --cov=app --cov-report=term-missing
```

Esse comando executa os testes automatizados e apresenta o relatório de cobertura do código.

Os testes de integração utilizam o banco `nextrip_test_db`, separado do banco principal.

## 7. Endpoints da API

A API do NexTrip disponibiliza endpoints para gerenciamento de usuários, autenticação, preferências, pontos de interesse e roteiros turísticos.

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/usuarios` | Cadastrar usuário |
| POST | `/auth/login` | Autenticar usuário e obter token JWT |
| POST | `/usuarios/{usuario_id}/preferencias` | Cadastrar preferências |
| GET | `/usuarios/{usuario_id}/preferencias` | Consultar preferências |
| PUT | `/usuarios/{usuario_id}/preferencias` | Atualizar preferências |
| POST | `/pontos-interesse` | Cadastrar ponto de interesse |
| GET | `/pontos-interesse` | Listar pontos de interesse |
| GET | `/pontos-interesse/{poi_id}` | Consultar ponto de interesse |
| POST | `/roteiros/gerar` | Gerar roteiro personalizado |
| GET | `/roteiros` | Listar roteiros |
| GET | `/roteiros/{roteiro_id}` | Consultar roteiro específico |
| GET | `/health` | Verificar funcionamento da API |
| GET | `/health/db` | Verificar conexão com PostgreSQL |

A documentação interativa dos endpoints, incluindo os campos obrigatórios, exemplos de requisições e respostas, está disponível em:

http://127.0.0.1:8000/docs

## 8. Autenticação JWT

O NexTrip utiliza autenticação por token JWT.

O fluxo básico de autenticação é:

1. O usuário realiza o cadastro pelo endpoint `POST /usuarios`.
2. O usuário informa suas credenciais em `POST /auth/login`.
3. O backend valida as credenciais e retorna um token JWT.
4. O frontend utiliza esse token para acessar os endpoints protegidos.

Exemplo de resposta do login:

```json
{
  "access_token": "TOKEN_JWT_RETORNADO_PELA_API",
  "token_type": "bearer"
}
```

Nas requisições autenticadas, o token deve ser enviado no cabeçalho HTTP:

```http
Authorization: Bearer TOKEN_JWT_RETORNADO_PELA_API
```

Os endpoints de preferências exigem autenticação e verificam se o usuário autenticado possui permissão para acessar os dados solicitados.

O frontend não deve armazenar senhas de usuários nem incluir tokens JWT diretamente no código-fonte.

## 9. Integração com React Native

O frontend do NexTrip será desenvolvido em React Native e consumirá a API REST do FastAPI por meio de requisições HTTP.

### 9.1. Endereço da API

Durante o desenvolvimento local, a API utiliza a porta `8000`.

O endereço depende do ambiente em que o aplicativo está sendo executado:

| Ambiente | Endereço de referência |
|---|---|
| Navegador no mesmo computador | `http://127.0.0.1:8000` |
| Emulador Android padrão | `http://10.0.2.2:8000` |
| Simulador iOS no mesmo computador | `http://localhost:8000` |
| Celular físico na mesma rede | `http://IP_DO_COMPUTADOR:8000` |

Para permitir conexões de outros dispositivos na rede local, o backend pode ser iniciado com:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0
```

Nesse caso, substitua `IP_DO_COMPUTADOR` pelo endereço IPv4 do computador que está executando a API.

O computador e o celular devem estar na mesma rede, e o firewall precisa permitir a conexão. Dependendo da configuração do Android ou iOS, também pode ser necessário autorizar o uso de HTTP durante o desenvolvimento.

O endereço `localhost` de um celular físico se refere ao próprio celular, não ao computador que executa o backend.

### 9.2. Exemplo de requisição

Exemplo de consulta ao estado da API utilizando JavaScript:

```javascript
const API_BASE_URL = "http://10.0.2.2:8000";

async function verificarAPI() {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error("Falha ao consultar a API");
  }

  return await response.json();
}
```

O valor de `API_BASE_URL` deve ser ajustado conforme o dispositivo utilizado.

### 9.3. Envio do token JWT

Exemplo de requisição autenticada:

```javascript
async function consultarPreferencias(usuarioId, token) {
  const response = await fetch(
    `${API_BASE_URL}/usuarios/${usuarioId}/preferencias`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error("Falha ao consultar preferências");
  }

  return await response.json