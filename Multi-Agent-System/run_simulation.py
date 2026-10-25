"""Jalankan simulasi Multi-Agent Deforestation & Fire Monitoring System.

Contoh:
    python run_simulation.py                      # 120 hari, seed 42
    python run_simulation.py --days 180 --seed 7 --detectors 3 --validators 2
    python run_simulation.py --compare            # bandingkan MAS vs detektor tunggal
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from deforestation_mas import ForestMonitoringModel
from deforestation_mas.evaluation import evaluate

HERE = Path(__file__).resolve().parent


def run(days, seed, detectors, validators, use_validation=True, verbose=False):
    model = ForestMonitoringModel(
        seed=seed, n_detectors=detectors, n_validators=validators,
        use_validation=use_validation, verbose=verbose,
    )
    for _ in range(days):
        model.step()
    return model


def fmt(v):
    if isinstance(v, float):
        return "-" if math.isnan(v) else f"{v:.2f}"
    return str(v)


def print_metrics(rows: dict[str, dict]):
    keys = ["true_logging", "true_fire", "cloud_episodes", "cases", "confirmed", "dismissed",
            "uncertain", "false_alarms", "recall", "precision", "cause_accuracy", "mean_latency_days", "messages"]
    names = list(rows)
    print(f"\n{'metrik':22s}" + "".join(f"{n:>22s}" for n in names))
    for k in keys:
        print(f"{k:22s}" + "".join(f"{fmt(rows[n][k]):>22s}" for n in names))


def print_trace(model, status, limit=1):
    shown = 0
    for case in model.cases.values():
        if case.status != status or case.round == 0 and status == "uncertain":
            continue
        print(f"\nTrace percakapan kasus {case.case_id} (status akhir: {status}, penyebab: {case.cause})")
        for m in model.bus.conversation(case.case_id):
            c = {k: v for k, v in m.content.items() if k not in ("mask",)}
            print(f"  hari {m.day:3d} | {m.sender:12s} -> {m.receiver:12s} | {m.performative.upper():8s} {m.topic:9s} {c}")
        shown += 1
        if shown >= limit:
            break


def plot(model, path: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    df = model.datacollector.get_model_vars_dataframe()
    env = model.env
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.3))

    ax = axes[0]
    ax.imshow(model.archive[max(model.archive)].ndvi, cmap="YlGn", vmin=0, vmax=1)
    for e in env.events:
        ax.contour(e.footprint, levels=[0.5], colors="red" if e.kind == "fire" else "saddlebrown", linewidths=1)
    style = {"fire": ("*", "red"), "logging": ("s", "saddlebrown"), "uncertain": ("o", "royalblue"),
             "unknown": ("x", "black")}
    for a in model.alerts:
        c = model.cases[a.case_id]
        r, col = (sum(x) / len(x) for x in c.mask.nonzero())
        mk, colr = style.get(a.kind, ("x", "black"))
        ax.scatter(col, r, marker=mk, s=70, facecolors="none" if mk != "x" else colr, edgecolors=colr)
    ax.set_title(f"NDVI hari {model.day}: kontur = kejadian nyata, simbol = peringatan")
    ax.legend(handles=[Patch(color="saddlebrown", label="tebang liar"), Patch(color="red", label="kebakaran"),
                       Patch(color="royalblue", label="perlu tinjauan")], loc="lower right", fontsize=8)
    ax.set_xticks([]), ax.set_yticks([])

    ax = axes[1]
    ax.plot(df["day"], df["true_events"], "k--", label="kejadian nyata (kumulatif)")
    ax.plot(df["day"], df["confirmed_logging"], color="saddlebrown", label="terkonfirmasi: tebang liar")
    ax.plot(df["day"], df["confirmed_fire"], color="red", label="terkonfirmasi: kebakaran")
    ax.plot(df["day"], df["dismissed"], color="gray", label="ditolak (alarm palsu/awan)")
    if df["confirmed_unknown"].any():
        ax.plot(df["day"], df["confirmed_unknown"], color="black", label="terkonfirmasi tanpa validasi")
    ax.set_xlabel("hari"), ax.set_ylabel("jumlah kasus"), ax.legend(fontsize=8)
    ax.set_title("Perkembangan kasus")

    ax = axes[2]
    ax.bar(df["day"], df["messages_today"], color="steelblue")
    ax.set_xlabel("hari"), ax.set_ylabel("pesan antaragen")
    ax.set_title("Lalu lintas komunikasi MAS per hari")

    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--days", type=int, default=120)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--detectors", type=int, default=1, help="jumlah Agen Deteksi Perubahan")
    p.add_argument("--validators", type=int, default=1, help="jumlah Agen Validasi")
    p.add_argument("--compare", action="store_true", help="bandingkan dengan detektor tunggal tanpa validasi")
    p.add_argument("--quiet", action="store_true", help="jangan cetak setiap peringatan")
    p.add_argument("--out", type=Path, default=HERE / "output")
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    print(f"Simulasi {args.days} hari | seed {args.seed} | {args.detectors} detektor, {args.validators} validator")
    print("Peringatan yang dikirim Agen Notifikasi:")
    model = run(args.days, args.seed, args.detectors, args.validators, verbose=not args.quiet)

    rows = {"MAS (dengan konsensus)": evaluate(model)}
    if args.compare:
        base = run(args.days, args.seed, args.detectors, 0, use_validation=False)
        rows["Detektor tunggal"] = evaluate(base)
    print_metrics(rows)

    print_trace(model, "confirmed")
    print_trace(model, "dismissed")

    (args.out / "alerts.json").write_text(json.dumps([a.to_dict() for a in model.alerts], indent=2))
    model.datacollector.get_model_vars_dataframe().to_csv(args.out / "timeseries.csv", index=False)
    plot(model, args.out / "simulation.png")
    print(f"\nHasil disimpan di {args.out}: alerts.json, timeseries.csv, simulation.png")


if __name__ == "__main__":
    main()
