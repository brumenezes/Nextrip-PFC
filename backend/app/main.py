from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.usuarios import router as usuarios_router
from app.routers.preferencias import router as preferencias_router
from app.routers.auth import router as auth_router
from app.routers.pontos_interesse import router as pontos_interesse_router
from app.routers.roteiros import router as roteiros_router

# Criação da aplicação FastAPI
app = FastAPI(
    title="NexTrip API",
    description="API para geração de roteiros turísticos personalizados",
    version="0.1.0"
)

app.include_router(auth_router)

# Registro das rotas de usuários
app.include_router(usuarios_router)
app.include_router(preferencias_router)
app.include_router(auth_router)
app.include_router(pontos_interesse_router)
app.include_router(roteiros_router)

# Endpoint inicial
@app.get("/")
def home():
    return {
        "mensagem": "Bem-vindo à API do NexTrip!"
    }


# Endpoint para verificar se a API está funcionando
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "servico": "NexTrip Backend"
    }


@app.get("/health/db")
def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "banco": "PostgreSQL",
            "conexao": "ativa"
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Banco de dados indisponível"
        )

