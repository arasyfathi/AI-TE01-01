"""Lingkungan pemantauan per periode (bawaan 2 minggu) untuk satu wilayah, dari Google Earth Engine.

Satu langkah Mesa = satu periode. Data yang diambil:

  ndvi      : komposit median NDVI Sentinel-2 per periode (COPERNICUS/S2_SR_HARMONIZED); piksel berawan
              dibuang memakai Cloud Score+ (GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED, cs_cdf >= ambang).
  fire      : 1 = ada titik api VIIRS (keyakinan nominal/tinggi) dalam periode itu, 0 = tidak ada,
              NaN = tidak ada data titik api untuk periode itu. Dipakai Agen Validasi.
  landcover : peta statis 1 = hutan alam, 2 = kebun sawit, 3 = lahan lain.
              Hutan alam = hutan menurut JRC GFC2020 V4 (definisinya mengecualikan perkebunan
              komoditas termasuk sawit) dan bukan sawit menurut BIOPAMA Global Oil Palm v1.2.
              Bila ``forest_only``, NDVI hanya dipantau di hutan alam: pembukaan/peremajaan kebun
              sawit bukan deforestasi.
  hotspots  : titik api VIIRS per sel ~375 m (jumlah deteksi, hari pertama/terakhir, FRP maks.) untuk
              Agen Titik Api. Jendela langkah terakhir diperpanjang sampai hari ini (peringatan dini).

Piksel di luar poligon wilayah diberi NaN. Suhu permukaan tidak dipakai (selalu NaN).

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
HOTSPOT_BANDS = ("count", "first", "last", "frp")
S2 = "COPERNICUS/S2_SR_HARMONIZED"
CLOUD_SCORE = "GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED"
JRC_FOREST = "JRC/GFC2020/V4"
OIL_PALM = "BIOPAMA/GlobalOilPalm/v1_2"
VIIRS_FIRE = ("NASA/LANCE/SNPP_VIIRS/C2", "NASA/LANCE/NOAA20_VIIRS/C2")
FOREST, PALM, OTHER = 1, 2, 3
LANDCOVER_NAMES = {FOREST: "hutan", PALM: "sawit", OTHER: "lahan lain"}
EPOCH = dt.date(2015, 6, 29)  # Senin, awal era Sentinel-2
M_PER_DEG = 111_320.0
VIIRS_M = 375.0


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
        # "sekarang": batas akhir data titik api (peringatan dini). Uji historis: end_date + latensi.
        self.now = today or ((end_date + dt.timedelta(latency_days)) if end_date else dt.date.today())
        end = end_date or self.now - dt.timedelta(latency_days)
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

        # Grid titik api: blok k x k piksel utama (~375 m), pojok kiri-atas sama
        self.hs_block = max(1, round(VIIRS_M / pixel_m))
        self.hs_shape = (math.ceil(height / self.hs_block), math.ceil(width / self.hs_block))
        self.hs_region = self._block_reduce(self.region_mask.astype(float), np.nanmax) > 0

        self.day = 0
        self.events: list = []
        self.cloud_log: list = []
        self.errors: list[str] = []
        self._ee = None
        self._mem: dict[int, dict[str, np.ndarray]] = {}
        self._hs_mem: dict[tuple[str, str], dict[str, np.ndarray]] = {}
        self._failures: dict = {}
        self._landcover: np.ndarray | None = None
        self._hs_landcover: tuple[np.ndarray, np.ndarray] | None = None
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

    def hotspot_window(self, day: int) -> tuple[dt.date, dt.date]:
        """Jendela titik api untuk langkah ``day``; langkah terakhir diperpanjang sampai hari ini."""
        start, end = self.period_of(day)
        if day == self.n_periods:
            end = max(end, self.now + dt.timedelta(days=1))
        return start, end

    def advance_day(self) -> None:
        self.day += 1

    def to_latlon(self, r: float, c: float) -> tuple[float, float]:
        return (
            round(self.lat0 - (r + 0.5) * self.cell_deg, 5),
            round(self.lon0 + (c + 0.5) * self.cell_deg, 5),
        )

    def hs_to_latlon(self, hr: float, hc: float) -> tuple[float, float]:
        k = self.hs_block
        return self.to_latlon((hr + 0.5) * k - 0.5, (hc + 0.5) * k - 0.5)

    def hs_box(self, hr: int, hc: int) -> tuple[slice, slice]:
        """Potongan grid utama yang ditutup satu sel titik api."""
        k = self.hs_block
        return slice(hr * k, (hr + 1) * k), slice(hc * k, (hc + 1) * k)

    def _block_reduce(self, a: np.ndarray, func) -> np.ndarray:
        k = self.hs_block
        hh, ww = self.hs_shape
        padded = np.full((hh * k, ww * k), np.nan)
        padded[: a.shape[0], : a.shape[1]] = a
        blocks = padded.reshape(hh, k, ww, k).swapaxes(1, 2).reshape(hh, ww, k * k)
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            return func(blocks, axis=2)

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

    def _fire_collection(self, ee, start, end):
        fires = ee.ImageCollection(self.fire_collections[0])
        for cid in self.fire_collections[1:]:
            fires = fires.merge(ee.ImageCollection(cid))
        return fires.filterDate(start, end)

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
        fires = self._fire_collection(ee, start, end).map(
            lambda img: img.select("confidence").gte(1).rename("fire")
        )
        fire = ee.Image(ee.Algorithms.If(fires.size().gt(0), fires.max().unmask(0), empty("fire"))).rename("fire")
        return ndvi.addBands(fire).toFloat().unmask(NODATA)

    def _build_landcover_image(self, ee):
        forest = ee.Image(JRC_FOREST).select("Map").unmask(0).eq(1)
        palm = ee.ImageCollection(OIL_PALM).select("classification").mosaic().unmask(0)
        landcover = ee.Image.constant(OTHER).where(forest, FOREST).where(palm.gte(1), PALM)
        return landcover.rename("landcover").toFloat().unmask(NODATA)

    def _build_hotspot_image(self, ee, start: str, end: str):
        start_d = ee.Date(start)

        def per_image(img):
            fire = img.select("confidence").gte(1)
            day = ee.Image(img.date().difference(start_d, "day")).toFloat().updateMask(fire)
            frp = img.select("frp").toFloat().updateMask(fire)
            return (fire.updateMask(fire).toFloat().rename("count")
                    .addBands(day.rename("first")).addBands(day.rename("last")).addBands(frp.rename("frp")))

        col = self._fire_collection(ee, start, end).map(per_image)
        stats = (col.select("count").sum().rename("count")
                 .addBands(col.select("first").min().rename("first"))
                 .addBands(col.select("last").max().rename("last"))
                 .addBands(col.select("frp").max().rename("frp")))
        empty = ee.Image.constant([0, 0, 0, 0]).selfMask().rename(list(HOTSPOT_BANDS))
        image = ee.Image(ee.Algorithms.If(col.size().gt(0), stats, empty)).rename(list(HOTSPOT_BANDS))
        return image.toFloat().unmask(NODATA)

    def _tiles(self):
        h, w = self.shape
        for ty in range(0, h, self.tile_px):
            for tx in range(0, w, self.tile_px):
                yield ty, tx, min(self.tile_px, h - ty), min(self.tile_px, w - tx)

    def _tile_grid(self, ty, tx, th, tw, cell=None) -> dict:
        cell = cell or self.cell_deg
        return {
            "dimensions": {"width": tw, "height": th},
            "affineTransform": {
                "scaleX": cell, "shearX": 0, "translateX": self.lon0 + tx * cell,
                "shearY": 0, "scaleY": -cell, "translateY": self.lat0 - ty * cell,
            },
            "crsCode": "EPSG:4326",
        }

    def _compute(self, ee, request, names, shape):
        last = None
        for attempt in range(self.retries):
            try:
                return decode_planes(ee.data.computePixels(request), names, shape)
            except Exception as exc:  # noqa: BLE001 - EEException, kuota, jaringan
                last = exc
                time.sleep(min(2 ** attempt, 8))
        raise RuntimeError(f"{type(last).__name__}: {last}")

    def _fetch_tiles(self, image, names, label, progress=None) -> dict[str, np.ndarray] | None:
        ee = self.connect()
        out = {b: np.full(self.shape, np.nan, dtype=np.float32) for b in names}
        tiles = list(self._tiles())
        for i, (ty, tx, th, tw) in enumerate(tiles, 1):
            if progress:
                progress(f"{label}: ubin {i}/{len(tiles)}")
            request = {"expression": image, "fileFormat": "NUMPY_NDARRAY", "grid": self._tile_grid(ty, tx, th, tw)}
            try:
                planes = self._compute(ee, request, names, (th, tw))
            except RuntimeError as exc:
                self.errors.append(f"{label} ubin {i}: {exc}")
                return None
            for b in names:
                out[b][ty:ty + th, tx:tx + tw] = planes[b]
        return out

    def _request_period(self, day: int, progress=None) -> dict[str, np.ndarray] | None:
        """Ambil satu periode (per ubin, lalu disatukan). None bila gagal (alasannya di ``errors``)."""
        ee = self.connect()
        start, end = (d.isoformat() for d in self.period_of(day))
        try:
            image = self._build_period_image(ee, start, end)
        except Exception as exc:  # noqa: BLE001
            self.errors.append(f"{start}: {type(exc).__name__}: {exc}")
            return None
        return self._fetch_tiles(image, BANDS, f"periode {self.label_of(day)}", progress)

    def _request_landcover(self, progress=None) -> dict[str, np.ndarray] | None:
        ee = self.connect()
        try:
            image = self._build_landcover_image(ee)
        except Exception as exc:  # noqa: BLE001
            self.errors.append(f"tutupan lahan: {type(exc).__name__}: {exc}")
            return None
        return self._fetch_tiles(image, ("landcover",), "peta tutupan lahan", progress)

    def _request_hotspots(self, start: str, end: str) -> dict[str, np.ndarray] | None:
        ee = self.connect()
        hh, ww = self.hs_shape
        request = {
            "expression": self._build_hotspot_image(ee, start, end),
            "fileFormat": "NUMPY_NDARRAY",
            "grid": self._tile_grid(0, 0, hh, ww, cell=self.cell_deg * self.hs_block),
        }
        try:
            return self._compute(ee, request, HOTSPOT_BANDS, (hh, ww))
        except Exception as exc:  # noqa: BLE001
            self.errors.append(f"titik api {start}..{end}: {exc}")
            return None

    # ------------------------------------------------------ cache & pemuatan
    def _cache_file(self, name: str) -> Path | None:
        if self.cache_dir is None:
            return None
        return self.cache_dir / self.region.slug / name

    def _cached(self, key, name, request):
        """Muat dari cache npz, atau minta ke GEE lalu simpan. Mencatat kegagalan per ``key``."""
        if self._failures.get(key, 0) >= self.max_failures:
            return None
        path = self._cache_file(name)
        if path is not None and path.exists():
            with np.load(path) as z:
                return {b: z[b] for b in z.files}
        data = request()
        if data is None:
            self._failures[key] = self._failures.get(key, 0) + 1
            return None
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(path, **data)
        return data

    def landcover(self, progress=None) -> np.ndarray | None:
        """Peta tutupan lahan (1 hutan alam, 2 sawit, 3 lahan lain; NaN di luar wilayah)."""
        if self._landcover is None:
            data = self._cached("landcover", f"tutupan_lahan_{self.pixel_m:g}m.npz",
                                lambda: self._request_landcover(progress))
            if data is None:
                return None
            self._landcover = np.where(self.region_mask, data["landcover"], np.nan).astype(np.float32)
        return self._landcover

    def hotspot_landcover(self) -> tuple[np.ndarray, np.ndarray] | None:
        """Porsi hutan alam dan sawit di tiap sel titik api."""
        if self._hs_landcover is None:
            lc = self.landcover()
            if lc is None:
                return None
            forest = self._block_reduce(np.where(np.isfinite(lc), (lc == FOREST).astype(float), np.nan), np.nanmean)
            palm = self._block_reduce(np.where(np.isfinite(lc), (lc == PALM).astype(float), np.nan), np.nanmean)
            self._hs_landcover = (np.nan_to_num(forest), np.nan_to_num(palm))
        return self._hs_landcover

    def _load(self, day: int, progress=None) -> dict[str, np.ndarray] | None:
        if day in self._mem:
            return self._mem[day]
        if not 1 <= day <= self.n_periods:
            return None
        lc = self.landcover(progress)
        if lc is None:
            return None
        name = f"{self.date_of(day)}_{self.period_days}h_{self.pixel_m:g}m_cs{self.cloud_threshold:g}.npz"
        data = self._cached(("period", day), name, lambda: self._request_period(day, progress))
        if data is None:
            return None
        outside = ~self.region_mask
        ndvi = np.where(outside, np.nan, data["ndvi"])
        if self.forest_only:
            ndvi = np.where(lc == FOREST, ndvi, np.nan)  # kebun sawit & lahan lain tidak dipantau NDVI-nya
        data = {"ndvi": ndvi.astype(np.float32), "fire": np.where(outside, np.nan, data["fire"]).astype(np.float32)}
        self._mem[day] = data
        return data

    def fetch_hotspots(self, day: int, progress=None) -> dict[str, np.ndarray] | None:
        """Titik api per sel ~375 m dalam jendela langkah ``day``: count, first/last (hari sejak awal
        jendela), frp. Sel di luar wilayah diberi count 0."""
        if not 1 <= day <= self.n_periods:
            return None
        start, end = (d.isoformat() for d in self.hotspot_window(day))
        key = (start, end)
        if key not in self._hs_mem:
            if progress:
                progress(f"titik api {start} s.d. {end}")
            data = self._cached(("hotspot", key), f"titik_api_{start}_{end}_{self.hs_block}.npz",
                                lambda: self._request_hotspots(start, end))
            if data is None:
                return None
            count = np.nan_to_num(data["count"]) * self.hs_region
            self._hs_mem[key] = {"count": count, "first": data["first"], "last": data["last"], "frp": data["frp"]}
        return self._hs_mem[key]

    def prefetch(self, progress=None, hotspots_from: int | None = None) -> list[tuple[int, bool]]:
        """Unduh tutupan lahan, semua periode, dan (bila diminta) titik api mulai langkah ``hotspots_from``."""
        results = [(d, self._load(d, progress) is not None) for d in range(1, self.n_periods + 1)]
        if hotspots_from:
            for d in range(hotspots_from, self.n_periods + 1):
                self.fetch_hotspots(d, progress)
        return results

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
        """Ringkasan satu periode di dalam wilayah: hutan alam teramati bebas awan dan titik api."""
        data = self._mem.get(day)
        if data is None:
            return {"ok": False}
        inside = self.region_mask
        fire = data["fire"][inside]
        lc = self._landcover
        forest_ha = float(np.sum(lc == FOREST) * self.ha_per_px) if lc is not None else float("nan")
        return {
            "ok": True,
            "clear_ha": float(np.isfinite(data["ndvi"][inside]).sum() * self.ha_per_px),
            "forest_ha": forest_ha,
            "fire_data": bool(np.isfinite(fire).any()),
            "fire_px": int(np.nansum(fire > 0.5)),
        }

    def landcover_summary(self) -> dict[str, float]:
        lc = self._landcover
        if lc is None:
            return {}
        return {name: float(np.sum(lc == code) * self.ha_per_px) for code, name in LANDCOVER_NAMES.items()}

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
