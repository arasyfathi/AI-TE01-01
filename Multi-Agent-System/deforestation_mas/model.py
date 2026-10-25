"""Model Mesa: satu langkah = satu hari pemantauan."""

from __future__ import annotations

import mesa

from .agents import (
    CONFIRMED,
    DISMISSED,
    PENDING,
    UNCERTAIN,
    ChangeDetectionAgent,
    DataIngestionAgent,
    NotificationAgent,
    ValidationAgent,
)
from .environment import ForestEnvironment
from .messaging import MessageBus

# Urutan giliran agen tiap hari (pipeline). Pesan yang dikirim pada hari yang
# sama langsung bisa dibaca oleh agen yang gilirannya lebih belakang.
PIPELINE = (DataIngestionAgent, ChangeDetectionAgent, ValidationAgent, NotificationAgent)


class ForestMonitoringModel(mesa.Model):
    def __init__(
        self,
        size: int = 64,
        n_detectors: int = 1,
        n_validators: int = 1,
        use_validation: bool = True,
        seed: int | None = 0,
        env_kwargs: dict | None = None,
        detector_kwargs: dict | None = None,
        validator_kwargs: dict | None = None,
        verbose: bool = False,
        env=None,
    ):
        """``env``: lingkungan data apa pun yang memenuhi antarmuka ``ForestEnvironment``
        (misalnya ``GEEEnvironment``). Bila kosong, dipakai lingkungan sintetis."""
        super().__init__(rng=seed)
        self.env = env if env is not None else ForestEnvironment(size=size, seed=seed, **(env_kwargs or {}))
        size = self.env.size
        self.bus = MessageBus()
        self.archive: dict = {}  # citra yang sudah diunduh ("data lake")
        self.cases: dict = {}  # semua kasus (registry bersama)
        self.alerts: list = []
        self.use_validation = use_validation
        self.day = 0

        self.ingestion = DataIngestionAgent(self)
        bounds = [round(i * size / n_detectors) for i in range(n_detectors + 1)]
        self.detectors = [
            ChangeDetectionAgent(self, f"detector-{i + 1}", (bounds[i], bounds[i + 1]), **(detector_kwargs or {}))
            for i in range(n_detectors)
        ]
        self.validators = (
            [ValidationAgent(self, f"validator-{j + 1}", **(validator_kwargs or {})) for j in range(n_validators)]
            if use_validation
            else []
        )
        self.notifier = NotificationAgent(self, ha_per_px=getattr(self.env, "ha_per_px", 1.0), verbose=verbose)

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "day": lambda m: m.day,
                "scenes_ingested": lambda m: len(m.archive),
                "cases_total": lambda m: len(m.cases),
                "pending": lambda m: m.count_cases(PENDING),
                "confirmed_logging": lambda m: m.count_cases(CONFIRMED, "logging"),
                "confirmed_fire": lambda m: m.count_cases(CONFIRMED, "fire"),
                "confirmed_unknown": lambda m: m.count_cases(CONFIRMED, "unknown"),
                "dismissed": lambda m: m.count_cases(DISMISSED),
                "uncertain": lambda m: m.count_cases(UNCERTAIN),
                "alerts": lambda m: len(m.alerts),
                "messages_today": lambda m: m.bus.count_on(m.day),
                "true_events": lambda m: len(m.env.events),
            }
        )

    def count_cases(self, status, cause=None) -> int:
        return sum(1 for c in self.cases.values() if c.status == status and (cause is None or c.cause == cause))

    def least_loaded_validator(self) -> ValidationAgent:
        return min(self.validators, key=lambda v: v.load)

    def step(self):
        self.env.advance_day()
        self.day = self.env.day
        for agent_type in PIPELINE:
            agents = self.agents_by_type.get(agent_type)
            if agents:
                agents.do("step")
        self.datacollector.collect(self)
