"""Batas wilayah administrasi (kecamatan) dari GeoJSON dan rasterisasinya ke grid pemantauan."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

NAME_KEYS = ("kecamatan", "KECAMATAN", "NAMOBJ", "WADMKC", "nama", "NAMA", "name", "NAME")


class Region:
    """Satu wilayah: daftar poligon, tiap poligon = [cincin luar, lubang, ...], titik (bujur, lintang)."""

    def __init__(self, name: str, polygons: list, properties: dict | None = None):
        self.name = name
        self.polygons = polygons
        self.properties = properties or {}

    @property
    def slug(self) -> str:
        return re.sub(r"[^a-z0-9]+", "_", self.name.lower()).strip("_")

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        xs = [p[0] for poly in self.polygons for ring in poly for p in ring]
        ys = [p[1] for poly in self.polygons for ring in poly for p in ring]
        return min(xs), min(ys), max(xs), max(ys)

    @property
    def area_km2(self) -> float:
        def ring_area(ring):
            lat0 = math.radians(sum(p[1] for p in ring) / len(ring))
            xs = [p[0] * 111.32 * math.cos(lat0) for p in ring]
            ys = [p[1] * 111.32 for p in ring]
            return abs(sum(xs[i] * ys[i + 1] - xs[i + 1] * ys[i] for i in range(len(ring) - 1))) / 2

        return sum(ring_area(poly[0]) - sum(ring_area(h) for h in poly[1:]) for poly in self.polygons)

    def rasterize(self, lon0: float, lat0: float, cell_deg: float, shape: tuple[int, int]) -> np.ndarray:
        """Masker boolean (H, W): True untuk piksel di dalam wilayah. (lon0, lat0) = pojok kiri-atas grid."""
        h, w = shape
        img = Image.new("1", (w, h), 0)
        draw = ImageDraw.Draw(img)

        def to_px(ring):
            return [((x - lon0) / cell_deg, (lat0 - y) / cell_deg) for x, y in ring]

        for poly in self.polygons:
            if len(poly[0]) >= 3:
                draw.polygon(to_px(poly[0]), fill=1)
        for poly in self.polygons:  # lubang dikosongkan setelah semua cincin luar digambar
            for hole in poly[1:]:
                if len(hole) >= 3:
                    draw.polygon(to_px(hole), fill=0)
        return np.array(img, dtype=bool)


def _polygons(geometry: dict) -> list:
    kind, coords = geometry["type"], geometry["coordinates"]
    polys = [coords] if kind == "Polygon" else coords if kind == "MultiPolygon" else None
    if polys is None:
        raise ValueError(f"geometri {kind} tidak didukung (hanya Polygon/MultiPolygon)")
    return [[[(float(p[0]), float(p[1])) for p in ring] for ring in poly] for poly in polys]


def load_regions(path: str | Path) -> list[Region]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    crs = (data.get("crs") or {}).get("properties", {}).get("name", "")
    if crs and not any(k in crs.upper() for k in ("CRS84", "4326")):
        raise ValueError(f"CRS {crs} tidak didukung; ekspor ulang GeoJSON dalam WGS84 (EPSG:4326)")
    regions = []
    for i, feat in enumerate(data["features"]):
        props = feat.get("properties") or {}
        name = next((str(props[k]) for k in NAME_KEYS if props.get(k)), f"wilayah_{i + 1}")
        name = re.sub(r"^kecamatan\s+", "", name, flags=re.I).strip()
        regions.append(Region(name, _polygons(feat["geometry"]), props))
    return regions


def find_region(regions: list[Region], query: str) -> Region:
    """Cari berdasarkan nama (tidak peka huruf besar, awalan 'Kecamatan' boleh). Nama persis didahulukan."""
    q = re.sub(r"^kecamatan\s+", "", query.strip(), flags=re.I).lower()
    exact = [r for r in regions if r.name.lower() == q]
    if exact:
        return exact[0]
    partial = [r for r in regions if q in r.name.lower()]
    if len(partial) == 1:
        return partial[0]
    names = ", ".join(r.name for r in (partial or regions))
    if partial:
        raise ValueError(f"'{query}' cocok dengan beberapa kecamatan: {names}. Tulis lebih lengkap.")
    raise ValueError(f"kecamatan '{query}' tidak ditemukan. Pilihan: {names}")
