
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, cast
from geoalchemy2 import Geometry
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.domain_models import PontoDeInteresse
from app.schemas.ponto_interesse import (
    PontoInteresseCreate,
    PontoInteresseResponse
)


router = APIRouter(
    prefix="/pontos-interesse",
    tags=["Pontos de Interesse"]
)


def converter_poi_para_resposta(poi, latitude, longitude):
    """
    Converte um ponto turístico do banco de dados
    para o formato de resposta da API.
    """
    return PontoInteresseResponse(
        id=poi.id,
        nome=poi.nome,
        categoria=poi.categoria,
        latitude=latitude,
        longitude=longitude,
        preco_estimado=poi.preco_estimado,
        duracao_minutos=poi.duracao_minutos,
        avaliacao_media=poi.avaliacao_media,
        osm_id=poi.osm_id,
        google_place_id=poi.google_place_id
    )


# ==========================================
# POST - CADASTRAR PONTO DE INTERESSE
# ==========================================

@router.post(
    "",
    response_model=PontoInteresseResponse,
    status_code=status.HTTP_201_CREATED
)
def cadastrar_ponto_interesse(
    dados: PontoInteresseCreate,
    db: Session = Depends(get_db)
):
    novo_poi = PontoDeInteresse(
        nome=dados.nome,
        categoria=dados.categoria,
        localizacao=func.ST_SetSRID(
            func.ST_MakePoint(
                dados.longitude,
                dados.latitude
            ),
            4326
        ),
        preco_estimado=dados.preco_estimado,
        duracao_minutos=dados.duracao_minutos,
        avaliacao_media=dados.avaliacao_media,
        osm_id=dados.osm_id,
        google_place_id=dados.google_place_id
    )

    db.add(novo_poi)
    db.commit()
    db.refresh(novo_poi)

    
    coordenadas = db.execute(
        select(
            func.ST_Y(cast(novo_poi.localizacao, Geometry)),
            func.ST_X(cast(novo_poi.localizacao, Geometry))
        )
    ).one()


    return converter_poi_para_resposta(
        novo_poi,
        coordenadas[0],
        coordenadas[1]
    )


# ==========================================
# GET - LISTAR PONTOS DE INTERESSE
# ==========================================

@router.get(
    "",
    response_model=list[PontoInteresseResponse]
)
def listar_pontos_interesse(
    db: Session = Depends(get_db)
):
    
    resultado = db.execute(
        select(
            PontoDeInteresse,
            func.ST_Y(
                cast(PontoDeInteresse.localizacao, Geometry)
            ).label("latitude"),
            func.ST_X(
                cast(PontoDeInteresse.localizacao, Geometry)
            ).label("longitude")
        )
    ).all()


    return [
        converter_poi_para_resposta(
            poi,
            latitude,
            longitude
        )
        for poi, latitude, longitude in resultado
    ]


# ==========================================
# GET - CONSULTAR PONTO POR ID
# ==========================================

@router.get(
    "/{poi_id}",
    response_model=PontoInteresseResponse
)
def consultar_ponto_interesse(
    poi_id: UUID,
    db: Session = Depends(get_db)
):
    
    resultado = db.execute(
        select(
            PontoDeInteresse,
            func.ST_Y(
                cast(PontoDeInteresse.localizacao, Geometry)
            ).label("latitude"),
            func.ST_X(
                cast(PontoDeInteresse.localizacao, Geometry)
            ).label("longitude")
        ).where(PontoDeInteresse.id == poi_id)
    ).one_or_none()


    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail="Ponto de interesse não encontrado"
        )

    poi, latitude, longitude = resultado

    return converter_poi_para_resposta(
        poi,
        latitude,
        longitude
    )
