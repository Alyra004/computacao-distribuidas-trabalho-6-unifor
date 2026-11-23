"""Entrega Python 4: Servidor gRPC reutilizando common.StreamingService."""

from __future__ import annotations

import os
from concurrent import futures
from functools import wraps
from typing import Callable

import grpc

from common.models import Musica, Playlist, Usuario
from common.service import (
    EntityNotFoundError,
    StreamingService,
    ValidationError,
    get_streaming_service,
)

try:
    from . import streaming_pb2, streaming_pb2_grpc
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "Stubs gRPC não encontrados. Execute 'python -m grpc_api.generate_proto' antes de iniciar."
    ) from exc


def _handle_errors(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(self, request, context):
        try:
            return fn(self, request, context)
        except EntityNotFoundError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        except ValidationError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))

    return wrapper


def _to_pb_usuario(u: Usuario) -> streaming_pb2.Usuario:
    return streaming_pb2.Usuario(id=u.id, nome=u.nome, idade=u.idade)


def _to_pb_musica(m: Musica) -> streaming_pb2.Musica:
    return streaming_pb2.Musica(id=m.id, nome=m.nome, artista=m.artista)


def _to_pb_playlist(p: Playlist) -> streaming_pb2.Playlist:
    return streaming_pb2.Playlist(
        id=p.id, nome=p.nome, usuario_id=p.usuario_id, musica_ids=p.musica_ids
    )


class StreamingGrpcServicer(streaming_pb2_grpc.StreamingServiceServicer):
    """Implementação gRPC delegando todas as operações para common.StreamingService."""

    def __init__(self, service: StreamingService | None = None) -> None:
        self._service = service or get_streaming_service()

    def HealthCheck(self, request, context):
        info = self._service.health_check()
        return streaming_pb2.StatusResponse(
            sucesso=bool(info["sucesso"]), mensagem=str(info["mensagem"])
        )

    def ResetSeed(self, request, context):
        info = self._service.reset_seed()
        return streaming_pb2.StatusResponse(
            sucesso=bool(info["sucesso"]), mensagem=str(info["mensagem"])
        )

    @_handle_errors
    def ListarUsuarios(self, request, context):
        return streaming_pb2.UsuarioListResponse(
            usuarios=[_to_pb_usuario(u) for u in self._service.listar_usuarios()]
        )

    @_handle_errors
    def ObterUsuario(self, request, context):
        return _to_pb_usuario(self._service.obter_usuario(request.id))

    @_handle_errors
    def CriarUsuario(self, request, context):
        return _to_pb_usuario(
            self._service.criar_usuario(
                nome=request.nome, idade=request.idade, id=request.id or None
            )
        )

    @_handle_errors
    def AtualizarUsuario(self, request, context):
        return _to_pb_usuario(
            self._service.atualizar_usuario(request.id, request.nome, request.idade)
        )

    @_handle_errors
    def RemoverUsuario(self, request, context):
        sucesso = self._service.remover_usuario(request.id)
        return streaming_pb2.StatusResponse(sucesso=sucesso, mensagem="Usuário removido")

    @_handle_errors
    def ListarMusicas(self, request, context):
        return streaming_pb2.MusicaListResponse(
            musicas=[_to_pb_musica(m) for m in self._service.listar_musicas()]
        )

    @_handle_errors
    def ObterMusica(self, request, context):
        return _to_pb_musica(self._service.obter_musica(request.id))

    @_handle_errors
    def CriarMusica(self, request, context):
        return _to_pb_musica(
            self._service.criar_musica(
                nome=request.nome, artista=request.artista, id=request.id or None
            )
        )

    @_handle_errors
    def AtualizarMusica(self, request, context):
        return _to_pb_musica(
            self._service.atualizar_musica(request.id, request.nome, request.artista)
        )

    @_handle_errors
    def RemoverMusica(self, request, context):
        sucesso = self._service.remover_musica(request.id)
        return streaming_pb2.StatusResponse(sucesso=sucesso, mensagem="Música removida")

    @_handle_errors
    def ListarPlaylists(self, request, context):
        return streaming_pb2.PlaylistListResponse(
            playlists=[_to_pb_playlist(p) for p in self._service.listar_playlists()]
        )

    @_handle_errors
    def ObterPlaylist(self, request, context):
        return _to_pb_playlist(self._service.obter_playlist(request.id))

    @_handle_errors
    def CriarPlaylist(self, request, context):
        return _to_pb_playlist(
            self._service.criar_playlist(
                nome=request.nome,
                usuario_id=request.usuario_id,
                musica_ids=list(request.musica_ids),
                id=request.id or None,
            )
        )

    @_handle_errors
    def AtualizarPlaylist(self, request, context):
        return _to_pb_playlist(
            self._service.atualizar_playlist(
                playlist_id=request.id,
                nome=request.nome,
                usuario_id=request.usuario_id or None,
                musica_ids=list(request.musica_ids),
            )
        )

    @_handle_errors
    def RemoverPlaylist(self, request, context):
        sucesso = self._service.remover_playlist(request.id)
        return streaming_pb2.StatusResponse(sucesso=sucesso, mensagem="Playlist removida")

    @_handle_errors
    def AdicionarMusicaNaPlaylist(self, request, context):
        return _to_pb_playlist(
            self._service.adicionar_musica_na_playlist(request.playlist_id, request.musica_id)
        )

    @_handle_errors
    def RemoverMusicaDaPlaylist(self, request, context):
        return _to_pb_playlist(
            self._service.remover_musica_da_playlist(request.playlist_id, request.musica_id)
        )

    @_handle_errors
    def ListarPlaylistsPorUsuario(self, request, context):
        return streaming_pb2.PlaylistListResponse(
            playlists=[
                _to_pb_playlist(p)
                for p in self._service.listar_playlists_por_usuario(request.id)
            ]
        )

    @_handle_errors
    def ListarMusicasPorPlaylist(self, request, context):
        return streaming_pb2.MusicaListResponse(
            musicas=[
                _to_pb_musica(m)
                for m in self._service.listar_musicas_por_playlist(request.id)
            ]
        )

    @_handle_errors
    def ListarPlaylistsPorMusica(self, request, context):
        return streaming_pb2.PlaylistListResponse(
            playlists=[
                _to_pb_playlist(p)
                for p in self._service.listar_playlists_por_musica(request.id)
            ]
        )


def serve() -> None:
    port = os.getenv("PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    streaming_pb2_grpc.add_StreamingServiceServicer_to_server(StreamingGrpcServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Python gRPC StreamingService ativo na porta {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
