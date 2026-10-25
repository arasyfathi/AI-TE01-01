"""Jalankan sistem multi-agen pada data NYATA Google Earth Engine (replay periode lampau).

Langkah yang disarankan:

  1) Uji koneksi dan satu hari data (cepat, hanya 1 permintaan ke GEE):
         python run_gee.py --project PROJECT-ID --check

  2) Putar ulang periode (hasil unduhan di-cache di gee_cache/, jadi pengulangan tidak memakai kuota):
         python run_gee.py --project PROJECT-ID --days 60

  3) Ganti wilayah/periode, atau kalibrasi ambang:
         python run_gee.py --project PROJECT-ID --lat -2.35 --lon 114.0 --start 2023-08-15 --days 90
         python run_gee.py --project PROJECT-ID --drop-threshold 0.15 --persist-threshold 0.10

``--project`` boleh dikosongkan bila variabel lingkungan EE_PROJECT sudah diatur.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

from deforestation_mas import ForestMonitoringModel
from deforestation_mas.agents import CONFIRMED, DISMISSED, UNCERTAIN
from deforestation_mas.gee_environment import GEEEnvironment

HERE = Path(__file__).resolve().parent


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--project", default=os.environ.get("EE_PROJECT"), help="Project ID Google Cloud untuk GEE")
    p.add_argument("--lat", type=float, default=-2.35, help="lintang pusat area (default: dekat Palangka Raya)")
    p.add_argument("--lon", type=float, default=114.00, help="bujur pusat area")
    p.add_argument("--size", type=int, default=40, help="jumlah piksel per sisi (40 x 250 m = 10 km)")
    p.add_argument("--pixel", type=float, default=250.0, help="ukuran piksel (meter)")
    p.add_argument("--start", default="2023-08-15", help="tanggal awal replay (YYYY-MM-DD)")
    p.add_argument("--days", type=int, default=60, help="lama replay (hari)")
    p.add_argument("--latency", type=int, default=0, help="jeda ketersediaan data (hari)")
    p.add_argument("--check", nargs="?", const="", metavar="TANGGAL", help="uji satu hari lalu keluar")
    p.add_argument("--scan", type=int, metavar="N", help="periksa N hari pertama (mengisi cache) lalu keluar")
    p.add_argument("--find-fires", action="store_true",
                   help="cari area dengan titik api MODIS terbanyak selama --start/--days di dalam --bbox, lalu keluar")
    p.add_argument("--bbox", default="110.7,-3.6,115.9,0.8",
                   help="kotak pencarian: bujur_min,lintang_min,bujur_maks,lintang_maks (default: Kalimantan Tengah)")
    p.add_argument("--keep-haze", action="store_true",
                   help="jangan buang piksel beraerosol/asap tinggi dan bercirrus tinggi dari NDVI")
    p.add_argument("--detectors", type=int, default=1)
    p.add_argument("--validators", type=int, default=1)
    p.add_argument("--drop-threshold", type=float, default=0.20, help="penurunan NDVI yang dianggap drastis")
    p.add_argument("--persist-threshold", type=float, default=0.15, help="penurunan NDVI minimal agar dianggap menetap")
    p.add_argument("--min-pixels", type=int, default=4, help="luas minimal wilayah curiga (piksel)")
    p.add_argument("--cache-dir", default=str(HERE / "gee_cache"))
    p.add_argument("--out", type=Path, default=HERE / "output_gee")
    p.add_argument("--quiet", action="store_true")
    return p.parse_args(argv)


def make_env(args) -> GEEEnvironment:
    return GEEEnvironment(
        project=args.project, center=(args.lat, args.lon), start=args.start, n_days=args.days,
        size=args.size, pixel_m=args.pixel, latency_days=args.latency, cache_dir=args.cache_dir,
        mask_haze=not args.keep_haze,
    )


def build_model(args, env) -> ForestMonitoringModel:
    return ForestMonitoringModel(
        env=env, n_detectors=args.detectors, n_validators=args.validators, verbose=not args.quiet,
        detector_kwargs={
            "drop_threshold": args.drop_threshold,
            "persist_threshold": args.persist_threshold,
            "min_pixels": args.min_pixels,
        },
        # Pada data nyata tanah gundul pun lebih panas, jadi kebakaran hanya dibuktikan oleh titik api MODIS.
        validator_kwargs={"fire_from_lst": False},
    )


def run_check(args) -> int:
    env = make_env(args)
    date = args.check or env.date_of(1)
    print(f"Menguji koneksi GEE untuk {date} di ({args.lat}, {args.lon}), {args.size}x{args.size} piksel @ {args.pixel:g} m ...")
    try:
        stats, data = env.check(date)
    except Exception as exc:  # noqa: BLE001
        print(f"\nGAGAL: {type(exc).__name__}: {exc}")
        print("Periksa: login (earthengine authenticate), --project, dan apakah koleksi MODIS memiliki data pada tanggal itu.")
        return 1
    labels = {"ndvi": "NDVI 250 m (bebas awan)", "lst": "Suhu permukaan siang (C)", "fire": "Titik api (1=api, 0=tidak)"}
    print(f"\n{'band':30s}{'piksel valid':>14s}{'min':>9s}{'maks':>9s}{'rata2':>9s}")
    for k, s in stats.items():
        fmt = lambda v: "-" if v is None else f"{v:.2f}"  # noqa: E731
        print(f"{labels[k]:30s}{s['valid_pct']:>13.1f}%{fmt(s['min']):>9s}{fmt(s['max']):>9s}{fmt(s['mean']):>9s}")
    n_fire = int(np.nansum(data["fire"] > 0.5))
    print(f"\nPiksel (250 m) bertanda titik api hari itu: {n_fire}")
    print_diagnosis(env, date, args)
    print("\nWajar bila: NDVI hutan tropis sekitar 0.6-0.9, suhu siang sekitar 25-40 C. Jika tidak, kabari saya.")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    args.out.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    for ax, (k, cmap, lim) in zip(axes, [("ndvi", "YlGn", (0, 1)), ("lst", "inferno", None), ("fire", "Reds", (0, 1))]):
        im = ax.imshow(data[k], cmap=cmap, vmin=lim[0] if lim else None, vmax=lim[1] if lim else None)
        ax.set_title(labels[k], fontsize=10)
        ax.set_xticks([]), ax.set_yticks([])
        fig.colorbar(im, ax=ax, fraction=0.046)
    fig.suptitle(f"Uji GEE {date} (abu-abu/putih = tidak ada data)")
    fig.tight_layout()
    path = args.out / "check.png"
    fig.savefig(path, dpi=110)
    print(f"Pratinjau disimpan: {path}")
    return 0


LST_QC = {0: "baik", 1: "kualitas lain", 2: "tidak ada (awan)", 3: "tidak ada (lainnya)"}
FIRE_CLASS = {0: "data hilang", 1: "tidak diproses", 2: "tidak diproses", 3: "air", 4: "awan",
              5: "tanah tanpa api", 6: "tidak diketahui", 7: "api (rendah)", 8: "api (sedang)", 9: "api (tinggi)"}


def print_diagnosis(env, date, args):
    """Rincian kenapa piksel terbuang, agar bisa dibedakan antara 'memang berawan' dan 'masker terlalu ketat'."""
    try:
        rep = env.diagnose(date)
    except Exception as exc:  # noqa: BLE001
        print(f"\n(Rincian masker tidak tersedia: {type(exc).__name__}: {exc})")
        return
    flag_labels = {
        "awan": "awan / campuran awan",
        "bayangan_awan": "bayangan awan",
        "awan_internal": "awan (algoritma internal)",
        "aerosol_tinggi": "aerosol/asap tinggi",
        "cirrus_tinggi": "cirrus tinggi",
    }
    print(f"\nRincian masker NDVI (band state_1km MOD09GA, data state tersedia "
          f"{rep['awan']['tersedia_pct']:.0f}% piksel):")
    print(f"  {'ada data reflektansi 250 m':30s}: {rep['ada_reflektansi']['ya_pct']}%")
    for key, label in flag_labels.items():
        haze = key in ("aerosol_tinggi", "cirrus_tinggi")
        note = ""
        if haze:
            note = "  <- tidak dibuang (--keep-haze)" if args.keep_haze else "  <- dibuang; --keep-haze untuk mempertahankan"
        print(f"  {label:30s}: {rep[key]['ya_pct']}%{note}")

    def classes(entry, labels):
        if not entry.get("kelas_pct"):
            return "tidak ada data"
        return ", ".join(f"{labels.get(k, k)} {v}%" for k, v in entry["kelas_pct"].items())

    print(f"Kualitas suhu (QC_Day)        : {classes(rep['lst_qc'], LST_QC)}")
    print(f"Kelas titik api (FireMask)    : {classes(rep['firemask'], FIRE_CLASS)}")

    haze_pct = max(rep["aerosol_tinggi"]["ya_pct"] or 0, rep["cirrus_tinggi"]["ya_pct"] or 0)
    cloud_pct = rep["awan"]["ya_pct"] or 0
    if (rep["ada_reflektansi"]["ya_pct"] or 0) < 50:
        print("Kesimpulan: citra 250 m hari itu tidak menutupi area ini (celah lintasan satelit). Coba tanggal lain.")
    elif not args.keep_haze and haze_pct >= 50 and cloud_pct < 50:
        print("Kesimpulan: yang membuang piksel terutama bendera asap/cirrus, bukan awan. Coba ulangi dengan --keep-haze.")
    elif cloud_pct >= 50:
        print("Kesimpulan: area ini memang tertutup awan hari itu. Coba tanggal lain atau jalankan --scan untuk mencari hari cerah.")


def run_find_fires(args) -> int:
    import datetime as dt

    env = make_env(args)
    try:
        bbox = tuple(float(x) for x in args.bbox.split(","))
        assert len(bbox) == 4 and bbox[0] < bbox[2] and bbox[1] < bbox[3]
    except (ValueError, AssertionError):
        print("GAGAL: --bbox harus berformat bujur_min,lintang_min,bujur_maks,lintang_maks")
        return 1
    print(f"Mencari titik api MODIS (MOD14A1) {env.date_of(1)} s.d. {env.date_of(args.days)} "
          f"di kotak bujur {bbox[0]}..{bbox[2]}, lintang {bbox[1]}..{bbox[3]} ...")
    try:
        spots = env.find_fire_hotspots(bbox)
    except Exception as exc:  # noqa: BLE001
        print(f"\nGAGAL: {type(exc).__name__}: {exc}")
        return 1
    if not spots:
        print("\nTidak ada titik api di kotak dan periode ini. Coba periode lain (--start/--days) atau --bbox lain.")
        return 0
    km = args.size * args.pixel / 1000
    print(f"\nArea {km:g} x {km:g} km dengan titik api terbanyak (hari-piksel = jumlah piksel ~1 km x hari menyala):")
    print(f"{'no':>3s}{'lintang':>10s}{'bujur':>10s}{'hari-piksel':>13s}{'api pertama':>14s}{'api terakhir':>14s}")
    for i, s in enumerate(spots, 1):
        print(f"{i:>3d}{s['lat']:>10.3f}{s['lon']:>10.3f}{s['fire_pixel_days']:>13d}"
              f"{s['first_date'] or '-':>14s}{s['last_date'] or '-':>14s}")
    best = spots[0]
    start = (dt.date.fromisoformat(best["first_date"]) - dt.timedelta(days=10)).isoformat() if best["first_date"] else args.start
    project = f" --project {args.project}" if args.project else ""
    print("\nLangkah berikutnya untuk kandidat #1 (mulai 10 hari sebelum api pertama agar ada citra acuan):")
    print(f"  python run_gee.py{project} --lat {best['lat']} --lon {best['lon']} --start {start} --keep-haze --scan 30")
    print(f"  python run_gee.py{project} --lat {best['lat']} --lon {best['lon']} --start {start} --keep-haze --days 60")
    return 0


def run_scan(args) -> int:
    env = make_env(args)
    n = min(args.scan, args.days)
    print(f"Memeriksa {n} hari mulai {args.start} di ({args.lat}, {args.lon}); hasilnya disimpan ke cache untuk replay.")
    print(f"\n{'tanggal':12s}{'NDVI valid':>12s}{'suhu valid':>12s}{'api teramati':>14s}{'piksel api':>12s}")
    rows = []
    try:
        for date, s, err in env.scan(n):
            if s is None:
                print(f"{date:12s}  {err}")
                continue
            rows.append(s)
            print(f"{date:12s}{s['ndvi_pct']:>11.1f}%{s['lst_pct']:>11.1f}%{s['fire_obs_pct']:>13.1f}%{s['fire_px']:>12d}")
    except Exception as exc:  # noqa: BLE001
        print(f"\nGAGAL: {type(exc).__name__}: {exc}")
        return 1
    if rows:
        clear = sum(r["ndvi_pct"] >= 50 for r in rows)
        print(f"\n{clear} dari {len(rows)} hari punya NDVI bersih >= 50% area; "
              f"{sum(r['fire_px'] > 0 for r in rows)} hari dengan titik api.")
        if clear == 0:
            print("Tidak ada hari cerah. Coba --keep-haze, periode lain (--start), atau lokasi lain (--lat/--lon).")
    return 0


def plot(model, env, path: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    days = sorted(model.archive)
    valid = {d: float(np.isfinite(model.archive[d].ndvi).mean()) for d in days}
    early = max(days[:10], key=valid.get)
    late = max(days[-10:], key=valid.get)
    style = {"fire": ("*", "red"), "logging": ("s", "saddlebrown"), "uncertain": ("o", "royalblue"),
             "unknown": ("x", "black")}

    fig, axes = plt.subplots(1, 3, figsize=(17, 5.3))
    for ax, d, title in ((axes[0], early, "awal"), (axes[1], late, "akhir")):
        ax.imshow(model.archive[d].ndvi, cmap="YlGn", vmin=0, vmax=1)
        ax.set_title(f"NDVI {title} periode ({env.date_of(d)})")
        ax.set_xticks([]), ax.set_yticks([])
    for a in model.alerts:
        r, c = (float(np.mean(x)) for x in model.cases[a.case_id].mask.nonzero())
        mk, col = style.get(a.kind, ("x", "black"))
        axes[1].scatter(c, r, marker=mk, s=90, facecolors="none" if mk != "x" else col, edgecolors=col)
    axes[1].text(0.5, -0.04, "simbol = peringatan (bintang: api, kotak: tebang liar, lingkaran: perlu tinjauan)",
                 transform=axes[1].transAxes, ha="center", va="top", fontsize=8)

    ax = axes[2]
    ax.bar(days, [100 * valid[d] for d in days], color="lightsteelblue")
    for a in model.alerts:
        ax.axvline(a.scene_day, color=style.get(a.kind, ("x", "black"))[1], lw=1.5)
    ax.set_xlabel("hari sejak awal replay"), ax.set_ylabel("% piksel NDVI bebas awan/asap")
    ax.set_title("Cakupan data harian (garis = peringatan)")
    fig.tight_layout()
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.check is not None:
        return run_check(args)
    if args.find_fires:
        return run_find_fires(args)
    if args.scan:
        return run_scan(args)

    env = make_env(args)
    model = build_model(args, env)
    print(f"Replay {args.days} hari dari {args.start} | pusat ({args.lat}, {args.lon}) | "
          f"{args.size}x{args.size} piksel @ {args.pixel:g} m ({env.ha_per_px:.1f} ha/piksel)")
    print("Peringatan yang dikirim Agen Notifikasi (hari ke-N = N hari sejak awal replay):")
    for i in range(args.days):
        model.step()
        if (i + 1) % 10 == 0 and not args.quiet:
            print(f"  ... hari {i + 1}/{args.days}: {len(model.archive)} citra terunduh, {len(model.cases)} kasus")

    cases = list(model.cases.values())
    n = lambda s: sum(c.status == s for c in cases)  # noqa: E731
    cover = [float(np.isfinite(s.ndvi).mean()) for s in model.archive.values()]
    print("\nRingkasan")
    print(f"  citra terunduh        : {len(model.archive)} dari {args.days} hari")
    print(f"  rata-rata data bersih : {100 * np.mean(cover):.0f}% piksel/hari" if cover else "  tidak ada citra terunduh")
    print(f"  kasus dibuka          : {len(cases)} (terkonfirmasi {n(CONFIRMED)}, ditolak {n(DISMISSED)}, "
          f"perlu tinjauan {n(UNCERTAIN)}, menunggu {n('pending')})")
    kinds = [a.kind for a in model.alerts]
    print(f"  peringatan            : {len(kinds)} (api {kinds.count('fire')}, tebang liar {kinds.count('logging')}, "
          f"perlu tinjauan {kinds.count('uncertain')})")
    print(f"  hari MODIS mendeteksi titik api di area: {env.observed_fire_days() or 'tidak ada'}")
    if env.errors:
        print(f"  PERMINTAAN GAGAL ({len(env.errors)}), contoh: {env.errors[0]}")

    args.out.mkdir(parents=True, exist_ok=True)
    alerts = []
    for a in model.alerts:
        d = a.to_dict()
        d["scene_date"], d["alert_date"] = env.date_of(a.scene_day), env.date_of(a.alert_day)
        alerts.append(d)
    (args.out / "alerts.json").write_text(json.dumps(alerts, indent=2, ensure_ascii=False))
    model.datacollector.get_model_vars_dataframe().to_csv(args.out / "timeseries.csv", index=False)
    if model.archive:
        plot(model, env, args.out / "gee_replay.png")
    print(f"\nHasil disimpan di {args.out}: alerts.json, timeseries.csv, gee_replay.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
