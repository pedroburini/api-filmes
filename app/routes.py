from fastapi import APIRouter, HTTPException, Query
from app.services import search_titles, get_title_details
from app.schemas import MovieResponse, SearchResult

router = APIRouter()

@router.get("/search", response_model=list[SearchResult])
async def search(q: str = Query(..., min_length=1, description="Título do filme ou série")):
    results = await search_titles(q)
    if not results:
        raise HTTPException(status_code=404, detail="Nenhum resultado encontrado")
    return results

@router.get("/details/{media_type}/{tmdb_id}", response_model=MovieResponse)
async def details(tmdb_id: int, media_type: str):
    if media_type not in ["movie", "tv"]:
        raise HTTPException(status_code=400, detail="media_type deve ser 'movie' ou 'tv'")
    result = await get_title_details(tmdb_id, media_type)
    return result
