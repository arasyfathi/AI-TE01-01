import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deforestation_mas import ForestMonitoringModel  # noqa: E402
from deforestation_mas.agents import CONFIRMED  # noqa: E402
from deforestation_mas.environment import ForestEnvironment  # noqa: E402
from deforestation_mas.evaluation import evaluate  # noqa: E402


def run(days=120, **kw):
    m = ForestMonitoringModel(**kw)
    for _ in range(days):
        m.step()
    return m


def test_environment_is_reproducible():
    a, b = ForestEnvironment(seed=5), ForestEnvironment(seed=5)
    for _ in range(30):
        a.advance_day()
        b.advance_day()
    assert np.array_equal(a.scenes[30].ndvi, b.scenes[30].ndvi)
    assert [(e.kind, e.start_day) for e in a.events] == [(e.kind, e.start_day) for e in b.events]


def test_clouds_only_produce_no_alerts_with_consensus():
    env = {"p_logging": 0.0, "p_fire": 0.0, "p_cloud": 0.4}
    mas = run(80, seed=3, env_kwargs=env)
    base = run(80, seed=3, env_kwargs=env, use_validation=False)
    assert mas.count_cases(CONFIRMED) == 0
    assert mas.count_cases("dismissed") > 0
    assert len(base.alerts) > 0  # tanpa validasi, awan menjadi alarm palsu


@pytest.mark.parametrize("kind,env", [
    ("logging", {"p_logging": 0.15, "p_fire": 0.0, "p_cloud": 0.0}),
    ("fire", {"p_logging": 0.0, "p_fire": 0.12, "p_cloud": 0.0}),
])
def test_cause_is_identified(kind, env):
    m = run(100, seed=1, env_kwargs=env)
    r = evaluate(m)
    assert r["recall"] >= 0.9
    assert r["precision"] == 1.0
    assert {c.cause for c in m.cases.values() if c.status == CONFIRMED} == {kind}


def test_consensus_protocol_messages():
    m = run(60, seed=2, env_kwargs={"p_logging": 0.2, "p_fire": 0.0, "p_cloud": 0.0})
    case = next(c for c in m.cases.values() if c.status == CONFIRMED)
    flow = [(msg.performative, msg.topic) for msg in m.bus.conversation(case.case_id)]
    assert flow[0] == ("request", "validate")
    assert ("propose", "verdict") in flow
    assert ("confirm", "consensus") in flow
    assert flow[-1] == ("inform", "report")


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_mas_beats_single_detector(seed):
    mas, base = evaluate(run(seed=seed)), evaluate(run(seed=seed, use_validation=False))
    assert mas["precision"] >= 0.9
    assert mas["recall"] >= 0.85
    assert mas["precision"] > base["precision"]


def test_multiple_detectors_and_validators_share_work():
    m = run(seed=4, n_detectors=3, n_validators=2)
    r = evaluate(m)
    assert r["recall"] >= 0.85 and r["precision"] >= 0.9
    used_detectors = {c.detector for c in m.cases.values()}
    used_validators = {c.validator for c in m.cases.values()}
    assert len(used_detectors) >= 2 and len(used_validators) == 2


def test_survives_unreliable_downloads():
    m = run(90, seed=6, env_kwargs={"download_fail_prob": 0.4, "thermal_dropout_prob": 0.3})
    r = evaluate(m)
    assert len(m.archive) >= 85
    assert not math.isnan(r["recall"]) and r["recall"] >= 0.8
