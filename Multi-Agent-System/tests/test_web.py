"""Uji server web pemantauan (API, pekerjaan latar, keamanan jalur) dengan lingkungan Sentinel tiruan."""

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import web_pantau  # noqa: E402
from deforestation_mas.sentinel_environment import SentinelEnvironment  # noqa: E402
from test_pantau import END, FakeSentinel, absolute  # noqa: E402


@pytest.fixture()
def server(tmp_path):
    def factory(args, region):
        probe = SentinelEnvironment(region, cache_dir=None, end_date=END)
        h, w = probe.shape
        r, c = h // 2, w // 2
        world = absolute([("fire_late", 1, r - 20, r + 20, c - 30, c + 30), ("cloud", 2, 0, h, 0, w),
                          ("logging", 3, r - 60, r - 40, c + 40, c + 70)], probe)
        time.sleep(0.3)  # beri waktu untuk menguji permintaan ganda
        return FakeSentinel(region, world)

    app = web_pantau.App(out_dir=tmp_path / "out", cache_dir=tmp_path / "cache", env_factory=factory)
    srv = web_pantau.serve(app, port=0)
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    yield app, base
    srv.shutdown()


def get(url):
    with urllib.request.urlopen(url) as r:
        return r.status, r.headers.get("Content-Type"), r.read()


def post(url, obj):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def wait(base, job_id):
    for _ in range(200):
        j = json.loads(get(f"{base}/api/job/{job_id}")[2])
        if j["status"] != "berjalan":
            return j
        time.sleep(0.1)
    raise AssertionError("pekerjaan tidak selesai")


def test_page_and_kecamatan_list(server):
    app, base = server
    code, ctype, body = get(base + "/")
    assert code == 200 and "text/html" in ctype and b"Karhutla Kubu Raya" in body
    data = json.loads(get(base + "/api/kecamatan")[2])
    assert data["project"] == web_pantau.PROJECT_ID == "disco-genius-472910-g7"
    assert len(data["kecamatan"]) == 9 and all(k["terakhir"] is None for k in data["kecamatan"])
    geo = json.loads(get(base + "/api/wilayah.geojson")[2])
    assert len(geo["features"]) == 9 and geo["features"][0]["geometry"]["type"] == "MultiPolygon"


def test_run_job_and_agent_outputs(server):
    app, base = server
    code, body = post(base + "/api/pantau", {"kecamatan": "rasau jaya"})
    assert code == 202 and body["kecamatan"] == "Rasau Jaya"
    busy_code, busy = post(base + "/api/pantau", {"kecamatan": "Kubu"})
    assert busy_code == 409 and busy["job"] == body["job"]  # hanya satu pemantauan sekaligus

    job = wait(base, body["job"])
    assert job["status"] == "selesai" and any("Kecamatan Rasau Jaya" in line for line in job["log"])

    h = json.loads(get(base + "/api/hasil/rasau_jaya")[2])
    assert set(h["agen"]) == set(web_pantau.AGENT_ORDER)
    assert len(h["agen"]["ingestion"]["periode"]) == 4
    assert h["agen"]["hotspot"]["klaster"] and h["agen"]["hotspot"]["klaster"][0]["sel"]
    assert {c["status"] for c in h["agen"]["detection"]["kasus"]} == {"confirmed", "dismissed"}
    assert h["agen"]["validation"]["vonis"] and h["agen"]["validation"]["sepakat"] >= 1
    inc = h["agen"]["incident"]["kejadian"]
    assert len(inc) == 1 and inc[0]["tepi"] and len(inc[0]["tepi"][0][0]) == 2  # cincin [lat, lon]
    assert {a["jenis"] for a in h["agen"]["notification"]["peringatan"]} == {"hotspot", "fire"}
    roles = {m["dari"] for m in h["pesan"]} | {m["ke"] for m in h["pesan"]}
    assert roles <= set(web_pantau.AGENT_ORDER)
    code, ctype, _ = get(base + h["peta_png"])
    assert code == 200 and ctype == "image/png"

    listed = json.loads(get(base + "/api/kecamatan")[2])["kecamatan"]
    assert next(k for k in listed if k["slug"] == "rasau_jaya")["terakhir"]


def test_bad_requests(server):
    app, base = server
    assert post(base + "/api/pantau", {"kecamatan": "sungai"})[0] == 400  # ambigu
    assert post(base + "/api/pantau", {"kecamatan": "Kubu", "end_date": "26-10-2026"})[0] == 400
    for path in ("/api/hasil/kubu", "/output/../web_pantau.py", "/output/%2e%2e/web_pantau.py", "/tidak-ada"):
        with pytest.raises(urllib.error.HTTPError) as e:
            get(base + path)
        assert e.value.code == 404


def test_failed_job_is_reported(tmp_path):
    def broken(args, region):
        raise RuntimeError("Caller does not have permission")

    app = web_pantau.App(out_dir=tmp_path / "out", cache_dir=tmp_path / "cache", env_factory=broken)
    srv = web_pantau.serve(app, port=0)
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        job = wait(base, post(base + "/api/pantau", {"kecamatan": "Kubu"})[1]["job"])
        assert job["status"] == "gagal" and "Caller does not have permission" in job["error"]
        assert post(base + "/api/pantau", {"kecamatan": "Kubu"})[0] == 202  # bisa dicoba lagi
    finally:
        srv.shutdown()
