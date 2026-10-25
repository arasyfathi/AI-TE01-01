"""Uji adapter GEE tanpa jaringan.

``FakeGEE`` meniru perilaku produk MODIS di GEE (piksel berawan -> NaN, titik api 1/0/NaN) dengan
dunia sintetis di belakangnya, dan melewati jalur ``_decode`` yang sama dengan jalur sungguhan.
Yang TIDAK teruji di sini: pembentukan ekspresi dan panggilan ke server GEE (lihat ``run_gee.py --check``).
"""

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deforestation_mas import ForestMonitoringModel  # noqa: E402
from deforestation_mas.environment import ForestEnvironment  # noqa: E402
from deforestation_mas.evaluation import evaluate  # noqa: E402
from deforestation_mas.gee_environment import COLLECTIONS, NODATA, GEEEnvironment  # noqa: E402


class FakeGEE(GEEEnvironment):
    def __init__(self, world, **kw):
        kw.setdefault("cache_dir", None)
        super().__init__(size=world.size, n_days=world.day, start="2023-08-15", **kw)
        self.world = world
        self.calls = []
        self.missing = set()  # tanggal tanpa citra
        self.fail_dates = {}  # tanggal -> sisa kegagalan

    def _list_dates(self):
        dates = {self.date_of(d) for d in range(1, self.n_days + 1)} - self.missing
        return {k: set(dates) for k in COLLECTIONS}

    def _request_pixels(self, date):
        self.calls.append(date)
        if self.fail_dates.get(date, 0) > 0:
            self.fail_dates[date] -= 1
            return None
        day = (dt.date.fromisoformat(date) - self.start).days + 1
        w, s = self.world, self.world.size
        cloud = np.zeros((s, s), bool)
        for d, m in w.cloud_log:
            if d == day:
                cloud |= m
        ndvi = w.scenes[day].ndvi.astype(float)
        lst = w.thermal[day].astype(float)
        fire = np.zeros((s, s))
        for e in w.events:
            if e.kind == "fire" and e.start_day <= day <= e.start_day + 3:
                fire[e.footprint] = 1.0
        raw = np.stack([ndvi, lst, fire], axis=-1)
        raw[cloud] = np.nan  # awan: tak ada NDVI, LST maupun titik api
        return self._decode(np.where(np.isnan(raw), NODATA, raw))


def make_world(seed=1, days=100, **kw):
    world = ForestEnvironment(size=40, seed=seed, download_fail_prob=0, thermal_dropout_prob=0, **kw)
    for _ in range(days):
        world.advance_day()
    return world


def run_fake(seed=1, days=100, world_kw=None, **model_kw):
    world = make_world(seed, days, **(world_kw or {}))
    env = FakeGEE(world)
    model = ForestMonitoringModel(env=env, validator_kwargs={"fire_from_lst": False}, **model_kw)
    for _ in range(days):
        model.step()
    env.events, env.cloud_log = world.events, world.cloud_log  # ground truth hanya untuk evaluasi
    return model, env, world


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_pipeline_on_cloud_masked_data(seed):
    model, _, _ = run_fake(seed)
    r = evaluate(model)
    assert r["true_events"] > 5
    assert r["recall"] >= 0.8
    assert r["precision"] >= 0.9
    assert r["cause_accuracy"] >= 0.9  # api dibuktikan oleh titik api, bukan oleh suhu


def test_clouds_alone_never_alert():
    model, _, _ = run_fake(3, 80, world_kw={"p_logging": 0, "p_fire": 0, "p_cloud": 0.5})
    assert len(model.alerts) == 0


def test_decode_paths():
    env = GEEEnvironment(size=3, cache_dir=None)
    h = np.full((3, 3, 3), 0.5)
    h[0, 0, 0] = NODATA
    out = env._decode(h)
    assert np.isnan(out["ndvi"][0, 0]) and out["ndvi"][1, 1] == pytest.approx(0.5)
    assert out["lst"].dtype == np.float32

    structured = np.zeros((3, 3), dtype=[("ndvi", "f4"), ("lst", "f4"), ("fire", "f4")])
    structured["lst"] = NODATA
    assert np.isnan(env._decode(structured)["lst"]).all()

    with pytest.raises(ValueError):
        env._decode(np.zeros((4, 4, 3)))
    with pytest.raises(ValueError):
        env._decode(np.zeros((3, 3)))


def test_geometry_and_dates():
    env = GEEEnvironment(size=40, center=(-2.35, 114.0), start="2023-08-15", cache_dir=None)
    assert env.date_of(1) == "2023-08-15" and env.date_of(18) == "2023-09-01"
    grid = env._grid()
    assert grid["dimensions"] == {"width": 40, "height": 40} and grid["crsCode"] == "EPSG:4326"
    assert grid["affineTransform"]["scaleY"] < 0 < grid["affineTransform"]["scaleX"]
    assert env.ha_per_px == pytest.approx(6.25, rel=0.01)
    lat, lon = env.to_latlon(0, 0)
    assert -2.35 < lat < -2.35 + 0.1 and 114.0 - 0.1 < lon < 114.0
    lat2, lon2 = env.to_latlon(39, 39)
    assert lat2 < -2.35 and lon2 > 114.0


def test_latency_and_missing_days():
    env = FakeGEE(make_world(1, 30), latency_days=3)
    env.missing = {env.date_of(5)}
    env.day = 10
    assert env.available_days() == [1, 2, 3, 4, 6, 7]
    assert env.download(9) is None and env.fetch_thermal(8) is None  # belum tersedia
    assert env.download(5) is None  # tidak ada citra pada tanggal itu


def test_cache_roundtrip(tmp_path):
    world = make_world(1, 12)
    first = FakeGEE(world, cache_dir=tmp_path)
    first.day = 12
    a = first.fetch_thermal(8)
    assert first.calls == [first.date_of(8)] and list(tmp_path.glob("*.npz"))
    first.fetch_fire(8)
    assert len(first.calls) == 1  # hari yang sama tidak diminta dua kali

    second = FakeGEE(world, cache_dir=tmp_path)
    second.day = 12
    b = second.fetch_thermal(8)
    assert second.calls == []  # dibaca dari cache, tanpa memakai kuota GEE
    assert np.array_equal(a, b, equal_nan=True)


def test_transient_and_permanent_failures():
    world = make_world(1, 40)
    env = FakeGEE(world)
    env.fail_dates = {env.date_of(20): 2, env.date_of(30): 999}
    model = ForestMonitoringModel(env=env, validator_kwargs={"fire_from_lst": False})
    for _ in range(40):
        model.step()
    assert 20 in model.archive  # gagal dua kali, berhasil pada percobaan berikutnya
    assert 30 not in model.archive and env._failures[30] >= env.max_failures
    assert len(model.archive) == 39


def _validator(model, **fire_arrays):
    v = model.validators[0]
    s = model.env.size
    for d in range(1, 13):
        v.thermal[d] = np.full((s, s), np.nan)
        v.fire.pop(d, None)
    return v


def _ask(model, v, mask):
    n = len(model.bus.log)
    ok = v._validate({"day": 12, "mask": mask, "case_id": "X", "round": 0, "requester": "detector-1"})
    reply = model.bus.log[-1].content if len(model.bus.log) > n else None
    return ok, reply


def test_validator_semantics_with_missing_data():
    model, env, _ = run_fake(1, 5)
    v = _validator(model)
    s = env.size
    mask = np.zeros((s, s), bool)
    mask[10:13, 10:13] = True

    # suhu dan titik api sama-sama tertutup awan -> belum bisa menilai
    assert _ask(model, v, mask) == (False, None)

    # titik api teramati dan tidak ada -> tebang liar
    for d in range(8, 13):
        v.fire[d] = np.zeros((s, s))
    ok, reply = _ask(model, v, mask)
    assert ok and reply["cause"] == "logging" and reply["fire_fraction"] == 0.0 and reply["mean_anomaly"] is None

    # titik api di dekat wilayah (dalam toleransi 2 piksel) -> kebakaran
    f = np.zeros((s, s))
    f[8:10, 8:15] = 1.0
    v.fire[11] = f
    ok, reply = _ask(model, v, mask)
    assert ok and reply["cause"] == "fire" and reply["confidence"] >= 0.8

    # titik api jauh dari wilayah -> tetap tebang liar
    f = np.zeros((s, s))
    f[30:33, 30:33] = 1.0
    v.fire[11] = f
    assert _ask(model, v, mask)[1]["cause"] == "logging"

    # hari berawan (hampir semua NaN) tidak dihitung sebagai "tidak ada api"
    for d in range(1, 13):
        v.fire[d] = np.full((s, s), np.nan)
    assert _ask(model, v, mask) == (False, None)


def _cloudy_after(world, cutoff_day, **detector_kwargs):
    """Model GEE tiruan di mana semua citra setelah ``cutoff_day`` tertutup awan/asap."""
    env = FakeGEE(world)
    orig = env._request_pixels

    def request(date):
        data = orig(date)
        day = (dt.date.fromisoformat(date) - env.start).days + 1
        if data is not None and day > cutoff_day:
            data = {k: np.full_like(v, np.nan) for k, v in data.items()}
        return data

    env._request_pixels = request
    return ForestMonitoringModel(
        env=env, validator_kwargs={"fire_from_lst": False}, detector_kwargs=detector_kwargs or None
    )


def test_case_escalates_when_sky_never_clears():
    """Kejadian terjadi, lalu seluruh citra berikutnya tertutup: kasus tidak boleh menggantung selamanya."""
    world = make_world(2, 60, p_logging=0.3, p_fire=0, p_cloud=0)
    start = min(e.start_day for e in world.events if e.start_day >= 12)

    model = _cloudy_after(world, start)
    for _ in range(start + 15):
        model.step()
    stuck = [c for c in model.cases.values() if c.day == start]
    assert stuck and all(c.status == "uncertain" for c in stuck)
    assert all("tidak ada citra bersih" in c.evidence["catatan"] for c in stuck)
    assert any(a.kind == "uncertain" and a.case_id == stuck[0].case_id for a in model.alerts)

    # kontrol negatif: tanpa batas tunggu, kasus yang sama memang menggantung
    model = _cloudy_after(world, start, max_wait_days=10**6)
    for _ in range(start + 15):
        model.step()
    assert any(c.status == "pending" for c in model.cases.values() if c.day == start)


def test_run_gee_cli_end_to_end(tmp_path, monkeypatch, capsys):
    import json

    import run_gee

    world = make_world(1, 60)
    monkeypatch.setattr(run_gee, "make_env", lambda args: FakeGEE(world))

    assert run_gee.main(["--days", "60", "--out", str(tmp_path), "--quiet"]) == 0
    out = capsys.readouterr().out
    assert "Ringkasan" in out and "peringatan" in out
    alerts = json.loads((tmp_path / "alerts.json").read_text())
    assert alerts and alerts[0]["scene_date"] >= "2023-08-15" and alerts[0]["alert_date"] >= alerts[0]["scene_date"]
    assert (tmp_path / "gee_replay.png").exists() and (tmp_path / "timeseries.csv").exists()

    assert run_gee.main(["--check", "2023-08-20", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "NDVI 250 m" in out and (tmp_path / "check.png").exists()


def test_check_reports_failure_cleanly(tmp_path, monkeypatch, capsys):
    import run_gee

    class Broken(FakeGEE):
        def _request_pixels(self, date):
            self.errors.append(f"{date}: Permission denied")
            return None

    monkeypatch.setattr(run_gee, "make_env", lambda args: Broken(make_world(1, 5)))
    assert run_gee.main(["--check", "--out", str(tmp_path)]) == 1
    assert "Permission denied" in capsys.readouterr().out


# --- Menjalankan kode pembangun ekspresi GEE yang sesungguhnya dengan objek `ee` palsu -------------
# (tidak memeriksa makna ekspresi di server, tetapi menangkap kesalahan Python seperti None[...])

def _stub_ee(images_per_day=1, pixels=None):
    from unittest.mock import MagicMock

    ee = MagicMock()
    coll = ee.ImageCollection.return_value.filterDate.return_value
    coll.size.return_value.getInfo.return_value = images_per_day
    ee.data.computePixels.return_value = np.full((40, 40, 3), 0.5) if pixels is None else pixels
    return ee


def test_check_works_without_replay_listing():
    """Mode --check tidak memuat daftar tanggal replay; sebelumnya ini memicu 'NoneType is not subscriptable'."""
    ee = _stub_ee()
    env = GEEEnvironment(project="x", size=40, cache_dir=None, retries=1)
    env._ee = ee
    assert env._dates is None
    stats, data = env.check("2023-08-20")
    assert stats["ndvi"]["valid_pct"] == 100.0 and data["fire"].shape == (40, 40)
    request = ee.data.computePixels.call_args[0][0]
    assert request["fileFormat"] == "NUMPY_NDARRAY" and request["grid"]["crsCode"] == "EPSG:4326"
    assert "expression" in request


def test_check_reports_missing_modis_day():
    ee = _stub_ee(images_per_day=0)
    env = GEEEnvironment(project="x", size=40, cache_dir=None, retries=1)
    env._ee = ee
    with pytest.raises(RuntimeError, match="MOD09GQ"):
        env.check("2023-08-20")


def test_check_reports_server_error_with_type():
    ee = _stub_ee()
    ee.data.computePixels.side_effect = PermissionError("Caller does not have permission")
    env = GEEEnvironment(project="x", size=40, cache_dir=None, retries=1)
    env._ee = ee
    with pytest.raises(RuntimeError, match="PermissionError: Caller does not have permission"):
        env.check("2023-08-20")


def test_replay_listing_and_download_with_stub_ee():
    from unittest.mock import MagicMock

    ms = [int(dt.datetime(2023, 8, d, tzinfo=dt.timezone.utc).timestamp() * 1000) for d in (15, 16, 18)]
    ee = _stub_ee()
    ee.ImageCollection.return_value.filterDate.return_value.aggregate_array.return_value.getInfo.return_value = ms
    env = GEEEnvironment(project="x", size=40, n_days=10, cache_dir=None, retries=1)
    env._ee = ee
    env.day = 5
    assert env.available_days() == [1, 2, 4]  # 15, 16, 18 Agustus
    assert env.download(2).ndvi.shape == (40, 40)
    assert env.download(3) is None  # 17 Agustus tidak ada citra
    assert env.fetch_fire(4).shape == (40, 40)
    assert isinstance(ee.ImageCollection, MagicMock)


DIAG_NAMES = ("ada_reflektansi", "awan", "bayangan_awan", "awan_internal", "aerosol_tinggi", "cirrus_tinggi",
              "lst_qc", "firemask")


def _diag_array(**values):
    arr = np.zeros((40, 40), dtype=[(n, "f4") for n in DIAG_NAMES])
    for k, v in values.items():
        arr[k] = v
    return arr


def test_ndvi_uses_normalized_difference_and_haze_switch():
    ee = _stub_ee()
    env = GEEEnvironment(project="x", size=40, cache_dir=None, retries=1)
    env._ee = ee
    env.check("2023-08-20")
    mosaic = ee.ImageCollection.return_value.filterDate.return_value.mosaic.return_value
    mosaic.normalizedDifference.assert_called_with(["sur_refl_b02", "sur_refl_b01"])

    on = GEEEnvironment(cache_dir="c")._cache_path("2023-08-20").name
    off = GEEEnvironment(cache_dir="c", mask_haze=False)._cache_path("2023-08-20").name
    assert on != off and "_h1_" in on and "_h0_" in off  # cache tidak tercampur antar pengaturan


def test_diagnose_reports_flags_and_classes():
    ee = _stub_ee()
    ee.data.computePixels.return_value = _diag_array(ada_reflektansi=1, aerosol_tinggi=1, lst_qc=2, firemask=5)
    env = GEEEnvironment(project="x", size=40, cache_dir=None, retries=1)
    env._ee = ee
    rep = env.diagnose("2023-08-15")
    assert rep["ada_reflektansi"]["ya_pct"] == 100.0 and rep["awan"]["ya_pct"] == 0.0
    assert rep["aerosol_tinggi"]["ya_pct"] == 100.0
    assert rep["lst_qc"]["kelas_pct"] == {2: 100.0} and rep["firemask"]["kelas_pct"] == {5: 100.0}


@pytest.mark.parametrize("flags,expected", [
    ({"ada_reflektansi": 1, "aerosol_tinggi": 1}, "--keep-haze"),
    ({"ada_reflektansi": 1, "awan": 1}, "memang tertutup awan"),
    ({"ada_reflektansi": 0}, "tidak menutupi area"),
])
def test_check_explains_why_ndvi_is_empty(tmp_path, monkeypatch, capsys, flags, expected):
    import run_gee

    ee = _stub_ee()
    main = np.full((40, 40, 3), NODATA)
    ee.data.computePixels.side_effect = [main, _diag_array(lst_qc=2, firemask=5, **flags)]

    def env_with_stub(args):
        env = GEEEnvironment(project="x", size=40, cache_dir=None, retries=1)
        env._ee = ee
        return env

    monkeypatch.setattr(run_gee, "make_env", env_with_stub)
    assert run_gee.main(["--check", "2023-08-15", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Rincian masker NDVI" in out and expected in out
    assert "tidak ada (awan) 100.0%" in out and "tanah tanpa api 100.0%" in out


def test_scan_fills_cache_for_replay(tmp_path, monkeypatch, capsys):
    import run_gee

    world = make_world(1, 20)
    env = FakeGEE(world, cache_dir=tmp_path)
    env.missing = {env.date_of(3)}
    rows = list(env.scan(10))
    assert len(rows) == 10 and rows[2][1] is None and "tidak ada citra" in rows[2][2]
    assert rows[0][1]["ndvi_pct"] > 50 and len(list(tmp_path.glob("*.npz"))) == 9

    replay = FakeGEE(world, cache_dir=tmp_path)
    replay.day = 10
    replay.download(5)
    assert replay.calls == []  # replay memakai hasil scan dari cache

    monkeypatch.setattr(run_gee, "make_env", lambda args: FakeGEE(world))
    assert run_gee.main(["--scan", "8", "--days", "20"]) == 0
    assert "hari punya NDVI bersih" in capsys.readouterr().out


def _fire_grid(h=100, w=100, blobs=()):
    arr = np.zeros((h, w), dtype=[("count", "f4"), ("first", "f4"), ("last", "f4")])
    arr["first"] = NODATA
    arr["last"] = NODATA
    for (r0, r1, c0, c1, n, first, last) in blobs:
        arr["count"][r0:r1, c0:c1] = n
        arr["first"][r0:r1, c0:c1] = first
        arr["last"][r0:r1, c0:c1] = last
    return arr


BLOBS = ((20, 26, 60, 66, 5, 10, 20), (70, 73, 10, 13, 3, 30, 35))


def test_find_fire_hotspots_ranks_planted_fires():
    ee = _stub_ee()
    ee.data.computePixels.return_value = _fire_grid(blobs=BLOBS)
    env = GEEEnvironment(project="x", start="2023-08-15", n_days=60, cache_dir=None)
    env._ee = ee
    spots = env.find_fire_hotspots(bbox=(113.0, -3.0, 114.0, -2.0))
    assert len(spots) == 2  # hanya dua kumpulan api; sisanya kosong
    a, b = spots
    assert a["fire_pixel_days"] == 36 * 5 and b["fire_pixel_days"] == 9 * 3
    assert a["lat"] == pytest.approx(-2.0 - 23 * 0.01, abs=0.03) and a["lon"] == pytest.approx(113.63, abs=0.03)
    assert b["lat"] == pytest.approx(-2.0 - 71.5 * 0.01, abs=0.03) and b["lon"] == pytest.approx(113.115, abs=0.03)
    assert (a["first_date"], a["last_date"]) == ("2023-08-25", "2023-09-04")
    grid = ee.data.computePixels.call_args[0][0]["grid"]
    assert grid["dimensions"] == {"width": 100, "height": 100}


def test_find_fires_cli(monkeypatch, capsys):
    import run_gee

    ee = _stub_ee()
    ee.data.computePixels.side_effect = [_fire_grid(blobs=BLOBS), _fire_grid()]

    def env_with_stub(args):
        env = run_gee.GEEEnvironment(project=args.project, start=args.start, n_days=args.days, cache_dir=None)
        env._ee = ee
        return env

    monkeypatch.setattr(run_gee, "make_env", env_with_stub)
    argv = ["--project", "p", "--find-fires", "--bbox", "113,-3,114,-2", "--days", "60"]
    assert run_gee.main(argv) == 0
    out = capsys.readouterr().out
    assert "--lat -2.23" in out and "--start 2023-08-15" in out and "--keep-haze --scan 30" in out

    assert run_gee.main(argv) == 0  # tanpa titik api sama sekali
    assert "Tidak ada titik api" in capsys.readouterr().out
    assert run_gee.main(["--find-fires", "--bbox", "1,2,3"]) == 1


# --- Aturan konsensus, ditiru dari kasus nyata Kalimantan Tengah (Sep-Okt 2023) ---------------------

def _case_with_verdict(model, real, cause, strong, det_vote, fire_fraction=None):
    from deforestation_mas.agents import Case
    from deforestation_mas.messaging import PROPOSE, Message

    det = model.detectors[0]
    s = model.env.size
    mask = np.zeros((s, s), bool)
    mask[5:9, 5:9] = True
    case = Case(case_id=f"T{len(model.cases)}", detector=det.name, validator=model.validators[0].name, day=1,
                mask=mask, reference=np.full((s, s), 0.8), drop=0.3, centroid=(0.0, 0.0), last_check_day=1)
    case.det_vote = det_vote
    model.cases[case.case_id] = case
    det._receive_verdict(Message(PROPOSE, "validator-1", det.name, "verdict", {
        "case_id": case.case_id, "round": 0, "day": 1, "real": real, "cause": cause, "confidence": 0.9,
        "strong": strong, "mean_anomaly": None, "hot_fraction": 0.0, "fire_fraction": fire_fraction}))
    det._try_resolve(case)
    return case


def _gee_model(**detector_kwargs):
    return ForestMonitoringModel(env=FakeGEE(make_world(1, 5)), validator_kwargs={"fire_from_lst": False},
                                 detector_kwargs=detector_kwargs or None)


def test_fire_fast_track_like_alert_001():
    """ALERT-001: titik api 93% di lokasi penurunan NDVI, tetapi tak ada citra bersih 10 hari -> dulu 'uncertain'."""
    case = _case_with_verdict(_gee_model(), True, "fire", True, det_vote=None, fire_fraction=0.93)
    assert case.status == "confirmed" and case.cause == "fire" and "jalur_cepat" in case.evidence

    case = _case_with_verdict(_gee_model(fire_fast_track=False), True, "fire", True, det_vote=None)
    assert case.status == "pending"  # kontrol: tanpa jalur cepat tetap menunggu citra bersih


def test_weak_logging_vote_cannot_beat_recovered_ndvi_like_alert_004():
    """ALERT-004/005: NDVI turun hanya 0.02-0.03 (pulih), validator bilang 'tebang liar' karena tak ada api."""
    case = _case_with_verdict(_gee_model(), True, "logging", False, det_vote=False, fire_fraction=0.0)
    assert case.status == "dismissed"


def test_weak_logging_vote_with_persistent_loss_confirms():
    case = _case_with_verdict(_gee_model(), True, "logging", False, det_vote=True, fire_fraction=0.0)
    assert case.status == "confirmed" and case.cause == "logging"


def test_strong_disagreement_still_gets_another_round():
    model = _gee_model()
    case = _case_with_verdict(model, True, "logging", True, det_vote=False)
    assert case.status == "pending" and case.round == 1  # suara kuat: kumpulkan bukti lagi, jangan buang
    case = _case_with_verdict(model, None, "inconclusive", False, det_vote=False)
    assert case.status == "dismissed"  # validator tak punya bukti, NDVI pulih


def test_fire_confirmed_end_to_end_when_ndvi_stays_cloudy():
    """Seperti kasus nyata: api terdeteksi MODIS, tetapi NDVI tertutup awan/asap terus setelahnya."""
    world = make_world(4, 60, p_logging=0, p_fire=0.3, p_cloud=0)
    fire_day = min(e.start_day for e in world.events if e.start_day >= 12)
    env = FakeGEE(world)
    orig = env._request_pixels

    def ndvi_cloudy_after_fire(date):
        data = orig(date)
        day = (dt.date.fromisoformat(date) - env.start).days + 1
        if data is not None and day > fire_day:
            data = dict(data, ndvi=np.full_like(data["ndvi"], np.nan))  # suhu & titik api tetap teramati
        return data

    env._request_pixels = ndvi_cloudy_after_fire
    model = ForestMonitoringModel(env=env, validator_kwargs={"fire_from_lst": False})
    for _ in range(fire_day + 15):
        model.step()
    first = [c for c in model.cases.values() if c.day == fire_day]
    assert first and all(c.status == "confirmed" and c.cause == "fire" for c in first)
    assert all(c.decided_day <= fire_day + 1 for c in first)  # peringatan keesokan harinya, bukan setelah 10 hari
