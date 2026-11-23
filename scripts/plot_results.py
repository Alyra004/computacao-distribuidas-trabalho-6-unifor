"""Gera tabelas e gráficos comparativos a partir dos CSVs gerados em results/."""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"
CHARTS_DIR = REPO_ROOT / "graficos"

NEW_FILENAME_RE = re.compile(
    r"^(python|java)_(rest|soap|graphql|grpc)_([a-zA-Z0-9_-]+)_(read|mixed|nested)_u(\d+)_stats\.csv$"
)
LEGACY_FILENAME_RE = re.compile(r"^(python|java)_(rest|soap|graphql|grpc)_u(\d+)_stats\.csv$")


def _parse_filename(name: str) -> tuple[str, str, str, str, int] | None:
    match = NEW_FILENAME_RE.match(name)
    if match:
        lang, tech, dataset, workload, users_str = match.groups()
        return lang, tech, dataset, workload, int(users_str)
    legacy = LEGACY_FILENAME_RE.match(name)
    if legacy:
        lang, tech, users_str = legacy.groups()
        return lang, tech, "default", "read", int(users_str)
    return None


def collect_aggregated_stats() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for csv_path in sorted(RESULTS_DIR.glob("*_stats.csv")):
        parsed = _parse_filename(csv_path.name)
        if not parsed:
            continue
        lang, tech, dataset, workload, users = parsed
        df = pd.read_csv(csv_path)
        agg = df[df["Name"] == "Aggregated"]
        if agg.empty:
            continue
        row = agg.iloc[0]
        req_count = float(row["Request Count"])
        fail_count = float(row["Failure Count"])
        avg_size = float(row["Average Content Size"]) if "Average Content Size" in row else 0.0
        tech_label = "GraphQL" if tech == "graphql" else tech.upper()
        rows.append(
            {
                "Dataset": dataset,
                "Workload": workload,
                "Linguagem": lang.capitalize(),
                "Tecnologia": tech_label,
                "Cenário": f"{lang.capitalize()} - {tech_label}",
                "Usuários": users,
                "Requisições": int(req_count),
                "Falhas": int(fail_count),
                "Taxa de Falhas (%)": (fail_count / req_count * 100.0) if req_count else 0.0,
                "Tempo Médio (ms)": float(row["Average Response Time"]),
                "Mediana p50 (ms)": float(row["Median Response Time"]),
                "p95 (ms)": float(row["95%"]),
                "Vazão (req/s)": float(row["Requests/s"]),
                "Payload Médio (bytes)": avg_size,
            }
        )
    return pd.DataFrame(rows)


def save_metric_chart(
    df: pd.DataFrame,
    metric: str,
    filename: str,
    title: str,
    ylabel: str,
) -> None:
    plt.figure(figsize=(11, 6))
    sns.lineplot(data=df, x="Usuários", y=metric, hue="Cenário", marker="o", linewidth=2.2)
    plt.title(title, fontsize=13, fontweight="bold")
    plt.xlabel("Usuários Simultâneos")
    plt.ylabel(ylabel)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / filename, dpi=180)
    plt.close()


def main() -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    df = collect_aggregated_stats()
    if df.empty:
        print("Nenhum arquivo *_stats.csv encontrado em results/. Execute run_benchmarks.py primeiro.")
        return

    df = df.sort_values(["Dataset", "Workload", "Linguagem", "Tecnologia", "Usuários"])
    df.to_csv(CHARTS_DIR / "tabela_desempenho.csv", index=False)

    sns.set_theme(style="whitegrid")
    for (dataset, workload), group_df in df.groupby(["Dataset", "Workload"]):
        suffix = f"{dataset}_{workload}"
        label = f"[{dataset} / {workload}]"
        save_metric_chart(
            group_df,
            "Tempo Médio (ms)",
            f"tempo_medio_{suffix}.png",
            f"Tempo Médio de Resposta {label}",
            "Tempo Médio (ms)",
        )
        save_metric_chart(
            group_df,
            "p95 (ms)",
            f"percentil_95_{suffix}.png",
            f"Latência p95 {label}",
            "p95 (ms)",
        )
        save_metric_chart(
            group_df,
            "Vazão (req/s)",
            f"vazao_rps_{suffix}.png",
            f"Vazão (Throughput) {label}",
            "Requisições/s",
        )
        save_metric_chart(
            group_df,
            "Taxa de Falhas (%)",
            f"taxa_falhas_{suffix}.png",
            f"Taxa de Falhas (%) {label}",
            "Falhas (%)",
        )
        save_metric_chart(
            group_df,
            "Payload Médio (bytes)",
            f"tamanho_payload_{suffix}.png",
            f"Tamanho Médio de Payload {label}",
            "Bytes por Resposta",
        )

    print(f"Gráficos e tabela salvos em: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
