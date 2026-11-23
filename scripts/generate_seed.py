"""Gerador determinístico de massas de dados sintéticas para testes de carga.

Perfis embutidos:
- small: 10 usuários, 20 músicas, 15 playlists, 3–5 músicas por playlist -> contracts/seed/seed_small.json
- large: 50 usuários, 500 músicas, 50 playlists, 200 músicas por playlist -> contracts/seed/seed_large.json
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = REPO_ROOT / "contracts" / "seed"

FIRST_NAMES = [
    "Amanda", "João", "Raquel", "Lucas", "Mariana", "Pedro", "Camila", "Gabriel",
    "Beatriz", "Rafael", "Larissa", "Mateus", "Juliana", "Thiago", "Fernanda",
    "Bruno", "Letícia", "Gustavo", "Carolina", "Felipe",
]
LAST_NAMES = [
    "Lira", "Andrade", "Quirino", "Mendes", "Costa", "Rocha", "Alves", "Nunes",
    "Souza", "Barbosa", "Cardoso", "Ferreira", "Oliveira", "Ribeiro", "Teixeira",
]
SONG_PREFIXES = [
    "Noite", "Amanhecer", "Saudade", "Horizonte", "Estrela", "Maré", "Vento",
    "Caminho", "Ritmo", "Eco", "Brisa", "Memória", "Luz", "Sinfonia", "Pulso",
]
SONG_THEMES = [
    "de Verão", "do Norte", "em Fortaleza", "na Estrada", "Sem Fim", "Azul",
    "de Domingo", "Tropical", "Acústica", "Urbana", "do Sertão", "Noturna",
]
ARTISTS = [
    "Elis & Tom", "Legião Urbana", "Alceu Valença", "Chico Buarque", "Queen",
    "Coldplay", "Muse", "Tom Jobim", "Luiz Gonzaga", "Cazuza", "The Weeknd",
    "Djavan", "Marisa Monte", "Caetano Veloso", "Gilberto Gil", "Paralamas",
]
PLAYLIST_MOODS = [
    "Clássicos", "Foco & Estudo", "Viagem", "Treino", "Acústico", "MPB",
    "Rock", "Pop Hits", "Favoritas", "Relax", "Nordeste", "Sextou",
]

PROFILES: dict[str, dict[str, int]] = {
    "small": {"users": 10, "songs": 20, "playlists": 15, "min_songs": 3, "max_songs": 5},
    "large": {"users": 50, "songs": 500, "playlists": 50, "min_songs": 200, "max_songs": 200},
}


def generate_dataset(
    users_count: int,
    songs_count: int,
    playlists_count: int,
    min_songs_per_playlist: int,
    max_songs_per_playlist: int,
    seed: int = 42,
) -> dict[str, list[dict[str, Any]]]:
    """Gera um dicionário compatível com initial_data.json de forma determinística."""
    if users_count < 1 or songs_count < 1 or playlists_count < 1:
        raise ValueError("Quantidades de usuários, músicas e playlists devem ser positivas.")
    if min_songs_per_playlist < 0 or max_songs_per_playlist < min_songs_per_playlist:
        raise ValueError("Intervalo de músicas por playlist inválido.")
    if max_songs_per_playlist > songs_count:
        raise ValueError("Músicas por playlist não pode exceder o total de músicas do catálogo.")

    rng = random.Random(seed)

    usuarios = [
        {
            "id": f"u{i}",
            "nome": f"{FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]} {LAST_NAMES[((i - 1) // len(FIRST_NAMES) + i) % len(LAST_NAMES)]} #{i}",
            "idade": 18 + ((i * 3) % 25),
        }
        for i in range(1, users_count + 1)
    ]

    musicas = [
        {
            "id": f"m{i}",
            "nome": f"{SONG_PREFIXES[(i - 1) % len(SONG_PREFIXES)]} {SONG_THEMES[((i - 1) // len(SONG_PREFIXES)) % len(SONG_THEMES)]} ({i})",
            "artista": ARTISTS[(i - 1) % len(ARTISTS)],
        }
        for i in range(1, songs_count + 1)
    ]

    song_ids = [m["id"] for m in musicas]
    playlists = []
    for i in range(1, playlists_count + 1):
        owner_id = usuarios[(i - 1) % users_count]["id"]
        k = rng.randint(min_songs_per_playlist, max_songs_per_playlist)
        selected_songs = rng.sample(song_ids, k)
        playlists.append(
            {
                "id": f"p{i}",
                "nome": f"{PLAYLIST_MOODS[(i - 1) % len(PLAYLIST_MOODS)]} #{i}",
                "usuarioId": owner_id,
                "musicaIds": selected_songs,
            }
        )

    return {"usuarios": usuarios, "musicas": musicas, "playlists": playlists}


def write_dataset(payload: dict[str, list[dict[str, Any]]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(
        f"Gerado {output_path}: {len(payload['usuarios'])} usuários, "
        f"{len(payload['musicas'])} músicas, {len(payload['playlists'])} playlists."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerador determinístico de seeds para benchmarks.")
    parser.add_argument(
        "--profile",
        choices=["small", "large", "all", "custom"],
        default="all",
        help="Perfil de massa de dados a gerar.",
    )
    parser.add_argument("--users", type=int, default=50)
    parser.add_argument("--songs", type=int, default=500)
    parser.add_argument("--playlists", type=int, default=50)
    parser.add_argument("--songs-per-playlist", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if args.profile in ("small", "all"):
        cfg = PROFILES["small"]
        payload = generate_dataset(
            cfg["users"], cfg["songs"], cfg["playlists"], cfg["min_songs"], cfg["max_songs"], args.seed
        )
        write_dataset(payload, args.output or (SEED_DIR / "seed_small.json"))

    if args.profile in ("large", "all"):
        cfg = PROFILES["large"]
        payload = generate_dataset(
            cfg["users"], cfg["songs"], cfg["playlists"], cfg["min_songs"], cfg["max_songs"], args.seed
        )
        write_dataset(payload, args.output or (SEED_DIR / "seed_large.json"))

    if args.profile == "custom":
        output = args.output or (SEED_DIR / "seed_custom.json")
        payload = generate_dataset(
            args.users,
            args.songs,
            args.playlists,
            args.songs_per_playlist,
            args.songs_per_playlist,
            args.seed,
        )
        write_dataset(payload, output)


if __name__ == "__main__":
    main()
