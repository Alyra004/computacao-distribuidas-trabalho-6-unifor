"""Smoke test ponta-a-ponta para validar as 8 APIs em execução.

Verifica saúde, as 5 consultas obrigatórias do Slide 6 e um ciclo CRUD básico.
Exemplo:
    python scripts/smoke_test.py --langs python java --techs rest soap graphql grpc
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

HTTP_PORTS = {
    ("python", "rest"): 8001,
    ("python", "soap"): 8002,
    ("python", "graphql"): 8003,
    ("java", "rest"): 8081,
    ("java", "soap"): 8082,
    ("java", "graphql"): 8083,
}

GRPC_TARGETS = {
    "python": "localhost:50051",
    "java": "localhost:50052",
}

SOAP_ENV = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
    'xmlns:tns="http://unifor.br/distribuidos/streaming">'
    "<soapenv:Body>{body}</soapenv:Body></soapenv:Envelope>"
)


def _http_req(url: str, method: str = "GET", body: bytes | None = None, headers: dict | None = None) -> tuple[int, str]:
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, resp.read().decode("utf-8")


def test_rest(base_url: str) -> None:
    status, _ = _http_req(f"{base_url}/health")
    assert status == 200
    for path in ["/usuarios", "/musicas", "/usuarios/u1/playlists", "/playlists/p1/musicas", "/musicas/m1/playlists"]:
        s, payload = _http_req(f"{base_url}{path}")
        assert s == 200 and len(json.loads(payload)) >= 1, f"Falha em {path}"

    uid = f"smoke-{uuid.uuid4().hex[:6]}"
    s, _ = _http_req(
        f"{base_url}/usuarios",
        method="POST",
        body=json.dumps({"id": uid, "nome": "Smoke", "idade": 20}).encode(),
        headers={"Content-Type": "application/json"},
    )
    assert s == 201
    s, _ = _http_req(f"{base_url}/usuarios/{uid}", method="DELETE")
    assert s == 204


def test_soap(base_url: str) -> None:
    status, _ = _http_req(f"{base_url}/health")
    assert status == 200
    status, wsdl = _http_req(f"{base_url}/soap?wsdl")
    assert status == 200 and "definitions" in wsdl

    headers = {"Content-Type": "text/xml; charset=utf-8"}
    for body in [
        "<tns:ListarUsuariosRequest/>",
        "<tns:ListarMusicasRequest/>",
        "<tns:ListarPlaylistsPorUsuarioRequest><tns:usuarioId>u1</tns:usuarioId></tns:ListarPlaylistsPorUsuarioRequest>",
        "<tns:ListarMusicasPorPlaylistRequest><tns:playlistId>p1</tns:playlistId></tns:ListarMusicasPorPlaylistRequest>",
        "<tns:ListarPlaylistsPorMusicaRequest><tns:musicaId>m1</tns:musicaId></tns:ListarPlaylistsPorMusicaRequest>",
    ]:
        s, xml = _http_req(f"{base_url}/soap", method="POST", body=SOAP_ENV.format(body=body).encode(), headers=headers)
        assert s == 200
        ET.fromstring(xml)

    uid = f"smoke-{uuid.uuid4().hex[:6]}"
    _http_req(
        f"{base_url}/soap",
        method="POST",
        body=SOAP_ENV.format(
            body=f"<tns:CriarUsuarioRequest><tns:id>{uid}</tns:id><tns:nome>Smoke</tns:nome><tns:idade>20</tns:idade></tns:CriarUsuarioRequest>"
        ).encode(),
        headers=headers,
    )
    _http_req(
        f"{base_url}/soap",
        method="POST",
        body=SOAP_ENV.format(body=f"<tns:RemoverUsuarioRequest><tns:id>{uid}</tns:id></tns:RemoverUsuarioRequest>").encode(),
        headers=headers,
    )


def test_graphql(base_url: str) -> None:
    status, _ = _http_req(f"{base_url}/health")
    assert status == 200
    headers = {"Content-Type": "application/json"}
    queries = [
        "{ usuarios { id nome } }",
        "{ musicas { id nome artista } }",
        '{ playlistsPorUsuario(usuarioId: "u1") { id nome } }',
        '{ musicasPorPlaylist(playlistId: "p1") { id nome } }',
        '{ playlistsPorMusica(musicaId: "m1") { id nome } }',
    ]
    for q in queries:
        s, raw = _http_req(f"{base_url}/graphql", method="POST", body=json.dumps({"query": q}).encode(), headers=headers)
        data = json.loads(raw)
        assert s == 200 and "errors" not in data, f"Erro GraphQL: {raw}"

    uid = f"smoke-{uuid.uuid4().hex[:6]}"
    _http_req(
        f"{base_url}/graphql",
        method="POST",
        body=json.dumps({
            "query": "mutation($id: ID, $nome: String!, $idade: Int!) { criarUsuario(id: $id, nome: $nome, idade: $idade) { id } }",
            "variables": {"id": uid, "nome": "Smoke", "idade": 20},
        }).encode(),
        headers=headers,
    )
    _http_req(
        f"{base_url}/graphql",
        method="POST",
        body=json.dumps({
            "query": "mutation($id: ID!) { removerUsuario(id: $id) }",
            "variables": {"id": uid},
        }).encode(),
        headers=headers,
    )


def test_grpc(target: str) -> None:
    import grpc
    from grpc_api import streaming_pb2, streaming_pb2_grpc

    with grpc.insecure_channel(target) as channel:
        stub = streaming_pb2_grpc.StreamingServiceStub(channel)
        assert stub.HealthCheck(streaming_pb2.Empty()).sucesso
        assert len(stub.ListarUsuarios(streaming_pb2.Empty()).usuarios) >= 1
        assert len(stub.ListarMusicas(streaming_pb2.Empty()).musicas) >= 1
        assert len(stub.ListarPlaylistsPorUsuario(streaming_pb2.IdRequest(id="u1")).playlists) >= 1
        assert len(stub.ListarMusicasPorPlaylist(streaming_pb2.IdRequest(id="p1")).musicas) >= 1
        assert len(stub.ListarPlaylistsPorMusica(streaming_pb2.IdRequest(id="m1")).playlists) >= 1

        uid = f"smoke-{uuid.uuid4().hex[:6]}"
        created = stub.CriarUsuario(streaming_pb2.CriarUsuarioRequest(id=uid, nome="Smoke", idade=20))
        assert created.id == uid
        assert stub.RemoverUsuario(streaming_pb2.IdRequest(id=uid)).sucesso


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test das APIs de streaming.")
    parser.add_argument("--langs", nargs="+", default=["python", "java"], choices=["python", "java"])
    parser.add_argument("--techs", nargs="+", default=["rest", "soap", "graphql", "grpc"], choices=["rest", "soap", "graphql", "grpc"])
    args = parser.parse_args()

    failures = 0
    for lang in args.langs:
        for tech in args.techs:
            label = f"{lang}-{tech}"
            try:
                if tech == "rest":
                    test_rest(f"http://localhost:{HTTP_PORTS[(lang, tech)]}")
                elif tech == "soap":
                    test_soap(f"http://localhost:{HTTP_PORTS[(lang, tech)]}")
                elif tech == "graphql":
                    test_graphql(f"http://localhost:{HTTP_PORTS[(lang, tech)]}")
                elif tech == "grpc":
                    test_grpc(GRPC_TARGETS[lang])
                print(f"[OK] {label}")
            except Exception as exc:
                failures += 1
                print(f"[FAIL] {label}: {exc}")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
