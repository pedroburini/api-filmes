from pydantic import BaseModel
from typing import Optional

class StreamingProvider(BaseModel):
    provider_name: str
    logo_path: Optional[str] = None

class MovieResponse(BaseModel):
    title: str
    year: Optional[str] = None
    synopsis: Optional[str] = None
    director: Optional[str] = None
    cast: Optional[str] = None
    genres: Optional[str] = None
    poster: Optional[str] = None
    runtime: Optional[str] = None
    
    # Notas
    imdb_rating: Optional[str] = None
    rotten_tomatoes: Optional[str] = None
    metacritic: Optional[str] = None
    tmdb_rating: Optional[str] = None
    average_rating: Optional[float] = None
    
    # Streaming
    streaming: Optional[list[StreamingProvider]] = None

class SearchResult(BaseModel):
    tmdb_id: int
    title: str
    year: Optional[str] = None
    poster: Optional[str] = None
    media_type: str
    