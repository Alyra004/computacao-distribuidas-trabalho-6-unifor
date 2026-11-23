"""Modelos de domínio compartilhados entre todas as APIs Python."""

from dataclasses import dataclass, field


@dataclass
class Usuario:
    """Representa um usuário do serviço de streaming."""

    id: str
    nome: str
    idade: int

    def to_dict(self) -> dict:
        return {"id": self.id, "nome": self.nome, "idade": self.idade}


@dataclass
class Musica:
    """Representa uma música mantida no catálogo do serviço."""

    id: str
    nome: str
    artista: str

    def to_dict(self) -> dict:
        return {"id": self.id, "nome": self.nome, "artista": self.artista}


@dataclass
class Playlist:
    """Representa uma playlist pertencente a um usuário e composta por músicas."""

    id: str
    nome: str
    usuario_id: str
    musica_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "usuarioId": self.usuario_id,
            "musicaIds": list(self.musica_ids),
        }
