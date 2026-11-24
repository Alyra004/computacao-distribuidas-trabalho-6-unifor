"""Entrega Python 2: API SOAP/XML com WSDL reutilizando common.StreamingService."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse

from common.models import Musica, Playlist, Usuario
from common.service import (
    EntityNotFoundError,
    StreamingService,
    ValidationError,
    get_streaming_service,
)

SOAP_ENV_NS = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "http://unifor.br/distribuidos/streaming"

app = FastAPI(title="Streaming de Músicas - Python SOAP", version="1.0.0")
service: StreamingService = get_streaming_service()


def _resolve_contract_file(env_var: str, filename: str) -> Path:
    env_path = os.getenv(env_var)
    if env_path and Path(env_path).is_file():
        return Path(env_path)
    return Path(__file__).resolve().parents[2] / "contracts" / "soap" / filename


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _child_text(node: ET.Element, name: str, default: str | None = None) -> str | None:
    for child in node:
        if _local_name(child.tag) == name:
            return (child.text or "").strip()
    return default


def _child_texts(node: ET.Element, name: str) -> list[str]:
    return [
        (child.text or "").strip()
        for child in node
        if _local_name(child.tag) == name and child.text
    ]


def _append_text(parent: ET.Element, tag: str, value: object) -> None:
    el = ET.SubElement(parent, f"{{{TNS}}}{tag}")
    el.text = str(value)


def _append_usuario(parent: ET.Element, u: Usuario, tag: str = "usuario") -> None:
    node = ET.SubElement(parent, f"{{{TNS}}}{tag}")
    _append_text(node, "id", u.id)
    _append_text(node, "nome", u.nome)
    _append_text(node, "idade", u.idade)


def _append_musica(parent: ET.Element, m: Musica, tag: str = "musica") -> None:
    node = ET.SubElement(parent, f"{{{TNS}}}{tag}")
    _append_text(node, "id", m.id)
    _append_text(node, "nome", m.nome)
    _append_text(node, "artista", m.artista)


def _append_playlist(parent: ET.Element, p: Playlist, tag: str = "playlist") -> None:
    node = ET.SubElement(parent, f"{{{TNS}}}{tag}")
    _append_text(node, "id", p.id)
    _append_text(node, "nome", p.nome)
    _append_text(node, "usuarioId", p.usuario_id)
    for mid in p.musica_ids:
        _append_text(node, "musicaIds", mid)


def _wrap_soap_response(body_element: ET.Element) -> str:
    ET.register_namespace("soapenv", SOAP_ENV_NS)
    ET.register_namespace("tns", TNS)
    envelope = ET.Element(f"{{{SOAP_ENV_NS}}}Envelope")
    body = ET.SubElement(envelope, f"{{{SOAP_ENV_NS}}}Body")
    body.append(body_element)
    return ET.tostring(envelope, encoding="unicode", xml_declaration=True)


def _soap_fault(fault_code: str, message: str, status_code: int = 400) -> Response:
    ET.register_namespace("soapenv", SOAP_ENV_NS)
    envelope = ET.Element(f"{{{SOAP_ENV_NS}}}Envelope")
    body = ET.SubElement(envelope, f"{{{SOAP_ENV_NS}}}Body")
    fault = ET.SubElement(body, f"{{{SOAP_ENV_NS}}}Fault")
    ET.SubElement(fault, "faultcode").text = fault_code
    ET.SubElement(fault, "faultstring").text = message
    xml = ET.tostring(envelope, encoding="unicode", xml_declaration=True)
    return Response(content=xml, media_type="text/xml; charset=utf-8", status_code=status_code)


def _op_listar_usuarios(_: ET.Element) -> ET.Element:
    resp = ET.Element(f"{{{TNS}}}ListarUsuariosResponse")
    for u in service.listar_usuarios():
        _append_usuario(resp, u)
    return resp


def _op_obter_usuario(req: ET.Element) -> ET.Element:
    uid = _child_text(req, "id", "") or ""
    resp = ET.Element(f"{{{TNS}}}ObterUsuarioResponse")
    _append_usuario(resp, service.obter_usuario(uid))
    return resp


def _op_criar_usuario(req: ET.Element) -> ET.Element:
    nome = _child_text(req, "nome", "") or ""
    idade = int(_child_text(req, "idade", "0") or 0)
    uid = _child_text(req, "id")
    resp = ET.Element(f"{{{TNS}}}CriarUsuarioResponse")
    _append_usuario(resp, service.criar_usuario(nome=nome, idade=idade, id=uid))
    return resp


def _op_atualizar_usuario(req: ET.Element) -> ET.Element:
    uid = _child_text(req, "id", "") or ""
    nome = _child_text(req, "nome", "") or ""
    idade = int(_child_text(req, "idade", "0") or 0)
    resp = ET.Element(f"{{{TNS}}}AtualizarUsuarioResponse")
    _append_usuario(resp, service.atualizar_usuario(uid, nome, idade))
    return resp


def _op_remover_usuario(req: ET.Element) -> ET.Element:
    uid = _child_text(req, "id", "") or ""
    sucesso = service.remover_usuario(uid)
    resp = ET.Element(f"{{{TNS}}}RemoverUsuarioResponse")
    _append_text(resp, "sucesso", str(sucesso).lower())
    return resp


def _op_listar_musicas(_: ET.Element) -> ET.Element:
    resp = ET.Element(f"{{{TNS}}}ListarMusicasResponse")
    for m in service.listar_musicas():
        _append_musica(resp, m)
    return resp


def _op_obter_musica(req: ET.Element) -> ET.Element:
    mid = _child_text(req, "id", "") or ""
    resp = ET.Element(f"{{{TNS}}}ObterMusicaResponse")
    _append_musica(resp, service.obter_musica(mid))
    return resp


def _op_criar_musica(req: ET.Element) -> ET.Element:
    nome = _child_text(req, "nome", "") or ""
    artista = _child_text(req, "artista", "") or ""
    mid = _child_text(req, "id")
    resp = ET.Element(f"{{{TNS}}}CriarMusicaResponse")
    _append_musica(resp, service.criar_musica(nome=nome, artista=artista, id=mid))
    return resp


def _op_atualizar_musica(req: ET.Element) -> ET.Element:
    mid = _child_text(req, "id", "") or ""
    nome = _child_text(req, "nome", "") or ""
    artista = _child_text(req, "artista", "") or ""
    resp = ET.Element(f"{{{TNS}}}AtualizarMusicaResponse")
    _append_musica(resp, service.atualizar_musica(mid, nome, artista))
    return resp


def _op_remover_musica(req: ET.Element) -> ET.Element:
    mid = _child_text(req, "id", "") or ""
    sucesso = service.remover_musica(mid)
    resp = ET.Element(f"{{{TNS}}}RemoverMusicaResponse")
    _append_text(resp, "sucesso", str(sucesso).lower())
    return resp


def _op_listar_playlists(_: ET.Element) -> ET.Element:
    resp = ET.Element(f"{{{TNS}}}ListarPlaylistsResponse")
    for p in service.listar_playlists():
        _append_playlist(resp, p)
    return resp


def _op_obter_playlist(req: ET.Element) -> ET.Element:
    pid = _child_text(req, "id", "") or ""
    resp = ET.Element(f"{{{TNS}}}ObterPlaylistResponse")
    _append_playlist(resp, service.obter_playlist(pid))
    return resp


def _op_criar_playlist(req: ET.Element) -> ET.Element:
    nome = _child_text(req, "nome", "") or ""
    uid = _child_text(req, "usuarioId", "") or ""
    mids = _child_texts(req, "musicaIds")
    pid = _child_text(req, "id")
    resp = ET.Element(f"{{{TNS}}}CriarPlaylistResponse")
    _append_playlist(resp, service.criar_playlist(nome=nome, usuario_id=uid, musica_ids=mids, id=pid))
    return resp


def _op_atualizar_playlist(req: ET.Element) -> ET.Element:
    pid = _child_text(req, "id", "") or ""
    nome = _child_text(req, "nome", "") or ""
    uid = _child_text(req, "usuarioId")
    mids = _child_texts(req, "musicaIds") if any(_local_name(c.tag) == "musicaIds" for c in req) else None
    resp = ET.Element(f"{{{TNS}}}AtualizarPlaylistResponse")
    _append_playlist(resp, service.atualizar_playlist(pid, nome, uid, mids))
    return resp


def _op_remover_playlist(req: ET.Element) -> ET.Element:
    pid = _child_text(req, "id", "") or ""
    sucesso = service.remover_playlist(pid)
    resp = ET.Element(f"{{{TNS}}}RemoverPlaylistResponse")
    _append_text(resp, "sucesso", str(sucesso).lower())
    return resp


def _op_adicionar_musica_playlist(req: ET.Element) -> ET.Element:
    pid = _child_text(req, "playlistId", "") or ""
    mid = _child_text(req, "musicaId", "") or ""
    resp = ET.Element(f"{{{TNS}}}AdicionarMusicaNaPlaylistResponse")
    _append_playlist(resp, service.adicionar_musica_na_playlist(pid, mid))
    return resp


def _op_remover_musica_playlist(req: ET.Element) -> ET.Element:
    pid = _child_text(req, "playlistId", "") or ""
    mid = _child_text(req, "musicaId", "") or ""
    resp = ET.Element(f"{{{TNS}}}RemoverMusicaDaPlaylistResponse")
    _append_playlist(resp, service.remover_musica_da_playlist(pid, mid))
    return resp


def _op_playlists_por_usuario(req: ET.Element) -> ET.Element:
    uid = _child_text(req, "usuarioId", "") or ""
    resp = ET.Element(f"{{{TNS}}}ListarPlaylistsPorUsuarioResponse")
    for p in service.listar_playlists_por_usuario(uid):
        _append_playlist(resp, p)
    return resp


def _op_musicas_por_playlist(req: ET.Element) -> ET.Element:
    pid = _child_text(req, "playlistId", "") or ""
    resp = ET.Element(f"{{{TNS}}}ListarMusicasPorPlaylistResponse")
    for m in service.listar_musicas_por_playlist(pid):
        _append_musica(resp, m)
    return resp


def _op_playlists_por_musica(req: ET.Element) -> ET.Element:
    mid = _child_text(req, "musicaId", "") or ""
    resp = ET.Element(f"{{{TNS}}}ListarPlaylistsPorMusicaResponse")
    for p in service.listar_playlists_por_musica(mid):
        _append_playlist(resp, p)
    return resp


SOAP_HANDLERS: dict[str, Callable[[ET.Element], ET.Element]] = {
    "ListarUsuariosRequest": _op_listar_usuarios,
    "ObterUsuarioRequest": _op_obter_usuario,
    "CriarUsuarioRequest": _op_criar_usuario,
    "AtualizarUsuarioRequest": _op_atualizar_usuario,
    "RemoverUsuarioRequest": _op_remover_usuario,
    "ListarMusicasRequest": _op_listar_musicas,
    "ObterMusicaRequest": _op_obter_musica,
    "CriarMusicaRequest": _op_criar_musica,
    "AtualizarMusicaRequest": _op_atualizar_musica,
    "RemoverMusicaRequest": _op_remover_musica,
    "ListarPlaylistsRequest": _op_listar_playlists,
    "ObterPlaylistRequest": _op_obter_playlist,
    "CriarPlaylistRequest": _op_criar_playlist,
    "AtualizarPlaylistRequest": _op_atualizar_playlist,
    "RemoverPlaylistRequest": _op_remover_playlist,
    "AdicionarMusicaNaPlaylistRequest": _op_adicionar_musica_playlist,
    "RemoverMusicaDaPlaylistRequest": _op_remover_musica_playlist,
    "ListarPlaylistsPorUsuarioRequest": _op_playlists_por_usuario,
    "ListarMusicasPorPlaylistRequest": _op_musicas_por_playlist,
    "ListarPlaylistsPorMusicaRequest": _op_playlists_por_musica,
}


@app.get("/", response_class=HTMLResponse)
def playground() -> Response:
    playground_path = _resolve_contract_file("SOAP_PLAYGROUND_PATH", "playground.html")
    if not playground_path.is_file():
        return Response(content="SOAP playground não encontrado.", media_type="text/plain", status_code=404)
    html = playground_path.read_text(encoding="utf-8").replace("{{SERVICE_LABEL}}", "Python SOAP (FastAPI)")
    return HTMLResponse(content=html)


@app.get("/health")
def health() -> dict[str, object]:
    return service.health_check()


@app.get("/soap")
def get_wsdl(request: Request) -> Response:
    if "wsdl" in request.query_params:
        wsdl_path = _resolve_contract_file("WSDL_PATH", "streaming.wsdl")
        if wsdl_path.is_file():
            return Response(content=wsdl_path.read_text(encoding="utf-8"), media_type="text/xml")
    return Response(content="Use POST /soap ou GET /soap?wsdl", media_type="text/plain")


@app.post("/soap")
async def soap_endpoint(request: Request) -> Response:
    raw_body = await request.body()
    try:
        root = ET.fromstring(raw_body)
        body = next((el for el in root if _local_name(el.tag) == "Body"), None)
        if body is None or len(body) == 0:
            return _soap_fault("soapenv:Client", "Corpo SOAP ausente ou vazio.", status_code=400)

        op_node = body[0]
        op_name = _local_name(op_node.tag)
        handler = SOAP_HANDLERS.get(op_name)
        if handler is None:
            return _soap_fault("soapenv:Client", f"Operação SOAP desconhecida: {op_name}", status_code=400)

        resp_element = handler(op_node)
        return Response(content=_wrap_soap_response(resp_element), media_type="text/xml; charset=utf-8")
    except EntityNotFoundError as exc:
        return _soap_fault("soapenv:Client", str(exc), status_code=404)
    except (ValidationError, ValueError, ET.ParseError) as exc:
        return _soap_fault("soapenv:Client", str(exc), status_code=400)


if __name__ == "__main__":
    uvicorn.run("soap_api.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8002")))
