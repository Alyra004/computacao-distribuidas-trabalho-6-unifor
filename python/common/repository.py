"""Repositório em memória thread-safe com carga determinística e índices invertidos."""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import RLock
from typing import Any

from .models import Musica, Playlist, Usuario

DEFAULT_SEED_FALLBACK: dict[str, list[dict[str, Any]]] = {
    "usuarios": [
        {"id": "u1", "nome": "Amanda Lira", "idade": 22},
        {"id": "u2", "nome": "João Igor", "idade": 23},
        {"id": "u3", "nome": "Raquel Quirino", "idade": 22},
    ],
    "musicas": [
        {"id": "m1", "nome": "Evidências", "artista": "Chitãozinho & Xororó"},
        {"id": "m2", "nome": "Águas de Março", "artista": "Elis Regina & Tom Jobim"},
        {"id": "m3", "nome": "Tempo Perdido", "artista": "Legião Urbana"},
    ],
    "playlists": [
        {
            "id": "p1",
            "nome": "Clássicos Brasileiros",
            "usuarioId": "u1",
            "musicaIds": ["m1", "m2"],
        },
        {
            "id": "p2",
            "nome": "Rock Nacional",
            "usuarioId": "u2",
            "musicaIds": ["m3"],
        },
    ],
}


def _resolve_seed_path(seed_path: str | Path | None = None) -> Path | None:
    candidates = []
    if seed_path:
        candidates.append(Path(seed_path))
    env_path = os.getenv("SEED_DATA_PATH")
    if env_path:
        candidates.append(Path(env_path))
    repo_root = Path(__file__).resolve().parents[2]
    candidates.append(repo_root / "contracts" / "seed" / "initial_data.json")
    candidates.append(Path("contracts/seed/initial_data.json"))

    for path in candidates:
        if path.is_file():
            return path
    return None


class InMemoryStreamingRepository:
    """Armazenamento em memória protegido por RLock, com índices invertidos O(1)/O(K)."""

    def __init__(self, seed_path: str | Path | None = None) -> None:
        self._lock = RLock()
        self._seed_path = seed_path
        self.usuarios: dict[str, Usuario] = {}
        self.musicas: dict[str, Musica] = {}
        self.playlists: dict[str, Playlist] = {}
        # Índices invertidos preservando ordem de inserção (dict[id, None] atua como OrderedSet)
        self.usuario_playlists: dict[str, dict[str, None]] = {}
        self.musica_playlists: dict[str, dict[str, None]] = {}
        self.reset_seed()

    @property
    def lock(self) -> RLock:
        return self._lock

    def reset_seed(self) -> None:
        """Recarrega o conjunto de dados inicial e reconstrói os índices invertidos."""
        resolved = _resolve_seed_path(self._seed_path)
        if resolved is not None:
            with resolved.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
        else:
            payload = DEFAULT_SEED_FALLBACK

        with self._lock:
            self.usuarios = {}
            self.musicas = {}
            self.playlists = {}
            self.usuario_playlists = {}
            self.musica_playlists = {}

            for item in payload.get("usuarios", []):
                uid = str(item["id"])
                self.usuarios[uid] = Usuario(id=uid, nome=str(item["nome"]), idade=int(item["idade"]))
                self.usuario_playlists[uid] = {}

            for item in payload.get("musicas", []):
                mid = str(item["id"])
                self.musicas[mid] = Musica(id=mid, nome=str(item["nome"]), artista=str(item["artista"]))
                self.musica_playlists[mid] = {}

            for item in payload.get("playlists", []):
                pid = str(item["id"])
                uid = str(item["usuarioId"])
                mids = list(dict.fromkeys(str(m) for m in item.get("musicaIds", [])))
                playlist = Playlist(id=pid, nome=str(item["nome"]), usuario_id=uid, musica_ids=mids)
                self.playlists[pid] = playlist
                self.usuario_playlists.setdefault(uid, {})[pid] = None
                for mid in mids:
                    self.musica_playlists.setdefault(mid, {})[pid] = None
