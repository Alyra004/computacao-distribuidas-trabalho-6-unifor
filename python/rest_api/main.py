"""Entrega Python 1: API REST com FastAPI reutilizando common.StreamingService."""

from __future__ import annotations

import os
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from common.service import (
    EntityNotFoundError,
    StreamingService,
    ValidationError,
    get_streaming_service,
)

app = FastAPI(
    title="Streaming de Músicas - Python REST",
    version="1.0.0",
    description="Implementação REST (Trabalho 6 - Computação Distribuída / UNIFOR).",
)

service: StreamingService = get_streaming_service()


class UsuarioInput(BaseModel):
    id: Optional[str] = None
    nome: str = Field(..., min_length=1)
    idade: int = Field(..., ge=0)


class MusicaInput(BaseModel):
    id: Optional[str] = None
    nome: str = Field(..., min_length=1)
    artista: str = Field(..., min_length=1)


class PlaylistInput(BaseModel):
    id: Optional[str] = None
    nome: str = Field(..., min_length=1)
    usuarioId: str = Field(..., min_length=1)
    musicaIds: Optional[list[str]] = None


@app.exception_handler(EntityNotFoundError)
async def not_found_handler(_: Request, exc: EntityNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"erro": str(exc)})


@app.exception_handler(ValidationError)
async def validation_handler(_: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"erro": str(exc)})


@app.get("/health")
def health() -> dict[str, object]:
    return service.health_check()


@app.post("/reset")
def reset() -> dict[str, object]:
    return service.reset_seed()


# =============================================================================
# Usuários
# =============================================================================


@app.get("/usuarios")
def listar_usuarios() -> list[dict]:
    return [u.to_dict() for u in service.listar_usuarios()]


@app.get("/usuarios/{usuario_id}")
def obter_usuario(usuario_id: str) -> dict:
    return service.obter_usuario(usuario_id).to_dict()


@app.post("/usuarios", status_code=status.HTTP_201_CREATED)
def criar_usuario(payload: UsuarioInput) -> dict:
    return service.criar_usuario(nome=payload.nome, idade=payload.idade, id=payload.id).to_dict()


@app.put("/usuarios/{usuario_id}")
def atualizar_usuario(usuario_id: str, payload: UsuarioInput) -> dict:
    return service.atualizar_usuario(
        usuario_id=usuario_id, nome=payload.nome, idade=payload.idade
    ).to_dict()


@app.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_usuario(usuario_id: str) -> None:
    service.remover_usuario(usuario_id)


@app.get("/usuarios/{usuario_id}/playlists")
def listar_playlists_por_usuario(usuario_id: str) -> list[dict]:
    return [p.to_dict() for p in service.listar_playlists_por_usuario(usuario_id)]


# =============================================================================
# Músicas
# =============================================================================


@app.get("/musicas")
def listar_musicas() -> list[dict]:
    return [m.to_dict() for m in service.listar_musicas()]


@app.get("/musicas/{musica_id}")
def obter_musica(musica_id: str) -> dict:
    return service.obter_musica(musica_id).to_dict()


@app.post("/musicas", status_code=status.HTTP_201_CREATED)
def criar_musica(payload: MusicaInput) -> dict:
    return service.criar_musica(nome=payload.nome, artista=payload.artista, id=payload.id).to_dict()


@app.put("/musicas/{musica_id}")
def atualizar_musica(musica_id: str, payload: MusicaInput) -> dict:
    return service.atualizar_musica(
        musica_id=musica_id, nome=payload.nome, artista=payload.artista
    ).to_dict()


@app.delete("/musicas/{musica_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_musica(musica_id: str) -> None:
    service.remover_musica(musica_id)


@app.get("/musicas/{musica_id}/playlists")
def listar_playlists_por_musica(musica_id: str) -> list[dict]:
    return [p.to_dict() for p in service.listar_playlists_por_musica(musica_id)]


# =============================================================================
# Playlists
# =============================================================================


@app.get("/playlists")
def listar_playlists() -> list[dict]:
    return [p.to_dict() for p in service.listar_playlists()]


@app.get("/playlists/{playlist_id}")
def obter_playlist(playlist_id: str) -> dict:
    return service.obter_playlist(playlist_id).to_dict()


@app.post("/playlists", status_code=status.HTTP_201_CREATED)
def criar_playlist(payload: PlaylistInput) -> dict:
    return service.criar_playlist(
        nome=payload.nome,
        usuario_id=payload.usuarioId,
        musica_ids=payload.musicaIds,
        id=payload.id,
    ).to_dict()


@app.put("/playlists/{playlist_id}")
def atualizar_playlist(playlist_id: str, payload: PlaylistInput) -> dict:
    return service.atualizar_playlist(
        playlist_id=playlist_id,
        nome=payload.nome,
        usuario_id=payload.usuarioId,
        musica_ids=payload.musicaIds,
    ).to_dict()


@app.delete("/playlists/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_playlist(playlist_id: str) -> None:
    service.remover_playlist(playlist_id)


@app.get("/playlists/{playlist_id}/musicas")
def listar_musicas_por_playlist(playlist_id: str) -> list[dict]:
    return [m.to_dict() for m in service.listar_musicas_por_playlist(playlist_id)]


@app.post("/playlists/{playlist_id}/musicas/{musica_id}")
def adicionar_musica_na_playlist(playlist_id: str, musica_id: str) -> dict:
    return service.adicionar_musica_na_playlist(playlist_id, musica_id).to_dict()


@app.delete("/playlists/{playlist_id}/musicas/{musica_id}")
def remover_musica_da_playlist(playlist_id: str, musica_id: str) -> dict:
    return service.remover_musica_da_playlist(playlist_id, musica_id).to_dict()


if __name__ == "__main__":
    uvicorn.run("rest_api.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
