# Nextrip Mobile

Aplicativo Android e iOS do Nextrip, construído com Expo, React Native e TypeScript.

## Requisitos

- Node.js 24 (versão usada pelo CI do projeto)
- npm
- Expo Go em um dispositivo físico, ou Android Studio/Xcode para simuladores
- backend Nextrip em execução

> O simulador iOS e builds locais para iOS exigem macOS. Em Windows/Linux, use um iPhone com Expo Go ou um build remoto EAS.

## Instalação

```powershell
cd mobile
npm install
Copy-Item .env.example .env
```

Edite `.env` e escolha a URL adequada:

```dotenv
# Android Emulator
EXPO_PUBLIC_API_URL=http://10.0.2.2:8088

# iOS Simulator
EXPO_PUBLIC_API_URL=http://localhost:8088

# Dispositivo físico (mesma rede do computador)
EXPO_PUBLIC_API_URL=http://192.168.x.x:8088
```

Essas URLs consideram a API iniciada pelo Docker Compose, que publica a porta `8088`. Se você executar o Uvicorn diretamente na porta padrão, use `8000`.

Variáveis `EXPO_PUBLIC_*` são incorporadas ao bundle e não devem conter segredos. A URL é pública; tokens de sessão são mantidos no `expo-secure-store` no Android e iOS. Na execução Web, a sessão fica somente em memória e é encerrada ao recarregar a página, evitando persistir o token em armazenamento web inseguro.

Para um dispositivo físico, inicie a API aceitando conexões da rede:

```powershell
cd ..\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0
```

O computador e o aparelho devem estar na mesma rede, e a porta escolhida (`8088` com Compose ou `8000` com Uvicorn direto) deve estar liberada no firewall.

## Execução

Inicie o Metro bundler:

```powershell
npm start
```

Então pressione `a` para abrir no Android ou escaneie o QR code com o Expo Go. Atalhos diretos:

```powershell
npm run android
npm run ios
```

`npm run ios` abre o iOS Simulator apenas no macOS. Como o projeto usa Continuous Native Generation, as pastas nativas `android/` e `ios/` não são versionadas; configurações nativas ficam em `app.json` e nos config plugins.

## Verificações

```powershell
npm run typecheck
npm run lint
npm run doctor
```

O CI repete essas verificações, executa auditoria de dependências e gera o bundle das três plataformas. Builds nativos assinados usam `eas.json` e são iniciados manualmente pelo workflow **Delivery Mobile**, após configurar no ambiente GitHub escolhido:

- secret `EXPO_TOKEN`;
- variable `EXPO_PUBLIC_API_URL` com HTTPS para preview/produção;
- vínculo inicial do projeto com `eas init`.

## Arquitetura

```text
src/
  app/                 rotas e layouts do Expo Router
  api/                 cliente HTTP, erros e TanStack Query
  auth/                sessão e armazenamento seguro
  components/          componentes reutilizáveis
  config/              configuração por ambiente
  design-system/       tokens visuais
  features/            contratos, schemas e serviços por domínio
  hooks/               hooks compartilhados
  utils/               utilitários sem dependência de domínio
```

O cliente HTTP aplica timeout, serializa JSON, normaliza erros do FastAPI e adiciona Bearer somente quando uma chamada declara `authenticated: true`. Uma resposta `401` autenticada encerra a sessão local. Mutações não possuem retry automático.

## Integração disponível

- `POST /usuarios`: cadastro real, respeitando os limites do contrato.
- `POST /auth/login`: login real e armazenamento seguro do access token.
- Home autenticada: estrutura visual inicial, sem dados fictícios.
- Explorar: listagem real de `GET /pontos-interesse`, com atribuição OpenStreetMap.
- Roteiros: listagem real e geração otimizada por `POST /roteiros/gerar`.
- Geração: origem, retorno ao ponto inicial e matriz viária configuráveis na tela.
- Perfil: consulta, cadastro e atualização das preferências reais do usuário.
- Logout: remove apenas a sessão local, pois o backend não oferece logout/revogação.

## Pendências contratuais

- O login não retorna um objeto de usuário e não existe `/usuarios/me`; o app usa provisoriamente o claim `sub` do JWT para obter o UUID necessário às preferências.
- Não há refresh token; um `401` limpa a sessão e exige novo login.
- Categorias/interesses ainda são strings livres e não existe endpoint de catálogo.
- POIs não incluem imagens, endereço, descrição ou horários.
- Atividades de um roteiro não incluem coordenadas; mapas exigiriam consultas adicionais.
- Roteiros não podem ser editados, reordenados, concluídos ou excluídos pela API atual.
- Listas não possuem paginação.
- A API ainda recebe valores somente em BRL. O app consulta taxas de referência da Frankfurter, converte BRL, EUR, GBP e USD antes do envio e apresenta os valores na moeda escolhida. Se a cotação estiver indisponível, moedas estrangeiras ficam bloqueadas para evitar valores incorretos.

Consulte `../ANALISE_TECNICA_FRONTEND.md` para o contrato completo e as regras de negócio.
