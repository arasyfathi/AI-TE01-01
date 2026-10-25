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
    """events: daftar (jenis, indeks_periode_absolut, r0, r1, c0, c1); jenis: logging, fire, cloud, haze."""

    def __init__(self, region, events, **kw):
        kw.setdefault("cache_dir", None)
        kw.setdefault("end_date", END)
        super().__init__(region, **kw)
        self.events = []  # ground truth tidak dipakai agen
        self.world = events
        self.calls = []

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
    assert result["ok"] and "PERINGATAN BARU: 2" in out

    hist = json.loads((tmp_path / region.slug / "riwayat_peringatan.json").read_text())
    kinds = {h["kind"]: h for h in hist}
    assert set(kinds) == {"fire", "logging"}
    # kebakaran dikonfirmasi pada periode yang sama (bukan menunggu 2 minggu)
    assert kinds["fire"]["scene_day"] == kinds["fire"]["alert_day"] == 3
    # tebang liar dikonfirmasi setelah periode berikutnya membuktikan kehilangan menetap
    assert kinds["logging"]["scene_day"] == 3 and kinds["logging"]["alert_day"] == 4
    assert result["pending"] == 1  # kabut di periode terakhir: belum bisa diputuskan, diperiksa putaran berikut
    gj = json.loads((tmp_path / region.slug / "peringatan.geojson").read_text())
    assert len(gj["features"]) == 2 and gj["features"][0]["geometry"]["type"] == "Point"
    assert list((tmp_path / region.slug).glob("laporan_*.json")) and list((tmp_path / region.slug).glob("peta_*.png"))

    # Putaran yang sama diulang: tidak ada peringatan ganda
    run_pantau.run_kecamatan(args, region, FakeSentinel(region, world))
    assert "PERINGATAN BARU: 0" in capsys.readouterr().out

    # Putaran 2 minggu kemudian: kejadian lama sudah jadi acuan, tidak terdeteksi ulang;
    # kabut yang kemarin "menunggu" kini terbukti hilang -> ditolak.
    end2 = (dt.date.fromisoformat(END) + dt.timedelta(days=14)).isoformat()
    args2 = run_pantau.parse_args(["--out", str(tmp_path), "--quiet", "--end-date", end2])
    env2 = FakeSentinel(region, world, end_date=end2)
    r2 = run_pantau.run_kecamatan(args2, region, env2)
    out2 = capsys.readouterr().out
    hist2 = json.loads((tmp_path / region.slug / "riwayat_peringatan.json").read_text())
    assert len(hist2) == 2 and "PERINGATAN BARU: 0" in out2
    assert r2["pending"] == 0
    assert "ditolak 1" in out2 and "NDVI pulih" in out2


def test_cloud_only_world_gives_no_cases(tmp_path, capsys):
    region = square_region()
    probe = SentinelEnvironment(region, cache_dir=None, end_date=END)
    world = absolute([("cloud", 3, 0, 60, 0, 60), ("cloud", 4, 40, 104, 40, 104)], probe)
    result = run_pantau.run_kecamatan(args_for(tmp_path), region, FakeSentinel(region, world))
    assert result["ok"] and result["new"] == 0 and result["pending"] == 0
    assert "Kasus: 0" in capsys.readouterr().out


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
    first.prefetch()
    assert len(first.calls) == 4 and len(list((tmp_path / "c").rglob("*.npz"))) == 4
    second = FakeSentinel(region, [], cache_dir=tmp_path / "c")
    second.prefetch()
    assert second.calls == []


# -------------------------------------------- kode GEE sungguhan dengan ee palsu
def _stub_ee():
    ee = MagicMock()

    def compute(request):
        dims = request["grid"]["dimensions"]
        h, w = dims["height"], dims["width"]
        tx = request["grid"]["affineTransform"]["translateX"]
        arr = np.zeros((h, w), dtype=[("ndvi", "f4"), ("fire", "f4")])
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
    ee.ImageCollection.assert_any_call("ESA/WorldCover/v200")
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
    assert [h["kind"] for h in hist] == ["fire"] and hist[0]["scene_day"] == 3

    # kontrol: dengan jangkauan titik api hanya 1 periode, bekas terbakar salah dicap tebang liar
    orig = run_pantau.build_model

    def short_lookback(args, env):
        model = orig(args, env)
        for v in model.validators:
            v.fire_lookback = 1
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
