"""Uji pemantauan per periode (Sentinel-2 + VIIRS) tanpa jaringan.

``FakeSentinel`` menyajikan komposit periode tiruan yang ditentukan per *indeks periode absolut*, sehingga
putaran yang bergeser satu periode melihat dunia yang sama (untuk menguji riwayat & duplikasi).
"""

import datetime as dt
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run_pantau  # noqa: E402
from deforestation_mas.region import Region, find_region, load_regions  # noqa: E402
from deforestation_mas.sentinel_environment import (  # noqa: E402
    EPOCH,
    NODATA,
    SentinelEnvironment,
    decode_planes,
)

DATA = Path(__file__).resolve().parents[1] / "data" / "kubu_raya_kecamatan.geojson"
END = "2023-10-20"  # periode lengkap terakhir sebelum tanggal ini dipakai sebagai periode ke-4


def square_region(name="Uji", lon=109.5, lat=-0.3, half=0.0135, hole=False):
    outer = [(lon - half, lat - half), (lon + half, lat - half), (lon + half, lat + half),
             (lon - half, lat + half), (lon - half, lat - half)]
    poly = [outer]
    if hole:
        h = half / 3
        poly.append([(lon - h, lat - h), (lon + h, lat - h), (lon + h, lat + h), (lon - h, lat + h), (lon - h, lat - h)])
    return Region(name, [poly])


class FakeSentinel(SentinelEnvironment):
    """events: daftar (jenis, indeks_periode_absolut | tanggal, r0, r1, c0, c1).

    jenis: logging, fire, fire_late, cloud, haze (NDVI); palm, other (tutupan lahan statis, periode diabaikan);
    hotspot (titik api tanpa perubahan NDVI pada hari ke-5 periode), hotspot_on (titik api pada tanggal tertentu).
    Titik api untuk 'fire'/'fire_late' muncul pada hari ke-3 periode kejadiannya."""

    def __init__(self, region, events, **kw):
        kw.setdefault("cache_dir", None)
        kw.setdefault("end_date", END)
        super().__init__(region, **kw)
        self.events = []  # ground truth tidak dipakai agen
        self.world = events
        self.calls = []
        self.hotspot_calls = []

    @staticmethod
    def start_of(period: int) -> dt.date:
        return EPOCH + dt.timedelta(days=14 * period)

    def _request_period(self, day, progress=None):
        p = self.period_index(day)
        self.calls.append(p)
        rng = np.random.default_rng(p)
        ndvi = 0.85 + rng.normal(0, 0.02, self.shape)
        fire = np.zeros(self.shape)
        for kind, ep, r0, r1, c0, c1 in self.world:
            if kind in ("logging", "fire") and p >= ep:
                ndvi[r0:r1, c0:c1] = 0.30 if kind == "logging" else 0.25
            if kind == "fire" and p == ep:
                fire[max(0, r0 - 6):r1 + 6, max(0, c0 - 6):c1 + 6] = 1.0  # piksel VIIRS 375 m, berblok
            if kind == "fire_late":  # api terdeteksi pada ep, bekas terbakar baru terlihat 2 periode kemudian
                if p >= ep + 2:
                    ndvi[r0:r1, c0:c1] = 0.25
                if p == ep:
                    fire[max(0, r0 - 6):r1 + 6, max(0, c0 - 6):c1 + 6] = 1.0
            if kind == "haze" and p == ep:
                ndvi[r0:r1, c0:c1] = 0.55  # kabut tipis: turun sementara
            if kind == "cloud" and p == ep:
                ndvi[r0:r1, c0:c1] = np.nan
        raw = np.stack([ndvi, fire], axis=-1)
        return decode_planes(np.where(np.isnan(raw), NODATA, raw), ("ndvi", "fire"), self.shape)

    def _request_landcover(self, progress=None):
        lc = np.full(self.shape, 1.0)  # bawaan: semua hutan alam
        for kind, _, r0, r1, c0, c1 in self.world:
            if kind in ("palm", "other"):
                lc[r0:r1, c0:c1] = 2.0 if kind == "palm" else 3.0
        return {"landcover": lc.astype(np.float32)}

    def _request_hotspots(self, start, end):
        self.hotspot_calls.append((start, end))
        s, e = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
        k, (hh, ww) = self.hs_block, self.hs_shape
        out = {"count": np.zeros((hh, ww)), "first": np.full((hh, ww), np.nan),
               "last": np.full((hh, ww), np.nan), "frp": np.full((hh, ww), np.nan)}
        for kind, ep, r0, r1, c0, c1 in self.world:
            if kind in ("fire", "fire_late"):
                when, box = self.start_of(ep) + dt.timedelta(3), (r0 - 6, r1 + 6, c0 - 6, c1 + 6)
            elif kind == "hotspot":
                when, box = self.start_of(ep) + dt.timedelta(5), (r0, r1, c0, c1)
            elif kind == "hotspot_on":
                when, box = dt.date.fromisoformat(ep), (r0, r1, c0, c1)
            else:
                continue
            if not s <= when < e:
                continue
            ra, rb, ca, cb = max(0, box[0]) // k, (box[1] - 1) // k + 1, max(0, box[2]) // k, (box[3] - 1) // k + 1
            off = float((when - s).days)
            out["count"][ra:rb, ca:cb] += 1
            out["first"][ra:rb, ca:cb] = np.fmin(out["first"][ra:rb, ca:cb], off)
            out["last"][ra:rb, ca:cb] = np.fmax(out["last"][ra:rb, ca:cb], off)
            out["frp"][ra:rb, ca:cb] = 25.0
        return {b: a.astype(np.float32) for b, a in out.items()}


def args_for(tmp_path, *extra):
    return run_pantau.parse_args(["--out", str(tmp_path), "--quiet", "--end-date", END, *extra])


def P(day, env):
    return env.period_index(day)


# ----------------------------------------------------------------- wilayah
def test_kubu_raya_regions_and_name_matching():
    regions = load_regions(DATA)
    assert len(regions) == 9
    assert find_region(regions, "kecamatan sungai raya").name == "Sungai Raya"
    assert find_region(regions, "KUBU").name == "Kubu"  # nama persis didahulukan atas "Kubu Raya"-mirip
    with pytest.raises(ValueError, match="beberapa kecamatan"):
        find_region(regions, "sungai")
    with pytest.raises(ValueError, match="tidak ditemukan"):
        find_region(regions, "Pontianak Kota")


def test_rasterized_area_matches_polygon():
    region = find_region(load_regions(DATA), "Rasau Jaya")
    env = SentinelEnvironment(region, cache_dir=None, end_date=END)
    raster_km2 = env.region_mask.sum() * env.ha_per_px / 100
    assert raster_km2 == pytest.approx(region.area_km2, rel=0.02)


def test_polygon_hole_is_excluded():
    full = SentinelEnvironment(square_region(), cache_dir=None, end_date=END).region_mask.sum()
    holed = SentinelEnvironment(square_region(hole=True), cache_dir=None, end_date=END).region_mask.sum()
    assert holed == pytest.approx(full * (1 - 1 / 9), rel=0.05)


# ----------------------------------------------------------------- periode
def test_periods_are_fixed_calendar_windows():
    env = SentinelEnvironment(square_region(), cache_dir=None, end_date="2023-10-20", n_periods=4)
    start, end = env.period_of(4)
    assert (end - start).days == 14 and (start - EPOCH).days % 14 == 0
    assert end <= dt.date(2023, 10, 20) < end + dt.timedelta(days=14)  # periode lengkap terakhir
    assert env.period_of(3)[1] == env.period_of(4)[0]
    same = SentinelEnvironment(square_region(), cache_dir=None, end_date="2023-10-22", n_periods=4)
    assert same.period_of(4) == env.period_of(4)  # tanggal jalan berbeda dalam periode yang sama: jendela tetap
    nxt = SentinelEnvironment(square_region(), cache_dir=None, end_date=env.period_of(4)[1] + dt.timedelta(14))
    assert nxt.period_of(4)[0] == env.period_of(4)[1]  # melewati batas: bergeser tepat satu periode

    live = SentinelEnvironment(square_region(), cache_dir=None, latency_days=3, today=dt.date(2026, 10, 26))
    assert live.end_date == dt.date(2026, 10, 23) and live.period_of(4)[1] <= dt.date(2026, 10, 23)


# ------------------------------------------------------------ ujung ke ujung
WORLD = [
    ("logging", 3, 10, 22, 10, 22),   # tebang liar pada periode ke-3 jendela pertama
    ("fire", 3, 60, 72, 60, 72),      # kebakaran pada periode ke-3
    ("cloud", 4, 30, 50, 70, 95),     # awan pada periode ke-4 (bukan di atas kejadian)
    ("haze", 4, 80, 92, 15, 30),      # kabut tipis pada periode ke-4, hilang pada periode ke-5
]


def absolute(world, env):
    """Ubah indeks periode relatif (1..n pada jendela pertama) menjadi indeks absolut."""
    return [(k, env.period_index(p), *box) for k, p, *box in world]


def test_fortnightly_run_end_to_end(tmp_path, capsys):
    region = square_region()
    probe = SentinelEnvironment(region, cache_dir=None, end_date=END)
    world = absolute(WORLD, probe)
    args = args_for(tmp_path)

    env = FakeSentinel(region, world)
    result = run_pantau.run_kecamatan(args, region, env)
    out = capsys.readouterr().out
    assert result["ok"] and result["hotspots"] == 1 and result["events"] == 2

    hist = json.loads((tmp_path / region.slug / "riwayat_peringatan.json").read_text())
    kinds = {h["kind"]: h for h in hist}
    assert set(kinds) == {"hotspot", "fire", "logging"}
    # peringatan dini titik api di hutan alam: DARURAT, pada periode kejadian
    assert kinds["hotspot"]["priority"] == "DARURAT" and kinds["hotspot"]["evidence"]["landcover"] == "hutan"
    # kebakaran dikonfirmasi pada periode yang sama (bukan menunggu 2 minggu) dan tertaut ke klaster titik api
    assert kinds["fire"]["scene_day"] == kinds["fire"]["alert_day"] == 3
    assert kinds["fire"]["evidence"]["hotspots"]
    # tebang liar dikonfirmasi setelah periode berikutnya membuktikan kehilangan menetap
    assert kinds["logging"]["scene_day"] == 3 and kinds["logging"]["alert_day"] == 4
    assert result["pending"] == 1  # kabut di periode terakhir: belum bisa diputuskan, diperiksa putaran berikut
    gj = json.loads((tmp_path / region.slug / "peringatan.geojson").read_text())
    assert len(gj["features"]) == 3 and gj["features"][0]["geometry"]["type"] == "Point"
    assert list((tmp_path / region.slug).glob("laporan_*.json")) and list((tmp_path / region.slug).glob("peta_*.png"))

    # Putaran yang sama diulang: tidak ada peringatan ganda
    run_pantau.run_kecamatan(args, region, FakeSentinel(region, world))
    out = capsys.readouterr().out
    assert "TITIK API (baru): 0" in out and "TERKONFIRMASI (baru): 0" in out

    # Putaran 2 minggu kemudian: kejadian lama sudah jadi acuan, tidak terdeteksi ulang;
    # kabut yang kemarin "menunggu" kini terbukti hilang -> ditolak.
    end2 = (dt.date.fromisoformat(END) + dt.timedelta(days=14)).isoformat()
    args2 = run_pantau.parse_args(["--out", str(tmp_path), "--quiet", "--end-date", end2])
    r2 = run_pantau.run_kecamatan(args2, region, FakeSentinel(region, world, end_date=end2))
    out2 = capsys.readouterr().out
    hist2 = json.loads((tmp_path / region.slug / "riwayat_peringatan.json").read_text())
    assert len(hist2) == 3 and r2["new"] == 0 and r2["pending"] == 0
    assert "ditolak 1" in out2


def test_cloud_only_world_gives_no_cases(tmp_path, capsys):
    region = square_region()
    probe = SentinelEnvironment(region, cache_dir=None, end_date=END)
    world = absolute([("cloud", 3, 0, 60, 0, 60), ("cloud", 4, 40, 104, 40, 104)], probe)
    result = run_pantau.run_kecamatan(args_for(tmp_path), region, FakeSentinel(region, world))
    assert result["ok"] and result["new"] == 0 and result["pending"] == 0
    assert "Agen Deteksi: 0 wilayah" in capsys.readouterr().out


def test_missing_fire_data_is_reported(tmp_path, capsys):
    region = square_region()

    class NoFire(FakeSentinel):
        def _request_period(self, day, progress=None):
            data = super()._request_period(day, progress)
            data["fire"][:] = np.nan
            return data

    run_pantau.run_kecamatan(args_for(tmp_path), region, NoFire(region, []))
    assert "tak ada data" in capsys.readouterr().out


def test_cache_reused_between_runs(tmp_path):
    region = square_region()
    first = FakeSentinel(region, [], cache_dir=tmp_path / "c")
    first.prefetch(hotspots_from=3)
    assert len(first.calls) == 4 and len(first.hotspot_calls) == 2
    assert len(list((tmp_path / "c").rglob("*.npz"))) == 4 + 1 + 2  # periode, tutupan lahan, titik api
    second = FakeSentinel(region, [], cache_dir=tmp_path / "c")
    second.prefetch(hotspots_from=3)
    assert second.calls == [] and second.hotspot_calls == []


# -------------------------------------------- kode GEE sungguhan dengan ee palsu
def _stub_ee():
    ee = MagicMock()

    def compute(request):
        dims = request["grid"]["dimensions"]
        h, w = dims["height"], dims["width"]
        tx = request["grid"]["affineTransform"]["translateX"]
        names = ("ndvi", "fire", "landcover", "count", "first", "last", "frp")
        arr = np.zeros((h, w), dtype=[(n, "f4") for n in names])
        arr["landcover"] = 1
        arr["ndvi"] = round(tx, 6) % 1  # nilai khas per ubin untuk memeriksa penyatuan
        return arr

    ee.data.computePixels.side_effect = compute
    return ee


def test_tiles_are_stitched_in_place():
    region = square_region(half=0.05)  # ~11 km -> beberapa ubin
    env = SentinelEnvironment(region, cache_dir=None, end_date=END, tile_px=128, retries=1)
    env._ee = _stub_ee()
    data = env._request_period(1)
    tiles = list(env._tiles())
    assert len(tiles) > 1 and env._ee.data.computePixels.call_count == len(tiles)
    for ty, tx, th, tw in tiles:
        expected = round(env.lon0 + tx * env.cell_deg, 6) % 1
        assert np.allclose(data["ndvi"][ty:ty + th, tx:tx + tw], expected, atol=1e-5)


def test_period_image_builds_with_real_code_path():
    env = SentinelEnvironment(square_region(), cache_dir=None, end_date=END, retries=1)
    ee = _stub_ee()
    env._ee = ee
    assert env._request_period(1) is not None
    ee.ImageCollection.assert_any_call("COPERNICUS/S2_SR_HARMONIZED")
    ee.ImageCollection.assert_any_call("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
    ee.ImageCollection.assert_any_call("NASA/LANCE/SNPP_VIIRS/C2")
    ee.ImageCollection.assert_any_call("NASA/LANCE/NOAA20_VIIRS/C2")


def test_request_failure_is_recorded():
    env = SentinelEnvironment(square_region(), cache_dir=None, end_date=END, retries=1)
    ee = _stub_ee()
    ee.data.computePixels.side_effect = PermissionError("Caller does not have permission")
    env._ee = ee
    assert env._request_period(1) is None
    assert "PermissionError" in env.errors[-1]


def test_status_reports_latest_dates():
    env = SentinelEnvironment(square_region(), cache_dir=None, end_date=END)
    ee = MagicMock()
    ms = int(dt.datetime(2026, 10, 19, tzinfo=dt.timezone.utc).timestamp() * 1000)
    col = ee.ImageCollection.return_value.filterDate.return_value
    col.aggregate_max.return_value.getInfo.return_value = ms
    col.filterBounds.return_value.aggregate_max.return_value.getInfo.return_value = ms
    env._ee = ee
    status = env.status(today=dt.date(2026, 10, 26))
    assert len(status) == 4 and set(status.values()) == {"2026-10-19"}


def test_cli_list_and_bad_name(capsys):
    assert run_pantau.main(["--list"]) == 0
    assert "Batu Ampar" in capsys.readouterr().out
    assert run_pantau.main(["--kecamatan", "sungai"]) == 1
    assert "beberapa kecamatan" in capsys.readouterr().out


def test_burn_scar_after_cloudy_period_is_fire_not_logging(tmp_path, capsys):
    """Seperti Rasau Jaya Agustus-Oktober 2026: titik api pada periode 1, periode 2 tertutup awan total,
    bekas terbakar baru terlihat pada periode 3. Dulu dicap 'tebang liar' karena titik api di luar jangkauan."""
    region = square_region()
    probe = SentinelEnvironment(region, cache_dir=None, end_date=END)
    world = absolute([("fire_late", 1, 40, 60, 40, 60), ("cloud", 2, 0, 999, 0, 999)], probe)
    run_pantau.run_kecamatan(args_for(tmp_path), region, FakeSentinel(region, world))
    hist = json.loads((tmp_path / region.slug / "riwayat_peringatan.json").read_text())
    fires = [h for h in hist if h["kind"] == "fire"]
    assert {h["kind"] for h in hist} == {"hotspot", "fire"} and len(fires) == 1 and fires[0]["scene_day"] == 3

    # kontrol: dengan jangkauan titik api hanya 1 periode, bekas terbakar salah dicap tebang liar
    orig = run_pantau.build_model

    def short_lookback(args, env):
        model = orig(args, env)
        for v in model.validators:
            v.fire_lookback = 1
        model.hotspot_agent.start_day = 3  # tanpa klaster titik api periode 1 untuk Agen Pengelompokan
        return model

    run_pantau.build_model = short_lookback
    try:
        out = tmp_path / "kontrol"
        run_pantau.run_kecamatan(run_pantau.parse_args(["--out", str(out), "--quiet", "--end-date", END]),
                                 region, FakeSentinel(region, world))
    finally:
        run_pantau.build_model = orig
    capsys.readouterr()
    assert all(c["kind"] != "fire" for c in json.loads((out / region.slug / "riwayat_peringatan.json").read_text()))


def test_cli_status(monkeypatch, capsys):
    def env_with_status(args, region):
        env = SentinelEnvironment(region, cache_dir=None, end_date=END)
        env.status = lambda: {
            "COPERNICUS/S2_SR_HARMONIZED": "2026-10-22",
            "GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED": "2026-10-22",
            "NASA/LANCE/SNPP_VIIRS/C2": "2026-10-19",
            "NASA/LANCE/NOAA20_VIIRS/C2": "2026-09-13",
        }
        return env

    monkeypatch.setattr(run_pantau, "make_env", env_with_status)
    assert run_pantau.main(["--status", "--project", "p"]) == 0
    out = capsys.readouterr().out
    assert "Sentinel-2 (NDVI)" in out and "Titik api VIIRS SNPP_VIIRS" in out and "Titik api VIIRS NOAA20_VIIRS" in out
    assert "tidak diperbarui lebih dari 10 hari" in out  # NOAA-20 tertinggal


# ------------------------------------------- tutupan lahan, titik api, pengelompokan kejadian
def test_karhutla_scope_fire_on_any_land_logging_only_in_forest(tmp_path, capsys):
    """Karhutla: kebakaran dipantau di semua lahan (prioritas menurut tutupan lahan), sedangkan penurunan
    NDVI tanpa api di kebun sawit (panen/peremajaan) bukan tebang liar dan tidak diperingatkan."""
    region = square_region()
    probe = SentinelEnvironment(region, cache_dir=None, end_date=END)
    world = absolute([
        ("palm", 0, 0, 60, 0, 104), ("other", 0, 60, 104, 0, 40),   # sisanya hutan alam
        ("logging", 3, 5, 20, 70, 90),         # peremajaan kebun sawit tanpa api
        ("fire", 3, 35, 45, 10, 20),           # kebakaran di kebun sawit
        ("hotspot", 4, 80, 86, 10, 16),        # titik api di lahan lain
        ("logging", 3, 70, 82, 70, 82),        # pembukaan hutan alam
    ], probe)
    result = run_pantau.run_kecamatan(args_for(tmp_path), region, FakeSentinel(region, world))
    out = capsys.readouterr().out
    hist = json.loads((tmp_path / region.slug / "riwayat_peringatan.json").read_text())
    events = {h["kind"]: h for h in hist if h["kind"] != "hotspot"}
    assert set(events) == {"fire", "logging"}
    assert events["fire"]["evidence"]["landcover"] == "sawit" and events["fire"]["priority"] == "SIAGA"
    assert events["logging"]["evidence"]["causes"] == {"logging": 1} and events["logging"]["lon"] > 109.5
    hotspot_cover = {h["evidence"]["landcover"]: h["priority"] for h in hist if h["kind"] == "hotspot"}
    assert hotspot_cover == {"sawit": "SIAGA", "lahan lain": "WASPADA"}
    assert "1 perubahan kebun/ladang tanpa api" in out and "kebakaran sawit" in out
    assert result["ok"]

    # dengan --forest-only, kebakaran di kebun sawit tidak terlihat NDVI-nya (hanya titik api yang tersisa)
    out_dir = tmp_path / "hutan_saja"
    args = run_pantau.parse_args(["--out", str(out_dir), "--quiet", "--end-date", END, "--forest-only"])
    run_pantau.run_kecamatan(args, region, FakeSentinel(region, world, forest_only=True))
    capsys.readouterr()
    hist2 = json.loads((out_dir / region.slug / "riwayat_peringatan.json").read_text())
    assert [h["kind"] for h in hist2 if h["kind"] != "hotspot"] == ["logging"]


def test_incident_agent_merges_fragments_and_links_hotspots():
    """Bekas terbakar yang terpotong menjadi fragmen digabung menjadi satu kejadian; fragmen tepi tanpa
    titik api ikut tercatat kebakaran; titik api di dekat kejadian tebang liar mengubahnya menjadi kebakaran."""
    from deforestation_mas.agents import CONFIRMED, Case
    from deforestation_mas.messaging import INFORM, Message

    region = square_region()
    env = FakeSentinel(region, [])
    model = run_pantau.build_model(args_for(Path("/tmp")), env)
    inc_agent, s = model.incident_agent, env.shape

    def confirmed(cid, box, cause):
        mask = np.zeros(s, bool)
        mask[box] = True
        c = Case(cid, "detector-1", "validator-1", 3, mask, np.zeros(s), 0.3,
                 env.to_latlon(box[0].start, box[1].start), status=CONFIRMED, cause=cause, val_confidence=0.9)
        model.cases[cid] = c
        model.bus.send(Message(INFORM, "detector-1", inc_agent.name, "report",
                               {"case_id": cid, "status": CONFIRMED, "cause": cause}, cid, 3))

    model.day = 3
    confirmed("A", np.s_[40:46, 40:46], "fire")
    confirmed("B", np.s_[40:46, 52:58], "logging")   # 6 px (~180 m) dari A: tepi bekas terbakar
    confirmed("C", np.s_[48:54, 40:46], "fire")      # bagian lain dari kebakaran yang sama
    confirmed("D", np.s_[90:96, 90:96], "logging")   # jauh: kejadian terpisah
    inc_agent.step()
    model.notifier.step()
    assert len(inc_agent.incidents) == 2
    big = next(i for i in inc_agent.incidents if "A" in i.members)
    assert sorted(big.members) == ["A", "B", "C"] and big.kind == "fire"
    assert [a.kind for a in model.alerts] == ["fire", "logging"]

    # Agen Titik Api melaporkan klaster di dekat D -> D menjadi kebakaran (pembaruan, bukan peringatan baru)
    k = env.hs_block
    cluster = {"cluster_id": "HS-3-001", "cells": [(95 // k, 95 // k)]}
    model.bus.send(Message(INFORM, "hotspot", inc_agent.name, "hotspot", cluster, "HS-3-001", 3))
    inc_agent.step()
    model.notifier.step()
    assert len(model.alerts) == 2
    alert_d = next(a for a in model.alerts if a.evidence["member_ids"] == ["D"])
    assert alert_d.kind == "fire" and alert_d.updates[-1]["to_kind"] == "fire"


def test_hotspot_in_running_period_is_early_warning_and_not_duplicated(tmp_path, capsys):
    """Titik api setelah periode lengkap terakhir (periode berjalan) langsung diperingatkan, dan tidak
    dilaporkan ulang ketika periode itu sudah lengkap pada putaran berikutnya."""
    region = square_region()
    env1 = FakeSentinel(region, [])
    running_day = (env1.period_of(4)[1] + dt.timedelta(days=1)).isoformat()  # sesudah periode lengkap terakhir
    assert running_day <= env1.now.isoformat()
    world = [("hotspot_on", running_day, 30, 36, 30, 36)]
    result = run_pantau.run_kecamatan(args_for(tmp_path), region, FakeSentinel(region, world))
    out = capsys.readouterr().out
    assert result["hotspots"] == 1 and running_day in out

    end2 = (dt.date.fromisoformat(END) + dt.timedelta(days=14)).isoformat()
    args2 = run_pantau.parse_args(["--out", str(tmp_path), "--quiet", "--end-date", end2])
    r2 = run_pantau.run_kecamatan(args2, region, FakeSentinel(region, world, end_date=end2))
    capsys.readouterr()
    assert r2["hotspots"] == 0  # sudah dilaporkan sebagai peringatan dini pada putaran sebelumnya


def test_landcover_and_hotspot_images_use_verified_datasets():
    env = SentinelEnvironment(square_region(), cache_dir=None, end_date=END, retries=1)
    ee = _stub_ee()
    env._ee = ee
    lc = env.landcover()
    assert lc is not None and np.nanmax(lc) == 1
    ee.Image.assert_any_call("JRC/GFC2020/V4")
    ee.ImageCollection.assert_any_call("BIOPAMA/GlobalOilPalm/v1_2")
    hs = env.fetch_hotspots(4)
    assert hs is not None and hs["count"].shape == env.hs_shape
    grid = ee.data.computePixels.call_args[0][0]["grid"]
    assert grid["dimensions"] == {"width": env.hs_shape[1], "height": env.hs_shape[0]}
    assert grid["affineTransform"]["scaleX"] == pytest.approx(env.cell_deg * env.hs_block)
    start, end = env.hotspot_window(4)
    assert end == env.now + dt.timedelta(days=1)  # jendela terakhir sampai hari ini
