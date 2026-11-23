"""Gera os stubs Python gRPC a partir de contracts/proto/streaming.proto."""

from __future__ import annotations

from pathlib import Path
from grpc_tools import protoc


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    proto_dir = repo_root / "contracts" / "proto"
    proto_file = proto_dir / "streaming.proto"
    out_dir = Path(__file__).resolve().parent

    exit_code = protoc.main(
        [
            "grpc_tools.protoc",
            f"-I{proto_dir}",
            f"--python_out={out_dir}",
            f"--grpc_python_out={out_dir}",
            str(proto_file),
        ]
    )
    if exit_code != 0:
        raise RuntimeError(f"Falha ao compilar streaming.proto (código {exit_code})")

    # Corrige import relativo no arquivo *_pb2_grpc.py para funcionar como pacote Python
    grpc_file = out_dir / "streaming_pb2_grpc.py"
    content = grpc_file.read_text(encoding="utf-8")
    content = content.replace(
        "import streaming_pb2 as streaming__pb2",
        "from . import streaming_pb2 as streaming__pb2",
    )
    grpc_file.write_text(content, encoding="utf-8")
    print(f"Stubs gRPC gerados em: {out_dir}")


if __name__ == "__main__":
    main()
