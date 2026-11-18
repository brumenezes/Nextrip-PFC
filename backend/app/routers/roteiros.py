from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import obter_usuario_atual
from app.models.domain_models import (
    Usuario,
    Preferencias,
    PontoDeInteresse,
    Roteiro,
    RoteiroDia,
    VisitaAtividade
)

from app.schemas.roteiro import (
    GerarRoteiroRequest,
    GerarRoteiroResponse,
    AtividadeRoteiroResponse,
    RoteiroResumoResponse,
    RoteiroDiaResponse,
    RoteiroDetalhadoResponse
)
from app.services.gerador_roteiros import selecionar_pontos_interesse


router = APIRouter(
    prefix="/roteiros",
    tags=["Roteiros"]
)


@router.post(
    "/gerar",
    response_model=GerarRoteiroResponse,
    status_code=status.HTTP_201_CREATED
)
def gerar_roteiro(
    dados: GerarRoteiroRequest,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual)
):
    """
    Gera e salva um roteiro turístico de um dia,
    respeitando orçamento e tempo disponível.
    """
    # Consulta as preferências do usuário autenticado
    preferencias = db.scalar(
        select(Preferencias).where(
            Preferencias.usuario_id == usuario_atual.id
        )
    )

    # Se não houver preferências, utiliza uma lista vazia
    interesses_usuario = (
        preferencias.interesses or []
        if preferencias is not None
        else []
    )


    # 1. Consulta os pontos turísticos cadastrados
    pontos = db.scalars(
        select(PontoDeInteresse)
    ).all()

    if not pontos:
        raise HTTPException(
            status_code=404,
            detail="Nenhum ponto turístico cadastrado"
        )

    # 2. Seleciona as atrações
    selecionados, custo_total, tempo_total = selecionar_pontos_interesse(
        pontos=list(pontos),
        orcamento_maximo=dados.orcamento_maximo,
        tempo_disponivel_minutos=dados.tempo_disponivel_minutos,
        interesses=interesses_usuario
    )

    if not selecionados:
        raise HTTPException(
            status_code=422,
            detail="Nenhuma atração atende ao orçamento e tempo disponíveis"
        )

    # 3. Cria o roteiro associado ao usuário autenticado
    novo_roteiro = Roteiro(
        usuario_id=usuario_atual.id,
        data_inicio=dados.data_visita,
        data_fim=dados.data_visita,
        custo_total_estimado=custo_total
    )

    # 4. Cria o dia do roteiro
    novo_dia = RoteiroDia(
        roteiro=novo_roteiro,
        data_referencia=dados.data_visita,
        tempo_disponivel_minutos=dados.tempo_disponivel_minutos
    )

    db.add(novo_roteiro)
    db.add(novo_dia)

    # 5. Adiciona as atrações selecionadas
    atividades_resposta = []

    for ordem, ponto in enumerate(selecionados, start=1):
        visita = VisitaAtividade(
            roteiro_dia=novo_dia,
            poi_id=ponto.id,
            ordem_sequencia=ordem,
            status="Planejado"
        )

        db.add(visita)

        atividades_resposta.append(
            AtividadeRoteiroResponse(
                poi_id=ponto.id,
                nome=ponto.nome,
                categoria=ponto.categoria,
                ordem_sequencia=ordem,
                preco_estimado=ponto.preco_estimado,
                duracao_minutos=ponto.duracao_minutos
            )
        )

    # 6. Salva todos os registros no banco
    try:
        db.commit()
        db.refresh(novo_roteiro)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erro ao salvar o roteiro no banco de dados"
        )

    # 7. Retorna o roteiro gerado
    return GerarRoteiroResponse(
        roteiro_id=novo_roteiro.id,
        data_visita=dados.data_visita,
        tempo_disponivel_minutos=dados.tempo_disponivel_minutos,
        tempo_total_visitas=tempo_total,
        orcamento_maximo=dados.orcamento_maximo,
        custo_total_estimado=custo_total,
        atividades=atividades_resposta
    )


# ==========================================
# GET - LISTAR ROTEIROS DO USUÁRIO
# ==========================================

@router.get(
    "",
    response_model=list[RoteiroResumoResponse]
)
def listar_roteiros(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual)
):
    """
    Lista os roteiros do usuário autenticado.
    """

    roteiros = db.scalars(
        select(Roteiro)
        .where(Roteiro.usuario_id == usuario_atual.id)
        .order_by(Roteiro.data_inicio.desc())
    ).all()

    return roteiros


# ==========================================
# GET - CONSULTAR ROTEIRO POR ID
# ==========================================

@router.get(
    "/{roteiro_id}",
    response_model=RoteiroDetalhadoResponse
)
def consultar_roteiro(
    roteiro_id: UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual)
):
    """
    Consulta um roteiro específico, incluindo
    seus dias e pontos turísticos.
    """

    # Busca somente roteiros pertencentes ao usuário
    roteiro = db.scalar(
        select(Roteiro).where(
            Roteiro.id == roteiro_id,
            Roteiro.usuario_id == usuario_atual.id
        )
    )

    if roteiro is None:
        raise HTTPException(
            status_code=404,
            detail="Roteiro não encontrado"
        )

    dias_resposta = []

    # Percorre os dias do roteiro
    for dia in sorted(
        roteiro.dias,
        key=lambda item: item.data_referencia
    ):
        atividades_resposta = []

        # Percorre as atividades na ordem de visita
        for visita in sorted(
            dia.atividades,
            key=lambda item: item.ordem_sequencia
        ):
            ponto = db.get(PontoDeInteresse, visita.poi_id)

            if ponto is None:
                continue

            atividades_resposta.append(
                AtividadeRoteiroResponse(
                    poi_id=ponto.id,
                    nome=ponto.nome,
                    categoria=ponto.categoria,
                    ordem_sequencia=visita.ordem_sequencia,
                    preco_estimado=ponto.preco_estimado or 0.0,
                    duracao_minutos=ponto.duracao_minutos or 0
                )
            )

        dias_resposta.append(
            RoteiroDiaResponse(
                data_referencia=dia.data_referencia,
                tempo_disponivel_minutos=dia.tempo_disponivel_minutos,
                atividades=atividades_resposta
            )
        )

    return RoteiroDetalhadoResponse(
        id=roteiro.id,
        data_inicio=roteiro.data_inicio,
        data_fim=roteiro.data_fim,
        custo_total_estimado=roteiro.custo_total_estimado,
        dias=dias_resposta
    )

