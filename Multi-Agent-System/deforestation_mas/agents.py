"""Agen-agen perangkat lunak dalam sistem pemantau deforestasi & kebakaran.

Alur kerja (satu langkah Mesa = satu hari):

  DataIngestionAgent  --INFORM new_scene-->  ChangeDetectionAgent
  ChangeDetectionAgent --REQUEST validate-->  ValidationAgent
  ValidationAgent      --PROPOSE verdict-->   ChangeDetectionAgent
  (konsensus tercapai)  --CONFIRM / CANCEL--> ValidationAgent
  ChangeDetectionAgent --INFORM report----->  NotificationAgent

Konsensus: kasus hanya dinyatakan nyata bila DUA bukti independen setuju.
  * suara detektor  = apakah hilangnya NDVI MENETAP pada citra berikutnya
                      (awan hanya sementara, tebangan/kebakaran permanen)
  * suara validator = apakah sinyal TERMAL cocok dengan kehilangan vegetasi
                      (panas sekali -> kebakaran, sedikit hangat -> tebangan,
                       lebih dingin -> awan / alarm palsu)
  Bila keduanya berbeda pendapat, dilakukan ronde ulang dengan data hari
  berikutnya. Setelah ``max_rounds`` tetap tidak sepakat, kasus diteruskan
  sebagai "uncertain" untuk ditinjau manusia.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import mesa
import numpy as np
from scipy import ndimage

from .environment import CROSS, EIGHT
from .messaging import CANCEL, CONFIRM, INFORM, PROPOSE, REQUEST, Message

PENDING, CONFIRMED, DISMISSED, UNCERTAIN = "pending", "confirmed", "dismissed", "uncertain"


def reference_window(day: int) -> range:
    """Hari-hari 'minggu lalu' yang dijadikan acuan: H-9 sampai H-5."""
    return range(day - 9, day - 4)


@dataclass
class Case:
    case_id: str
    detector: str
    validator: str | None
    day: int  # hari citra saat pertama terdeteksi
    mask: np.ndarray
    reference: np.ndarray  # komposit NDVI acuan saat terdeteksi
    drop: float  # rata-rata penurunan NDVI
    centroid: tuple[float, float]  # (lat, lon)
    status: str = PENDING
    det_vote: bool | None = None
    val_vote: bool | None = None
    val_received: bool = False
    cause: str | None = None
    val_confidence: float = 0.0
    evidence: dict = field(default_factory=dict)
    round: int = 0
    last_check_day: int = 0
    decided_day: int | None = None

    @property
    def area_px(self) -> int:
        return int(self.mask.sum())


class MonitorAgent(mesa.Agent):
    role = "agent"

    def __init__(self, model, name: str):
        super().__init__(model)
        self.name = name

    def send(self, performative, receiver, topic, content=None, conversation_id=None):
        self.model.bus.send(
            Message(performative, self.name, receiver, topic, content or {}, conversation_id, self.model.day)
        )

    def inbox(self) -> list[Message]:
        return self.model.bus.receive_all(self.name)


# ---------------------------------------------------------------------------
class DataIngestionAgent(MonitorAgent):
    """Memantau 'cloud storage' dan mengunduh citra baru begitu tersedia.
    Unduhan yang gagal dicoba ulang pada langkah berikutnya."""

    role = "ingestion"

    def __init__(self, model, name="ingestion", max_retries=5):
        super().__init__(model, name)
        self.max_retries = max_retries
        self.failures: dict[int, int] = {}
        self.gave_up: set[int] = set()
        self.downloaded = 0

    def step(self):
        env, archive = self.model.env, self.model.archive
        new_days = []
        for d in env.available_days():
            if d in archive or d in self.gave_up:
                continue
            scene = env.download(d)
            if scene is None:
                self.failures[d] = self.failures.get(d, 0) + 1
                if self.failures[d] >= self.max_retries:
                    self.gave_up.add(d)
                continue
            archive[d] = scene
            new_days.append(d)
            self.downloaded += 1
        if new_days:
            for det in self.model.detectors:
                self.send(INFORM, det.name, "new_scene", {"days": new_days})


# ---------------------------------------------------------------------------
class ChangeDetectionAgent(MonitorAgent):
    """Membandingkan citra hari ini dengan komposit citra minggu lalu untuk
    mencari area hijau yang hilang drastis. Tidak boleh menyimpulkan sendiri:
    setiap wilayah curiga dikirim ke Agen Validasi dan diputuskan lewat konsensus."""

    role = "detection"

    def __init__(
        self,
        model,
        name: str,
        rows: tuple[int, int],
        drop_threshold=0.20,
        persist_threshold=0.15,
        min_pixels=4,
        max_rounds=2,
        memory_days=10,
        fire_growth_days=5,
    ):
        super().__init__(model, name)
        self.rows = rows  # wilayah tanggung jawab (baris citra), untuk pembagian kerja
        self.drop_threshold = drop_threshold
        self.persist_threshold = persist_threshold
        self.min_pixels = min_pixels
        self.max_rounds = max_rounds
        self.memory_days = memory_days
        self.fire_growth_days = fire_growth_days
        self.queue: list[int] = []
        self._counter = 0

    # -- siklus utama --------------------------------------------------------
    def step(self):
        for msg in self.inbox():
            if msg.topic == "new_scene":
                self.queue.extend(msg.content["days"])
            elif msg.topic == "verdict":
                self._receive_verdict(msg)

        for day in sorted(set(self.queue)):
            self._check_persistence(day)
            self._detect(day)
        self.queue.clear()

        for case in self.my_cases(PENDING):
            self._try_resolve(case)

    def my_cases(self, status=None):
        return [
            c for c in self.model.cases.values()
            if c.detector == self.name and (status is None or c.status == status)
        ]

    # -- deteksi -------------------------------------------------------------
    def reference_composite(self, day: int) -> np.ndarray | None:
        stack = [self.model.archive[d].ndvi for d in reference_window(day) if d in self.model.archive]
        if len(stack) < 2:
            return None
        return np.median(np.stack(stack), axis=0)

    def _detect(self, day: int):
        ref = self.reference_composite(day)
        if ref is None:
            return
        diff = ref - self.model.archive[day].ndvi
        cand = ndimage.binary_opening(diff > self.drop_threshold, structure=CROSS)
        labels, n = ndimage.label(cand, structure=EIGHT)
        for lab in range(1, n + 1):
            region = labels == lab
            if region.sum() < self.min_pixels:
                continue
            r, c = ndimage.center_of_mass(region)
            if not (self.rows[0] <= r < self.rows[1]):
                continue  # milik detektor lain
            self._handle_region(day, region, ref, diff)

    def _handle_region(self, day, region, ref, diff):
        # Kasus lama hanya "menutupi" deteksi baru selama kehilangannya belum
        # masuk ke citra acuan (~10 hari). Setelah itu penurunan baru = kejadian baru.
        active = [
            c for c in self.model.cases.values()
            if c.status in (PENDING, CONFIRMED, UNCERTAIN)
            and day - c.day <= self.memory_days
            and (c.mask & region).any()
        ]
        if not active:
            self._open_case(day, region, ref, diff)
            return
        covered = np.zeros_like(region)
        for c in active:
            covered |= c.mask
        new_part = region & ~covered
        growable = [
            c for c in active
            if c.status == PENDING
            or (c.status == CONFIRMED and c.cause == "fire" and day - c.day <= self.fire_growth_days)
        ]
        if growable:
            target = max(growable, key=lambda c: int((c.mask & region).sum()))
            if new_part.sum() > 0:
                target.mask = target.mask | new_part
                if target.status == CONFIRMED and new_part.sum() >= 2:
                    self.send(
                        INFORM, self.model.notifier.name, "update",
                        {"case_id": target.case_id, "added_px": int(new_part.sum())},
                        target.case_id,
                    )
        elif new_part.sum() >= self.min_pixels:
            self._open_case(day, new_part, ref, diff)

    def _open_case(self, day, region, ref, diff):
        self._counter += 1
        r, c = ndimage.center_of_mass(region)
        rows, cols = np.nonzero(region)
        case = Case(
            case_id=f"{self.name}-C{self._counter:03d}",
            detector=self.name,
            validator=None,
            day=day,
            mask=region.copy(),
            reference=ref,
            drop=round(float(diff[region].mean()), 3),
            centroid=self.model.env.to_latlon(r, c),
            last_check_day=day,
        )
        self.model.cases[case.case_id] = case

        if not self.model.use_validation:
            # Mode baseline (tanpa MAS): detektor langsung menyimpulkan sendiri.
            case.det_vote = True
            self._finalize(case, CONFIRMED, cause="unknown")
            return

        validator = self.model.least_loaded_validator()
        case.validator = validator.name
        self.send(
            REQUEST, validator.name, "validate",
            {
                "case_id": case.case_id,
                "day": day,
                "mask": case.mask,
                "centroid_latlon": case.centroid,
                "bbox_rc": (int(rows.min()), int(cols.min()), int(rows.max()), int(cols.max())),
                "ndvi_drop": case.drop,
                "round": 0,
            },
            case.case_id,
        )

    # -- konsensus -----------------------------------------------------------
    def _check_persistence(self, day: int):
        for case in self.my_cases(PENDING):
            if case.det_vote is not None or day <= case.last_check_day:
                continue
            drop = float((case.reference - self.model.archive[day].ndvi)[case.mask].mean())
            case.det_vote = drop >= self.persist_threshold
            case.last_check_day = day
            case.evidence[f"persist_r{case.round}"] = {"day": day, "ndvi_drop": round(drop, 3)}

    def _receive_verdict(self, msg: Message):
        case = self.model.cases.get(msg.content["case_id"])
        if case is None or case.status != PENDING or msg.content["round"] != case.round:
            return
        case.val_vote = msg.content["real"]
        case.val_received = True
        case.cause = msg.content["cause"]
        case.val_confidence = msg.content["confidence"]
        case.evidence[f"thermal_r{case.round}"] = {
            k: msg.content[k] for k in ("day", "mean_anomaly", "hot_fraction", "cause")
        }

    def _try_resolve(self, case: Case):
        if case.det_vote is None or not case.val_received:
            return
        if case.det_vote and case.val_vote:
            self.send(CONFIRM, case.validator, "consensus", {"case_id": case.case_id, "cause": case.cause}, case.case_id)
            self._finalize(case, CONFIRMED, cause=case.cause)
        elif case.det_vote is False and case.val_vote is False:
            self.send(CANCEL, case.validator, "consensus", {"case_id": case.case_id}, case.case_id)
            self._finalize(case, DISMISSED, cause=case.cause)
        else:
            case.round += 1
            if case.round > self.max_rounds:
                self._finalize(case, UNCERTAIN, cause=case.cause)
                return
            # Belum sepakat: kumpulkan bukti baru dari hari berikutnya.
            case.det_vote, case.val_vote, case.val_received = None, None, False
            self.send(
                REQUEST, case.validator, "validate",
                {"case_id": case.case_id, "day": case.last_check_day, "mask": case.mask,
                 "centroid_latlon": case.centroid, "round": case.round},
                case.case_id,
            )

    def _finalize(self, case: Case, status: str, cause: str | None):
        case.status = status
        case.cause = cause
        case.decided_day = self.model.day
        if status in (CONFIRMED, UNCERTAIN):
            self.send(
                INFORM, self.model.notifier.name, "report",
                {"case_id": case.case_id, "status": status, "cause": cause},
                case.case_id,
            )


# ---------------------------------------------------------------------------
class ValidationAgent(MonitorAgent):
    """Memvalidasi wilayah curiga memakai data termal (mirip MODIS LST).
    Menghasilkan usulan (PROPOSE): nyata/tidak, penyebab, dan tingkat keyakinan."""

    role = "validation"

    def __init__(self, model, name: str, fire_anomaly=6.0, cloud_anomaly=-3.0, max_attempts=3):
        super().__init__(model, name)
        self.fire_anomaly = fire_anomaly
        self.cloud_anomaly = cloud_anomaly
        self.max_attempts = max_attempts
        self.thermal: dict[int, np.ndarray] = {}
        self.queue: list[dict] = []
        self.agreements = 0
        self.cancellations = 0

    @property
    def load(self) -> int:
        return len(self.queue) + self.model.bus.pending(self.name)

    def step(self):
        for msg in self.inbox():
            if msg.topic == "validate":
                self.queue.append({**msg.content, "requester": msg.sender, "attempts": 0})
            elif msg.performative == CONFIRM:
                self.agreements += 1
            elif msg.performative == CANCEL:
                self.cancellations += 1

        self._sync_thermal()
        remaining = []
        for req in self.queue:
            if not self._validate(req):
                req["attempts"] += 1
                if req["attempts"] >= self.max_attempts:
                    self._reply(req, real=None, cause="inconclusive", conf=0.0, anom=float("nan"), hot=0.0)
                else:
                    remaining.append(req)
        self.queue = remaining

    def _sync_thermal(self):
        for d in range(max(1, self.model.day - 15), self.model.day + 1):
            if d not in self.thermal:
                t = self.model.env.fetch_thermal(d)
                if t is not None:
                    self.thermal[d] = t

    def _validate(self, req) -> bool:
        day, mask = req["day"], req["mask"]
        ref_days = [d for d in reference_window(day) if d in self.thermal]
        if day not in self.thermal or len(ref_days) < 2:
            return False  # data termal belum lengkap -> coba lagi besok
        ref = np.median(np.stack([self.thermal[d] for d in ref_days]), axis=0)
        anom = (self.thermal[day] - ref)[mask]
        mean_anom = float(anom.mean())
        hot = float((anom > 8.0).mean())

        if mean_anom >= self.fire_anomaly or hot >= 0.3:
            conf = min(0.99, 0.6 + 0.04 * (mean_anom - self.fire_anomaly) + 0.3 * hot)
            self._reply(req, True, "fire", max(conf, 0.6), mean_anom, hot)
        elif mean_anom <= self.cloud_anomaly:
            conf = min(0.99, 0.6 + 0.05 * (self.cloud_anomaly - mean_anom))
            self._reply(req, False, "cloud", conf, mean_anom, hot)
        else:
            conf = float(np.clip(1.0 - abs(mean_anom - 2.0) / 5.0, 0.5, 0.95))
            self._reply(req, True, "logging", conf, mean_anom, hot)
        return True

    def _reply(self, req, real, cause, conf, anom, hot):
        self.send(
            PROPOSE, req["requester"], "verdict",
            {"case_id": req["case_id"], "round": req["round"], "day": req["day"], "real": real,
             "cause": cause, "confidence": round(conf, 2), "mean_anomaly": round(anom, 2),
             "hot_fraction": round(hot, 2)},
            req["case_id"],
        )


# ---------------------------------------------------------------------------
CHANNELS = {
    "fire": ("DARURAT", "Tim Pemadam Kebakaran Hutan"),
    "logging": ("TINGGI", "Polisi Hutan / Dinas Kehutanan"),
    "unknown": ("SEDANG", "Dinas Kehutanan"),
    "uncertain": ("RENDAH", "Analis GIS (tinjauan manual)"),
}


@dataclass
class Alert:
    alert_id: str
    case_id: str
    kind: str
    priority: str
    channel: str
    scene_day: int
    alert_day: int
    lat: float
    lon: float
    initial_area_ha: float  # luas saat peringatan pertama dikirim
    area_ha: float  # luas terkini (bertambah bila kebakaran meluas)
    confidence: float
    evidence: dict
    updates: list = field(default_factory=list)  # riwayat perluasan: {day, from_ha, to_ha}

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


class NotificationAgent(MonitorAgent):
    """Menerima laporan hasil konsensus, menentukan prioritas & kanal,
    lalu mengirim peringatan ke pihak berwenang (di sini: dicatat ke log)."""

    role = "notification"

    def __init__(self, model, name="notifier", ha_per_px=1.0, verbose=False):
        super().__init__(model, name)
        self.ha_per_px = ha_per_px
        self.verbose = verbose
        self.by_case: dict[str, Alert] = {}

    def step(self):
        for msg in self.inbox():
            case = self.model.cases[msg.content["case_id"]]
            if msg.topic == "report" and case.case_id not in self.by_case:
                self._alert(case, msg.content["status"])
            elif msg.topic == "update" and case.case_id in self.by_case:
                alert = self.by_case[case.case_id]
                new_area = case.area_px * self.ha_per_px
                if new_area <= alert.area_ha:
                    continue  # luas sudah tercatat (laporan & perluasan tiba di hari yang sama)
                alert.updates.append({"day": self.model.day, "from_ha": alert.area_ha, "to_ha": new_area})
                alert.area_ha = new_area
                if self.verbose:
                    u = alert.updates[-1]
                    print(
                        f"  [hari {self.model.day:3d}] UPDATE  {alert.alert_id}: area meluas "
                        f"{u['from_ha']:.0f} -> {u['to_ha']:.0f} ha"
                    )

    def _alert(self, case: Case, status: str):
        kind = "uncertain" if status == UNCERTAIN else (case.cause or "unknown")
        priority, channel = CHANNELS.get(kind, CHANNELS["unknown"])
        alert = Alert(
            alert_id=f"ALERT-{len(self.model.alerts) + 1:03d}",
            case_id=case.case_id,
            kind=kind,
            priority=priority,
            channel=channel,
            scene_day=case.day,
            alert_day=self.model.day,
            lat=round(case.centroid[0], 5),
            lon=round(case.centroid[1], 5),
            initial_area_ha=case.area_px * self.ha_per_px,
            area_ha=case.area_px * self.ha_per_px,
            confidence=case.val_confidence,
            evidence=case.evidence,
        )
        self.model.alerts.append(alert)
        self.by_case[case.case_id] = alert
        if self.verbose:
            print(
                f"  [hari {self.model.day:3d}] {alert.priority:7s} {alert.alert_id} {kind:9s} "
                f"({alert.lat:.4f}, {alert.lon:.4f}) {alert.area_ha:4.0f} ha -> {alert.channel}"
            )
