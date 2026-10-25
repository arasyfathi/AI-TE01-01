"""Pemantauan kebakaran hutan dan lahan (karhutla) per kecamatan, siklus 2 minggu (Sentinel-2 + titik api VIIRS).

Dua jenis peringatan, tanpa membedakan tutupan lahan:
  * titik api aktif (Agen Titik Api, VIIRS sampai hari ini)       -> DARURAT
  * bekas terbakar terkonfirmasi (penurunan NDVI + bukti api)     -> TINGGI
Penurunan NDVI tanpa bukti api (panen, pembukaan lahan, kabut) tidak diperingatkan.

Contoh:
    python run_pantau.py --list                                   # daftar kecamatan
    python run_pantau.py --project PROJECT-ID --status            # cek kesegaran data di GEE
    python run_pantau.py --project PROJECT-ID --kecamatan "Sungai Raya"
    python run_pantau.py --project PROJECT-ID --kecamatan semua
    python run_pantau.py --project PROJECT-ID --kecamatan "Sungai Raya" --end-date 2023-10-15   # uji historis

Setiap putaran memproses 4 periode terakhir (2 periode acuan + 2 periode dipantau). Peringatan baru
ditambahkan ke riwayat per kecamatan, jadi menjalankan ulang tidak menggandakan peringatan.
``--project`` boleh dikosongkan bila variabel lingkungan EE_PROJECT sudah diatur.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

from deforestation_mas import ForestMonitoringModel
from deforestation_mas.agents import CONFIRMED, DISMISSED, PENDING, UNCERTAIN
from deforestation_mas.region import find_region, load_regions
from deforestation_mas.sentinel_environment import CLOUD_SCORE, S2, SentinelEnvironment

HERE = Path(__file__).resolve().parent
DEFAULT_REGIONS = HERE / "data" / "kubu_raya_kecamatan.geojson"


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--project", default=os.environ.get("EE_PROJECT"), help="Project ID Google Cloud untuk GEE")
    p.add_argument("--wilayah", type=Path, default=DEFAULT_REGIONS, help="GeoJSON batas kecamatan (WGS84)")
    p.add_argument("--list", action="store_true", help="tampilkan daftar kecamatan lalu keluar")
    p.add_argument("--status", action="store_true", help="tampilkan tanggal data terbaru tiap sumber lalu keluar")
    p.add_argument("--kecamatan", help='nama kecamatan, atau "semua"')
    p.add_argument("--end-date", help="anggap hari ini = tanggal ini (uji historis), YYYY-MM-DD")
    p.add_argument("--periods", type=int, default=4, help="jumlah periode yang diproses per putaran (min. 3)")
    p.add_argument("--period-days", type=int, default=14, help="panjang satu periode (hari)")
    p.add_argument("--latency", type=int, default=3, help="jeda masuknya data ke GEE (hari)")
    p.add_argument("--pixel", type=float, default=30.0, help="ukuran piksel (m); 10 = paling tajam tetapi lambat")
    p.add_argument("--min-ha", type=float, default=2.0, help="luas minimal wilayah curiga (ha)")
    p.add_argument("--merge-m", type=float, default=500.0, help="jarak penggabungan kasus menjadi satu kejadian (m)")
    p.add_argument("--drop-threshold", type=float, default=0.20)
    p.add_argument("--persist-threshold", type=float, default=0.15)
    p.add_argument("--cloud-threshold", type=float, default=0.60, help="ambang Cloud Score+ cs_cdf (0.5-0.65)")
    p.add_argument("--cache-dir", default=str(HERE / "pantau_cache"))
    p.add_argument("--out", type=Path, default=HERE / "output_pantau")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)
    if args.periods < 3:
        p.error("--periods minimal 3 (2 periode acuan + 1 periode dipantau)")
    return args


def make_env(args, region) -> SentinelEnvironment:
    return SentinelEnvironment(
        region, project=args.project, end_date=args.end_date, n_periods=args.periods,
        period_days=args.period_days, latency_days=args.latency, pixel_m=args.pixel, cache_dir=args.cache_dir,
        cloud_threshold=args.cloud_threshold,  # tanpa peta tutupan lahan: lahan tidak dibedakan
    )


def build_model(args, env) -> ForestMonitoringModel:
    return ForestMonitoringModel(
        env=env,
        reference_lags=(2, 1),  # acuan = dua periode sebelumnya
        reference_mode="latest",  # acuan = pengamatan bersih terakhir (tidak mendeteksi ulang kejadian lama)
        resolve_after_validation=True,  # kebakaran dikonfirmasi pada periode yang sama
        verbose=False,
        detector_kwargs={
            "drop_threshold": args.drop_threshold,
            "persist_threshold": args.persist_threshold,
            "min_pixels": max(4, math.ceil(args.min_ha / env.ha_per_px)),
            "memory_days": 2,  # dalam periode
            "fire_growth_days": 1,
            "max_wait_days": 2,
        },
        validator_kwargs={
            "fire_from_lst": False,
            "fire_lookback": 2,  # sejak pengamatan acuan: bila periode lalu berawan, acuan mundur 2 periode
            "fire_buffer_px": math.ceil(375 / args.pixel),  # toleransi lokasi titik api VIIRS 375 m
        },
        hotspot_kwargs={"start_day": 1},  # semua periode; riwayat mencegah laporan ganda antar-putaran
        fire_only=True,  # hanya kebakaran yang diperingatkan
        incident_kwargs={"merge_px": max(1, math.ceil(args.merge_m / args.pixel))},
    )


# --------------------------------------------------------------- riwayat
def alert_key(entry: dict) -> str:
    """Kunci untuk mengenali peringatan yang sama antar-putaran: jenis, waktu, dan titik jangkar."""
    lat = entry.get("anchor_lat") if entry.get("anchor_lat") is not None else entry["lat"]
    lon = entry.get("anchor_lon") if entry.get("anchor_lon") is not None else entry["lon"]
    when = entry["evidence"].get("first_date") if entry["kind"] == "hotspot" else entry["scene_period"]
    return f"{entry['kind']}|{when}|{lat:.3f}|{lon:.3f}"


def load_history(path: Path) -> list[dict]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def save_history(path: Path, history: list[dict]) -> None:
    path.write_text(json.dumps(history, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def history_geojson(history: list[dict]) -> dict:
    """Riwayat peringatan sebagai titik GeoJSON (bisa dibuka di QGIS / Google Earth)."""
    features = []
    for h in history:
        props = {k: v for k, v in h.items() if k not in ("evidence", "updates")}
        props.update({k: v for k, v in h.get("evidence", {}).items()
                      if k in ("first_date", "last_date", "detections", "members")})
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [h["lon"], h["lat"]]},
                         "properties": props})
    return {"type": "FeatureCollection", "features": features}


KIND_LABEL = {"hotspot": "titik api", "fire": "bekas terbakar", "logging": "tebang liar", "uncertain": "perlu tinjauan"}


# ------------------------------------------------------------- satu kecamatan
def run_kecamatan(args, region, env=None) -> dict:
    env = env or make_env(args, region)
    print(f"\n=== Kecamatan {region.name} ({region.area_km2:,.0f} km2) ===")
    print(f"Periode dipantau: {env.label_of(1)} ... {env.label_of(env.n_periods)} "
          f"(grid {env.shape[1]}x{env.shape[0]} piksel @ {env.pixel_m:g} m); "
          f"titik api sampai {env.now.isoformat()}")

    def progress(msg):
        if not args.quiet:
            print(f"  mengunduh {msg}", flush=True)

    results = env.prefetch(progress, hotspots_from=3)
    if not any(ok for _, ok in results):
        print(f"GAGAL mengambil data: {env.errors[-1] if env.errors else 'tidak diketahui'}")
        return {"region": region.name, "ok": False}


    model = build_model(args, env)
    print(f"\n{'periode':26s}{'lahan bebas awan':>23s}{'titik api':>16s}")
    for day in range(1, env.n_periods + 1):
        model.step()
        cov = env.coverage(day)
        if not cov["ok"]:
            print(f"{env.label_of(day):26s}  data gagal diunduh")
            continue
        fire = f"{cov['fire_px'] * env.ha_per_px:,.0f} ha" if cov["fire_data"] else "tak ada data"
        role = "  (acuan)" if day <= 2 else ""
        print(f"{env.label_of(day):26s}{cov['clear_ha']:>20,.0f} ha{fire:>16s}{role}")

    out_dir = args.out / region.slug
    out_dir.mkdir(parents=True, exist_ok=True)
    hist_path = out_dir / "riwayat_peringatan.json"
    history = load_history(hist_path)
    known = {alert_key(h) for h in history}
    run_date = dt.date.today().isoformat()

    new_alerts = []
    for a in model.alerts:
        entry = a.to_dict()
        entry.update(kecamatan=region.name, scene_period=env.label_of(a.scene_day),
                     alert_period=env.label_of(a.alert_day), run_date=run_date)
        if alert_key(entry) not in known:
            new_alerts.append(entry)
            known.add(alert_key(entry))
    history.extend(new_alerts)
    save_history(hist_path, history)
    (out_dir / "peringatan.geojson").write_text(json.dumps(history_geojson(history), ensure_ascii=False,
                                                           default=str), encoding="utf-8")

    cases = list(model.cases.values())
    pending = [c for c in cases if c.status == PENDING]
    n = lambda s: sum(c.status == s for c in cases)  # noqa: E731
    incidents = model.incident_agent.incidents if model.incident_agent else []
    no_fire = sum(c.cause == "bukan kebakaran" for c in cases)
    print(f"\nAgen Deteksi: {len(cases)} wilayah NDVI turun -> bekas terbakar {n(CONFIRMED)}, "
          f"ditolak {n(DISMISSED)} (termasuk {no_fire} tanpa bukti api), "
          f"perlu tinjauan {n(UNCERTAIN)}, menunggu {len(pending)}")
    print(f"Agen Pengelompokan: {n(CONFIRMED)} bagian bekas terbakar -> {len(incidents)} kejadian kebakaran")
    if model.hotspot_agent:
        print(f"Agen Titik Api: {len(model.hotspot_agent.clusters)} klaster titik api")

    hotspots = [e for e in new_alerts if e["kind"] == "hotspot"]
    events = [e for e in new_alerts if e["kind"] != "hotspot"]
    print(f"\nPERINGATAN DINI TITIK API (baru): {len(hotspots)}" + ("" if hotspots else " (tidak ada)"))
    for e in sorted(hotspots, key=lambda e: e["evidence"]["first_date"]):
        ev = e["evidence"]
        print(f"  {e['priority']:7s} ({e['lat']:.4f}, {e['lon']:.4f}) {ev['first_date']} s.d. {ev['last_date']}, "
              f"{ev['detections']:4d} deteksi, ~{e['area_ha']:,.0f} ha -> {e['channel']}")
    print(f"\nBEKAS TERBAKAR TERKONFIRMASI (baru): {len(events)}" + ("" if events else " (tidak ada)"))
    for e in sorted(events, key=lambda e: -e["area_ha"]):
        ev = e["evidence"]
        extra = f"{ev.get('members', 1)} bagian" + (f", {len(ev['hotspots'])} klaster titik api"
                                                     if ev.get("hotspots") else "")
        label = KIND_LABEL.get(e["kind"], e["kind"])
        print(f"  {e['priority']:7s} {label:14s} ({e['lat']:.4f}, {e['lon']:.4f}) "
              f"{e['area_ha']:7.1f} ha  periode {e['scene_period']} ({extra}) -> {e['channel']}")
    if pending:
        biggest = sorted(pending, key=lambda c: -c.area_px)[:5]
        print(f"\nWilayah curiga yang diperiksa ulang pada putaran berikutnya: {len(pending)}"
              + (f" (5 terluas)" if len(pending) > 5 else ""))
        for c in biggest:
            lat, lon = c.centroid
            print(f"  ({lat:.4f}, {lon:.4f}) {c.area_px * env.ha_per_px:7.1f} ha  periode {env.label_of(c.day)}")
    if env.errors:
        print(f"Permintaan gagal ({len(env.errors)}), contoh: {env.errors[0]}")

    report = {
        "kecamatan": region.name, "run_date": run_date, "titik_api_sampai": env.now.isoformat(),
        "periode": [env.label_of(d) for d in range(1, env.n_periods + 1)],
        "peringatan_baru": new_alerts,
        "menunggu": [{"periode": env.label_of(c.day), "lat": c.centroid[0], "lon": c.centroid[1],
                      "area_ha": round(c.area_px * env.ha_per_px, 2), "bukti": c.evidence} for c in pending],
    }
    stamp = env.period_of(env.n_periods)[0].isoformat()
    (out_dir / f"laporan_{stamp}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str),
                                                  encoding="utf-8")
    plot(model, env, out_dir / f"peta_{stamp}.png")
    print(f"Hasil: {out_dir} (laporan_{stamp}.json, peta_{stamp}.png, riwayat_peringatan.json, peringatan.geojson)")
    return {"region": region.name, "ok": True, "new": len(new_alerts), "pending": len(pending),
            "hotspots": len(hotspots), "events": len(events),
            # untuk tampilan web: model & lingkungan lengkap beserta peringatan baru dan riwayat
            "model": model, "env": env, "new_alerts": new_alerts, "history": history,
            "out_dir": out_dir, "stamp": stamp}


def plot(model, env, path: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    last = max(model.archive) if model.archive else None
    if last is None:
        return
    ref = model.detectors[0].reference_composite(last)
    fig, axes = plt.subplots(1, 2, figsize=(15, 7 * env.shape[0] / max(env.shape[1], 1) + 1.2))
    for ax, img, title in ((axes[0], ref, "NDVI acuan (pengamatan bersih sebelumnya)"),
                           (axes[1], model.archive[last].ndvi, f"NDVI {env.label_of(last)}")):
        ax.set_facecolor("#dddddd")
        if img is not None:
            ax.imshow(img, cmap="YlGn", vmin=0, vmax=1, interpolation="nearest")
        ax.contour(env.region_mask.astype(float), levels=[0.5], colors="black", linewidths=0.6)
        ax.set_title(title, fontsize=9)
        ax.set_xticks([]), ax.set_yticks([])

    k = env.hs_block
    if model.hotspot_agent:
        for cl in model.hotspot_agent.clusters:
            rr, cc = zip(*cl["cells"])
            for a in axes:
                a.scatter([(c + 0.5) * k for c in cc], [(r + 0.5) * k for r in rr], marker="^", s=18,
                          color="red", linewidths=0)
    for inc in (model.incident_agent.incidents if model.incident_agent else []):
        if inc.kind != "fire":
            continue
        axes[1].contour(inc.mask.astype(float), levels=[0.5], colors="darkred", linewidths=1.0)
    for c in model.cases.values():
        if c.status == PENDING:
            rr, cc = np.nonzero(c.mask)
            axes[1].scatter(cc.mean(), rr.mean(), marker="o", s=60, facecolors="none", edgecolors="orange",
                            linewidths=1.2)
    fig.suptitle(f"Kecamatan {env.region.name}. Segitiga merah = titik api VIIRS; garis merah tua = bekas "
                 "terbakar terkonfirmasi; lingkaran oranye = menunggu periode berikutnya; abu-abu = awan",
                 fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------ perintah
def run_list(args) -> int:
    regions = load_regions(args.wilayah)
    print(f"Kecamatan dalam {args.wilayah.name}:")
    for r in regions:
        print(f"  {r.name:20s} {r.area_km2:8,.0f} km2")
    print('\nContoh: python run_pantau.py --kecamatan "' + regions[0].name + '"')
    return 0


def run_status(args) -> int:
    regions = load_regions(args.wilayah)
    region = find_region(regions, args.kecamatan) if args.kecamatan and args.kecamatan.lower() != "semua" else regions[0]
    env = make_env(args, region)
    print(f"Tanggal citra terbaru di GEE (60 hari terakhir, area {region.name}):")
    try:
        status = env.status()
    except Exception as exc:  # noqa: BLE001
        print(f"GAGAL: {type(exc).__name__}: {exc}")
        return 1
    today = dt.date.today()
    labels = {S2: "Sentinel-2 (NDVI)", CLOUD_SCORE: "Cloud Score+ (masker awan)"}
    for cid, latest in status.items():
        label = labels[cid] if cid in labels else f"Titik api VIIRS {cid.split('/')[-2]}"
        if latest and not latest.startswith("GAGAL"):
            age = (today - dt.date.fromisoformat(latest)).days
            warn = "" if age <= 10 else "  <- tidak diperbarui lebih dari 10 hari"
            print(f"  {label:32s} {latest} ({age} hari lalu){warn}")
        else:
            print(f"  {label:32s} {latest or 'tidak ada data 60 hari terakhir'}")
    print(f"\nPeriode terakhir yang akan dipantau: {env.label_of(env.n_periods)}")
    return 0


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.list:
        return run_list(args)
    if args.status:
        return run_status(args)
    if not args.kecamatan:
        print('Pilih kecamatan dengan --kecamatan "NAMA" (lihat --list), atau --kecamatan semua.')
        return 1
    regions = load_regions(args.wilayah)
    if args.kecamatan.lower() == "semua":
        targets = regions
    else:
        try:
            targets = [find_region(regions, args.kecamatan)]
        except ValueError as exc:
            print(f"GAGAL: {exc}")
            return 1
    results = [run_kecamatan(args, r) for r in targets]
    if len(results) > 1:
        print("\n=== Ringkasan kabupaten ===")
        for r in results:
            print(f"  {r['region']:20s} " + (f"peringatan baru {r['new']}, menunggu {r['pending']}" if r["ok"]
                                             else "gagal mengambil data"))
    return 0 if any(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
