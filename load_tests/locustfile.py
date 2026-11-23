"""Testes de carga multi-protocolo (REST, SOAP, GraphQL e gRPC) com Locust.

Variáveis de ambiente suportadas:
- TARGET_TECH: rest | soap | graphql | grpc (padrão: rest)
- TARGET_LANG: python | java (padrão: python)
- TARGET_URL: sobrescreve a URL base HTTP ou endereço host:port do gRPC
- WORKLOAD_MODE: read (5 consultas do Slide 6) | mixed (consultas + CRUD) | nested (consulta aninhada)
- SEED_DATA_PATH: caminho para o JSON de seed usado para sortear IDs válidos
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
import uuid
from pathlib import Path

from locust import HttpUser, User, between, events

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

DEFAULT_ENDPOINTS = {
    ("python", "rest"): "http://localhost:8001",
    ("python", "soap"): "http://localhost:8002",
    ("python", "graphql"): "http://localhost:8003",
    ("python", "grpc"): "localhost:50051",
    ("java", "rest"): "http://localhost:8081",
    ("java", "soap"): "http://localhost:8082",
    ("java", "graphql"): "http://localhost:8083",
    ("java", "grpc"): "localhost:50052",
}

TARGET_TECH = os.getenv("TARGET_TECH", "rest").lower()
TARGET_LANG = os.getenv("TARGET_LANG", "python").lower()
WORKLOAD_MODE = os.getenv("WORKLOAD_MODE", "read").lower()
TARGET_ENDPOINT = os.getenv(
    "TARGET_URL",
    DEFAULT_ENDPOINTS.get((TARGET_LANG, TARGET_TECH), "http://localhost:8001"),
)


def _load_seed_ids() -> tuple[list[str], list[str], list[str]]:
    candidates = []
    env_path = os.getenv("SEED_DATA_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(REPO_ROOT / "contracts" / "seed" / "initial_data.json")

    for path in candidates:
        if path.is_file():
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            uids = [str(u["id"]) for u in data.get("usuarios", [])]
            mids = [str(m["id"]) for m in data.get("musicas", [])]
            pids = [str(p["id"]) for p in data.get("playlists", [])]
            if uids and mids and pids:
                return uids, mids, pids

    return (
        [f"u{i}" for i in range(1, 11)],
        [f"m{i}" for i in range(1, 21)],
        [f"p{i}" for i in range(1, 16)],
    )


USER_IDS, SONG_IDS, PLAYLIST_IDS = _load_seed_ids()

SOAP_TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
    'xmlns:tns="http://unifor.br/distribuidos/streaming">'
    "<soapenv:Body>{body}</soapenv:Body>"
    "</soapenv:Envelope>"
)


# =============================================================================
# Tarefas HTTP (REST, SOAP, GraphQL)
# =============================================================================


def _http_dispatch_query(
    user: HttpUser, op: str, uid: str = "u1", pid: str = "p1", mid: str = "m1"
) -> None:
    if TARGET_TECH == "rest":
        routes = {
            "listar_usuarios": "/usuarios",
            "listar_musicas": "/musicas",
            "playlists_por_usuario": f"/usuarios/{uid}/playlists",
            "musicas_por_playlist": f"/playlists/{pid}/musicas",
            "playlists_por_musica": f"/musicas/{mid}/playlists",
        }
        user.client.get(routes[op], name=f"rest_{op}")
    elif TARGET_TECH == "soap":
        bodies = {
            "listar_usuarios": "<tns:ListarUsuariosRequest/>",
            "listar_musicas": "<tns:ListarMusicasRequest/>",
            "playlists_por_usuario": f"<tns:ListarPlaylistsPorUsuarioRequest><tns:usuarioId>{uid}</tns:usuarioId></tns:ListarPlaylistsPorUsuarioRequest>",
            "musicas_por_playlist": f"<tns:ListarMusicasPorPlaylistRequest><tns:playlistId>{pid}</tns:playlistId></tns:ListarMusicasPorPlaylistRequest>",
            "playlists_por_musica": f"<tns:ListarPlaylistsPorMusicaRequest><tns:musicaId>{mid}</tns:musicaId></tns:ListarPlaylistsPorMusicaRequest>",
        }
        xml = SOAP_TEMPLATE.format(body=bodies[op])
        user.client.post(
            "/soap",
            data=xml,
            headers={"Content-Type": "text/xml; charset=utf-8"},
            name=f"soap_{op}",
        )
    elif TARGET_TECH == "graphql":
        queries = {
            "listar_usuarios": ("{ usuarios { id nome idade } }", {}),
            "listar_musicas": ("{ musicas { id nome artista } }", {}),
            "playlists_por_usuario": (
                "query($id: ID!) { playlistsPorUsuario(usuarioId: $id) { id nome usuarioId } }",
                {"id": uid},
            ),
            "musicas_por_playlist": (
                "query($id: ID!) { musicasPorPlaylist(playlistId: $id) { id nome artista } }",
                {"id": pid},
            ),
            "playlists_por_musica": (
                "query($id: ID!) { playlistsPorMusica(musicaId: $id) { id nome usuarioId } }",
                {"id": mid},
            ),
        }
        q, variables = queries[op]
        user.client.post("/graphql", json={"query": q, "variables": variables}, name=f"graphql_{op}")


def http_listar_usuarios(user: HttpUser) -> None:
    _http_dispatch_query(user, "listar_usuarios")


def http_listar_musicas(user: HttpUser) -> None:
    _http_dispatch_query(user, "listar_musicas")


def http_playlists_por_usuario(user: HttpUser) -> None:
    _http_dispatch_query(user, "playlists_por_usuario", uid=random.choice(USER_IDS))


def http_musicas_por_playlist(user: HttpUser) -> None:
    _http_dispatch_query(user, "musicas_por_playlist", pid=random.choice(PLAYLIST_IDS))


def http_playlists_por_musica(user: HttpUser) -> None:
    _http_dispatch_query(user, "playlists_por_musica", mid=random.choice(SONG_IDS))


def http_criar_e_remover_usuario(user: HttpUser) -> None:
    uid = f"bench-{uuid.uuid4().hex[:8]}"
    if TARGET_TECH == "rest":
        user.client.post(
            "/usuarios",
            json={"id": uid, "nome": "Benchmark User", "idade": 25},
            name="rest_criar_usuario",
        )
        user.client.delete(f"/usuarios/{uid}", name="rest_remover_usuario")
    elif TARGET_TECH == "graphql":
        user.client.post(
            "/graphql",
            json={
                "query": "mutation($id: ID, $nome: String!, $idade: Int!) { criarUsuario(id: $id, nome: $nome, idade: $idade) { id } }",
                "variables": {"id": uid, "nome": "Benchmark User", "idade": 25},
            },
            name="graphql_criar_usuario",
        )
        user.client.post(
            "/graphql",
            json={
                "query": "mutation($id: ID!) { removerUsuario(id: $id) }",
                "variables": {"id": uid},
            },
            name="graphql_remover_usuario",
        )
    elif TARGET_TECH == "soap":
        create_xml = SOAP_TEMPLATE.format(
            body=f"<tns:CriarUsuarioRequest><tns:id>{uid}</tns:id><tns:nome>Benchmark User</tns:nome><tns:idade>25</tns:idade></tns:CriarUsuarioRequest>"
        )
        delete_xml = SOAP_TEMPLATE.format(
            body=f"<tns:RemoverUsuarioRequest><tns:id>{uid}</tns:id></tns:RemoverUsuarioRequest>"
        )
        headers = {"Content-Type": "text/xml; charset=utf-8"}
        user.client.post("/soap", data=create_xml, headers=headers, name="soap_criar_usuario")
        user.client.post("/soap", data=delete_xml, headers=headers, name="soap_remover_usuario")


def http_consulta_aninhada(user: HttpUser) -> None:
    """Compara 1 query aninhada em GraphQL contra múltiplas chamadas em REST/SOAP."""
    uid = random.choice(USER_IDS)
    if TARGET_TECH == "graphql":
        query = (
            "query($id: ID!) { "
            "usuario(id: $id) { id nome playlists { id nome musicas { id nome } } } "
            "}"
        )
        user.client.post(
            "/graphql",
            json={"query": query, "variables": {"id": uid}},
            name="graphql_nested_usuario_completo",
        )
    elif TARGET_TECH == "rest":
        user.client.get(f"/usuarios/{uid}", name="rest_nested_usuario")
        resp = user.client.get(f"/usuarios/{uid}/playlists", name="rest_nested_playlists")
        if resp.ok:
            for pl in resp.json():
                user.client.get(f"/playlists/{pl['id']}/musicas", name="rest_nested_musicas")
    elif TARGET_TECH == "soap":
        headers = {"Content-Type": "text/xml; charset=utf-8"}
        user.client.post(
            "/soap",
            data=SOAP_TEMPLATE.format(body=f"<tns:ObterUsuarioRequest><tns:id>{uid}</tns:id></tns:ObterUsuarioRequest>"),
            headers=headers,
            name="soap_nested_usuario",
        )
        resp = user.client.post(
            "/soap",
            data=SOAP_TEMPLATE.format(
                body=f"<tns:ListarPlaylistsPorUsuarioRequest><tns:usuarioId>{uid}</tns:usuarioId></tns:ListarPlaylistsPorUsuarioRequest>"
            ),
            headers=headers,
            name="soap_nested_playlists",
        )
        if resp.ok and "<tns:id>" in resp.text:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(resp.text)
            for pl_node in root.iter():
                if pl_node.tag.endswith("playlist"):
                    for child in pl_node:
                        if child.tag.endswith("id") and child.text:
                            pid = child.text.strip()
                            user.client.post(
                                "/soap",
                                data=SOAP_TEMPLATE.format(
                                    body=f"<tns:ListarMusicasPorPlaylistRequest><tns:playlistId>{pid}</tns:playlistId></tns:ListarMusicasPorPlaylistRequest>"
                                ),
                                headers=headers,
                                name="soap_nested_musicas",
                            )
                            break


def _build_http_tasks() -> dict:
    if WORKLOAD_MODE == "nested":
        return {http_consulta_aninhada: 1}
    tasks = {
        http_listar_usuarios: 2,
        http_listar_musicas: 2,
        http_playlists_por_usuario: 2,
        http_musicas_por_playlist: 2,
        http_playlists_por_musica: 2,
    }
    if WORKLOAD_MODE == "mixed":
        tasks[http_criar_e_remover_usuario] = 1
    return tasks


class HttpStreamingUser(HttpUser):
    """Usuário virtual Locust para REST, SOAP e GraphQL."""

    host = TARGET_ENDPOINT if TARGET_TECH != "grpc" else "http://localhost:8001"
    wait_time = between(0.2, 0.8)
    tasks = _build_http_tasks()

    def on_start(self) -> None:
        if TARGET_TECH == "grpc":
            self.environment.runner.quit()


# =============================================================================
# Tarefas gRPC
# =============================================================================

if TARGET_TECH == "grpc":
    import grpc
    from grpc_api import streaming_pb2, streaming_pb2_grpc

    def _grpc_call(user: "GrpcStreamingUser", name: str, fn, req):
        start = time.perf_counter()
        exception = None
        response_length = 0
        resp = None
        try:
            resp = fn(req)
            if resp is not None:
                response_length = resp.ByteSize()
        except Exception as exc:  # pragma: no cover
            exception = exc
        elapsed_ms = (time.perf_counter() - start) * 1000
        events.request.fire(
            request_type="gRPC",
            name=name,
            response_time=elapsed_ms,
            response_length=response_length,
            exception=exception,
        )
        return resp

    def grpc_listar_usuarios(user: "GrpcStreamingUser") -> None:
        _grpc_call(user, "grpc_listar_usuarios", user.stub.ListarUsuarios, streaming_pb2.Empty())

    def grpc_listar_musicas(user: "GrpcStreamingUser") -> None:
        _grpc_call(user, "grpc_listar_musicas", user.stub.ListarMusicas, streaming_pb2.Empty())

    def grpc_playlists_por_usuario(user: "GrpcStreamingUser") -> None:
        uid = random.choice(USER_IDS)
        _grpc_call(
            user,
            "grpc_playlists_por_usuario",
            user.stub.ListarPlaylistsPorUsuario,
            streaming_pb2.IdRequest(id=uid),
        )

    def grpc_musicas_por_playlist(user: "GrpcStreamingUser") -> None:
        pid = random.choice(PLAYLIST_IDS)
        _grpc_call(
            user,
            "grpc_musicas_por_playlist",
            user.stub.ListarMusicasPorPlaylist,
            streaming_pb2.IdRequest(id=pid),
        )

    def grpc_playlists_por_musica(user: "GrpcStreamingUser") -> None:
        mid = random.choice(SONG_IDS)
        _grpc_call(
            user,
            "grpc_playlists_por_musica",
            user.stub.ListarPlaylistsPorMusica,
            streaming_pb2.IdRequest(id=mid),
        )

    def grpc_criar_e_remover_usuario(user: "GrpcStreamingUser") -> None:
        uid = f"bench-{uuid.uuid4().hex[:8]}"
        _grpc_call(
            user,
            "grpc_criar_usuario",
            user.stub.CriarUsuario,
            streaming_pb2.CriarUsuarioRequest(id=uid, nome="Benchmark User", idade=25),
        )
        _grpc_call(
            user,
            "grpc_remover_usuario",
            user.stub.RemoverUsuario,
            streaming_pb2.IdRequest(id=uid),
        )

    def grpc_consulta_aninhada(user: "GrpcStreamingUser") -> None:
        uid = random.choice(USER_IDS)
        _grpc_call(user, "grpc_nested_usuario", user.stub.ObterUsuario, streaming_pb2.IdRequest(id=uid))
        playlists_resp = _grpc_call(
            user,
            "grpc_nested_playlists",
            user.stub.ListarPlaylistsPorUsuario,
            streaming_pb2.IdRequest(id=uid),
        )
        if playlists_resp is not None:
            for pl in playlists_resp.playlists:
                _grpc_call(
                    user,
                    "grpc_nested_musicas",
                    user.stub.ListarMusicasPorPlaylist,
                    streaming_pb2.IdRequest(id=pl.id),
                )

    def _build_grpc_tasks() -> dict:
        if WORKLOAD_MODE == "nested":
            return {grpc_consulta_aninhada: 1}
        tasks = {
            grpc_listar_usuarios: 2,
            grpc_listar_musicas: 2,
            grpc_playlists_por_usuario: 2,
            grpc_musicas_por_playlist: 2,
            grpc_playlists_por_musica: 2,
        }
        if WORKLOAD_MODE == "mixed":
            tasks[grpc_criar_e_remover_usuario] = 1
        return tasks

    class GrpcStreamingUser(User):
        """Usuário virtual Locust para chamadas gRPC nativas."""

        wait_time = between(0.2, 0.8)
        tasks = _build_grpc_tasks()

        def on_start(self) -> None:
            self.channel = grpc.insecure_channel(TARGET_ENDPOINT)
            self.stub = streaming_pb2_grpc.StreamingServiceStub(self.channel)

        def on_stop(self) -> None:
            self.channel.close()
