"""Testes unitários do núcleo compartilhado (common.StreamingService)."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from common.repository import InMemoryStreamingRepository
from common.service import EntityNotFoundError, StreamingService, ValidationError


class StreamingServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = StreamingService()

    def test_seed_e_consultas_obrigatorias(self) -> None:
        usuarios = self.service.listar_usuarios()
        musicas = self.service.listar_musicas()
        playlists = self.service.listar_playlists()

        self.assertEqual(len(usuarios), 10)
        self.assertEqual(len(musicas), 20)
        self.assertEqual(len(playlists), 15)

        playlists_u1 = self.service.listar_playlists_por_usuario("u1")
        self.assertGreaterEqual(len(playlists_u1), 1)

        musicas_p1 = self.service.listar_musicas_por_playlist("p1")
        self.assertGreaterEqual(len(musicas_p1), 1)

        playlists_m1 = self.service.listar_playlists_por_musica("m1")
        self.assertGreaterEqual(len(playlists_m1), 1)

    def test_seed_large_e_indices_invertidos(self) -> None:
        large_seed = REPO_ROOT / "contracts" / "seed" / "seed_large.json"
        if not large_seed.is_file():
            self.skipTest("seed_large.json ainda não gerado.")

        large_service = StreamingService(InMemoryStreamingRepository(seed_path=large_seed))
        self.assertEqual(len(large_service.listar_usuarios()), 50)
        self.assertEqual(len(large_service.listar_musicas()), 500)
        self.assertEqual(len(large_service.listar_playlists()), 50)
        self.assertEqual(len(large_service.listar_musicas_por_playlist("p1")), 200)

        # Consistência de índices invertidos em consultas e atualizações
        playlists_u1 = large_service.listar_playlists_por_usuario("u1")
        self.assertGreaterEqual(len(playlists_u1), 1)
        primeira_musica_p1 = large_service.obter_playlist("p1").musica_ids[0]
        self.assertIn("p1", [p.id for p in large_service.listar_playlists_por_musica(primeira_musica_p1)])

        large_service.remover_musica_da_playlist("p1", primeira_musica_p1)
        self.assertNotIn("p1", [p.id for p in large_service.listar_playlists_por_musica(primeira_musica_p1)])

    def test_crud_e_integridade_relacional(self) -> None:
        user = self.service.criar_usuario("Teste", 25, id="u_test")
        self.assertEqual(user.id, "u_test")

        updated_user = self.service.atualizar_usuario("u_test", "Teste Editado", 26)
        self.assertEqual(updated_user.nome, "Teste Editado")
        self.assertEqual(updated_user.idade, 26)

        song = self.service.criar_musica("Som Teste", "Artista Teste", id="m_test")
        playlist = self.service.criar_playlist(
            "Playlist Teste", "u_test", musica_ids=[song.id], id="p_test"
        )
        self.assertEqual(len(self.service.listar_musicas_por_playlist(playlist.id)), 1)
        self.assertEqual(
            [p.id for p in self.service.listar_playlists_por_musica(song.id)],
            [playlist.id],
        )

        # Atualizar músicas da playlist atualiza os índices invertidos
        self.service.atualizar_playlist(playlist.id, "Playlist Editada", musica_ids=["m1"])
        self.assertEqual(self.service.listar_playlists_por_musica(song.id), [])
        self.assertIn(playlist.id, [p.id for p in self.service.listar_playlists_por_musica("m1")])

        # Remover música deve removê-la das playlists associadas
        self.service.adicionar_musica_na_playlist(playlist.id, song.id)
        self.service.remover_musica(song.id)
        self.assertEqual(
            [m.id for m in self.service.listar_musicas_por_playlist(playlist.id)],
            ["m1"],
        )

        # Remover usuário deve remover suas playlists em cascata e limpar índice das músicas
        self.service.remover_usuario("u_test")
        with self.assertRaises(EntityNotFoundError):
            self.service.obter_playlist(playlist.id)
        self.assertNotIn(playlist.id, [p.id for p in self.service.listar_playlists_por_musica("m1")])

    def test_validacoes(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.criar_usuario("   ", 20)
        with self.assertRaises(EntityNotFoundError):
            self.service.obter_usuario("inexistente")


if __name__ == "__main__":
    unittest.main()
