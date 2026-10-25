"""Lingkungan hutan sintetis yang meniru aliran data satelit.

Dua "sensor" disimulasikan:
  * optik (mirip Sentinel-2/Landsat) -> NDVI
  * termal (mirip MODIS LST)         -> suhu permukaan (derajat C)

Kejadian yang dibangkitkan (dengan ground truth untuk evaluasi):
  * logging : tebang liar, petak persegi panjang, NDVI turun permanen, sedikit lebih hangat
  * fire    : kebakaran, blob tidak beraturan yang menyebar, anomali termal besar lalu meluruh
  * cloud   : awan (decoy), NDVI turun sementara tetapi suhu justru turun

Awan sengaja dibuat sebagai pengecoh: dari citra optik saja ia tampak seperti
hilangnya tutupan hijau, sehingga Agen Validasi (termal) benar-benar dibutuhkan.

Ganti kelas ini dengan pembaca Google Earth Engine / MODIS untuk data nyata;
antarmuka yang dipakai agen hanya: available_days(), download(), fetch_thermal().
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

EIGHT = np.ones((3, 3), dtype=bool)
CROSS = ndimage.generate_binary_structure(2, 1)


def smooth_field(rng: np.random.Generator, size: int, sigma: float) -> np.ndarray:
    f = ndimage.gaussian_filter(rng.normal(size=(size, size)), sigma, mode="reflect")
    return (f - f.mean()) / (f.std() + 1e-9)


@dataclass
class Scene:
    day: int
    ndvi: np.ndarray


@dataclass
class TrueEvent:
    """Ground truth. Hanya dipakai evaluasi, tidak pernah dibaca agen."""

    kind: str  # "logging" | "fire"
    start_day: int
    footprint: np.ndarray
    peak_heat: float = 0.0
    spread_left: int = 0


class ForestEnvironment:
    def __init__(
        self,
        size: int = 64,
        seed: int | None = 0,
        p_logging: float = 0.10,
        p_fire: float = 0.06,
        p_cloud: float = 0.20,
        warmup_days: int = 7,
        download_fail_prob: float = 0.05,
        thermal_dropout_prob: float = 0.05,
        origin: tuple[float, float] = (-1.0, 113.0),
        cell_deg: float = 0.0009,
    ):
        env_ss, io_ss = np.random.SeedSequence(seed).spawn(2)
        self.rng = np.random.default_rng(env_ss)  # dunia
        self.io_rng = np.random.default_rng(io_ss)  # kegagalan unduh / data termal hilang
        self.size = size
        self.p_logging, self.p_fire, self.p_cloud = p_logging, p_fire, p_cloud
        self.warmup_days = warmup_days
        self.download_fail_prob = download_fail_prob
        self.thermal_dropout_prob = thermal_dropout_prob
        self.origin, self.cell_deg = origin, cell_deg

        self.base_ndvi = 0.80 + 0.04 * smooth_field(self.rng, size, 6)
        self.base_temp = 28.0 + 1.5 * smooth_field(self.rng, size, 8)
        self.veg_loss = np.zeros((size, size))
        self.static_heat = np.zeros((size, size))

        self.day = 0
        self.scenes: dict[int, Scene] = {}
        self.thermal: dict[int, np.ndarray] = {}
        self.events: list[TrueEvent] = []
        self.cloud_log: list[tuple[int, np.ndarray]] = []
        self._clouds: list[list] = []

    # ------------------------------------------------------------------ dunia
    def advance_day(self) -> None:
        s, d, rng = self.size, self.day + 1, self.rng
        self.day = d

        # Kejadian baru dibangkitkan lebih dulu agar panas hari pertama ikut terekam.
        if d > self.warmup_days:
            if rng.random() < self.p_logging:
                self._spawn_logging(d)
            if rng.random() < self.p_fire:
                self._spawn_fire(d)
            if rng.random() < self.p_cloud:
                self._spawn_cloud()

        fire_heat = np.zeros((s, s))
        for ev in self.events:
            if ev.kind != "fire":
                continue
            age = d - ev.start_day
            if age > 0 and ev.spread_left > 0:
                grown = ndimage.binary_dilation(ev.footprint, structure=EIGHT)
                new = (grown & (rng.random((s, s)) < 0.55)) | ev.footprint
                self._clear(new & ~ev.footprint)
                ev.footprint = new
                ev.spread_left -= 1
            if age <= 6:
                n = int(ev.footprint.sum())
                fire_heat[ev.footprint] += ev.peak_heat * np.exp(-age / 2.0) * rng.uniform(0.7, 1.0, n)

        cloud_mask = np.zeros((s, s), dtype=bool)
        for c in self._clouds:
            if c[1] > 0:
                cloud_mask |= c[0]
                c[1] -= 1
        self._clouds = [c for c in self._clouds if c[1] > 0]
        if cloud_mask.any():
            self.cloud_log.append((d, cloud_mask.copy()))

        season = 0.02 * np.sin(2 * np.pi * d / 90.0)
        ndvi = self.base_ndvi - self.veg_loss + season + rng.normal(0, 0.02, (s, s))
        ndvi[cloud_mask] -= rng.uniform(0.3, 0.5, int(cloud_mask.sum()))

        temp = self.base_temp + self.static_heat + fire_heat + 1.0 * np.sin(2 * np.pi * d / 30.0)
        temp[cloud_mask] -= 8.0 * rng.uniform(0.8, 1.2, int(cloud_mask.sum()))
        temp = temp + rng.normal(0, 0.7, (s, s))

        self.scenes[d] = Scene(day=d, ndvi=np.clip(ndvi, -0.1, 1.0))
        self.thermal[d] = temp

    def _clear(self, mask: np.ndarray) -> None:
        target = self.rng.uniform(0.15, 0.30, int(mask.sum()))
        self.veg_loss[mask] = np.maximum(self.veg_loss[mask], self.base_ndvi[mask] - target)
        self.static_heat[mask] += 2.0

    def _intact(self, mask: np.ndarray) -> bool:
        """Kejadian baru hanya di hutan utuh, dengan jarak 1 sel dari bekas kejadian lain."""
        buffered = ndimage.binary_dilation(mask, structure=EIGHT)
        return float(self.veg_loss[buffered].max()) < 0.05

    def _spawn_logging(self, d: int) -> None:
        s = self.size
        h, w = (int(x) for x in self.rng.integers(3, 9, size=2))
        r0, c0 = int(self.rng.integers(0, s - h + 1)), int(self.rng.integers(0, s - w + 1))
        mask = np.zeros((s, s), dtype=bool)
        mask[r0 : r0 + h, c0 : c0 + w] = True
        if not self._intact(mask):
            return
        self._clear(mask)
        self.events.append(TrueEvent("logging", d, mask))

    def _spawn_fire(self, d: int) -> None:
        s = self.size
        r, c = (int(x) for x in self.rng.integers(2, s - 2, size=2))
        seed = np.zeros((s, s), dtype=bool)
        seed[r, c] = True
        seed = ndimage.binary_dilation(seed, structure=CROSS)
        if not self._intact(seed):
            return
        self._clear(seed)
        self.events.append(
            TrueEvent("fire", d, seed, peak_heat=float(self.rng.uniform(18, 30)), spread_left=2)
        )

    def _spawn_cloud(self) -> None:
        s = self.size
        ry, rx = (float(x) for x in self.rng.uniform(3, 7, size=2))
        cy, cx = (float(x) for x in self.rng.uniform(0, s, size=2))
        yy, xx = np.ogrid[:s, :s]
        mask = ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2 <= 1.0
        if mask.sum() >= 4:
            self._clouds.append([mask, int(self.rng.integers(1, 3))])

    # ------------------------------------------- antarmuka "cloud storage"
    def available_days(self) -> list[int]:
        return sorted(self.scenes)

    def download(self, day: int) -> Scene | None:
        if self.io_rng.random() < self.download_fail_prob:
            return None
        return self.scenes[day]

    def fetch_thermal(self, day: int) -> np.ndarray | None:
        if self.io_rng.random() < self.thermal_dropout_prob:
            return None
        return self.thermal.get(day)

    def to_latlon(self, r: float, c: float) -> tuple[float, float]:
        return (
            round(float(self.origin[0] - r * self.cell_deg), 5),
            round(float(self.origin[1] + c * self.cell_deg), 5),
        )
