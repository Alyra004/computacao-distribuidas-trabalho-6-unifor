"""Núcleo compartilhado do serviço de streaming de músicas em Python."""

from .models import Musica, Playlist, Usuario
from .repository import InMemoryStreamingRepository
from .service import (
    EntityNotFoundError,
    StreamingService,
    ValidationError,
    get_streaming_service,
)

__all__ = [
    "EntityNotFoundError",
    "InMemoryStreamingRepository",
    "Musica",
    "Playlist",
    "StreamingService",
    "Usuario",
    "ValidationError",
    "get_streaming_service",
]
