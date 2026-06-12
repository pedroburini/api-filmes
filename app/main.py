from fastapi import FastAPI
from app.routes import router

app = FastAPI(
    title="API de Filmes e Séries",
    description="Agregador de informações e notas de filmes e séries usando TMDB e OMDb",
    version="1.0.0"
)

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "API de Filmes e Séries — acesse /docs para a documentação"}
