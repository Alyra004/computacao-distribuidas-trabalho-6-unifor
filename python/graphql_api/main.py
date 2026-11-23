"""Entrega Python 3: API GraphQL com Strawberry reutilizando common.StreamingService."""

from __future__ import annotations

import os
from typing import Optional

import strawberry
import uvicorn
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from common.models import Musica, Playlist, Usuario
from common.service import EntityNotFoundError, StreamingService, get_streaming_service

service: StreamingService = get_streaming_service()


@strawberry.type
class StatusResponseType:
    sucesso: bool
    mensagem: str


@strawberry.type
class MusicaType:
    id: strawberry.ID
    nome: str
    artista: str

    @strawberry.field
    def playlists(self) -> list["PlaylistType"]:
        return [_to_playlist_type(p) for p in service.listar_playlists_por_musica(str(self.id))]


@strawberry.type
class UsuarioType:
    id: strawberry.ID
    nome: str
    idade: int

    @strawberry.field
    def playlists(self) -> list["PlaylistType"]:
        return [_to_playlist_type(p) for p in service.listar_playlists_por_usuario(str(self.id))]


@strawberry.type
class PlaylistType:
    id: strawberry.ID
    nome: str
    usuario_id: strawberry.ID
    musica_ids: list[strawberry.ID]

    @strawberry.field
    def usuario(self) -> Optional[UsuarioType]:
        try:
            return _to_usuario_type(service.obter_usuario(str(self.usuario_id)))
        except EntityNotFoundError:
            return None

    @strawberry.field
    def musicas(self) -> list[MusicaType]:
        return [_to_musica_type(m) for m in service.listar_musicas_por_playlist(str(self.id))]


def _to_usuario_type(u: Usuario) -> UsuarioType:
    return UsuarioType(id=strawberry.ID(u.id), nome=u.nome, idade=u.idade)


def _to_musica_type(m: Musica) -> MusicaType:
    return MusicaType(id=strawberry.ID(m.id), nome=m.nome, artista=m.artista)


def _to_playlist_type(p: Playlist) -> PlaylistType:
    return PlaylistType(
        id=strawberry.ID(p.id),
        nome=p.nome,
        usuario_id=strawberry.ID(p.usuario_id),
        musica_ids=[strawberry.ID(mid) for mid in p.musica_ids],
    )


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> StatusResponseType:
        info = service.health_check()
        return StatusResponseType(sucesso=bool(info["sucesso"]), mensagem=str(info["mensagem"]))

    @strawberry.field
    def usuarios(self) -> list[UsuarioType]:
        return [_to_usuario_type(u) for u in service.listar_usuarios()]

    @strawberry.field
    def usuario(self, id: strawberry.ID) -> Optional[UsuarioType]:
        try:
            return _to_usuario_type(service.obter_usuario(str(id)))
        except EntityNotFoundError:
            return None

    @strawberry.field
    def musicas(self) -> list[MusicaType]:
        return [_to_musica_type(m) for m in service.listar_musicas()]

    @strawberry.field
    def musica(self, id: strawberry.ID) -> Optional[MusicaType]:
        try:
            return _to_musica_type(service.obter_musica(str(id)))
        except EntityNotFoundError:
            return None

    @strawberry.field
    def playlists(self) -> list[PlaylistType]:
        return [_to_playlist_type(p) for p in service.listar_playlists()]

    @strawberry.field
    def playlist(self, id: strawberry.ID) -> Optional[PlaylistType]:
        try:
            return _to_playlist_type(service.obter_playlist(str(id)))
        except EntityNotFoundError:
            return None

    @strawberry.field
    def playlists_por_usuario(self, usuario_id: strawberry.ID) -> list[PlaylistType]:
        return [_to_playlist_type(p) for p in service.listar_playlists_por_usuario(str(usuario_id))]

    @strawberry.field
    def musicas_por_playlist(self, playlist_id: strawberry.ID) -> list[MusicaType]:
        return [_to_musica_type(m) for m in service.listar_musicas_por_playlist(str(playlist_id))]

    @strawberry.field
    def playlists_por_musica(self, musica_id: strawberry.ID) -> list[PlaylistType]:
        return [_to_playlist_type(p) for p in service.listar_playlists_por_musica(str(musica_id))]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def reset_seed(self) -> StatusResponseType:
        info = service.reset_seed()
        return StatusResponseType(sucesso=bool(info["sucesso"]), mensagem=str(info["mensagem"]))

    @strawberry.mutation
    def criar_usuario(self, nome: str, idade: int, id: Optional[strawberry.ID] = None) -> UsuarioType:
        return _to_usuario_type(
            service.criar_usuario(nome=nome, idade=idade, id=str(id) if id else None)
        )

    @strawberry.mutation
    def atualizar_usuario(self, id: strawberry.ID, nome: str, idade: int) -> UsuarioType:
        return _to_usuario_type(service.atualizar_usuario(str(id), nome, idade))

    @strawberry.mutation
    def remover_usuario(self, id: strawberry.ID) -> bool:
        return service.remover_usuario(str(id))

    @strawberry.mutation
    def criar_musica(self, nome: str, artista: str, id: Optional[strawberry.ID] = None) -> MusicaType:
        return _to_musica_type(
            service.criar_musica(nome=nome, artista=artista, id=str(id) if id else None)
        )

    @strawberry.mutation
    def atualizar_musica(self, id: strawberry.ID, nome: str, artista: str) -> MusicaType:
        return _to_musica_type(service.atualizar_musica(str(id), nome, artista))

    @strawberry.mutation
    def remover_musica(self, id: strawberry.ID) -> bool:
        return service.remover_musica(str(id))

    @strawberry.mutation
    def criar_playlist(
        self,
        nome: str,
        usuario_id: strawberry.ID,
        musica_ids: Optional[list[strawberry.ID]] = None,
        id: Optional[strawberry.ID] = None,
    ) -> PlaylistType:
        return _to_playlist_type(
            service.criar_playlist(
                nome=nome,
                usuario_id=str(usuario_id),
                musica_ids=[str(m) for m in musica_ids] if musica_ids else None,
                id=str(id) if id else None,
            )
        )

    @strawberry.mutation
    def atualizar_playlist(
        self,
        id: strawberry.ID,
        nome: str,
        usuario_id: Optional[strawberry.ID] = None,
        musica_ids: Optional[list[strawberry.ID]] = None,
    ) -> PlaylistType:
        return _to_playlist_type(
            service.atualizar_playlist(
                playlist_id=str(id),
                nome=nome,
                usuario_id=str(usuario_id) if usuario_id else None,
                musica_ids=[str(m) for m in musica_ids] if musica_ids is not None else None,
            )
        )

    @strawberry.mutation
    def remover_playlist(self, id: strawberry.ID) -> bool:
        return service.remover_playlist(str(id))

    @strawberry.mutation
    def adicionar_musica_na_playlist(
        self, playlist_id: strawberry.ID, musica_id: strawberry.ID
    ) -> PlaylistType:
        return _to_playlist_type(
            service.adicionar_musica_na_playlist(str(playlist_id), str(musica_id))
        )

    @strawberry.mutation
    def remover_musica_da_playlist(
        self, playlist_id: strawberry.ID, musica_id: strawberry.ID
    ) -> PlaylistType:
        return _to_playlist_type(
            service.remover_musica_da_playlist(str(playlist_id), str(musica_id))
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
app = FastAPI(title="Streaming de Músicas - Python GraphQL", version="1.0.0")
app.include_router(GraphQLRouter(schema), prefix="/graphql")


@app.get("/health")
def health() -> dict[str, object]:
    return service.health_check()


if __name__ == "__main__":
    uvicorn.run("graphql_api.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8003")))
