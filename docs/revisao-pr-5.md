# Revisão técnica do PR #5 do Nextrip

Revisão de 22 de novembro de 2026. O PR integra recomendação, matriz de deslocamentos e otimização ao backend FastAPI. **Solicitar alterações.** O CI do commit original falhou durante a preparação do banco de testes. A revisão corrigida passou nos testes locais, com 196 testes e 96,32% de cobertura. O build dos contêineres e o novo CI no GitHub Actions são condições para a aprovação. [PR #5](https://github.com/brumenezes/Nextrip-PFC/pull/5) · [Execução original do CI](https://github.com/brumenezes/Nextrip-PFC/actions/runs/44919256872)

## Escopo

A base da comparação foi `upstream/develop` (`a9f49db`). A ponta revisada foi `jmauch99:codex/backend-integracao-pocs` (`3d79aae`). O diff do PR tem 31 arquivos em API, serviços, testes, catálogo OSM, dependências, documentação e infraestrutura. Os três commits revisados são:

- `de5c8b5` integra as POCs ao planejamento de roteiros.
- `555d204` adiciona validação com PostgreSQL e publicação da imagem.
- `3d79aae` acrescenta os testes de saúde.

As migrations e o frontend mobile estão fora do diff do PR e da correção. O inventário completo do PR está na aba de arquivos. [Arquivos do PR](https://github.com/brumenezes/Nextrip-PFC/pull/5/files)

## Achados bloqueantes

As referências de linha nesta seção correspondem ao commit original `3d79aae`.

| Local | Impacto e correção |
| --- | --- |
| `.github/workflows/ci-backend.yml:64` | O CI passou pela espera inicial e falhou em `Prepare test database`. O PostgreSQL pode responder no socket Unix antes de concluir a inicialização. Essa é a causa provável, pois o log detalhado do passo estava indisponível. O Compose passa a exigir prontidão via TCP. |
| `docker-compose.yml:4` | `docker compose up -d --build` selecionava apenas `db`, pois `api` tinha o perfil `app`. A configuração corrigida seleciona os dois serviços e o CI verifica os endpoints do contêiner da API. |
| `.github/workflows/cd-backend.yml:4` | O evento `workflow_run` exige que o arquivo exista na branch padrão. O fluxo estava ausente de `main`, o que impedia a entrega após um push em `develop`. O CI corrigido chama diretamente o workflow reutilizável depois da validação bem-sucedida. |
| `backend/app/services/planejador_roteiros.py:215` | Uma requisição sem `quantidade_paradas` ignorava origem, retorno e peso de preferências e podia incluir POIs genéricos. O filtro passou a valer nos dois modos. Origem, peso explícito ou matriz viária ativam a otimização com quantidade flexível. |
| `backend/app/services/planejador_roteiros.py:154` | Arredondar cada preço para centavos podia aprovar uma soma acima do orçamento. A correção preserva a precisão compatível com a capacidade inteira do solver e usa arredondamento conservador quando necessário. |

[Entrypoint do PostgreSQL](https://github.com/docker-library/postgres/blob/master/docker-entrypoint.sh#L337) · [Evento `workflow_run`](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run)

## Achados importantes

- Uma matriz assimétrica podia causar `422` para uma rota fechada viável. A estratégia inicial do OR-Tools e a avaliação do retorno no modo portátil foram corrigidas. A suíte executa os testes do otimizador com as duas implementações. Referência original `backend/app/services/pocs/otimizacao.py:187`.
- Matrizes OSRM inválidas podiam produzir distâncias negativas ou falha de geração. A validação da resposta passou a acionar o fallback Haversine. `usar_matriz_viaria` tem padrão `false`. Ao habilitar a opção, a API envia coordenadas ao serviço OSRM configurado. O comportamento foi testado com respostas simuladas. Referência original `backend/app/services/pocs/matriz_deslocamentos.py:113`.

## Contratos e compatibilidade

O JSON abaixo retornou `201` via HTTP com dados locais. A comparação com o OpenAPI de `develop` confirmou as mesmas operações e os mesmos esquemas de resposta.

```json
{
  "data_visita": "2026-11-24",
  "tempo_disponivel_minutos": 360,
  "orcamento_maximo": 150
}
```

- `quantidade_paradas` é opcional. Quando enviada, exige de 1 a 19 atrações.
- `latitude_origem` e `longitude_origem` são opcionais e devem ser enviadas juntas. `retornar_origem` tem padrão `false` e exige origem completa quando ativado.
- `peso_preferencias` e `peso_cosseno` aceitam valores de 0 a 1. Seus defaults são `0.8` e `0.7`. `metrica_recomendacao` aceita `cosseno` ou `hibrido`, com padrão `cosseno`.
- `usar_matriz_viaria` é opcional. O modo guloso continua disponível para o payload antigo.

A primeira atividade recebe o deslocamento desde a origem. Com retorno ativado, o trecho de volta entra em `tempo_total_deslocamentos`. O tempo total continua sendo visitas mais deslocamentos, dentro do limite disponível. Os testes exercitaram retorno ativado e desativado, origem ausente e completa, latitude e longitude isoladas, pesos `0`, `0.2`, `0.5`, `0.8` e `1`, pesos fora do intervalo e orçamento fracionário. Também verificaram afinidade em `[0, 1]`, ranking por afinidade, matriz válida, quantidade de paradas, ausência de atrações repetidas e `422` para rota inviável.

O filtro normaliza caixa, acentos e espaços externos, rejeita nomes curtos e compara os nomes genéricos por igualdade. Os testes do filtro cobriram `Abertura`, `Acesso`, `Entrada`, `Portão`, `Saída`, `Sem nome`, `Unnamed`, `Yes` e `No`. Também confirmaram que `Arena B3`, `Casa da Imagem`, `Galeria Florêncio`, `Museu da Imagem e do Som` e `Portão Cultural` são preservados. Os testes de API verificaram o uso do filtro na listagem e na seleção de candidatos.

| Requisição HTTP | Resultado observado |
| --- | --- |
| `POST /usuarios` e `POST /auth/login` | `201` e `200`. Cadastro repetido retornou `409`. |
| `POST`, `GET` e `PUT /usuarios/{id}/preferencias` | `201`, `200` e `200`. Acesso de outro usuário retornou `403`. |
| `POST /pontos-interesse`, `GET /pontos-interesse` e `GET /pontos-interesse/{id}` | `201`, `200` e `200`. Cadastro repetido retornou `409`. A lista omitiu o POI genérico. |
| `POST /roteiros/gerar`, `GET /roteiros` e `GET /roteiros/{id}` | `201`, `200` e `200`. O roteiro foi persistido e isolado por usuário. Acesso sem token retornou `401`, consulta por outro usuário retornou `404` e origem incompleta retornou `422`. |
| `GET /health`, `GET /health/db`, `GET /docs` e `GET /openapi.json` | `200` em todos. Os payloads de saúde estão registrados abaixo. |

## Saídas da validação

### Testes e catálogo

Os testes foram executados no Windows com Python 3.12.4 e PostgreSQL local. As versões fixadas nas dependências foram instaladas e `pip check` retornou `No broken requirements found.`. `python -m compileall -q app` terminou com código `0`. Os trechos abaixo registram os resultados finais observados.

| Comando ou execução | Saída relevante |
| --- | --- |
| `python -m scripts.importar_catalogo_osm data/catalogo_osm_teste.json --validate-only` | `Catálogo válido: 15 pontos OSM.` |
| `python -m pytest tests/test_roteiros_api.py::test_gerar_roteiro_inclui_retorno_ao_ponto_de_partida -q` | `1 passed, 1 warning` |
| `python -m pytest tests -q` na branch corrigida | `196 passed, 4 warnings` |
| Cobertura no commit original `3d79aae` | `155 passed, 1 warning` e `Total coverage: 90.43%` |
| Cobertura na branch corrigida | `196 passed, 4 warnings` e `Total coverage: 96.32%` |
| Cobertura com OR-Tools selecionado para os testes da API no Windows | `196 passed, 4 warnings` e `Total coverage: 96.32%` |

A execução de cobertura usou a política do CI, com 863 de 896 linhas cobertas na revisão corrigida.

```text
python -m pytest tests -q --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=90

Coverage XML written to file coverage.xml
Required test coverage of 90% reached. Total coverage: 96.32%
196 passed, 4 warnings in 24.75s
```

Os quatro avisos são de depreciação do Starlette TestClient com HTTPX e dos tipos SWIG carregados pelo OR-Tools.

### Migrations

`alembic heads`, `alembic upgrade head` e `alembic check` foram executados nos bancos locais `nextrip_db` e `nextrip_test_db`, com PostgreSQL 16.13, PostGIS 3.7.0 e pgvector 0.8.3. Ambos conservaram a tabela `spatial_ref_sys`. As migrations existentes foram aplicadas a partir de bancos novos, sem dados de produção.

```text
cef8e48e846f (head)
Running upgrade  -> 34458a9f0b43, Criacao inicial das tabelas
Running upgrade 34458a9f0b43 -> cef8e48e846f, adiciona interesses nas preferencias
No new upgrade operations detected.
```

### Compose e HTTP

`docker compose config --quiet` passou. `docker compose config --services` listou `db` na revisão original e `db` e `api` na revisão corrigida. `up`, `ps`, `logs` e `down` encontraram o mesmo bloqueio de execução neste ambiente.

```text
failed to connect to the docker API at npipe:////./pipe/docker_engine
```

A API executada via Uvicorn local, na porta `8088`, respondeu com os payloads esperados. `/docs` e `/openapi.json` responderam com `200`. Os serviços locais usados na validação foram encerrados.

```text
GET /health     200 {"status":"ok","servico":"NexTrip Backend"}
GET /health/db  200 {"status":"ok","banco":"PostgreSQL","conexao":"ativa"}
GET /docs       200
GET /openapi.json 200
```

### GitHub Actions e segredos

| Passo do CI original | Conclusão |
| --- | --- |
| Instalação de dependências, build do PostgreSQL e espera inicial | `success` |
| `Prepare test database` | `failure` |
| Migrations, compilação, catálogo e testes com cobertura | `skipped` |
| Logs em falha e encerramento | `success` |

`actionlint` aprovou os dois workflows corrigidos. O CI aciona em `backend/**`, configura Python, instala dependências, prepara PostgreSQL/PostGIS e o banco de testes, aplica migrations aos dois bancos, compila, valida o catálogo e exige cobertura de 90%. Também guarda o artefato, registra logs em falha e encerra os contêineres com `always()`. O job de validação usa `contents: read`, tem timeout e não executa npm ou Expo.

Na configuração corrigida, o job de entrega depende do sucesso da validação e só executa em push para `develop`, `release` ou `main`. Ele usa `GITHUB_TOKEN` com `packages: write` para publicar no GHCR, com tags da branch e do SHA, SBOM e provenance. O workflow contém apenas a entrega da imagem. A execução corrigida no GitHub Actions e a publicação no GHCR seguem pendentes de validação.

O Gitleaks retornou `no leaks found` nos três commits do PR e no diff de correção. A senha de CI e a chave JWT de exemplo do workflow são destinadas ao runner descartável. Os valores de desenvolvimento do `.env` ficaram fora do Git.

## Arquivos de correção e riscos restantes

| Área | Arquivos |
| --- | --- |
| Infraestrutura | `.github/workflows/ci-backend.yml`, `.github/workflows/cd-backend.yml`, `docker-compose.yml`, `backend/.dockerignore` |
| Contrato e planejamento | `backend/app/schemas/roteiro.py`, `backend/app/routers/roteiros.py`, `backend/app/services/calculadora_deslocamentos.py`, `backend/app/services/gerador_roteiros.py`, `backend/app/services/planejador_roteiros.py`, `backend/app/services/pocs/matriz_deslocamentos.py`, `backend/app/services/pocs/otimizacao.py` |
| Testes | `backend/tests/test_poc_matriz_deslocamentos.py`, `backend/tests/test_poc_otimizacao.py`, `backend/tests/test_pontos_interesse_api.py`, `backend/tests/test_qualidade_pois.py`, `backend/tests/test_roteiros_api.py` |
| Documentação | `backend/README.md`, `docs/revisao-pr-5.md` |

O otimizador busca entre até 19 candidatos e pode deixar uma rota viável fora do conjunto. O retorno compõe os totais da geração, mas o `GET` do roteiro salvo recupera apenas os trechos de chegada às atividades. Para identificar de forma imutável a imagem publicada, use o digest da imagem. [Referência por digest no GHCR](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry#pulling-container-images)

## Checklist de aprovação

- [x] Payload antigo e respostas existentes compatíveis.
- [x] Campos novos opcionais ou com defaults e origem incompleta rejeitada com `422`.
- [x] Retorno entra no total, com afinidade, deslocamento, tempo e orçamento verificados.
- [x] POIs genéricos rejeitados e nomes reais preservados.
- [x] Os 155 testes originais passaram. A revisão corrigida chegou a 196 testes e superou 90% de cobertura.
- [x] Migrations consistentes nos dois bancos locais.
- [x] Nenhum segredo detectado nos commits e no diff revisado.
- [ ] Build e subida da API e do PostgreSQL pelo Docker Compose confirmados.
- [ ] CI Backend verde no GitHub Actions com a correção.
- [ ] Publicação no GHCR verificada após CI bem-sucedido em uma branch configurada.

**Decisão.** Solicitar alterações no PR #5. Incorporar a correção e confirmar o CI verde e a subida dos contêineres antes de usar **Approve** e **Squash and merge**.
