import uuid
from sqlalchemy import Column, String, Float, Integer, ForeignKey, Date, Time, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from pgvector.sqlalchemy import Vector

from app.database import Base

class Usuario(Base):
    __tablename__ = 'usuario'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    senha_hash = Column(String, nullable=False)

    preferencias = relationship("Preferencias", back_populates="usuario", uselist=False)
    roteiros = relationship("Roteiro", back_populates="usuario")

class Preferencias(Base):
    __tablename__ = 'preferencias'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuario.id'), nullable=False)
    orcamento_maximo = Column(Float, nullable=True)
    perfil_embedding = Column(Vector(384), nullable=True) 

    usuario = relationship("Usuario", back_populates="preferencias")

class Roteiro(Base):
    __tablename__ = 'roteiro'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuario.id'), nullable=False)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=False)
    custo_total_estimado = Column(Float, nullable=True)

    usuario = relationship("Usuario", back_populates="roteiros")
    dias = relationship("RoteiroDia", back_populates="roteiro", cascade="all, delete-orphan")

class RoteiroDia(Base):
    __tablename__ = 'roteiro_dia'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roteiro_id = Column(UUID(as_uuid=True), ForeignKey('roteiro.id'), nullable=False)
    data_referencia = Column(Date, nullable=False)
    tempo_disponivel_minutos = Column(Integer, nullable=False)

    roteiro = relationship("Roteiro", back_populates="dias")
    atividades = relationship("VisitaAtividade", back_populates="roteiro_dia", cascade="all, delete-orphan")

class PontoDeInteresse(Base):
    __tablename__ = 'ponto_de_interesse'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    osm_id = Column(BigInteger, nullable=True)
    google_place_id = Column(String, nullable=True)
    nome = Column(String, nullable=False)
    categoria = Column(String, nullable=True)
    localizacao = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    preco_estimado = Column(Float, nullable=True)
    duracao_minutos = Column(Integer, nullable=True)
    horarios_funcionamento = Column(JSONB, nullable=True)
    avaliacao_media = Column(Float, nullable=True)
    descricao_embedding = Column(Vector(384), nullable=True)
    dados_brutos_osm = Column(JSONB, nullable=True)

    visitas = relationship("VisitaAtividade", back_populates="ponto_turistico")

class VisitaAtividade(Base):
    __tablename__ = 'visita_atividade'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roteiro_dia_id = Column(UUID(as_uuid=True), ForeignKey('roteiro_dia.id'), nullable=False)
    poi_id = Column(UUID(as_uuid=True), ForeignKey('ponto_de_interesse.id'), nullable=False)
    ordem_sequencia = Column(Integer, nullable=False)
    horario_inicio = Column(Time, nullable=True)
    horario_fim = Column(Time, nullable=True)
    tempo_deslocamento_previsto = Column(Integer, nullable=True)
    distancia_deslocamento_metros = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="Planejado")

    roteiro_dia = relationship("RoteiroDia", back_populates="atividades")
    ponto_turistico = relationship("PontoDeInteresse", back_populates="visitas")