"""Evaluasi hasil sistem terhadap ground truth simulasi."""

from __future__ import annotations

import numpy as np

from .agents import CONFIRMED, DISMISSED, UNCERTAIN


def evaluate(model, min_age: int = 3) -> dict:
    """Hitung metrik deteksi.

    * recall     : porsi kejadian nyata (berumur >= min_age hari) yang terkonfirmasi
    * precision  : porsi kasus terkonfirmasi yang memang menimpa kejadian nyata
    * cause_acc  : porsi kasus terkonfirmasi-benar yang penyebabnya tepat
    * latency    : rata-rata hari dari kejadian sampai peringatan terkonfirmasi
    """
    events = model.env.events
    confirmed = [c for c in model.cases.values() if c.status == CONFIRMED]
    dismissed = [c for c in model.cases.values() if c.status == DISMISSED]
    uncertain = [c for c in model.cases.values() if c.status == UNCERTAIN]

    def best_event(case):
        # hanya kejadian yang sudah dimulai saat kasus diputuskan
        overlaps = [(int((case.mask & e.footprint).sum()), e) for e in events if e.start_day <= case.decided_day]
        overlaps = [o for o in overlaps if o[0] > 0]
        return max(overlaps, key=lambda o: o[0])[1] if overlaps else None

    matched = [(c, best_event(c)) for c in confirmed]
    true_pos = [(c, e) for c, e in matched if e is not None]
    false_pos = [c for c, e in matched if e is None]

    eligible = [e for e in events if e.start_day <= model.day - min_age]
    latencies, detected = [], 0
    for e in eligible:
        hits = [c for c in confirmed if c.decided_day >= e.start_day and (c.mask & e.footprint).any()]
        if hits:
            detected += 1
            latencies.append(min(c.decided_day for c in hits) - e.start_day)

    known_cause = [(c, e) for c, e in true_pos if c.cause in ("logging", "fire")]
    return {
        "days": model.day,
        "true_events": len(events),
        "true_logging": sum(e.kind == "logging" for e in events),
        "true_fire": sum(e.kind == "fire" for e in events),
        "cloud_episodes": len(model.env.cloud_log),
        "cases": len(model.cases),
        "confirmed": len(confirmed),
        "dismissed": len(dismissed),
        "uncertain": len(uncertain),
        "false_alarms": len(false_pos),
        "recall": detected / len(eligible) if eligible else float("nan"),
        "precision": len(true_pos) / len(confirmed) if confirmed else float("nan"),
        "cause_accuracy": (
            sum(c.cause == e.kind for c, e in known_cause) / len(known_cause) if known_cause else float("nan")
        ),
        "mean_latency_days": float(np.mean(latencies)) if latencies else float("nan"),
        "messages": len(model.bus.log),
    }
