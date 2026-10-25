"""Lingkungan data NYATA dari Google Earth Engine (citra harian MODIS).

Memenuhi antarmuka yang sama dengan ``ForestEnvironment`` sehingga agen tidak perlu diubah:
``advance_day()``, ``available_days()``, ``download(day)``, ``fetch_thermal(day)``,
``fetch_fire(day)``, ``to_latlon(r, c)``, serta atribut ``size``, ``day``, ``ha_per_px``.

Sumber data (semua harian, satu grid 4326 yang sama berukuran ``size`` x ``size`` piksel):

  ndvi : MODIS/061/MOD09GQ  (250 m)  NDVI dari sur_refl_b02 (NIR) dan sur_refl_b01 (merah)
         dimasker awan, bayangan awan, awan tipis (cirrus) tinggi, dan aerosol/asap tinggi memakai
         band ``state_1km`` dari MODIS/061/MOD09GA
  lst  : MODIS/061/MOD11A1  (1 km)   suhu permukaan siang (derajat C), kualitas "tidak ada LST" dimasker
  fire : MODIS/061/MOD14A1  (1 km)   1 = titik api (kelas 7-9), 0 = tanah tanpa api (kelas 5),
                                     NaN = awan / tidak diproses / air

Piksel tanpa data (awan, asap) diberi NaN. Agen sudah dibuat tahan terhadap NaN.

Catatan penting:
  * Mode "replay": hari ke-1 = ``start``. Data masa lalu dimainkan ulang hari demi hari seolah-olah
    baru masuk. ``latency_days`` menunda ketersediaan data (data MODIS di GEE biasanya terlambat beberapa hari).
  * Hasil unduhan disimpan di ``cache_dir`` (satu file per hari) agar percobaan ulang tidak memakai kuota GEE.
  * Resolusi berbeda dicocokkan ke grid 250 m dengan nearest-neighbour, jadi suhu dan titik api tampak berblok.
"""

from __future__ import annotations

import datetime as dt
import math
import time
from pathlib import Path

import numpy as np

from .environment import Scene

NODATA = -9999.0
BANDS = ("ndvi", "lst", "fire")
COLLECTIONS = {
    "sr250": "MODIS/061/MOD09GQ",
    "sr500": "MODIS/061/MOD09GA",
    "lst": "MODIS/061/MOD11A1",
    "fire": "MODIS/061/MOD14A1",
}
M_PER_DEG = 111_320.0


class GEEEnvironment:
    def __init__(
        self,
        project: str | None = None,
        center: tuple[float, float] = (-2.35, 114.00),
        start: str = "2023-08-15",
        n_days: int = 90,
        size: int = 40,
        pixel_m: float = 250.0,
        latency_days: int = 0,
        cache_dir: str | Path | None = "gee_cache",
        retries: int = 3,
        max_failures: int = 5,
        mask_haze: bool = True,
    ):
        self.project = project
        # True: piksel beraerosol/asap tinggi dan bercirrus tinggi ikut dibuang dari NDVI. Pada musim
        # kebakaran asap bisa menutup seluruh area; False mempertahankannya (NDVI sedikit lebih rendah).
        self.mask_haze = mask_haze
        self.center = center  # (lat, lon)
        self.start = dt.date.fromisoformat(start)
        self.n_days = n_days
        self.size = size
        self.pixel_m = pixel_m
        self.latency_days = latency_days
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.retries = retries
        self.max_failures = max_failures

        self.cell_deg = pixel_m / M_PER_DEG
        self.lat0 = center[0] + size * self.cell_deg / 2  # tepi utara grid
        self.lon0 = center[1] - size * self.cell_deg / 2  # tepi barat grid
        self.ha_per_px = (pixel_m * pixel_m * math.cos(math.radians(center[0]))) / 10_000

        self.day = 0
        self.events: list = []  # tidak ada ground truth pada data nyata
        self.cloud_log: list = []
        self.errors: list[str] = []
        self._ee = None
        self._dates: dict[str, set[str]] | None = None
        self._exists_cache: dict[tuple[str, str], bool] = {}
        self._mem: dict[int, dict[str, np.ndarray]] = {}
        self._failures: dict[int, int] = {}

    # ----------------------------------------------------------- waktu & lokasi
    def date_of(self, day: int) -> str:
        return (self.start + dt.timedelta(days=day - 1)).isoformat()

    def advance_day(self) -> None:
        self.day += 1

    def to_latlon(self, r: float, c: float) -> tuple[float, float]:
        return (
            round(self.lat0 - (r + 0.5) * self.cell_deg, 5),
            round(self.lon0 + (c + 0.5) * self.cell_deg, 5),
        )

    def _grid(self) -> dict:
        return {
            "dimensions": {"width": self.size, "height": self.size},
            "affineTransform": {
                "scaleX": self.cell_deg, "shearX": 0, "translateX": self.lon0,
                "shearY": 0, "scaleY": -self.cell_deg, "translateY": self.lat0,
            },
            "crsCode": "EPSG:4326",
        }

    # ------------------------------------------------------------ koneksi GEE
    def connect(self):
        if self._ee is None:
            try:
                import ee
            except ImportError as exc:
                raise RuntimeError("Pustaka GEE belum terpasang. Jalankan: pip install earthengine-api") from exc
            ee.Initialize(project=self.project) if self.project else ee.Initialize()
            self._ee = ee
        return self._ee

    def _list_dates(self) -> dict[str, set[str]]:
        """Tanggal yang memiliki citra pada tiap koleksi (satu panggilan per koleksi)."""
        ee = self.connect()
        start, end = self.date_of(1), self.date_of(self.n_days + 1)
        out = {}
        for key, cid in COLLECTIONS.items():
            ms = ee.ImageCollection(cid).filterDate(start, end).aggregate_array("system:time_start").getInfo()
            out[key] = {dt.datetime.fromtimestamp(m / 1000, dt.timezone.utc).strftime("%Y-%m-%d") for m in ms}
        return out

    @staticmethod
    def _state_flags(state) -> dict:
        """Bendera kualitas dari band ``state_1km`` MOD09GA (masing-masing citra 0/1)."""
        cloud_state = state.bitwiseAnd(3)  # 0 bersih, 1 berawan, 2 campuran, 3 tidak diatur (dianggap bersih)
        return {
            "awan": cloud_state.eq(1).Or(cloud_state.eq(2)),
            "bayangan_awan": state.rightShift(2).bitwiseAnd(1).eq(1),
            "awan_internal": state.rightShift(10).bitwiseAnd(1).eq(1),
            "aerosol_tinggi": state.rightShift(6).bitwiseAnd(3).eq(3),
            "cirrus_tinggi": state.rightShift(8).bitwiseAnd(3).eq(3),
        }

    def _day_images(self, ee, date: str):
        d0 = ee.Date(date)
        d1 = d0.advance(1, "day")

        def day_image(key):
            return ee.ImageCollection(COLLECTIONS[key]).filterDate(d0, d1).mosaic()

        if not (self._exists(ee, "sr250", date) and self._exists(ee, "sr500", date)):
            raise LookupError(
                f"tidak ada citra {COLLECTIONS['sr250']} / {COLLECTIONS['sr500']} pada {date} "
                "(data MODIS biasanya terlambat beberapa hari; coba tanggal yang lebih lama)"
            )
        return day_image

    def _build_image(self, ee, date: str):
        day_image = self._day_images(ee, date)
        empty = lambda name: ee.Image.constant(0).selfMask().rename(name)  # noqa: E731 - seluruhnya tertutup

        # NDVI 250 m + masker awan (dan bila diminta, asap/cirrus) dari state_1km
        gq, ga = day_image("sr250"), day_image("sr500")
        flags = self._state_flags(ga.select("state_1km"))
        bad = flags["awan"].Or(flags["bayangan_awan"]).Or(flags["awan_internal"])
        if self.mask_haze:
            bad = bad.Or(flags["aerosol_tinggi"]).Or(flags["cirrus_tinggi"])
        ndvi = gq.normalizedDifference(["sur_refl_b02", "sur_refl_b01"]).rename("ndvi")
        ndvi = ndvi.updateMask(bad.Not()).updateMask(ndvi.gte(-0.2).And(ndvi.lte(1)))

        # Suhu permukaan siang (K -> C), buang piksel "tidak ada LST" (awan)
        if self._exists(ee, "lst", date):
            m = day_image("lst")
            raw = m.select("LST_Day_1km")
            qc = m.select("QC_Day").bitwiseAnd(3)
            lst = raw.updateMask(raw.gte(7500)).updateMask(qc.lt(2)).multiply(0.02).subtract(273.15).rename("lst")
        else:
            lst = empty("lst")

        # Titik api: 1 = api (kelas 7-9), 0 = tanah tanpa api (kelas 5), selain itu tertutup
        if self._exists(ee, "fire", date):
            fm = day_image("fire").select("FireMask")
            fire = fm.gte(7).updateMask(fm.eq(5).Or(fm.gte(7))).rename("fire")
        else:
            fire = empty("fire")

        return ndvi.addBands(lst).addBands(fire).toFloat().unmask(NODATA)

    def _exists(self, ee, key: str, date: str) -> bool:
        """Apakah koleksi ``key`` punya citra pada ``date``? Memakai daftar replay bila tanggalnya
        termasuk di dalamnya; jika tidak (misalnya mode --check), bertanya ke GEE dan menyimpan jawabannya."""
        if self._dates is not None and self.date_of(1) <= date <= self.date_of(self.n_days):
            return date in self._dates[key]
        cache_key = (key, date)
        if cache_key not in self._exists_cache:
            d0 = ee.Date(date)
            n = ee.ImageCollection(COLLECTIONS[key]).filterDate(d0, d0.advance(1, "day")).size().getInfo()
            self._exists_cache[cache_key] = n > 0
        return self._exists_cache[cache_key]

    def _request_pixels(self, date: str) -> dict[str, np.ndarray] | None:
        """Satu permintaan ke GEE untuk satu hari. Mengembalikan None bila gagal (alasannya di ``errors``)."""
        ee = self.connect()
        try:
            request = {
                "expression": self._build_image(ee, date),
                "fileFormat": "NUMPY_NDARRAY",
                "grid": self._grid(),
            }
        except Exception as exc:  # noqa: BLE001 - tanggal tanpa data, jaringan saat mengecek koleksi
            self.errors.append(f"{date}: {type(exc).__name__}: {exc}")
            return None
        last = None
        for attempt in range(self.retries):
            try:
                return self._decode(ee.data.computePixels(request))
            except Exception as exc:  # noqa: BLE001 - EEException, HTTP 429, jaringan, autentikasi
                last = exc
                time.sleep(min(2 ** attempt, 8))
        self.errors.append(f"{date}: {type(last).__name__}: {last}")
        return None

    def _decode(self, arr, names=BANDS) -> dict[str, np.ndarray]:
        """Ubah keluaran computePixels (larik terstruktur atau (H, W, B)) menjadi bidang per band, NODATA -> NaN."""
        if getattr(arr, "dtype", None) is not None and arr.dtype.names:
            planes = [np.asarray(arr[name], dtype=float) for name in names]
        else:
            a = np.asarray(arr, dtype=float)
            if a.ndim != 3 or a.shape[-1] < len(names):
                raise ValueError(f"bentuk keluaran GEE tidak dikenali: {a.shape}")
            planes = [a[..., i] for i in range(len(names))]
        out = {}
        for name, plane in zip(names, planes):
            if plane.shape != (self.size, self.size):
                raise ValueError(f"ukuran {name} {plane.shape}, diharapkan {(self.size, self.size)}")
            out[name] = np.where(plane <= NODATA + 0.5, np.nan, plane).astype(np.float32)
        return out

    # ------------------------------------------------------- cache & pemuatan
    def _cache_path(self, date: str) -> Path | None:
        if self.cache_dir is None:
            return None
        haze = "h1" if self.mask_haze else "h0"
        name = f"{self.center[0]:.4f}_{self.center[1]:.4f}_{self.size}_{self.pixel_m:g}_{haze}_{date}.npz"
        return self.cache_dir / name

    def _load(self, day: int) -> dict[str, np.ndarray] | None:
        if day in self._mem:
            return self._mem[day]
        if self._failures.get(day, 0) >= self.max_failures:
            return None
        date = self.date_of(day)
        path = self._cache_path(date)
        if path is not None and path.exists():
            with np.load(path) as z:
                data = {k: z[k] for k in BANDS}
        else:
            data = self._request_pixels(date)
            if data is None:
                self._failures[day] = self._failures.get(day, 0) + 1
                return None
            if path is not None:
                path.parent.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(path, **data)
        self._mem[day] = data
        return data

    # ---------------------------------------------------- antarmuka untuk agen
    def _available(self) -> list[int]:
        if self._dates is None:
            self._dates = self._list_dates()
        have = self._dates["sr250"] & self._dates["sr500"]
        last = min(self.day - self.latency_days, self.n_days)
        return [d for d in range(1, last + 1) if self.date_of(d) in have]

    def available_days(self) -> list[int]:
        return self._available()

    def _get(self, day: int, key: str) -> np.ndarray | None:
        if day not in self._available():
            return None
        data = self._load(day)
        return None if data is None else data[key]

    def download(self, day: int) -> Scene | None:
        ndvi = self._get(day, "ndvi")
        return None if ndvi is None else Scene(day=day, ndvi=ndvi)

    def fetch_thermal(self, day: int) -> np.ndarray | None:
        return self._get(day, "lst")

    def fetch_fire(self, day: int) -> np.ndarray | None:
        return self._get(day, "fire")

    # ------------------------------------------------------------ bantuan uji
    def observed_fire_days(self) -> list[str]:
        """Tanggal (yang sudah dimuat) saat MODIS mendeteksi titik api di area ini."""
        return [
            self.date_of(d) for d, data in sorted(self._mem.items())
            if np.nanmax(np.where(np.isfinite(data["fire"]), data["fire"], 0.0)) > 0.5
        ]

    def check(self, date: str | None = None) -> tuple[dict, dict[str, np.ndarray]]:
        """Uji satu hari: ambil data dan ringkas (dipakai ``run_gee.py --check``)."""
        data = self._request_pixels(date or self.date_of(1))
        if data is None:
            raise RuntimeError(self.errors[-1] if self.errors else "permintaan ke GEE gagal")
        stats = {}
        for key, a in data.items():
            ok = np.isfinite(a)
            stats[key] = {
                "valid_pct": round(100 * float(ok.mean()), 1),
                "min": float(a[ok].min()) if ok.any() else None,
                "max": float(a[ok].max()) if ok.any() else None,
                "mean": float(a[ok].mean()) if ok.any() else None,
            }
        return stats, data

    # ------------------------------------------------------------ diagnosis
    def _diagnostic_image(self, ee, date: str):
        day_image = self._day_images(ee, date)
        gq, ga = day_image("sr250"), day_image("sr500")
        empty = lambda name: ee.Image.constant(0).selfMask().rename(name)  # noqa: E731
        bands = [gq.select("sur_refl_b01").mask().gt(0).rename("ada_reflektansi")]
        bands += [img.rename(name) for name, img in self._state_flags(ga.select("state_1km")).items()]
        bands.append(
            day_image("lst").select("QC_Day").bitwiseAnd(3).rename("lst_qc")
            if self._exists(ee, "lst", date) else empty("lst_qc")
        )
        bands.append(
            day_image("fire").select("FireMask").rename("firemask")
            if self._exists(ee, "fire", date) else empty("firemask")
        )
        names = ("ada_reflektansi", *self.DIAG_FLAGS, "lst_qc", "firemask")
        return ee.Image.cat(bands).toFloat().unmask(NODATA), names

    DIAG_FLAGS = ("awan", "bayangan_awan", "awan_internal", "aerosol_tinggi", "cirrus_tinggi")

    def diagnose(self, date: str) -> dict:
        """Rincian alasan piksel terbuang pada satu hari: bendera state_1km, kelas QC suhu, kelas FireMask."""
        ee = self.connect()
        image, names = self._diagnostic_image(ee, date)
        arr = ee.data.computePixels({"expression": image, "fileFormat": "NUMPY_NDARRAY", "grid": self._grid()})
        planes = self._decode(arr, names)
        report = {}
        for name in names:
            a = planes[name]
            ok = np.isfinite(a)
            entry = {"tersedia_pct": round(100 * float(ok.mean()), 1)}
            if name in ("lst_qc", "firemask"):
                values, counts = np.unique(a[ok].astype(int), return_counts=True)
                entry["kelas_pct"] = {int(v): round(100 * c / ok.sum(), 1) for v, c in zip(values, counts)}
            else:
                entry["ya_pct"] = round(100 * float((a[ok] > 0.5).mean()), 1) if ok.any() else None
            report[name] = entry
        return report

    def scan(self, n_days: int | None = None):
        """Unduh (sekaligus mengisi cache) hari-hari pertama replay dan ringkas tiap hari.
        Menghasilkan (tanggal, ringkasan atau None, pesan error atau None)."""
        n = min(n_days or self.n_days, self.n_days)
        if self._dates is None:
            self._dates = self._list_dates()
        have = self._dates["sr250"] & self._dates["sr500"]
        for day in range(1, n + 1):
            date = self.date_of(day)
            if date not in have:
                yield date, None, "tidak ada citra MODIS"
                continue
            data = self._load(day)
            if data is None:
                yield date, None, self.errors[-1] if self.errors else "gagal"
                continue
            fire = data["fire"]
            yield date, {
                "ndvi_pct": round(100 * float(np.isfinite(data["ndvi"]).mean()), 1),
                "lst_pct": round(100 * float(np.isfinite(data["lst"]).mean()), 1),
                "fire_obs_pct": round(100 * float(np.isfinite(fire).mean()), 1),
                "fire_px": int(np.nansum(fire > 0.5)),
            }, None
