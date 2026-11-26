# Testes de desempenho — NexTrip

## 1. Objetivo

Avaliar o comportamento da API do NexTrip sob diferentes níveis de concorrência, considerando tempo de resposta, throughput, taxa de falhas, estabilidade e capacidade de recuperação após situações de sobrecarga.

Os testes foram desenvolvidos como parte do trabalho acadêmico de Qualidade de Software.

## 2. Ambiente de execução

Experimentos realizados em 25/11/2026.

| Componente | Configuração |
|---|---|
| Sistema operacional | Windows |
| Processador | Intel Core i5-1235U |
| Núcleos físicos | 10 |
| Processadores lógicos | 12 |
| Memória RAM | 15,69 GB |
| Linguagem | Python 3.11.9 |
| Framework | FastAPI |
| Servidor | Uvicorn 0.54.0 |
| Workers | 1 |
| Banco de dados | PostgreSQL 16 |
| Extensões | PostGIS 3.4.3 e pgvector 0.8.6 |
| Ferramenta de desempenho | Locust 2.47.0 |
| Infraestrutura do banco | Docker |
| Porta da API | 8001 |
| Porta do PostgreSQL | 5433 |

A API, o banco de dados e o gerador de carga foram executados no mesmo computador, compartilhando recursos computacionais.

## 3. Organização dos arquivos

- `locustfile.py`: cenários de carga constante.
- `locustfile_stress.py`: cenário de estresse progressivo.
- `results/`: relatórios HTML e arquivos CSV dos experimentos.
- `../scripts/seed_performance.py`: preparação da massa de dados.
- `../requirements-dev.txt`: dependências de desenvolvimento e testes.

## 4. Isolamento e massa de dados

Foi utilizado um banco de dados exclusivo para os experimentos, denominado `nextrip_performance_db`, separado do banco da aplicação e do banco de testes automatizados.

A massa de dados inicial foi composta por:

- 100 usuários fictícios;
- 100 registros de preferências;
- 15 pontos de interesse;
- nenhum roteiro previamente gerado no início dos experimentos.

Os roteiros gerados foram removidos entre os experimentos, preservando os usuários, as preferências e o catálogo de atrações.

A matriz viária externa foi desabilitada para reduzir a influência de serviços externos sobre os resultados.

## 5. Endpoints avaliados

| Método | Endpoint | Finalidade |
|---|---|---|
| POST | `/auth/login` | Autenticação |
| GET | `/pontos-interesse` | Consulta de atrações |
| POST | `/roteiros/gerar` | Geração de roteiro personalizado |
| GET | `/roteiros` | Consulta de roteiros salvos |

O cenário de geração considera cinco atividades, orçamento máximo de R$ 200,00 e tempo disponível de 480 minutos.

## 6. Critérios de aceitação

Foram adotados os seguintes critérios experimentais:

| Indicador | Limite |
|---|---|
| P95 das consultas | Até 1 segundo |
| P95 da autenticação | Até 2 segundos |
| P95 da geração de roteiros | Até 5 segundos |
| Taxa de falhas | Inferior a 1% |

Esses limites representam metas propostas para a avaliação acadêmica, não um SLA de produção.

## 7. Resultados consolidados

| Cenário | Requisições | Falhas | Taxa de falhas | Média (ms) | P95 (ms) | Req/s |
|---|---:|---:|---:|---:|---:|---:|
| Smoke — 1 usuário | 57 | 0 | 0% | 210,97 | 650 | 0,49 |
| Carga — 10 usuários | 503 | 0 | 0% | 395,00 | 1.400 | 4,23 |
| Carga — 25 usuários | 848 | 0 | 0% | 1.501,84 | 4.100 | 7,12 |
| Reteste — 25 usuários | 845 | 0 | 0% | 1.614,88 | 4.300 | 6,86 |
| Carga — 50 usuários | 671 | 0 | 0% | 7.148,05 | 14.000 | 5,35 |
| Carga — 100 usuários previstos | 371 | 106 | 28,57% | 10.737,91 | 30.000 | 3,15 |
| Estresse progressivo | 1.116 | 275 | 24,64% | 13.317,47 | 55.000 | 3,25 |
| Recuperação — 1 usuário | 58 | 0 | 0% | 109,04 | 360 | 0,49 |

O P95 representa o tempo dentro do qual aproximadamente 95% das requisições foram concluídas ou registradas pelo gerador de carga.

Para o cenário de estresse, foram adotados os resultados do CSV consolidado, que são consistentes com o arquivo de falhas. O relatório HTML apresenta uma diferença de duas requisições com falha, cuja causa não foi confirmada.

## 8. Análise dos resultados

O cenário com dez usuários simultâneos foi o maior nível de carga testado que atendeu a todos os critérios de aceitação por endpoint.

Com 25 usuários, observou-se aumento dos tempos de resposta, embora não tenham ocorrido falhas.

Com 50 usuários, houve degradação significativa dos tempos de resposta e redução do throughput, ainda sem falhas registradas.

No cenário de 100 usuários previstos, foram identificadas falhas de requisição e redução da quantidade de usuários ativos, associada ao comportamento do script diante de falhas de autenticação.

O teste de estresse progressivo atingiu 100 usuários ativos e apresentou falhas de comunicação, timeouts e respostas HTTP 500 e HTTP 401.

O teste de recuperação apresentou 58 requisições sem falhas, demonstrando o restabelecimento do atendimento sob baixa carga nas condições avaliadas.

A persistência dos dados também foi verificada. No cenário de recuperação, foram registrados 14 roteiros, 14 dias e 70 atividades, em conformidade com as 14 gerações bem-sucedidas.

## 9. Problemas identificados

| ID | Descrição | Severidade proposta | Status |
|---|---|---|---|
| DEF-03 | Degradação dos tempos de resposta e falhas sob alta concorrência | Alta | Aberto |
| DEF-04 | Respostas HTTP 500 durante a geração de roteiros sob estresse | Alta | Aberto |
| DEF-05 | Respostas HTTP 401 inesperadas durante o estresse | Média | Aberto |

As causas-raiz dos problemas ainda não foram confirmadas.

Também foram observadas diferenças entre a quantidade de roteiros persistidos e a quantidade de gerações bem-sucedidas registradas pelo Locust em alguns cenários. Essa ocorrência deverá ser investigada para avaliar possíveis efeitos de timeouts e novas tentativas de requisição.

## 10. Limitações

- Execução em ambiente local, com compartilhamento de recursos.
- Utilização de apenas um worker do Uvicorn.
- Catálogo reduzido de pontos de interesse.
- Massa de dados composta por usuários fictícios.
- Ausência de monitoramento detalhado de CPU, memória e consultas SQL.
- Ausência de serviços externos de cálculo de matriz viária durante os experimentos.
- Quantidade limitada de repetições dos cenários.
- Diferenças no comportamento de autenticação entre os scripts de carga e estresse.

Os resultados não devem ser extrapolados diretamente para um ambiente de produção nem utilizados para determinar uma capacidade máxima definitiva.

## 11. Regressão funcional após os testes de desempenho

Após a instalação do Locust e a conclusão dos experimentos, foi executada novamente a suíte completa de testes automatizados do backend.

| Indicador | Resultado |
|---|---|
| Testes aprovados | 280 |
| Testes reprovados | 0 |
| Cobertura de instruções | 94,89% |
| Instruções cobertas | 928 de 978 |
| Warnings | 4 |
| Tempo de execução | 26,24 segundos |

Não foram identificadas regressões nos comportamentos cobertos pela suíte automatizada.

## 12. Evidências

Os resultados originais estão disponíveis na pasta `results/`, nos seguintes formatos:

- HTML: relatório visual do experimento.
- `*_stats.csv`: métricas consolidadas.
- `*_stats_history.csv`: histórico temporal das métricas.
- `*_failures.csv`: registro de falhas.
- `*_exceptions.csv`: registro de exceções do Locust.

## 13. Reprodução dos experimentos

Os comandos apresentados nesta seção utilizam o PowerShell no Windows e devem ser executados a partir do diretório `backend/`, com o ambiente virtual Python e o Docker previamente configurados.

### 13.1. Instalação das dependências

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\venv\Scripts\python.exe -m pip check
.\venv\Scripts\python.exe -m locust --version
```

### 13.2. Inicialização do PostgreSQL

Caso o container existente esteja parado:

```powershell
docker start nextrip_db
docker ps
```

### 13.3. Criação do banco de desempenho

A criação do banco deve ser realizada apenas na primeira configuração do ambiente, caso ele ainda não exista.

```powershell
docker exec -it nextrip_db psql -U nextrip_user -d postgres -c "CREATE DATABASE nextrip_performance_db;"
```

Habilitar as extensões necessárias:

```powershell
docker exec -it nextrip_db psql -U nextrip_user -d nextrip_performance_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"

docker exec -it nextrip_db psql -U nextrip_user -d nextrip_performance_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 13.4. Configuração temporária da conexão

Configurar a variável de ambiente para direcionar a aplicação exclusivamente ao banco de desempenho, preservando as configurações originais do arquivo `.env`.

```powershell
$env:DATABASE_URL = (.\venv\Scripts\python.exe -c "from dotenv import dotenv_values; from sqlalchemy.engine import make_url; print(make_url(dotenv_values('.env')['DATABASE_URL']).set(database='nextrip_performance_db').render_as_string(hide_password=False))")
```

Verificar o banco utilizado:

```powershell
.\venv\Scripts\python.exe -c "from app.database import engine; from sqlalchemy import text; c = engine.connect(); print(c.execute(text('SELECT current_database(), current_user')).fetchone()); c.close()"
```

Resultado esperado:

```text
('nextrip_performance_db', 'nextrip_user')
```

Não prosseguir caso a conexão esteja direcionada a outro banco.

### 13.5. Aplicação das migrations

```powershell
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe -m alembic current
```

### 13.6. Preparação da massa de dados

Validar o catálogo de atrações:

```powershell
.\venv\Scripts\python.exe -m scripts.importar_catalogo_osm data/catalogo_osm_teste.json --validate-only
```

Importar os pontos de interesse com preço estimado padrão de R$ 20,00:

```powershell
.\venv\Scripts\python.exe -m scripts.importar_catalogo_osm data/catalogo_osm_teste.json --preco-padrao 20
```

Criar os usuários fictícios e suas preferências:

```powershell
.\venv\Scripts\python.exe -m scripts.seed_performance
```

A massa de dados deve conter 100 usuários, 100 registros de preferências e 15 pontos de interesse.

As contas utilizadas são exclusivamente destinadas aos experimentos e não devem ser utilizadas em produção.

### 13.7. Inicialização da API

No terminal em que foi configurada a variável `DATABASE_URL`, executar:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --workers 1 --no-access-log
```

Manter esse terminal aberto durante os experimentos.

Em outro terminal, também no diretório `backend/`, verificar a disponibilidade da API:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
Invoke-RestMethod http://127.0.0.1:8001/health/db
```

### 13.8. Preparação dos relatórios

Criar um diretório separado para novas exec