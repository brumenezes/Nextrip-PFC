from uuid import uuid4
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import date
from sqlalchemy import func

from app.models.domain_models import (
    Usuario,
    Preferencias,
    PontoDeInteresse,
    Roteiro,
    RoteiroDia,
    VisitaAtividade
)

# Carrega as variÃ¡veis de ambiente do arquivo .env
load_dotenv()

# Recupera a conexÃ£o exclusiva do banco de testes
DATABASE_TEST_URL = os.getenv("TEST_DATABASE_URL")

if not DATABASE_TEST_URL:
    raise RuntimeError(
        "A variÃ¡vel TEST_DATABASE_URL nÃ£o foi configurada."
    )

def test_cadastrar_e_consultar_usuario_postgresql():
    # ProteÃ§Ã£o: impede o teste de utilizar o banco principal.
    assert DATABASE_TEST_URL.rsplit("/", 1)[-1] == "nextrip_test_db"

    engine = create_engine(DATABASE_TEST_URL)

    try:
        with engine.connect() as conexao:
            transacao = conexao.begin()

            try:
                with Session(
                    bind=conexao,
                    join_transaction_mode="create_savepoint"
                ) as sessao:

                    usuario = Usuario(
                        id=uuid4(),
                        nome="Usuario Integracao",
                        email=f"integracao-{uuid4()}@example.com",
                        senha_hash="hash-ficticio"
                    )

                    sessao.add(usuario)
                    sessao.flush()

                    usuario_encontrado = sessao.scalar(
                        select(Usuario).where(
                            Usuario.id == usuario.id
                        )
                    )

                    assert usuario_encontrado is not None
                    assert usuario_encontrado.nome == "Usuario Integracao"
                    assert usuario_encontrado.email == usuario.email

            finally:
                # Desfaz as alteraÃ§Ãµes, mesmo se o teste falhar.
                transacao.rollback()

    finally:
        engine.dispose()


def test_calcular_distancia_postgis():
    from sqlalchemy import text

    assert DATABASE_TEST_URL.rsplit("/", 1)[-1] == "nextrip_test_db"

    engine = create_engine(DATABASE_TEST_URL)

    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                text("""
                    SELECT ST_Distance(
                        ST_SetSRID(
                            ST_MakePoint(-46.6097, -23.5855),
                            4326
                        )::geography,
                        ST_SetSRID(
                            ST_MakePoint(-46.6559, -23.5614),
                            4326
                        )::geography
                    ) AS distancia_metros
                """)
            ).scalar_one()

            # A distÃ¢ncia entre o Museu do Ipiranga
            # e o MASP deve ser maior que 5 km
            # e menor que 6 km, aproximadamente.
            assert 5000 < resultado < 6000

    finally:
        engine.dispose()


def test_cadastrar_e_consultar_ponto_turistico_postgresql():
    from sqlalchemy import func, cast
    from geoalchemy2 import Geometry

    assert DATABASE_TEST_URL.rsplit("/", 1)[-1] == "nextrip_test_db"

    engine = create_engine(DATABASE_TEST_URL)

    try:
        with engine.connect() as conexao:
            transacao = conexao.begin()

            try:
                with Session(
                    bind=conexao,
                    join_transaction_mode="create_savepoint"
                ) as sessao:

                    ponto = PontoDeInteresse(
                        id=uuid4(),
                        nome="Museu Teste NexTrip",
                        categoria="Museu",
                        localizacao=func.ST_SetSRID(
                            func.ST_MakePoint(-46.6097, -23.5855),
                            4326
                        ),
                        preco_estimado=30.0,
                        duracao_minutos=120,
                        avaliacao_media=4.7,
                        horarios_funcionamento={
                            "segunda": "09:00-17:00"
                        },
                        dados_brutos_osm={
                            "origem": "teste_integracao"
                        }
                    )

                    sessao.add(ponto)
                    sessao.flush()

                    resultado = sessao.execute(
                        select(
                            PontoDeInteresse.nome,
                            PontoDeInteresse.categoria,
                            PontoDeInteresse.preco_estimado,
                            PontoDeInteresse.duracao_minutos,
                            PontoDeInteresse.horarios_funcionamento,
                            func.ST_Y(
                                cast(PontoDeInteresse.localizacao, Geometry)
                            ).label("latitude"),
                            func.ST_X(
                                cast(PontoDeInteresse.localizacao, Geometry)
                            ).label("longitude")

                        ).where(
                            PontoDeInteresse.id == ponto.id
                        )
                    ).one()

                    assert resultado.nome == "Museu Teste NexTrip"
                    assert resultado.categoria == "Museu"
                    assert resultado.preco_estimado == 30.0
                    assert resultado.duracao_minutos == 120

                    assert resultado.horarios_funcionamento == {
                        "segunda": "09:00-17:00"
                    }

                    assert abs(resultado.latitude - (-23.5855)) < 0.0001
                    assert abs(resultado.longitude - (-46.6097)) < 0.0001

            finally:
                transacao.rollback()

    finally:
        engine.dispose()


def test_salvar_e_consultar_preferencias_postgresql():
    assert DATABASE_TEST_URL.rsplit("/", 1)[-1] == "nextrip_test_db"

    engine = create_engine(DATABASE_TEST_URL)

    try:
        with engine.connect() as conexao:
            transacao = conexao.begin()

            try:
                with Session(
                    bind=conexao,
                    join_transaction_mode="create_savepoint"
                ) as sessao:

                    usuario = Usuario(
                        id=uuid4(),
                        nome="Usuario Teste Preferencias",
                        email=f"preferencias-{uuid4()}@example.com",
                        senha_hash="hash-ficticio"
                    )

                    sessao.add(usuario)
                    sessao.flush()

                    preferencias = Preferencias(
                        id=uuid4(),
                        usuario_id=usuario.id,
                        orcamento_maximo=150.0,
                        interesses=["Museu", "Parque"]
                    )

                    sessao.add(preferencias)
                    sessao.flush()

                    resultado = sessao.scalar(
                        select(Preferencias).where(
                            Preferencias.usuario_id == usuario.id
                        )
                    )

                    assert resultado is not None
                    assert resultado.usuario_id == usuario.id
                    assert resultado.orcamento_maximo == 150.0
                    assert resultado.interesses == ["Museu", "Parque"]

                    # Confirma o relacionamento com o usuÃ¡rio.
                    assert resultado.usuario.id == usuario.id

            finally:
                transacao.rollback()

    finally:
        engine.dispose()

def test_salvar_roteiro_com_atividades_postgresql():
    assert DATABASE_TEST_URL.rsplit("/", 1)[-1] == "nextrip_test_db"

    engine = create_engine(DATABASE_TEST_URL)

    try:
        with engine.connect() as conexao:
            transacao = conexao.begin()

            try:
                with Session(
                    bind=conexao,
                    join_transaction_mode="create_savepoint"
                ) as sessao:

                    # 1. Cria um usuÃ¡rio de teste
                    usuario = Usuario(
                        id=uuid4(),
                        nome="Usuario Teste Roteiro",
                        email=f"roteiro-{uuid4()}@example.com",
                        senha_hash="hash-ficticio"
                    )
                    sessao.add(usuario)
                    sessao.flush()

                    # 2. Cria um ponto turÃ­stico
                    ponto = PontoDeInteresse(
                        id=uuid4(),
                        nome="Museu Teste Roteiro",
                        categoria="Museu",
                        localizacao=func.ST_SetSRID(
                            func.ST_MakePoint(-46.6097, -23.5855),
                            4326
                        ),
                        preco_estimado=30.0,
                        duracao_minutos=120
                    )
                    sessao.add(ponto)
                    sessao.flush()

                    # 3. Cria o roteiro
                    roteiro = Roteiro(
                        id=uuid4(),
                        usuario_id=usuario.id,
                        data_inicio=date(2026, 11, 24),
                        data_fim=date(2026, 11, 24),
                        custo_total_estimado=30.0
                    )
                    sessao.add(roteiro)
                    sessao.flush()

                    # 4. Cria o dia do roteiro
                    dia = RoteiroDia(
                        id=uuid4(),
                        roteiro_id=roteiro.id,
                        data_referencia=date(2026, 11, 24),
                        tempo_disponivel_minutos=360
                    )
                    sessao.add(dia)
                    sessao.flush()

                    # 5. Cria a atividade turÃ­stica
                    atividade = VisitaAtividade(
                        id=uuid4(),
                        roteiro_dia_id=dia.id,
                        poi_id=ponto.id,
                        ordem_sequencia=1,
                        tempo_deslocamento_previsto=0,
                        distancia_deslocamento_metros=0.0,
                        status="Planejado"
                    )
                    sessao.add(atividade)
                    sessao.flush()

                    # 6. Consulta os dados salvos
                    roteiro_salvo = sessao.get(Roteiro, roteiro.id)

                    assert roteiro_salvo is not None
                    assert roteiro_salvo.usuario_id == usuario.id
                    assert roteiro_salvo.custo_total_estimado == 30.0

                    assert len(roteiro_salvo.dias) == 1

                    dia_salvo = roteiro_salvo.dias[0]
                    assert dia_salvo.tempo_disponivel_minutos == 360
                    assert len(dia_salvo.atividades) == 1

                    atividade_salva = dia_salvo.atividades[0]
                    assert atividade_salva.poi_id == ponto.id
                    assert atividade_salva.ordem_sequencia == 1
                    assert atividade_salva.status == "Planejado"
                    assert atividade_salva.ponto_turistico.nome == "Museu Teste Roteiro"

            finally:
                # Desfaz todos os registros criados pelo teste
                transacao.rollback()

    finally:
        engine.dispose()
