# NexTrip — POCs e arquitetura em Python

Código do TCC NexTrip organizado pelas classes UML em `nextrip_arquitetura/`. As provas de conceito **1, 2 e 3** são executadas por scripts Python na raiz. A pasta `tests/` contém testes automatizados; **não substitui os scripts de execução**.

## Escopo e fontes dos dados

- **POC 1:** ranking por similaridade de cosseno e variante híbrida (cosseno + magnitude).
- **POC 2:** reordenação de atrações fixas com Google OR-Tools para reduzir deslocamentos.
- **POC 3:** escolha e reordenação de atrações por afinidade e deslocamento, com restrições de tempo, usando Google OR-Tools.
- **OpenStreetMap (OSM):** nomes, IDs e coordenadas reais de São Paulo nos catálogos JSON.
- **OSRM:** estimativas viárias entre as atrações, consultadas online; sem informação de trânsito ao vivo.

Dados incluídos: `dados/catalogo.json` (12 atrações), `dados/catalogo_teste.json` (15 atrações), `dados/catalogo_amplo.json` (6.888 atrações) e `dados/perfil_usuario.json` (perfil demonstrativo). **Os vetores por categoria e as durações de visita são heurísticos**, não gerados por IA e não medidos pelo OSM.

A implementação de LangGraph, aplicativo React Native, banco PostgreSQL e autenticação real **não está neste repositório de POCs**. Algumas classes do diagrama UML possuem interfaces iniciais para a evolução posterior.

## Organização das pastas

```text
NexTrip/
├── nextrip_arquitetura/
│   ├── modelos.py           Classes de usuário, roteiro, visita e ponto de interesse
│   ├── servicos.py          Recomendação, roteirização, otimização, integrações
│   ├── repositorios.py      Leitura e gravação de JSON
│   ├── interfaces.py        Adaptadores iniciais de cache, mapa e controller
│   └── __init__.py
├── dados/
│   ├── catalogo.json        12 pontos OSM de São Paulo
│   ├── catalogo_teste.json  15 pontos OSM para as POCs com OSRM
│   ├── catalogo_amplo.json  6.888 pontos OSM para a POC 1
│   └── perfil_usuario.json  Perfil de interesses para testes
├── tests/
│   ├── test_arquitetura.py
│   └── test_pocs.py
├── 01_cosseno.py           Entrada da POC 1 (cosseno)
├── 02_hibrido.py           Entrada da POC 1 (híbrido)
├── poc1_recomendacao.py    Interface de recomendação
├── poc2_otimizacao.py      Entrada da POC 2
├── poc3_personalizacao_rota.py  Entrada da POC 3
├── executar_todas.py       Integração das três POCs
├── nextrip_base.py         Funções matemáticas e validações compartilhadas
├── solvers.py              Algoritmos de otimização OR-Tools
├── providers.py            Consulta OSRM; integrações alternativas preservadas
├── coletar_osm_direto.py   Coleta online de recortes pequenos de São Paulo via API OSM
├── importar_osm_em_escala.py  Processamento local de extratos OSM XML
├── requirements.txt
└── README.md
```

A pasta `resultados/` é criada/mantida para gravação de saídas durante a execução, mas seus JSON/CSV são ignorados pelo Git. Os arquivos `.bat`, relatórios antigos e o coletor antigo baseado no Overpass foram retirados do pacote. Os scripts de coleta atual e importação continuam funcionando. A integração alternativa do Google Routes permanece no código, **desativada por padrão**, para preservar a compatibilidade dos scripts/testes existentes.

## Instalação (Windows PowerShell)

Instale Python **3.12, 64 bits** e abra o terminal na pasta do projeto.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Não é necessário ativar a `.venv`; basta usar seu `python.exe`. **Não envie `.venv/` ao GitHub.**

## Execução com os catálogos reais incluídos

POC 1: avaliar todas as 6.888 atrações e mostrar as 30 mais compatíveis:

```powershell
.\.venv\Scripts\python.exe 01_cosseno.py --catalogo dados\catalogo_amplo.json --top 30 --saida resultados\poc1_amplo_cosseno.json
.\.venv\Scripts\python.exe 02_hibrido.py --catalogo dados\catalogo_amplo.json --top 30 --saida resultados\poc1_amplo_hibrido.json
```

POC 2: otimizar a ordem das seis primeiras atrações do catálogo de teste:

```powershell
.\.venv\Scripts\python.exe poc2_otimizacao.py --catalogo dados\catalogo_teste.json --provedor osrm --quantidade 6
```

POC 3: selecionar quatro atrações entre as 15 do catálogo, respeitando até 480 minutos:

```powershell
.\.venv\Scripts\python.exe poc3_personalizacao_rota.py --catalogo dados\catalogo_teste.json --provedor osrm --paradas 4 --limite 480
```

Todas as POCs com uma única matriz OSRM:

```powershell
.\.venv\Scripts\python.exe executar_todas.py --catalogo dados\catalogo_teste.json --provedor osrm --quantidade 6 --paradas 4 --limite 480
```

Para as rotas, use catálogos de até **19 atrações + origem**, respeitando o limite conservador de 20 pontos para a matriz pública OSRM adotado neste projeto. A POC 1 pode avaliar todas as atrações do catálogo amplo diretamente.

## Reimportar os pontos de São Paulo a partir do arquivo OSM bruto

O extrato `SaoPaulo.osm.gz` **não está incluído**, pois é grande. Coloque-o localmente em `dados/`; o `.gitignore` impede seu envio acidental ao GitHub.

```powershell
.\.venv\Scripts\python.exe importar_osm_em_escala.py --arquivo-osm dados\SaoPaulo.osm.gz --limite 10000 --subconjunto 15 --raio-km 80 --categorias museu,galeria,cultura,historia,parque,mirante,atracao,gastronomia,compras,vida_noturna
```

Este comando atualiza `catalogo_amplo.json` e `catalogo_teste.json`. A seleção utiliza **raio**, não o limite territorial exato do município. Importar o arquivo OSM **não é automático** ao executar as POCs.

Para coletar novamente um recorte pequeno da cidade pela API oficial OSM (sem usar Overpass):

```powershell
.\.venv\Scripts\python.exe coletar_osm_direto.py --fonte sp --limite 12
```

O serviço público pode falhar por sobrecarga ou rede. O modo `--fonte sp` impede o fallback automático para outra cidade.

## Arquivos de teste e GitHub

Execute os testes com `python -m unittest discover -s tests -v`. O pacote `nextrip_arquitetura` e os scripts na raiz **são necessários**: não devem ser movidos para `tests/`.

Antes de fazer commit em uma branch de desenvolvimento, confira `git status` e `git diff --cached --stat`. O `.gitignore` protege ambientes virtuais, arquivos OSM brutos e resultados gerados; já os JSONs de catálogo estão incluídos para permitir executar a POC sem importar novamente o arquivo grande.

## Licenças e uso dos dados

**© OpenStreetMap contributors** — Dados OSM sob **Open Database License (ODbL)**, com atribuição e obrigações próprias: https://www.openstreetmap.org/copyright . Os dados dos catálogos provêm de extrações OSM feitas para os testes acadêmicos; conservar os metadados de origem e verificar as obrigações de distribuição da ODbL antes de publicar derivações ou disponibilizar um serviço. Os scripts e regras de classificação são parte deste projeto de POC e não transformam vetores heurísticos em dados OSM.
