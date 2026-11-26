from datetime import datetime, timezone

from sqlalchemy import select, text

from app.database import SessionLocal
from app.models.domain_models import Usuario, Preferencias
from app.core.security import gerar_hash_senha
from app.core.privacy import TERMS_VERSION, PRIVACY_NOTICE_VERSION


BANCO_PERFORMANCE = "nextrip_performance_db"
QUANTIDADE_USUARIOS = 100
SENHA_TESTE = "NextripPerformance123"

PERFIS_INTERESSES = [
    ["cultura", "historia"],
    ["gastronomia", "compras"],
    ["natureza", "cultura"],
    ["museu", "galeria"],
    ["parque", "mirante"],
]


def main():
    with SessionLocal() as sessao:

        # Proteção contra execução no banco incorreto
        banco_atual = sessao.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if banco_atual != BANCO_PERFORMANCE:
            raise RuntimeError(
                "Execução bloqueada: este script só pode "
                "ser executado no banco de desempenho."
            )

        print(f"Banco confirmado: {banco_atual}")

        usuarios_criados = 0
        usuarios_existentes = 0
        preferencias_criadas = 0

        try:
            for numero in range(1, QUANTIDADE_USUARIOS + 1):
                email = f"performance{numero:03d}@example.com"

                usuario = sessao.scalar(
                    select(Usuario).where(Usuario.email == email)
                )

                if usuario is None:
                    agora = datetime.now(timezone.utc)

                    usuario = Usuario(
                        nome=f"Usuario Performance {numero:03d}",
                        email=email,
                        senha_hash=gerar_hash_senha(SENHA_TESTE),
                        termos_versao=TERMS_VERSION,
                        termos_aceitos_em=agora,
                        privacidade_versao=PRIVACY_NOTICE_VERSION,
                        privacidade_aceita_em=agora,
                    )

                    sessao.add(usuario)
                    sessao.flush()

                    usuarios_criados += 1
                else:
                    usuarios_existentes += 1

                preferencias = sessao.scalar(
                    select(Preferencias).where(
                        Preferencias.usuario_id == usuario.id
                    )
                )

                if preferencias is None:
                    interesses = PERFIS_INTERESSES[
                        (numero - 1) % len(PERFIS_INTERESSES)
                    ]

                    preferencias = Preferencias(
                        usuario_id=usuario.id,
                        orcamento_maximo=200.0,
                        interesses=interesses,
                    )

                    sessao.add(preferencias)
                    preferencias_criadas += 1

                if numero % 10 == 0:
                    print(
                        f"Processados: {numero}/"
                        f"{QUANTIDADE_USUARIOS}"
                    )

            sessao.commit()

        except Exception:
            sessao.rollback()
            raise

        print("\nPreparação concluída!")
        print(f"Usuários criados: {usuarios_criados}")
        print(f"Usuários existentes: {usuarios_existentes}")
        print(f"Preferências criadas: {preferencias_criadas}")


if __name__ == "__main__":
    main()
