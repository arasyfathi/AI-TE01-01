"""Lingkungan pemantauan per periode (bawaan 2 minggu) untuk satu wilayah, dari Google Earth Engine.

Satu langkah Mesa = satu periode. Untuk setiap periode diambil:

  ndvi : komposit median NDVI Sentinel-2 (COPERNICUS/S2_SR_HARMONIZED), piksel berawan dibuang
         memakai Cloud Score+ (GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED, cs_cdf >= ambang).
         Bila ``forest_only``, hanya hutan dan mangrove menurut ESA WorldCover 2021 (kelas 10 dan 95)
         yang dipantau, agar panen sawah/kebun tidak menjadi alarm palsu.
  fire : 1 = ada titik api VIIRS (keyakinan nominal/tinggi) dalam periode itu, 0 = tidak ada,
         NaN = tidak ada data titik api sama sekali untuk periode itu.

Piksel di luar poligon wilayah diberi NaN. Suhu permukaan tidak dipakai (selalu NaN); bukti kebakaran
berasal dari titik api VIIRS.

Periode memakai kalender tetap: periode ke-i = [EPOCH + 14*i, EPOCH + 14*(i+1)), sehingga cache dan
riwayat peringatan konsisten antar-putaran. Periode terakhir = periode lengkap terakhir sebelum
``hari ini - latency_days`` (atau ``end_date`` untuk uji historis).
"""

from __future__ import annotations

import datetime as dt
import math
import time
from pathlib import Path

import numpy as np

from .environment import Scene
from .region import Region

NODATA = -9999.0
BANDS = ("ndvi", "fire")
S2 = "COPERNICUS/S2_SR_HARMONIZED"
CLOUD_SCORE = "GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED"
WORLDCOVER = "ESA/WorldCover/v200"
FOREST_CLASSES = (10, 95)  # tutupan pohon, mangrove
VIIRS_FIRE = ("NASA/LANCE/SNPP_VIIRS/C2", "NASA/LANCE/NOAA20_VIIRS/C2")
EPOCH = dt.date(2015, 6, 29)  # Senin, awal era Sentinel-2
M_PER_DEG = 111_320.0


def decode_planes(arr, names, shape) -> dict[str, np.ndarray]:
    """Keluaran computePixels (larik terstruktur atau (H, W, B)) -> bidang per band, NODATA -> NaN."""
    if getattr(arr, "dtype", None) is not None and arr.dtype.names:
        planes = [np.asarray(arr[n], dtype=float) for n in names]
    else:
        a = np.asarray(arr, dtype=float)
        if a.ndim != 3 or a.shape[-1] < len(names):
            raise ValueError(f"bentuk keluaran GEE tidak dikenali: {a.shape}")
        planes = [a[..., i] for i in range(len(names))]
    out = {}
    for n, p in zip(names, planes):
        if p.shape != tuple(shape):
            raise ValueError(f"ukuran {n} {p.shape}, diharapkan {tuple(shape)}")
        out[n] = np.where(p <= NODATA + 0.5, np.nan, p).astype(np.float32)
    return out


class SentinelEnvironment:
    def __init__(
        self,
        region: Region,
        project: str | None = None,
        end_date: str | dt.date | None = None,
        n_periods: int = 4,
        period_days: int = 14,
        latency_days: int = 3,
        pixel_m: float = 30.0,
        cache_dir: str | Path | None = "pantau_cache",
        forest_only: bool = True,
        cloud_threshold: float = 0.6,
        fire_collections: tuple[str, ...] = VIIRS_FIRE,
        tile_px: int = 1024,
        retries: int = 3,
        max_failures: int = 3,
        today: dt.date | None = None,
    ):
        self.region = region
        self.project = project
        self.period_days = period_days
        self.n_periods = n_periods
        self.pixel_m = pixel_m
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.forest_only = forest_only
        self.cloud_threshold = cloud_threshold
        self.fire_collections = tuple(fire_collections)
        self.tile_px = tile_px
        self.retries = retries
        self.max_failures = max_failures

        if isinstance(end_date, str):
            end_date = dt.date.fromisoformat(end_date)
        end = end_date or (today or dt.date.today()) - dt.timedelta(latency_days)
        self.end_date = end
        complete = (end - EPOCH).days // period_days  # jumlah periode yang sudah lengkap
        self.last_period = complete - 1
        self.first_period = self.last_period - n_periods + 1

        # Grid EPSG:4326 menutupi kotak batas wilayah (+1 piksel)
        self.cell_deg = pixel_m / M_PER_DEG
        lon_min, lat_min, lon_max, lat_max = region.bbox
        self.lon0 = lon_min - self.cell_deg
        self.lat0 = lat_max + self.cell_deg
        width = int(math.ceil((lon_max - lon_min) / self.cell_deg)) + 2
        height = int(math.ceil((lat_max - lat_min) / self.cell_deg)) + 2
        self.shape = (height, width)
        self.size = height  # jumlah baris (dipakai untuk membagi wilayah antar detektor)
        self.region_mask = region.rasterize(self.lon0, self.lat0, self.cell_deg, self.shape)
        lat_c = (lat_min + lat_max) / 2
        self.ha_per_px = pixel_m * pixel_m * math.cos(math.radians(lat_c)) / 10_000

        self.day = 0
        self.events: list = []
        self.cloud_log: list = []
        self.errors: list[str] = []
        self._ee = None
        self._mem: dict[int, dict[str, np.ndarray]] = {}
        self._failures: dict[int, int] = {}
        self._nan = np.full(self.shape, np.nan, dtype=np.float32)
        self._nan.setflags(write=False)

    # ------------------------------------------------------------- periode
    def period_index(self, day: int) -> int:
        return self.first_period + day - 1

    def period_of(self, day: int) -> tuple[dt.date, dt.date]:
        """(tanggal mulai, tanggal akhir eksklusif) periode untuk langkah ``day``."""
        start = EPOCH + dt.timedelta(days=self.period_days * self.period_index(day))
        return start, start + dt.timedelta(days=self.period_days)

    def date_of(self, day: int) -> str:
        return self.period_of(day)[0].isoformat()

    def label_of(self, day: int) -> str:
        start, end = self.period_of(day)
        return f"{start.isoformat()} s.d. {(end - dt.timedelta(days=1)).isoformat()}"

    def advance_day(self) -> None:
        self.day += 1

    def to_latlon(self, r: float, c: float) -> tuple[float, float]:
        return (
            round(self.lat0 - (r + 0.5) * self.cell_deg, 5),
            round(self.lon0 + (c + 0.5) * self.cell_deg, 5),
        )

    # ---------------------------------------------------------- koneksi GEE
    def connect(self):
        if self._ee is None:
            try:
                import ee
            except ImportError as exc:
                raise RuntimeError("Pustaka GEE belum terpasang. Jalankan: pip install earthengine-api") from exc
            ee.Initialize(project=self.project) if self.project else ee.Initialize()
            self._ee = ee
        return self._ee

    def _geometry(self, ee):
        h, w = self.shape
        return ee.Geometry.Rectangle(
            [self.lon0, self.lat0 - h * self.cell_deg, self.lon0 + w * self.cell_deg, self.lat0], None, False
        )

    def _build_period_image(self, ee, start: str, end: str):
        geom = self._geometry(ee)
        empty = lambda name: ee.Image.constant(0).selfMask().rename(name)  # noqa: E731 - seluruhnya tertutup
        threshold = self.cloud_threshold

        def ndvi_of(img):
            clear = img.select("cs_cdf").gte(threshold)
            return img.normalizedDifference(["B8", "B4"]).rename("ndvi").updateMask(clear)

        s2 = (
            ee.ImageCollection(S2).filterBounds(geom).filterDate(start, end)
            .linkCollection(ee.ImageCollection(CLOUD_SCORE), ["cs_cdf"])
            .map(ndvi_of)
        )
        ndvi = ee.Image(ee.Algorithms.If(s2.size().gt(0), s2.median(), empty("ndvi"))).rename("ndvi")
        if self.forest_only:
            cover = ee.ImageCollection(WORLDCOVER).first().select("Map")
            forest = cover.eq(FOREST_CLASSES[0])
            for cls in FOREST_CLASSES[1:]:
                forest = forest.Or(cover.eq(cls))
            ndvi = ndvi.updateMask(forest)

        fires = ee.ImageCollection(self.fire_collections[0])
        for cid in self.fire_collections[1:]:
            fires = fires.merge(ee.ImageCollection(cid))
        fires = fires.filterDate(start, end).map(lambda img: img.select("confidence").gte(1).rename("fire"))
        fire = ee.Image(ee.Algorithms.If(fires.size().gt(0), fires.max().unmask(0), empty("fire"))).rename("fire")

        return ndvi.addBands(fire).toFloat().unmask(NODATA)

    def _tiles(self):
        h, w = self.shape
        for ty in range(0, h, self.tile_px):
            for tx in range(0, w, self.tile_px):
                yield ty, tx, min(self.tile_px, h - ty), min(self.tile_px, w - tx)

    def _tile_grid(self, ty, tx, th, tw) -> dict:
        return {
            "dimensions": {"width": tw, "height": th},
            "affineTransform": {
                "scaleX": self.cell_deg, "shearX": 0, "translateX": self.lon0 + tx * self.cell_deg,
                "shearY": 0, "scaleY": -self.cell_deg, "translateY": self.lat0 - ty * self.cell_deg,
            },
            "crsCode": "EPSG:4326",
        }

    def _request_period(self, day: int, progress=None) -> dict[str, np.ndarray] | None:
        """Ambil satu periode (per ubin, lalu disatukan). None bila gagal (alasannya di ``errors``)."""
        ee = self.connect()
        start, end = (d.isoformat() for d in self.period_of(day))
        try:
            image = self._build_period_image(ee, start, end)
        except Exception as exc:  # noqa: BLE001
            self.errors.append(f"{start}: {type(exc).__name__}: {exc}")
            return None
        out = {b: np.full(self.shape, np.nan, dtype=np.float32) for b in BANDS}
        tiles = list(self._tiles())
        for i, (ty, tx, th, tw) in enumerate(tiles, 1):
            if progress:
                progress(f"periode {self.label_of(day)}: ubin {i}/{len(tiles)}")
            request = {"expression": image, "fileFormat": "NUMPY_NDARRAY", "grid": self._tile_grid(ty, tx, th, tw)}
            last = None
            for attempt in range(self.retries):
                try:
                    planes = decode_planes(ee.data.computePixels(request), BANDS, (th, tw))
                    break
                except Exception as exc:  # noqa: BLE001 - EEException, kuota, jaringan
                    last = exc
                    time.sleep(min(2 ** attempt, 8))
            else:
                self.errors.append(f"{start} ubin {i}: {type(last).__name__}: {last}")
                return None
            for b in BANDS:
                out[b][ty:ty + th, tx:tx + tw] = planes[b]
        return out

    # ------------------------------------------------------ cache & pemuatan
    def _cache_path(self, day: int) -> Path | None:
        if self.cache_dir is None:
            return None
        start = self.date_of(day)
        flags = f"{self.pixel_m:g}m_{'hutan' if self.forest_only else 'semua'}_cs{self.cloud_threshold:g}"
        return self.cache_dir / self.region.slug / f"{start}_{self.period_days}h_{flags}.npz"

    def _load(self, day: int, progress=None) -> dict[str, np.ndarray] | None:
        if day in self._mem:
            return self._mem[day]
        if not 1 <= day <= self.n_periods or self._failures.get(day, 0) >= self.max_failures:
            return None
        path = self._cache_path(day)
        if path is not None and path.exists():
            with np.load(path) as z:
                data = {b: z[b] for b in BANDS}
        else:
            data = self._request_period(day, progress)
            if data is None:
                self._failures[day] = self._failures.get(day, 0) + 1
                return None
            if path is not None:
                path.parent.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(path, **data)
        outside = ~self.region_mask
        data = {b: np.where(outside, np.nan, a).astype(np.float32) for b, a in data.items()}
        self._mem[day] = data
        return data

    def prefetch(self, progress=None) -> list[tuple[int, bool]]:
        """Unduh semua periode di jendela (dengan pesan kemajuan). Mengembalikan (langkah, berhasil)."""
        return [(d, self._load(d, progress) is not None) for d in range(1, self.n_periods + 1)]

    # --------------------------------------------------- antarmuka untuk agen
    def available_days(self) -> list[int]:
        return list(range(1, min(self.day, self.n_periods) + 1))

    def _get(self, day: int, key: str) -> np.ndarray | None:
        if day not in self.available_days():
            return None
        data = self._load(day)
        return None if data is None else data[key]

    def download(self, day: int) -> Scene | None:
        ndvi = self._get(day, "ndvi")
        return None if ndvi is None else Scene(day=day, ndvi=ndvi)

    def fetch_thermal(self, day: int) -> np.ndarray | None:
        return self._nan if day in self.available_days() else None  # suhu tidak dipakai

    def fetch_fire(self, day: int) -> np.ndarray | None:
        return self._get(day, "fire")

    # ------------------------------------------------------- ringkasan & status
    def coverage(self, day: int) -> dict:
        """Ringkasan satu periode di dalam wilayah: luas hutan teramati bebas awan dan titik api."""
        data = self._mem.get(day)
        if data is None:
            return {"ok": False}
        inside = self.region_mask
        fire = data["fire"][inside]
        return {
            "ok": True,
            "clear_ha": float(np.isfinite(data["ndvi"][inside]).sum() * self.ha_per_px),
            "fire_data": bool(np.isfinite(fire).any()),
            "fire_px": int(np.nansum(fire > 0.5)),
        }

    def status(self, lookback_days: int = 60, today: dt.date | None = None) -> dict[str, str | None]:
        """Tanggal citra terbaru tiap sumber data di atas wilayah ini (untuk memastikan data masih mengalir)."""
        ee = self.connect()
        today = today or dt.date.today()
        start = (today - dt.timedelta(days=lookback_days)).isoformat()
        end = (today + dt.timedelta(days=1)).isoformat()
        geom = self._geometry(ee)
        out = {}
        for cid in (S2, CLOUD_SCORE, *self.fire_collections):
            col = ee.ImageCollection(cid).filterDate(start, end)
            if cid in (S2, CLOUD_SCORE):
                col = col.filterBounds(geom)
            try:
                ms = col.aggregate_max("system:time_start").getInfo()
                out[cid] = dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).date().isoformat() if ms else None
            except Exception as exc:  # noqa: BLE001
                out[cid] = f"GAGAL: {type(exc).__name__}: {exc}"
        return out
