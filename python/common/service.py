"""Camada de serviço compartilhada (regras de negócio, CRUD e consultas)."""

from __future__ import annotations

import uuid
from functools import lru_cache

from .models import Musica, Playlist, Usuario
from .repository import InMemoryStreamingRepository


class EntityNotFoundError(LookupError):
    """Lançada quando um recurso solicitado não existe."""


class ValidationError(ValueError):
    """Lançada quando os parâmetros fornecidos são inválidos."""


def _clone_usuario(u: Usuario) -> Usuario:
    return Usuario(id=u.id, nome=u.nome, idade=u.idade)


def _clone_musica(m: Musica) -> Musica:
    return Musica(id=m.id, nome=m.nome, artista=m.artista)


def _clone_playlist(p: Playlist) -> Playlist:
    return Playlist(id=p.id, nome=p.nome, usuario_id=p.usuario_id, musica_ids=list(p.musica_ids))


class StreamingService:
    """Reaproveitada por todas as APIs Python (REST, SOAP, GraphQL e gRPC)."""

    def __init__(self, repository: InMemoryStreamingRepository | None = None) -> None:
        self._repo = repository or InMemoryStreamingRepository()

    def health_check(self) -> dict[str, object]:
        with self._repo.lock:
            return {
                "sucesso": True,
                "mensagem": "Serviço operacional",
                "usuarios": len(self._repo.usuarios),
                "musicas": len(self._repo.musicas),
                "playlists": len(self._repo.playlists),
            }

    def reset_seed(self) -> dict[str, object]:
        self._repo.reset_seed()
        return {"sucesso": True, "mensagem": "Dados iniciais restaurados"}

    # =========================================================================
    # Usuários (CRUD)
    # =========================================================================

    def listar_usuarios(self) -> list[Usuario]:
        with self._repo.lock:
            return [_clone_usuario(u) for u in self._repo.usuarios.values()]

    def obter_usuario(self, usuario_id: str) -> Usuario:
        with self._repo.lock:
            usuario = self._repo.usuarios.get(usuario_id)
            if usuario is None:
                raise EntityNotFoundError(f"Usuário '{usuario_id}' não encontrado.")
            return _clone_usuario(usuario)

    def criar_usuario(self, nome: str, idade: int, id: str | None = None) -> Usuario:
        nome_limpo = nome.strip()
        if not nome_limpo:
            raise ValidationError("O nome do usuário não pode ser vazio.")
        if idade < 0:
            raise ValidationError("A idade do usuário deve ser não negativa.")

        with self._repo.lock:
            novo_id = (id or "").strip() or f"u-{uuid.uuid4().hex[:8]}"
            if novo_id in self._repo.usuarios:
                raise ValidationError(f"Usuário com id '{novo_id}' já existe.")
            usuario = Usuario(id=novo_id, nome=nome_limpo, idade=int(idade))
            self._repo.usuarios[novo_id] = usuario
            self._repo.usuario_playlists[novo_id] = {}
            return _clone_usuario(usuario)

    def atualizar_usuario(self, usuario_id: str, nome: str, idade: int) -> Usuario:
        nome_limpo = nome.strip()
        if not nome_limpo:
            raise ValidationError("O nome do usuário não pode ser vazio.")
        if idade < 0:
            raise ValidationError("A idade do usuário deve ser não negativa.")

        with self._repo.lock:
            usuario = self._repo.usuarios.get(usuario_id)
            if usuario is None:
                raise EntityNotFoundError(f"Usuário '{usuario_id}' não encontrado.")
            usuario.nome = nome_limpo
            usuario.idade = int(idade)
            return _clone_usuario(usuario)

    def remover_usuario(self, usuario_id: str) -> bool:
        with self._repo.lock:
            if usuario_id not in self._repo.usuarios:
                raise EntityNotFoundError(f"Usuário '{usuario_id}' não encontrado.")
            del self._repo.usuarios[usuario_id]
            playlists_usuario = self._repo.usuario_playlists.pop(usuario_id, {})
            for pid in list(playlists_usuario.keys()):
                playlist = self._repo.playlists.pop(pid, None)
                if playlist is not None:
                    for mid in playlist.musica_ids:
                        idx = self._repo.musica_playlists.get(mid)
                        if idx is not None:
                            idx.pop(pid, None)
            return True

    # =========================================================================
    # Músicas (CRUD)
    # =========================================================================

    def listar_musicas(self) -> list[Musica]:
        with self._repo.lock:
            return [_clone_musica(m) for m in self._repo.musicas.values()]

    def obter_musica(self, musica_id: str) -> Musica:
        with self._repo.lock:
            musica = self._repo.musicas.get(musica_id)
            if musica is None:
                raise EntityNotFoundError(f"Música '{musica_id}' não encontrada.")
            return _clone_musica(musica)

    def criar_musica(self, nome: str, artista: str, id: str | None = None) -> Musica:
        nome_limpo = nome.strip()
        artista_limpo = artista.strip()
        if not nome_limpo or not artista_limpo:
            raise ValidationError("Nome e artista da música são obrigatórios.")

        with self._repo.lock:
            novo_id = (id or "").strip() or f"m-{uuid.uuid4().hex[:8]}"
            if novo_id in self._repo.musicas:
                raise ValidationError(f"Música com id '{novo_id}' já existe.")
            musica = Musica(id=novo_id, nome=nome_limpo, artista=artista_limpo)
            self._repo.musicas[novo_id] = musica
            self._repo.musica_playlists[novo_id] = {}
            return _clone_musica(musica)

    def atualizar_musica(self, musica_id: str, nome: str, artista: str) -> Musica:
        nome_limpo = nome.strip()
        artista_limpo = artista.strip()
        if not nome_limpo or not artista_limpo:
            raise ValidationError("Nome e artista da música são obrigatórios.")

        with self._repo.lock:
            musica = self._repo.musicas.get(musica_id)
            if musica is None:
                raise EntityNotFoundError(f"Música '{musica_id}' não encontrada.")
            musica.nome = nome_limpo
            musica.artista = artista_limpo
            return _clone_musica(musica)

    def remover_musica(self, musica_id: str) -> bool:
        with self._repo.lock:
            if musica_id not in self._repo.musicas:
                raise EntityNotFoundError(f"Música '{musica_id}' não encontrada.")
            del self._repo.musicas[musica_id]
            playlists_da_musica = self._repo.musica_playlists.pop(musica_id, {})
            for pid in playlists_da_musica.keys():
                playlist = self._repo.playlists.get(pid)
                if playlist is not None:
                    playlist.musica_ids = [mid for mid in playlist.musica_ids if mid != musica_id]
            return True

    # =========================================================================
    # Playlists (CRUD + Associação com Músicas)
    # =========================================================================

    def _validar_musicas_existentes(self, musica_ids: list[str]) -> list[str]:
        resultado: list[str] = []
        vistos: set[str] = set()
        for mid in musica_ids:
            if mid not in self._repo.musicas:
                raise EntityNotFoundError(f"Música '{mid}' não encontrada.")
            if mid not in vistos:
                vistos.add(mid)
                resultado.append(mid)
        return resultado

    def listar_playlists(self) -> list[Playlist]:
        with self._repo.lock:
            return [_clone_playlist(p) for p in self._repo.playlists.values()]

    def obter_playlist(self, playlist_id: str) -> Playlist:
        with self._repo.lock:
            playlist = self._repo.playlists.get(playlist_id)
            if playlist is None:
                raise EntityNotFoundError(f"Playlist '{playlist_id}' não encontrada.")
            return _clone_playlist(playlist)

    def criar_playlist(
        self,
        nome: str,
        usuario_id: str,
        musica_ids: list[str] | None = None,
        id: str | None = None,
    ) -> Playlist:
        nome_limpo = nome.strip()
        if not nome_limpo:
            raise ValidationError("O nome da playlist não pode ser vazio.")

        with self._repo.lock:
            if usuario_id not in self._repo.usuarios:
                raise EntityNotFoundError(f"Usuário '{usuario_id}' não encontrado.")
            musicas_validadas = self._validar_musicas_existentes(musica_ids or [])
            novo_id = (id or "").strip() or f"p-{uuid.uuid4().hex[:8]}"
            if novo_id in self._repo.playlists:
                raise ValidationError(f"Playlist com id '{novo_id}' já existe.")
            playlist = Playlist(
                id=novo_id,
                nome=nome_limpo,
                usuario_id=usuario_id,
                musica_ids=musicas_validadas,
            )
            self._repo.playlists[novo_id] = playlist
            self._repo.usuario_playlists.setdefault(usuario_id, {})[novo_id] = None
            for mid in musicas_validadas:
                self._repo.musica_playlists.setdefault(mid, {})[novo_id] = None
            return _clone_playlist(playlist)

    def atualizar_playlist(
        self,
        playlist_id: str,
        nome: str,
        usuario_id: str | None = None,
        musica_ids: list[str] | None = None,
    ) -> Playlist:
        nome_limpo = nome.strip()
        if not nome_limpo:
            raise ValidationError("O nome da playlist não pode ser vazio.")

        with self._repo.lock:
            playlist = self._repo.playlists.get(playlist_id)
            if playlist is None:
                raise EntityNotFoundError(f"Playlist '{playlist_id}' não encontrada.")

            if usuario_id is not None and usuario_id != playlist.usuario_id:
                if usuario_id not in self._repo.usuarios:
                    raise EntityNotFoundError(f"Usuário '{usuario_id}' não encontrado.")
                old_idx = self._repo.usuario_playlists.get(playlist.usuario_id)
                if old_idx is not None:
                    old_idx.pop(playlist_id, None)
                self._repo.usuario_playlists.setdefault(usuario_id, {})[playlist_id] = None
                playlist.usuario_id = usuario_id

            if musica_ids is not None:
                novas_musicas = self._validar_musicas_existentes(musica_ids)
                for old_mid in playlist.musica_ids:
                    idx = self._repo.musica_playlists.get(old_mid)
                    if idx is not None:
                        idx.pop(playlist_id, None)
                for new_mid in novas_musicas:
                    self._repo.musica_playlists.setdefault(new_mid, {})[playlist_id] = None
                playlist.musica_ids = novas_musicas

            playlist.nome = nome_limpo
            return _clone_playlist(playlist)

    def remover_playlist(self, playlist_id: str) -> bool:
        with self._repo.lock:
            playlist = self._repo.playlists.pop(playlist_id, None)
            if playlist is None:
                raise EntityNotFoundError(f"Playlist '{playlist_id}' não encontrada.")
            user_idx = self._repo.usuario_playlists.get(playlist.usuario_id)
            if user_idx is not None:
                user_idx.pop(playlist_id, None)
            for mid in playlist.musica_ids:
                music_idx = self._repo.musica_playlists.get(mid)
                if music_idx is not None:
                    music_idx.pop(playlist_id, None)
            return True

    def adicionar_musica_na_playlist(self, playlist_id: str, musica_id: str) -> Playlist:
        with self._repo.lock:
            playlist = self._repo.playlists.get(playlist_id)
            if playlist is None:
                raise EntityNotFoundError(f"Playlist '{playlist_id}' não encontrada.")
            if musica_id not in self._repo.musicas:
                raise EntityNotFoundError(f"Música '{musica_id}' não encontrada.")
            if playlist_id not in self._repo.musica_playlists.setdefault(musica_id, {}):
                playlist.musica_ids.append(musica_id)
                self._repo.musica_playlists[musica_id][playlist_id] = None
            return _clone_playlist(playlist)

    def remover_musica_da_playlist(self, playlist_id: str, musica_id: str) -> Playlist:
        with self._repo.lock:
            playlist = self._repo.playlists.get(playlist_id)
            if playlist is None:
                raise EntityNotFoundError(f"Playlist '{playlist_id}' não encontrada.")
            if musica_id not in self._repo.musicas:
                raise EntityNotFoundError(f"Música '{musica_id}' não encontrada.")
            playlist.musica_ids = [mid for mid in playlist.musica_ids if mid != musica_id]
            music_idx = self._repo.musica_playlists.get(musica_id)
            if music_idx is not None:
                music_idx.pop(playlist_id, None)
            return _clone_playlist(playlist)

    # =========================================================================
    # Consultas Relacionais Obrigatórias (Slide 6)
    # =========================================================================

    def listar_playlists_por_usuario(self, usuario_id: str) -> list[Playlist]:
        with self._repo.lock:
            if usuario_id not in self._repo.usuarios:
                raise EntityNotFoundError(f"Usuário '{usuario_id}' não encontrado.")
            pids = self._repo.usuario_playlists.get(usuario_id, {})
            return [
                _clone_playlist(self._repo.playlists[pid])
                for pid in pids.keys()
                if pid in self._repo.playlists
            ]

    def listar_musicas_por_playlist(self, playlist_id: str) -> list[Musica]:
        with self._repo.lock:
            playlist = self._repo.playlists.get(playlist_id)
            if playlist is None:
                raise EntityNotFoundError(f"Playlist '{playlist_id}' não encontrada.")
            return [
                _clone_musica(self._repo.musicas[mid])
                for mid in playlist.musica_ids
                if mid in self._repo.musicas
            ]

    def listar_playlists_por_musica(self, musica_id: str) -> list[Playlist]:
        with self._repo.lock:
            if musica_id not in self._repo.musicas:
                raise EntityNotFoundError(f"Música '{musica_id}' não encontrada.")
            pids = self._repo.musica_playlists.get(musica_id, {})
            return [
                _clone_playlist(self._repo.playlists[pid])
                for pid in pids.keys()
                if pid in self._repo.playlists
            ]


@lru_cache(maxsize=1)
def get_streaming_service() -> StreamingService:
    """Retorna instância única compartilhada do serviço de streaming."""
    return StreamingService()
