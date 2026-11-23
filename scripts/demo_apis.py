"""Script de demonstração ao vivo das 8 APIs (5 consultas obrigatórias + ciclo CRUD)."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import xml.dom.minidom
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


def _http_req(
    url: str,
    method: str = "GET",
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, str]:
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read().decode("utf-8")


def _print_header(lang: str, tech: str, endpoint: str) -> None:
    print("\n" + "=" * 72)
    print(f"DEMONSTRAÇÃO: {lang.upper()} / {tech.upper()} ({endpoint})")
    print("=" * 72)


def _print_json_sample(title: str, data: object, limit: int) -> None:
    if isinstance(data, list):
        preview = data[:limit]
        print(f"\n[{title}] (total={len(data)}, exibindo {len(preview)})")
        print(json.dumps(preview, ensure_ascii=False, indent=2))
    else:
        print(f"\n[{title}]")
        print(json.dumps(data, ensure_ascii=False, indent=2))


def _pretty_xml(raw_xml: str, limit: int) -> str:
    parsed = xml.dom.minidom.parseString(raw_xml.encode("utf-8"))
    lines = [line for line in parsed.toprettyxml(indent="  ").splitlines() if line.strip()]
    max_lines = max(12, limit * 8)
    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines]) + f"\n  ... ({len(lines) - max_lines} linhas omitidas)"
    return "\n".join(lines)


def demo_rest(lang: str, base_url: str, limit: int) -> None:
    _print_header(lang, "rest", base_url)
    queries = [
        ("1. Todos os usuários", "/usuarios"),
        ("2. Todas as músicas", "/musicas"),
        ("3. Playlists do usuário u1", "/usuarios/u1/playlists"),
        ("4. Músicas da playlist p1", "/playlists/p1/musicas"),
        ("5. Playlists com a música m1", "/musicas/m1/playlists"),
    ]
    for title, path in queries:
        _, raw = _http_req(f"{base_url}{path}")
        _print_json_sample(title, json.loads(raw), limit)

    headers = {"Content-Type": "application/json"}
    uid = "u_demo"
    status, created = _http_req(
        f"{base_url}/usuarios",
        method="POST",
        body=json.dumps({"id": uid, "nome": "Usuário Demo", "idade": 22}).encode(),
        headers=headers,
    )
    print(f"\n[CRUD - POST /usuarios] HTTP {status}: {created}")
    status, fetched = _http_req(f"{base_url}/usuarios/{uid}")
    print(f"[CRUD - GET /usuarios/{uid}] HTTP {status}: {fetched}")
    status, updated = _http_req(
        f"{base_url}/usuarios/{uid}",
        method="PUT",
        body=json.dumps({"nome": "Usuário Demo Editado", "idade": 23}).encode(),
        headers=headers,
    )
    print(f"[CRUD - PUT /usuarios/{uid}] HTTP {status}: {updated}")
    status, _ = _http_req(f"{base_url}/usuarios/{uid}", method="DELETE")
    print(f"[CRUD - DELETE /usuarios/{uid}] HTTP {status}")


def demo_soap(lang: str, base_url: str, limit: int) -> None:
    _print_header(lang, "soap", base_url)
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    queries = [
        ("1. Todos os usuários", "<tns:ListarUsuariosRequest/>"),
        ("2. Todas as músicas", "<tns:ListarMusicasRequest/>"),
        ("3. Playlists do usuário u1", "<tns:ListarPlaylistsPorUsuarioRequest><tns:usuarioId>u1</tns:usuarioId></tns:ListarPlaylistsPorUsuarioRequest>"),
        ("4. Músicas da playlist p1", "<tns:ListarMusicasPorPlaylistRequest><tns:playlistId>p1</tns:playlistId></tns:ListarMusicasPorPlaylistRequest>"),
        ("5. Playlists com a música m1", "<tns:ListarPlaylistsPorMusicaRequest><tns:musicaId>m1</tns:musicaId></tns:ListarPlaylistsPorMusicaRequest>"),
    ]
    for title, body in queries:
        _, raw = _http_req(f"{base_url}/soap", method="POST", body=SOAP_ENV.format(body=body).encode(), headers=headers)
        ET.fromstring(raw)
        print(f"\n[{title}]\n{_pretty_xml(raw, limit)}")

    uid = "u_demo"
    ops = [
        ("CRUD - CriarUsuario", f"<tns:CriarUsuarioRequest><tns:id>{uid}</tns:id><tns:nome>Usuário Demo</tns:nome><tns:idade>22</tns:idade></tns:CriarUsuarioRequest>"),
        ("CRUD - ObterUsuario", f"<tns:ObterUsuarioRequest><tns:id>{uid}</tns:id></tns:ObterUsuarioRequest>"),
        ("CRUD - AtualizarUsuario", f"<tns:AtualizarUsuarioRequest><tns:id>{uid}</tns:id><tns:nome>Usuário Demo Editado</tns:nome><tns:idade>23</tns:idade></tns:AtualizarUsuarioRequest>"),
        ("CRUD - RemoverUsuario", f"<tns:RemoverUsuarioRequest><tns:id>{uid}</tns:id></tns:RemoverUsuarioRequest>"),
    ]
    for label, body in ops:
        status, raw = _http_req(f"{base_url}/soap", method="POST", body=SOAP_ENV.format(body=body).encode(), headers=headers)
        print(f"\n[{label}] HTTP {status}\n{_pretty_xml(raw, limit)}")


def demo_graphql(lang: str, base_url: str, limit: int) -> None:
    _print_header(lang, "graphql", base_url)
    headers = {"Content-Type": "application/json"}
    queries = [
        ("1. Todos os usuários", "{ usuarios { id nome idade } }", "usuarios"),
        ("2. Todas as músicas", "{ musicas { id nome artista } }", "musicas"),
        ("3. Playlists do usuário u1", '{ playlistsPorUsuario(usuarioId: "u1") { id nome } }', "playlistsPorUsuario"),
        ("4. Músicas da playlist p1", '{ musicasPorPlaylist(playlistId: "p1") { id nome artista } }', "musicasPorPlaylist"),
        ("5. Playlists com a música m1", '{ playlistsPorMusica(musicaId: "m1") { id nome usuario { nome } } }', "playlistsPorMusica"),
    ]
    for title, query, field in queries:
        _, raw = _http_req(f"{base_url}/graphql", method="POST", body=json.dumps({"query": query}).encode(), headers=headers)
        payload = json.loads(raw)
        _print_json_sample(title, payload["data"][field], limit)

    uid = "u_demo"
    mutations = [
        ("CRUD - criarUsuario", "mutation($id: ID, $nome: String!, $idade: Int!) { criarUsuario(id: $id, nome: $nome, idade: $idade) { id nome idade } }", {"id": uid, "nome": "Usuário Demo", "idade": 22}),
        ("CRUD - atualizarUsuario", "mutation($id: ID!, $nome: String!, $idade: Int!) { atualizarUsuario(id: $id, nome: $nome, idade: $idade) { id nome idade } }", {"id": uid, "nome": "Usuário Demo Editado", "idade": 23}),
        ("CRUD - removerUsuario", "mutation($id: ID!) { removerUsuario(id: $id) }", {"id": uid}),
    ]
    for label, query, variables in mutations:
        _, raw = _http_req(f"{base_url}/graphql", method="POST", body=json.dumps({"query": query, "variables": variables}).encode(), headers=headers)
        _print_json_sample(label, json.loads(raw), limit)


def demo_grpc(lang: str, target: str, limit: int) -> None:
    import grpc
    from google.protobuf.json_format import MessageToDict
    from grpc_api import streaming_pb2, streaming_pb2_grpc

    _print_header(lang, "grpc", target)
    with grpc.insecure_channel(target) as channel:
        stub = streaming_pb2_grpc.StreamingServiceStub(channel)
        u_resp = stub.ListarUsuarios(streaming_pb2.Empty())
        _print_json_sample("1. Todos os usuários", MessageToDict(u_resp).get("usuarios", []), limit)

        m_resp = stub.ListarMusicas(streaming_pb2.Empty())
        _print_json_sample("2. Todas as músicas", MessageToDict(m_resp).get("musicas", []), limit)

        pu_resp = stub.ListarPlaylistsPorUsuario(streaming_pb2.IdRequest(id="u1"))
        _print_json_sample("3. Playlists do usuário u1", MessageToDict(pu_resp).get("playlists", []), limit)

        mp_resp = stub.ListarMusicasPorPlaylist(streaming_pb2.IdRequest(id="p1"))
        _print_json_sample("4. Músicas da playlist p1", MessageToDict(mp_resp).get("musicas", []), limit)

        pm_resp = stub.ListarPlaylistsPorMusica(streaming_pb2.IdRequest(id="m1"))
        _print_json_sample("5. Playlists com a música m1", MessageToDict(pm_resp).get("playlists", []), limit)

        uid = "u_demo"
        created = stub.CriarUsuario(streaming_pb2.CriarUsuarioRequest(id=uid, nome="Usuário Demo", idade=22))
        _print_json_sample("CRUD - CriarUsuario", MessageToDict(created), limit)
        fetched = stub.ObterUsuario(streaming_pb2.IdRequest(id=uid))
        _print_json_sample("CRUD - ObterUsuario", MessageToDict(fetched), limit)
        updated = stub.AtualizarUsuario(streaming_pb2.AtualizarUsuarioRequest(id=uid, nome="Usuário Demo Editado", idade=23))
        _print_json_sample("CRUD - AtualizarUsuario", MessageToDict(updated), limit)
        removed = stub.RemoverUsuario(streaming_pb2.IdRequest(id=uid))
        _print_json_sample("CRUD - RemoverUsuario", MessageToDict(removed), limit)


def main() -> None:
    parser = argparse.ArgumentParser(description="Demonstração interativa das APIs (Slide 6 + CRUD).")
    parser.add_argument("--langs", nargs="+", default=["python", "java"], choices=["python", "java"])
    parser.add_argument("--techs", nargs="+", default=["rest", "soap", "graphql", "grpc"], choices=["rest", "soap", "graphql", "grpc"])
    parser.add_argument("--limit", type=int, default=3, help="Quantidade máxima de itens exibidos por lista.")
    args = parser.parse_args()

    for lang in args.langs:
        for tech in args.techs:
            if tech == "rest":
                demo_rest(lang, f"http://localhost:{HTTP_PORTS[(lang, tech)]}", args.limit)
            elif tech == "soap":
                demo_soap(lang, f"http://localhost:{HTTP_PORTS[(lang, tech)]}", args.limit)
            elif tech == "graphql":
                demo_graphql(lang, f"http://localhost:{HTTP_PORTS[(lang, tech)]}", args.limit)
            elif tech == "grpc":
                demo_grpc(lang, GRPC_TARGETS[lang], args.limit)


if __name__ == "__main__":
    main()
