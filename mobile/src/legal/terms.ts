export const TERMS_VERSION = '2026-11-22';

export const TERMS_SECTIONS = [
  {
    title: 'Termos de uso',
    paragraphs: [
      'O NexTrip é um aplicativo de planejamento turístico. Roteiros, preços, horários, distâncias e disponibilidade são estimativas e devem ser conferidos antes do passeio.',
      'O usuário deve fornecer informações verdadeiras, proteger sua senha e utilizar o serviço de forma lícita. É proibido tentar acessar contas de terceiros, explorar vulnerabilidades ou inserir conteúdo que viole direitos.',
      'O serviço pode usar provedores de mapas, rotas, câmbio e conteúdo turístico. A disponibilidade desses serviços externos não é garantida pelo NexTrip.',
    ],
  },
  {
    title: 'Aviso de privacidade LGPD',
    paragraphs: [
      'Tratamos nome, e-mail, credencial protegida por hash, preferências de viagem, orçamento, roteiros e dados de localização fornecidos durante o uso. Não armazenamos a senha em texto aberto.',
      'Os dados são usados para criar e proteger a conta, autenticar o usuário, personalizar recomendações, gerar roteiros, manter o histórico solicitado e operar o serviço. A localização é usada somente quando o usuário a fornece para calcular um roteiro.',
      'As bases legais devem corresponder à execução do serviço solicitado, ao cumprimento de obrigações legais e, quando aplicável, ao consentimento livre e informado. Os dados não devem ser vendidos nem usados para publicidade comportamental sem informação e base legal específicas.',
      'O usuário pode solicitar confirmação de tratamento, acesso, correção, portabilidade quando aplicável, informação sobre compartilhamento, revogação de consentimento e eliminação nos limites da LGPD. Solicitações devem ser encaminhadas ao responsável identificado pelo projeto antes da publicação do aplicativo.',
      'Os dados devem ser mantidos apenas pelo período necessário às finalidades informadas, à segurança e às obrigações legais. Ambientes de produção devem utilizar HTTPS, controle de acesso, backups protegidos, monitoramento e resposta a incidentes.',
    ],
  },
  {
    title: 'Serviços externos e transferências',
    paragraphs: [
      'O cálculo de rotas pode consultar o OSRM; cotações podem consultar a Frankfurter; mapas e conteúdo turístico podem depender de outros provedores informados na tela. Antes da produção, o controlador deve avaliar contratos, localização dos servidores, retenção, licenças e eventual transferência internacional.',
    ],
  },
  {
    title: 'Versão e alterações',
    paragraphs: [
      `Versão ${TERMS_VERSION}. Mudanças relevantes nas finalidades ou no tratamento exigem novo aviso e, quando necessário, novo consentimento. Este texto é uma base técnica para o protótipo e deve passar por revisão jurídica antes da publicação comercial.`,
    ],
  },
] as const;

