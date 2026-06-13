from fastapi import APIRouter, HTTPException, Query
from app.services import search_titles, get_title_details, get_popular
from app.schemas import MovieResponse, SearchResult

router = APIRouter()

@router.get("/search", response_model=list[SearchResult])
async def search(q: str = Query(..., min_length=1, description="Título do filme ou série")):
    results = await search_titles(q)
    if not results:
        raise HTTPException(status_code=404, detail="Nenhum resultado encontrado")
    return results

@router.get("/popular", response_model=list[SearchResult])
async def popular(
    media_type: str = Query("all", description="movie, tv ou all"),
    genre_id: int = Query(None, description="ID do gênero TMDB"),
    year: int = Query(None, description="Ano de lançamento"),
    min_rating: float = Query(None, description="Nota mínima TMDB (0-10)"),
    page: int = Query(1, description="Página")
):
    results = await get_popular(media_type, genre_id, year, min_rating, page)
    return results

@router.get("/genres")
async def genres():
    from app.services import get_genres
    return await get_genres()

@router.get("/details/{media_type}/{tmdb_id}", response_model=MovieResponse)
async def details(tmdb_id: int, media_type: str):
    if media_type not in ["movie", "tv"]:
        raise HTTPException(status_code=400, detail="media_type deve ser 'movie' ou 'tv'")
    result = await get_title_details(tmdb_id, media_type)
    return result
