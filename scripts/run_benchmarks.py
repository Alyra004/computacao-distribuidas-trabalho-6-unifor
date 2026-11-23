"""Orquestrador de testes de carga automatizados com Locust (modo headless)."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"
LOCUSTFILE = REPO_ROOT / "load_tests" / "locustfile.py"
SEED_DIR = REPO_ROOT / "contracts" / "seed"

LOCAL_TARGETS = {
    ("python", "rest"): "http://localhost:8001",
    ("python", "soap"): "http://localhost:8002",
    ("python", "graphql"): "http://localhost:8003",
    ("python", "grpc"): "localhost:50051",
    ("java", "rest"): "http://localhost:8081",
    ("java", "soap"): "http://localhost:8082",
    ("java", "graphql"): "http://localhost:8083",
    ("java", "grpc"): "localhost:50052",
}

DOCKER_TARGETS = {
    ("python", "rest"): "http://python-rest:8001",
    ("python", "soap"): "http://python-soap:8002",
    ("python", "graphql"): "http://python-graphql:8003",
    ("python", "grpc"): "python-grpc:50051",
    ("java", "rest"): "http://java-rest:8081",
    ("java", "soap"): "http://java-soap:8082",
    ("java", "graphql"): "http://java-graphql:8083",
    ("java", "grpc"): "java-grpc:50052",
}

DATASETS = {
    "default": SEED_DIR / "initial_data.json",
    "small": SEED_DIR / "seed_small.json",
    "large": SEED_DIR / "seed_large.json",
}


def resolve_seed_path(dataset: str) -> Path:
    if dataset in DATASETS:
        path = DATASETS[dataset]
    else:
        path = Path(dataset)
    if not path.is_file():
        raise FileNotFoundError(
            f"Seed '{path}' não encontrado. Execute 'python scripts/generate_seed.py --profile all' antes."
        )
    return path


def _to_container_seed_path(seed_path: Path) -> str:
    try:
        rel = seed_path.resolve().relative_to(REPO_ROOT.resolve())
        return f"/app/{rel.as_posix()}"
    except ValueError:
        return "/app/contracts/seed/initial_data.json"


def run_single_benchmark(
    lang: str,
    tech: str,
    dataset: str,
    seed_path: Path,
    users: int,
    spawn_rate: int,
    duration: str,
    workload: str,
    mode: str,
    force: bool,
) -> None:
    prefix = RESULTS_DIR / f"{lang}_{tech}_{dataset}_{workload}_u{users}"
    stats_file = Path(f"{prefix}_stats.csv")
    if stats_file.exists() and not force:
        print(f"[SKIP] {stats_file.name} já existe (use --force para sobrescrever).")
        return

    user_class = "GrpcStreamingUser" if tech == "grpc" else "HttpStreamingUser"
    print(
        f"[RUN] [{mode.upper()}] {lang.upper()} / {tech.upper()} | dataset={dataset} | "
        f"workload={workload} | users={users} | duration={duration}"
    )

    if mode == "docker":
        container_prefix = f"/app/results/{prefix.name}"
        cmd = [
            "docker",
            "compose",
            "run",
            "--rm",
            "--no-deps",
            "-e",
            f"TARGET_LANG={lang}",
            "-e",
            f"TARGET_TECH={tech}",
            "-e",
            f"TARGET_URL={DOCKER_TARGETS[(lang, tech)]}",
            "-e",
            f"WORKLOAD_MODE={workload}",
            "-e",
            f"SEED_DATA_PATH={_to_container_seed_path(seed_path)}",
            "locust",
            "locust",
            "-f",
            "/app/load_tests/locustfile.py",
            "--headless",
            "-u",
            str(users),
            "-r",
            str(spawn_rate),
            "-t",
            duration,
            "--csv",
            container_prefix,
            "--exit-code-on-error",
            "0",
            user_class,
        ]
        subprocess.run(cmd, cwd=REPO_ROOT, check=True)
        return

    env = os.environ.copy()
    env["TARGET_LANG"] = lang
    env["TARGET_TECH"] = tech
    env["TARGET_URL"] = LOCAL_TARGETS[(lang, tech)]
    env["WORKLOAD_MODE"] = workload
    env["SEED_DATA_PATH"] = str(seed_path)

    cmd = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        str(LOCUSTFILE),
        "--headless",
        "-u",
        str(users),
        "-r",
        str(spawn_rate),
        "-t",
        duration,
        "--csv",
        str(prefix),
        "--exit-code-on-error",
        "0",
        user_class,
    ]
    subprocess.run(cmd, env=env, cwd=REPO_ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa bateria de benchmarks Locust.")
    parser.add_argument("--langs", nargs="+", default=["python", "java"], choices=["python", "java"])
    parser.add_argument(
        "--techs",
        nargs="+",
        default=["rest", "soap", "graphql", "grpc"],
        choices=["rest", "soap", "graphql", "grpc"],
    )
    parser.add_argument("--dataset", default="small", help="default | small | large | caminho para JSON")
    parser.add_argument("--users", nargs="+", type=int, default=[10, 50, 100, 200])
    parser.add_argument("--spawn-rate", type=int, default=10)
    parser.add_argument("--duration", default="30s")
    parser.add_argument("--workload", default="read", choices=["read", "mixed", "nested"])
    parser.add_argument("--mode", default="local", choices=["local", "docker"])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    seed_path = resolve_seed_path(args.dataset)
    dataset_label = args.dataset if args.dataset in DATASETS else seed_path.stem
    print(f"Usando seed '{seed_path}' (certifique-se de que os servidores ativos carregaram este mesmo seed).")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for lang in args.langs:
        for tech in args.techs:
            for users in args.users:
                run_single_benchmark(
                    lang=lang,
                    tech=tech,
                    dataset=dataset_label,
                    seed_path=seed_path,
                    users=users,
                    spawn_rate=min(args.spawn_rate, users),
                    duration=args.duration,
                    workload=args.workload,
                    mode=args.mode,
                    force=args.force,
                )


if __name__ == "__main__":
    main()
