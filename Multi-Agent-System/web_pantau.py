"""Aplikasi web lokal pemantauan karhutla Kabupaten Kubu Raya.

Jalankan:   python web_pantau.py            (lalu buka http://127.0.0.1:8765 bila tidak terbuka otomatis)

Server kecil (pustaka standar Python) yang:
  * menampilkan peta dan daftar kecamatan Kubu Raya,
  * menjalankan pemantauan (run_pantau) untuk kecamatan yang dipilih di latar belakang,
    memakai login Google Earth Engine di komputer ini dan Project ID di bawah,
  * menyajikan keluaran tiap agen (Pengunduh, Titik Api, Deteksi, Validasi, Pengelompokan, Notifikasi)
    dan lalu lintas pesan antaragen sebagai JSON untuk halaman web/index.html.

Server hanya mendengarkan 127.0.0.1 (tidak bisa dibuka dari komputer lain).
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import io
import json
import mimetypes
import os
import re
import threading
import time
import traceback
import uuid
import webbrowser
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np

import run_pantau
from deforestation_mas.agents import CONFIRMED, PENDING
from deforestation_mas.region import find_region, load_regions

PROJECT_ID = os.environ.get("EE_PROJECT", "disco-genius-472910-g7")
HERE = Path(__file__).resolve().parent
WEB_DIR = HERE / "web"
RESULT_FILE = "web_hasil.json"

AGENT_ORDER = ("ingestion", "hotspot", "detection", "validation", "incident", "notification")


# ------------------------------------------------------------------ utilitas
def to_py(o):
    """Ubah tipe numpy menjadi tipe Python biasa agar bisa dijadikan JSON."""
    if isinstance(o, dict):
        return {str(k): to_py(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_py(v) for v in o]
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, float) and not np.isfinite(o):
        return None
    if isinstance(o, (dt.date, Path)):
        return str(o)
    return o


def light_geojson(regions) -> dict:
    """Batas kecamatan dengan koordinat dibulatkan (~11 m) dan titik berulang dibuang, agar ringan di peramban."""
    features = []
    for r in regions:
        polys = []
        for poly in r.polygons:
            rings = []
            for ring in poly:
                pts = []
                for x, y in ring:
                    p = [round(x, 4), round(y, 4)]
                    if not pts or p != pts[-1]:
                        pts.append(p)
                if len(pts) >= 4:
                    rings.append(pts)
            if rings:
                polys.append(rings)
        features.append({
            "type": "Feature",
            "properties": {"name": r.name, "slug": r.slug, "area_km2": round(r.area_km2, 1)},
            "geometry": {"type": "MultiPolygon", "coordinates": polys},
        })
    return {"type": "FeatureCollection", "features": features}


def mask_outline(mask: np.ndarray, env, max_points: int = 400) -> list:
    """Garis tepi suatu mask sebagai daftar cincin [[lat, lon], ...] untuk peta."""
    import contourpy

    rows, cols = np.nonzero(mask)
    if rows.size == 0:
        return []
    r0, c0 = max(rows.min() - 1, 0), max(cols.min() - 1, 0)
    crop = np.zeros((rows.max() - r0 + 3, cols.max() - c0 + 3))
    crop[rows - r0 + 1, cols - c0 + 1] = 1.0
    rings = []
    for line in contourpy.contour_generator(z=crop).lines(0.5):
        step = max(1, len(line) // max_points)
        pts = line[::step]
        rings.append([list(env.to_latlon(y + r0 - 1, x + c0 - 1)) for x, y in pts])
    return rings


# ------------------------------------------------------------- tampilan per agen
def agent_views(result: dict, region) -> dict:
    """Ringkas keluaran setiap agen dari satu putaran run_pantau menjadi data untuk halaman web."""
    model, env = result["model"], result["env"]
    new_ids = {a["alert_id"] for a in result["new_alerts"]}
    names = {a.name: a.role for a in model.agents}

    periods = []
    for d in range(1, env.n_periods + 1):
        cov = env.coverage(d)
        periods.append({
            "periode": env.label_of(d), "peran": "acuan" if d <= 2 else "dipantau",
            "terunduh": d in model.archive,
            "lahan_bebas_awan_ha": round(cov["clear_ha"]) if cov["ok"] else None,
            "titik_api_ha": round(cov["fire_px"] * env.ha_per_px) if cov["ok"] and cov["fire_data"] else None,
        })

    clusters = []
    for cl in (model.hotspot_agent.clusters if model.hotspot_agent else []):
        alert = model.notifier.by_case.get(cl["cluster_id"])
        clusters.append({
            "id": cl["cluster_id"], "periode": env.label_of(cl["day"]), "awal": cl["first_date"],
            "akhir": cl["last_date"], "deteksi": cl["detections"], "luas_ha": round(cl["area_ha"]),
            "frp_maks": cl["frp_max"], "lat": cl["lat"], "lon": cl["lon"],
            "prioritas": alert.priority if alert else None,
            "baru": bool(alert and alert.alert_id in new_ids),
            "sel": [list(env.hs_to_latlon(r, c)) for r, c in cl["cells"]],
        })

    cases = []
    for c in sorted(model.cases.values(), key=lambda c: (c.day, c.case_id)):
        persist = [v["ndvi_drop"] for k, v in c.evidence.items() if k.startswith("persist_r")]
        cases.append({
            "id": c.case_id, "periode": env.label_of(c.day), "status": c.status, "penyebab": c.cause,
            "lat": c.centroid[0], "lon": c.centroid[1], "luas_ha": round(c.area_px * env.ha_per_px, 1),
            "ndvi_turun": c.drop, "cek_menetap": persist, "catatan": c.evidence.get("catatan"),
            "jalur_cepat": "jalur_cepat" in c.evidence,
        })

    verdicts = [
        {"kasus": m.content["case_id"], "periode": env.label_of(m.content["day"]), "ronde": m.content["round"],
         "vonis": m.content["cause"], "nyata": m.content["real"], "kuat": m.content.get("strong"),
         "keyakinan": m.content["confidence"], "porsi_api": m.content.get("fire_fraction")}
        for m in model.bus.log if m.topic == "verdict"
    ]

    incidents = []
    for inc in (model.incident_agent.incidents if model.incident_agent else []):
        alert = model.notifier.by_case.get(inc.incident_id)
        rr, cc = np.nonzero(inc.mask)
        lat, lon = env.to_latlon(rr.mean(), cc.mean())
        incidents.append({
            "id": inc.incident_id, "jenis": inc.kind, "periode": env.label_of(inc.scene_day),
            "luas_ha": round(inc.mask.sum() * env.ha_per_px, 1), "bagian": len(inc.members),
            "klaster_titik_api": list(inc.hotspots), "lat": lat, "lon": lon,
            "prioritas": alert.priority if alert else None, "baru": bool(alert and alert.alert_id in new_ids),
            "tepi": mask_outline(inc.mask, env),
        })

    alerts = []
    for a in model.alerts:
        ev = a.evidence or {}
        alerts.append({
            "id": a.alert_id, "jenis": a.kind, "prioritas": a.priority, "kanal": a.channel,
            "lat": a.lat, "lon": a.lon, "luas_ha": round(a.area_ha, 1), "periode": env.label_of(a.scene_day),
            "awal": ev.get("first_date"), "akhir": ev.get("last_date"), "baru": a.alert_id in new_ids,
        })

    traffic = Counter(
        (names.get(m.sender, m.sender), names.get(m.receiver, m.receiver), m.performative, m.topic)
        for m in model.bus.log
    )
    messages = [{"dari": f, "ke": t, "performative": p, "topik": tp, "jumlah": n}
                for (f, t, p, tp), n in sorted(traffic.items(), key=lambda kv: -kv[1])]

    val = model.validators[0] if model.validators else None
    n = Counter(c.status for c in model.cases.values())
    return to_py({
        "kecamatan": region.name, "slug": region.slug, "dijalankan": dt.datetime.now().isoformat(timespec="seconds"),
        "titik_api_sampai": env.now, "periode": [p["periode"] for p in periods],
        "ringkasan": {
            "titik_api_baru": result["hotspots"], "bekas_terbakar_baru": result["events"],
            "klaster_titik_api": len(clusters), "kejadian": len(incidents), "kasus": len(cases),
            "terkonfirmasi": n.get(CONFIRMED, 0), "ditolak": n.get("dismissed", 0),
            "menunggu": n.get(PENDING, 0), "riwayat": len(result["history"]), "pesan": len(model.bus.log),
        },
        "agen": {
            "ingestion": {"periode": periods, "gagal": env.errors},
            "hotspot": {"klaster": clusters, "ukuran_sel_deg": env.cell_deg * env.hs_block},
            "detection": {"kasus": cases},
            "validation": {"vonis": verdicts, "sepakat": val.agreements if val else 0,
                           "batal": val.cancellations if val else 0},
            "incident": {"kejadian": incidents},
            "notification": {"peringatan": alerts, "riwayat": len(result["history"])},
        },
        "pesan": messages,
        "peta_png": f"/output/{region.slug}/peta_{result['stamp']}.png",
    })


# ------------------------------------------------------------------ pekerjaan
class JobWriter(io.TextIOBase):
    """Menangkap keluaran konsol run_pantau baris demi baris untuk ditampilkan di halaman."""

    def __init__(self, job):
        self.job, self.buf = job, ""

    def write(self, s):
        self.buf += s
        while "\n" in self.buf:
            line, self.buf = self.buf.split("\n", 1)
            if line.strip():
                self.job["log"].append(line.rstrip())
        return len(s)


class App:
    def __init__(self, regions_path=run_pantau.DEFAULT_REGIONS, out_dir=None, cache_dir=None,
                 project=PROJECT_ID, env_factory=None):
        self.regions = load_regions(regions_path)
        self.regions_path = Path(regions_path)
        self.out_dir = Path(out_dir or HERE / "output_pantau")
        self.cache_dir = str(cache_dir or HERE / "pantau_cache")
        self.project = project
        self.env_factory = env_factory  # untuk uji: (args, region) -> lingkungan tiruan
        self.geojson = json.dumps(light_geojson(self.regions)).encode()
        self.jobs: dict[str, dict] = {}
        self.lock = threading.Lock()
        self.running: str | None = None

    def args_for(self, end_date=None):
        argv = ["--project", self.project, "--wilayah", str(self.regions_path), "--out", str(self.out_dir),
                "--cache-dir", self.cache_dir]
        if end_date:
            argv += ["--end-date", end_date]
        return run_pantau.parse_args(argv)

    def result_path(self, slug: str) -> Path:
        return self.out_dir / slug / RESULT_FILE

    def kecamatan_list(self) -> dict:
        items = []
        for r in self.regions:
            path = self.result_path(r.slug)
            last = json.loads(path.read_text(encoding="utf-8"))["dijalankan"] if path.exists() else None
            items.append({"name": r.name, "slug": r.slug, "area_km2": round(r.area_km2, 1), "terakhir": last})
        return {"project": self.project, "kecamatan": items}

    def start(self, kecamatan: str, end_date: str | None = None) -> dict:
        region = find_region(self.regions, kecamatan)  # ValueError bila tidak dikenal
        if end_date:
            dt.date.fromisoformat(end_date)  # ValueError bila format salah
        with self.lock:
            if self.running and self.jobs[self.running]["status"] == "berjalan":
                raise RuntimeError(self.running)
            job_id = uuid.uuid4().hex[:10]
            job = {"id": job_id, "kecamatan": region.name, "slug": region.slug, "status": "berjalan",
                   "log": [], "error": None, "mulai": time.time()}
            self.jobs[job_id] = job
            self.running = job_id
        threading.Thread(target=self._run, args=(job, region, end_date), daemon=True).start()
        return job

    def _run(self, job, region, end_date):
        try:
            args = self.args_for(end_date)
            env = self.env_factory(args, region) if self.env_factory else None
            with contextlib.redirect_stdout(JobWriter(job)):
                result = run_pantau.run_kecamatan(args, region, env)
            if not result["ok"]:
                raise RuntimeError(job["log"][-1] if job["log"] else "data tidak bisa diambil dari GEE")
            views = agent_views(result, region)
            path = self.result_path(region.slug)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(views, ensure_ascii=False), encoding="utf-8")
            job["status"] = "selesai"
        except Exception as exc:  # noqa: BLE001 - dilaporkan ke halaman
            job["error"] = f"{type(exc).__name__}: {exc}"
            job["log"].append(traceback.format_exc().strip().splitlines()[-1])
            job["status"] = "gagal"
        job["selesai"] = time.time()

    def data_status(self) -> dict:
        region = self.regions[0]
        env = run_pantau.make_env(self.args_for(), region)
        return {"project": self.project, "sumber": env.status(), "periode_terakhir": env.label_of(env.n_periods)}


# ---------------------------------------------------------------------- HTTP
def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # tenang di konsol
            pass

        def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code, obj):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode())

        def do_GET(self):  # noqa: N802
            url = urlparse(self.path)
            path = url.path
            if path in ("/", "/index.html"):
                return self._send(200, (WEB_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
            if path == "/api/kecamatan":
                return self._json(200, app.kecamatan_list())
            if path == "/api/wilayah.geojson":
                return self._send(200, app.geojson, "application/geo+json")
            if path.startswith("/api/job/"):
                job = app.jobs.get(path.rsplit("/", 1)[-1])
                if not job:
                    return self._json(404, {"error": "pekerjaan tidak ditemukan"})
                since = int(parse_qs(url.query).get("sejak", ["0"])[0])
                return self._json(200, {k: job[k] for k in ("id", "kecamatan", "slug", "status", "error")}
                                  | {"log": job["log"][since:], "jumlah_log": len(job["log"])})
            if path.startswith("/api/hasil/"):
                slug = re.sub(r"[^a-z0-9_]", "", path.rsplit("/", 1)[-1])
                p = app.result_path(slug)
                if not p.exists():
                    return self._json(404, {"error": "kecamatan ini belum pernah dipantau"})
                return self._send(200, p.read_bytes())
            if path == "/api/status":
                try:
                    return self._json(200, app.data_status())
                except Exception as exc:  # noqa: BLE001
                    return self._json(502, {"error": f"{type(exc).__name__}: {exc}"})
            if path.startswith("/output/"):
                target = (app.out_dir / path[len("/output/"):]).resolve()
                if app.out_dir.resolve() not in target.parents or not target.is_file():
                    return self._json(404, {"error": "berkas tidak ditemukan"})
                ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
                return self._send(200, target.read_bytes(), ctype)
            return self._json(404, {"error": "alamat tidak dikenal"})

        def do_POST(self):  # noqa: N802
            if urlparse(self.path).path != "/api/pantau":
                return self._json(404, {"error": "alamat tidak dikenal"})
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                job = app.start(body.get("kecamatan", ""), body.get("end_date") or None)
            except RuntimeError as exc:
                return self._json(409, {"error": "pemantauan lain masih berjalan", "job": str(exc)})
            except (ValueError, json.JSONDecodeError) as exc:
                return self._json(400, {"error": str(exc)})
            return self._json(202, {"job": job["id"], "kecamatan": job["kecamatan"]})

    return Handler


def serve(app: App, host="127.0.0.1", port=8765) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), make_handler(app))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--project", default=PROJECT_ID)
    p.add_argument("--no-browser", action="store_true", help="jangan membuka peramban otomatis")
    args = p.parse_args(argv)
    app = App(project=args.project)
    try:
        server = serve(app, port=args.port)
    except OSError:
        print(f"Port {args.port} sedang dipakai. Tutup jendela web_pantau lain, atau jalankan dengan --port 8766.")
        return 1
    url = f"http://127.0.0.1:{args.port}"
    print(f"Pemantauan karhutla Kubu Raya berjalan di {url}  (Project GEE: {app.project})")
    print("Biarkan jendela ini terbuka selama memakai halaman web. Tekan Ctrl+C untuk berhenti.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.shutdown()
        print("Berhenti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
